#!/usr/bin/env python3
"""Run an independent review pass with a NON-Claude model (FEAT-0018).

QUALITY.md requires a different model family or a human. Claude Code subagents
can only pin Claude models, so every review this fleet has recorded is
same-family harm reduction -- the notes say so, but the gate has never actually
been satisfied. This runs the reviewer outside Claude.

Design notes, in the order they matter:

1. THE REVIEWER NEEDS A SHELL. Five same-family rounds on the ISS-0011 guard
   found real defects only because the reviewer *executed*: induced mutations
   and re-ran --self-check, swept PYTHONHASHSEED across twelve values to prove
   a check was nondeterministic, found a silently doubled file by comparing
   line counts against a known-good commit. None of that is reachable by
   reading a diff. So the target is an agent CLI with tool access, not a chat
   completion.

2. ISOLATION. The reviewer works in a detached git worktree and may wreck it,
   which is what lets it test hypotheses by breaking things. Same primitive
   project-os-bench needs for candidate runs (FEAT-0001/TASK-0002) --
   deliberately one component, not two.

3. NO AUTO-STAMPING. This never writes review_verdict into a note.
   independent-review/SKILL.md rule 2: a verdict is transcribed from what the
   review returned, never anticipated. review_verdict is also the field
   ADR-0011 gates close-out on, so a script that writes back whatever came out
   makes the gate self-certifying through a longer pipe. It emits JSON; a human
   reads it and records the outcome.

4. A FINDING WITHOUT A REPRO IS NOT A FINDING. Enforced in the schema.
   Cross-family review buys DEcorrelation, not accuracy -- a reviewer weaker at
   this task produces plausible findings that cost real time to refute. The
   filter is what keeps that cost below the benefit.

Usage:
  review-external.py --repo ~/Dev/repos/project-os-dev \\
      --note ISS-0011 --note TST-0002 --rev 12a7c70..HEAD \\
      --task task.md --out verdict.json [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

#: Agent CLIs that run headless with tool access. Value is argv; {prompt} is
#: substituted. Model-agnostic on purpose -- the same runner is the benchmark's
#: candidate adapter, and a benchmark with one model measures nothing.
RUNNERS = {
    "kimi":   ["kimi", "-p", "{prompt}"],
    # `--sandbox workspace-write` matters and was learned the hard way: the
    # default read-only sandbox left Codex unable to mutate the file it was
    # reviewing, so it attacked by injecting globals instead. That still found
    # real defects, but it is not the same attack surface a Claude Code
    # subagent gets, and comparing the two without it measures the sandbox.
    # The reviewer works in a throwaway worktree; write access there is the
    # point.
    # Two flags, both learned by watching a run do nothing for 20 minutes.
    #
    # `--sandbox workspace-write`: the default read-only sandbox left Codex
    # unable to mutate the file it was reviewing, so it attacked by injecting
    # globals instead. Real findings, but not the attack surface a Claude Code
    # subagent gets -- comparing them without this measures the sandbox.
    #
    # `approval_policy="never"`: workspace-write alone HANGS. `codex exec` has
    # no --ask-for-approval flag, so it blocks on an approval prompt it cannot
    # display without a TTY: 80ms of CPU over 20 minutes, no child processes,
    # no output, and an exit code that never comes. Nothing in the output says
    # "waiting" -- the failure looks exactly like a slow review.
    "codex":  ["codex", "exec", "--sandbox", "workspace-write",
               "-c", 'approval_policy="never"', "{prompt}"],
    "gemini": ["gemini", "-p", "{prompt}"],
    # Claude entries exist for two legitimate uses and one illegitimate one.
    #
    #  Legitimate: (a) smoke-testing this runner end to end without a new
    #  dependency, and (b) MEASURING the premise QUALITY.md rests on -- that a
    #  fresh session of the authoring model is not independent because it
    #  reproduces the same blind spots. That premise has never been tested in
    #  this fleet, and it is testable: give clean-context Opus the identical
    #  prompt a different-family reviewer gets, and compare.
    #
    #  Illegitimate: recording the result as an independent review when the
    #  author was also Claude. Same family is same family however clean the
    #  context; a measurement of the rule is not an exemption from it.
    "claude-opus":  ["claude", "-p", "--model", "opus",
                     "--dangerously-skip-permissions", "{prompt}"],
    "claude-fable": ["claude", "-p", "--model", "claude-fable-5",
                     "--dangerously-skip-permissions", "{prompt}"],
}

#: Runners whose verdict must never be recorded as an independent review,
#: because they share a family with the fleet's authoring model.
SAME_FAMILY_AS_AUTHOR = frozenset({"claude-opus", "claude-fable"})

VERDICT_SCHEMA = """{
  "verdict": "approved" | "changes-requested",
  "reviewer": "<the model you are, e.g. model:kimi-k3>",
  "summary": "<2-4 sentences: what you attacked, what survived>",
  "findings": [
    {
      "title": "<one line>",
      "severity": "high" | "medium" | "low",
      "claim_refuted": "<the exact sentence or behaviour you are refuting>",
      "repro": "<a command, runnable from the repo root, that demonstrates it>",
      "observed": "<what that command actually printed when you ran it>"
    }
  ],
  "attacks_that_failed": ["<things you tried that did NOT break it>"]
}"""


def sh(args, cwd=None, check=True, timeout=120):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True,
                          text=True, timeout=timeout)


def find_note(repo: pathlib.Path, note_id: str):
    """Locate a note by ID: filename first, then a frontmatter `id:` line."""
    docs = repo / "docs"
    if not docs.is_dir():
        return None
    for p in sorted(docs.rglob("%s*.md" % note_id)):
        return p
    pat = re.compile(r"^id:\s*%s\s*$" % re.escape(note_id), re.MULTILINE)
    for p in sorted(docs.rglob("*.md")):
        try:
            head = p.read_text(encoding="utf-8")[:1200]
        except (OSError, UnicodeDecodeError):
            continue
        if pat.search(head):
            return p
    return None


def extract_json(raw: str):
    """Last balanced {...} that parses. Agent CLIs wrap answers in chatter."""
    found, depth, start = None, 0, None
    in_str = esc = False
    for i, ch in enumerate(raw):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0:
                try:
                    found = json.loads(raw[start:i + 1])
                except json.JSONDecodeError:
                    pass
    return found


def build_prompt(worktree, notes, diff, task_text, skill_text):
    parts = [
        # Deliberately says nothing about which model the reviewer is, or how
        # it relates to the author. Every runner must receive a byte-identical
        # prompt or a cross-model comparison measures the prompt instead of the
        # models -- and telling a Claude reviewer it is "a different family"
        # would also be false.
        "You are performing an INDEPENDENT REVIEW for the project-os "
        "documentation system. You are reviewing work you did not write, with "
        "no access to its author's reasoning -- only the notes and the diff. "
        "If the change cannot be justified from those alone, that is itself a "
        "finding.",
        "",
        "## Your working copy",
        "",
        "You are in a detached git worktree at `%s`. It is a scratch copy -- "
        "MUTATE IT FREELY. Break things deliberately to test whether the checks "
        "catch them, then restore. Nothing you do here touches the real repo, "
        "and a review that only reads files is a weak review." % worktree,
        "",
        "## How this review is judged",
        "",
        "Do not summarise the diff. Do not confirm the change looks reasonable. "
        "Your job is to REFUTE: find inputs or states where the change is wrong, "
        "and find guards that would still pass if the thing they guard were "
        "broken. A test that cannot fail does not guard.",
        "",
        "**A finding without a reproduction is not a finding.** Every entry in "
        "`findings` must carry a `repro` command you actually ran and the "
        "`observed` output you actually saw. If you cannot produce one, leave "
        "it out. Report the attacks that failed too -- those are evidence that "
        "the thing holds, and they are worth as much as a finding.",
        "",
        "## The review contract (project-os QUALITY.md / independent-review)",
        "",
        skill_text.strip(),
        "",
        "## The task",
        "",
        task_text.strip(),
        "",
    ]
    if notes:
        parts += ["## Notes under review", ""]
        for nid, rel, body in notes:
            parts += ["### %s -- `%s`" % (nid, rel), "", "```markdown",
                      body.strip(), "```", ""]
    if diff:
        parts += ["## Diff under review", "", "```diff", diff.strip(), "```", ""]
    parts += [
        "## Output",
        "",
        "Return ONE JSON object and nothing else -- no prose before or after, "
        "no markdown fence. Schema:",
        "",
        VERDICT_SCHEMA,
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--note", action="append", default=[],
                    help="note ID to include (repeatable)")
    ap.add_argument("--rev", default="", help="git range for the diff under review")
    ap.add_argument("--paths", action="append", default=[],
                    help="limit the diff to these paths (repeatable)")
    ap.add_argument("--task", default="",
                    help="path to a file with the review task, or literal text")
    ap.add_argument("--model", default="kimi", choices=sorted(RUNNERS))
    ap.add_argument("--out", default="verdict.json")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--dry-run", action="store_true",
                    help="assemble and save the prompt; invoke no model")
    ap.add_argument("--keep-worktree", action="store_true")
    args = ap.parse_args()

    repo = pathlib.Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        print("error: %s is not a git repo" % repo, file=sys.stderr)
        return 2

    skill = repo / "tools" / "skills" / "independent-review" / "SKILL.md"
    skill_text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    if not skill_text:
        print("warn: independent-review SKILL.md not found; prompt will lack "
              "the review contract", file=sys.stderr)

    task_text = args.task
    tp = pathlib.Path(args.task).expanduser()
    if args.task and tp.is_file():
        task_text = tp.read_text(encoding="utf-8")

    notes = []
    for nid in args.note:
        p = find_note(repo, nid)
        if p is None:
            print("warn: note %s not found" % nid, file=sys.stderr)
            continue
        notes.append((nid, p.relative_to(repo).as_posix(),
                      p.read_text(encoding="utf-8")))

    diff = ""
    if args.rev:
        cmd = ["git", "diff", args.rev]
        if args.paths:
            cmd += ["--"] + args.paths
        diff = sh(cmd, cwd=repo).stdout

    # Isolation. Created even for a dry run, so the prompt names a path that
    # exists and the setup path is exercised without a subscription.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="review-"))
    wt = tmp / "tree"
    head = sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    sh(["git", "worktree", "add", "--detach", str(wt), head], cwd=repo)

    out = pathlib.Path(args.out)
    try:
        prompt = build_prompt(wt, notes, diff, task_text, skill_text)
        print("prompt %d chars (~%dk tokens) | %d note(s) | diff %d lines | wt %s"
              % (len(prompt), len(prompt) // 4000, len(notes),
                 diff.count("\n"), wt), file=sys.stderr)

        if args.dry_run:
            out.with_suffix(".prompt.md").write_text(prompt, encoding="utf-8")
            print("dry run: prompt -> %s" % out.with_suffix(".prompt.md"),
                  file=sys.stderr)
            return 0

        argv = [a.replace("{prompt}", prompt) for a in RUNNERS[args.model]]
        if shutil.which(argv[0]) is None:
            print("error: %r is not installed or not on PATH" % argv[0],
                  file=sys.stderr)
            return 3

        if args.model in SAME_FAMILY_AS_AUTHOR:
            print("NOTE: %s shares a family with the fleet's authoring model. "
                  "Useful for smoke-testing this runner and for measuring the "
                  "independence premise itself; NOT admissible as the "
                  "QUALITY.md independent review." % args.model, file=sys.stderr)
        print("running %s (timeout %ds) ..." % (argv[0], args.timeout),
              file=sys.stderr)
        try:
            # stdin=DEVNULL is load-bearing, not tidiness. `codex exec`
            # documents "if stdin is piped and a prompt is also provided, stdin
            # is appended as a <stdin> block" -- so with an inherited pipe that
            # never reaches EOF it blocks FOREVER, before any network call.
            # Observed: 60ms of CPU over 5 minutes, zero TCP connections, no
            # output, no exit. Indistinguishable from a slow review unless you
            # go looking at CPU time. Every agent CLI here reads stdin the same
            # way, so this belongs on the call, not on one runner's argv.
            r = subprocess.run(argv, cwd=wt, capture_output=True, text=True,
                               timeout=args.timeout, stdin=subprocess.DEVNULL,
                               env={**os.environ, "NO_COLOR": "1"})
        except subprocess.TimeoutExpired:
            print("error: reviewer timed out after %ds" % args.timeout,
                  file=sys.stderr)
            return 4

        raw = (r.stdout or "").strip()
        out.with_suffix(".raw.txt").write_text(
            raw + "\n\n--- stderr ---\n" + (r.stderr or ""), encoding="utf-8")

        verdict = extract_json(raw)
        if verdict is None:
            print("error: no JSON verdict in output; raw saved to %s"
                  % out.with_suffix(".raw.txt"), file=sys.stderr)
            return 5

        # The filter. A decorrelated but weaker reviewer costs more than it
        # saves if unreproduced findings reach a human's triage queue.
        kept, dropped = [], []
        for f in verdict.get("findings") or []:
            ok = (f.get("repro") or "").strip() and (f.get("observed") or "").strip()
            (kept if ok else dropped).append(f)
        verdict["findings"] = kept
        if dropped:
            verdict["dropped_unreproduced"] = dropped

        out.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        print("\nverdict: %s | reviewer: %s | findings: %d kept, %d dropped"
              % (verdict.get("verdict"), verdict.get("reviewer"),
                 len(kept), len(dropped)), file=sys.stderr)
        for f in kept:
            print("  [%s] %s" % (f.get("severity", "?"), f.get("title")),
                  file=sys.stderr)
        for f in dropped:
            print("  (dropped, no repro) %s" % f.get("title"), file=sys.stderr)
        print("\nverdict is NOT stamped into any note -- transcribe it by hand "
              "(independent-review SKILL.md rule 2).", file=sys.stderr)
        return 0
    finally:
        if args.keep_worktree:
            print("worktree kept: %s" % wt, file=sys.stderr)
        else:
            sh(["git", "worktree", "remove", "--force", str(wt)], cwd=repo,
               check=False)
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
