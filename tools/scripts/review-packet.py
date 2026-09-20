#!/usr/bin/env python3
"""Write the packet an independent review starts from.

The notes and the code are not always in the same repo: project-os-dev holds the
notes for code that lives in project-os. `--repo-root` finds the note, and
`--code-root` is where the commits and the diff come from. Without it the diff
filter strips everything such a feature touched and the packet arrives empty,
which is now an error rather than a blank section (FEAT-0034 review, 2026-09-20).

A review used to start from folder names and a request to "reconstruct the
scope from the notes". Measured on 2026-09-18 (project-os-dev
REFERENCE-REVIEW-COST-AND-ISSUE-DEBT), a reviewer then spent 30-45 tool calls
finding out what had changed before it ran a single test. This script hands it
the answer instead: one Markdown file holding the feature's acceptance criteria,
the source diff of its commits, the tests those commits touched, and the
author's last full test run. The packet is the review's scope
(tools/skills/independent-review/SKILL.md).

Round two (--round 2 --since <commit>) holds only round one's review section
from the feature note and the source diff since that commit: round two checks
fixes and nothing else (QUALITY.md, "A gate runs at most two rounds").

Usage:
  review-packet.py FEAT-0001 [--range A..B] [--claim TEXT]... [--out PATH]
  review-packet.py FEAT-0001 --round 2 --since <commit> [--out PATH]

Commits are found by message: every commit reachable from HEAD whose message
names the feature or one of its tasks. --range replaces that search when the
messages do not name them. Notes (docs/) and SNAPSHOT.yaml are left out of the
diff; the reviewer reads the notes it needs by name.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

#: A diff longer than this is flagged, so the author splits the review or
#: accepts its size knowingly.
LARGE_DIFF_LINES = 1500
#: A diff up to this size is put in the packet itself. A longer one goes in a
#: companion .diff file with a per-file index of line ranges, so the reviewer
#: reads the part it needs: every turn re-reads the whole context, and a
#: 5,500-line diff read at once is 60-70k tokens carried by every later turn.
INLINE_DIFF_LINES = 400
MAX_CLAIMS = 3


def _budgets():
    """The budgets the hook enforces, read from the hook (project-os-dev REQ-0027).

    The packet prints the budget and the hook applies it. Two copies of 40 drift
    the day someone changes one, and a packet that promises a budget nobody
    enforces is worse than no number at all. `PROJECT_OS_REVIEW_BUDGET` and its
    round-two twin are honoured here for the same reason. If the hook cannot be
    read the script stops: inventing a number here is what it exists to prevent.
    """
    hook = Path(__file__).resolve().parent.parent / "adapters" / "claude-code" / "hooks" / "review-budget.py"
    try:
        spec = importlib.util.spec_from_file_location("_review_budget", hook)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.budgets()
    except Exception as exc:
        # No fallback number. A literal here was a second copy of the budget,
        # and the failure it invites is the one this function exists to stop:
        # with PROJECT_OS_REVIEW_BUDGET=30 and the hook unreadable, the packet
        # promised 40 while the hook enforced 30 (FEAT-0034 round two).
        fail("cannot read the review budget from %s (%s).\n"
             "  The hook holds the budget and this script reads it; there is no default here on purpose." % (hook, exc))


ROUND_ONE_BUDGET, ROUND_TWO_BUDGET = _budgets()
#: Notes are excluded from a packet's diff; the underscore directories are not
#: notes. `docs/__templates__/` is the scaffold every note is made from, so a
#: change to it is a source change. Excluding all of `docs/` dropped commit
#: 1f6dff4's only source file out of FEAT-0034's own round-two packet and showed
#: the reviewer a test with nothing behind it (2026-09-20). The glob keeps
#: `docs/__templates__` and `docs/__bases__` and drops every note directory.
#: Both forms are needed: git's glob `*` does not cross a `/`, so the first
#: drops `docs/PHASES.md` and the second drops `docs/features/x/FEAT-1.md`.
EXCLUDE = [":(exclude,glob)docs/[!_]*", ":(exclude,glob)docs/[!_]*/**",
           ":(exclude)SNAPSHOT.yaml"]
#: Generated and translated files. They are large, a reviewer cannot judge
#: them by reading, and on your-trainer's FEAT-0107 they were a fifth of the
#: diff (a Room schema, an .xcstrings catalogue, eight translated strings.xml).
#: The packet lists them by name, so the reviewer still knows they changed.
GENERATED = [
    "**/schemas/**/*.json", "**/*.xcstrings", "**/values-*/strings.xml",
    "**/*.lock", "**/package-lock.json", "**/*.pbxproj", "**/*.min.js", "**/dist/**",
]
EXCLUDE_ALL = EXCLUDE + [":(exclude,glob)%s" % g for g in GENERATED]
TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|androidTest|testFixtures)/"
    r"|(^|/)test_[^/]+\.py$|_test\.[a-z]+$|\.test\.[a-z]+$|Tests?\.(kt|swift|java)$"
)


def fail(msg):
    print("review-packet: " + msg, file=sys.stderr)
    sys.exit(1)


def git(root, *args):
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if out.returncode != 0:
        fail("git %s failed: %s" % (" ".join(args[:2]), out.stderr.strip()))
    return out.stdout


def frontmatter(text):
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[4:end] if end != -1 else ""


def fm_ids(fm, key, prefix):
    """IDs of one kind named in a frontmatter field, list or scalar."""
    m = re.search(r"^%s:\s*(.*)$" % re.escape(key), fm, re.M)
    return re.findall(r"\b%s-\d+" % prefix, m.group(1)) if m else []


def section(text, *headings):
    """The body of the first `## <heading>` present, without the heading."""
    for heading in headings:
        m = re.search(r"^## %s\s*$(.*?)(?=^## |\Z)" % re.escape(heading), text, re.M | re.S)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def find_note(root, note_id):
    hits = sorted((root / "docs").rglob("%s-*.md" % note_id))
    return hits[0] if hits else None


def commits_for(root, ids):
    # Matched on the subject line only. A body that mentions the feature in
    # passing ("the ledger says what 2.2.0 owes ... FEAT-0107") is another
    # piece of work, and on FEAT-0107 such commits roughly doubled the diff.
    # git's --grep has no \b, so the subject is checked again here.
    log = git(root, "log", "--format=%H%x09%s", "HEAD")
    exact = re.compile(r"\b(%s)\b" % "|".join(re.escape(i) for i in ids))
    rows = []
    for line in log.splitlines():
        if line.strip():
            sha, subject = line.split("\t", 1)
            if exact.search(subject):
                rows.append([sha, subject])
    return list(reversed(rows))  # oldest first, the order the work was done


def source_diff_of(root, sha):
    return git(root, "show", "--format=", "--unified=3", sha, "--", ".", *EXCLUDE_ALL)


def changed_files(diff):
    return sorted(set(re.findall(r"^\+\+\+ b/(.+)$", diff, re.M)))


def ci_suite_command(root):
    snap = root / "SNAPSHOT.yaml"
    if not snap.is_file():
        return ""
    m = re.search(r"^\s+suite_command:\s*[\"']?(.*?)[\"']?\s*$", snap.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


def diff_index(diff):
    """(file, first line, last line) for each file section of `diff`, 1-based."""
    rows, lines = [], diff.split("\n")
    starts = [i for i, l in enumerate(lines) if l.startswith("diff --git ")]
    for n, i in enumerate(starts):
        end = (starts[n + 1] if n + 1 < len(starts) else len(lines)) - 1
        f = re.search(r" b/(.+)$", lines[i]).group(1)
        rows.append((f, i + 1, end + 1))
    return rows


def diff_block(diff, diff_path, empty):
    if not diff.strip():
        return [empty, ""]
    if diff.count("\n") <= INLINE_DIFF_LINES:
        return ["```diff", diff.rstrip(), "```", ""]
    out = ["The diff is %d lines, so it is in `%s`, not here. Read one file's part at a time, with `sed -n '<first>,<last>p'`:" % (diff.count("\n"), diff_path), "",
           "| File | Lines in the .diff | Size |", "|---|---|---|"]
    for f, a, b in diff_index(diff):
        out.append("| `%s` | %d-%d | %d |" % (f, a, b, b - a + 1))
    return out + [""]


def build(root, feat_id, rng, claims, round_no, since, diff_path, code_root=None):
    note = find_note(root, feat_id)
    if not note:
        fail("no note found for %s under docs/" % feat_id)
    text = note.read_text(encoding="utf-8")
    fm = frontmatter(text)
    title = (re.search(r"^title:\s*[\"']?(.*?)[\"']?\s*$", fm, re.M) or [None, feat_id])[1]
    goal = (re.search(r"^goal:\s*[\"']?(.*?)[\"']?\s*$", fm, re.M) or [None, ""])[1]
    budget = ROUND_TWO_BUDGET if round_no == 2 else ROUND_ONE_BUDGET
    out = ["# Review packet: %s, round %d" % (feat_id, round_no), "",
           "**%s**" % title, ""]
    if goal:
        out += [goal, ""]
    cr = code_root or root
    out += ["- Feature note: `%s`" % note.relative_to(root),
            "- Budget: %d tool calls. The procedure is `tools/skills/independent-review/SKILL.md`." % budget,
            "- This packet is the review's scope. Read code outside it only when a line in this diff leads there.", ""]
    if cr != root:
        out += ["- The notes are in `%s`; the code this feature changed is in `%s`, and every commit and diff below comes from there." % (root, cr), ""]

    if round_no == 2:
        findings = section(text, "Review", "Independent review")
        if not findings:
            fail("round two needs round one's findings under '## Review' in %s" % note.relative_to(root))
        diff = git(cr, "diff", "--unified=3", "%s..HEAD" % since, "--", ".", *EXCLUDE_ALL)
        out += ["## Round one's findings", "",
                "Answer *fixed* or *not fixed* for each blocking finding, with the command that shows it. Raise no new findings.", "",
                findings, "",
                "## The fixes: source diff since `%s`" % since, ""]
        out += diff_block(diff, diff_path, "(no source change since %s)" % since)
        return "\n".join(out), diff

    tasks = fm_ids(fm, "tasks", "TASK")
    reqs = fm_ids(fm, "requirements", "REQ")
    tests = fm_ids(fm, "tests", "TST")
    for task in tasks:
        tnote = find_note(root, task)
        if tnote:
            tests += fm_ids(frontmatter(tnote.read_text(encoding="utf-8")), "tests", "TST")
    # ADR-0032: a test names what it verifies in its own `covers:`, and a
    # feature does not list its tests. The older task-side `tests:` is read above.
    covered = re.compile(r"\b(%s)\b" % "|".join(re.escape(i) for i in [feat_id] + tasks))
    for tnote in (root / "docs").rglob("TST-*.md"):
        tfm = frontmatter(tnote.read_text(encoding="utf-8"))
        m = re.search(r"^covers:\s*(.*)$", tfm, re.M)
        if m and covered.search(m.group(1)):
            tests.append(re.match(r"TST-\d+", tnote.name).group(0))

    out += ["## Claims to check", "",
            "Give each claim *holds*, *refuted* (with the command and what it printed) or *not checked*.", "",
            "### Acceptance criteria of %s" % feat_id, "",
            section(text, "Acceptance", "Acceptance Criteria") or "(the feature note states none: that is a finding)", ""]
    # The note's Scope says what the feature delivers, and it can promise
    # behaviour no criterion states. Measured on a known review (project-os-dev
    # TASK-0130): a reviewer given only the criteria missed a promised
    # behaviour the Scope named, so the Scope is carried too.
    scope = section(text, "Scope")
    if scope:
        out += ["### What the note's Scope says the feature delivers", "",
                "Check each behaviour here that no criterion above already covers.", "", scope, ""]
    for req in reqs:
        rnote = find_note(root, req)
        if rnote:
            out += ["### Acceptance criteria of %s" % req, "",
                    section(rnote.read_text(encoding="utf-8"), "Acceptance Criteria", "Acceptance") or "(none stated)", ""]
    if tests:
        out += ["### Linked tests: does each one fail when the behaviour it guards is broken?", ""]
        out += ["- %s" % t for t in sorted(set(tests))] + [""]
    out += ["### The author's claims", ""]
    out += ["- %s" % c for c in claims] if claims else ["(none)"]
    out += [""]

    out += ["## The author's last full test run", ""]
    verification = section(text, "Verification")
    out += [verification or "(not recorded: the feature note has no `## Verification` section. Run the targeted tests only; say in the report that the full-suite result was missing.)", ""]
    suite = ci_suite_command(root)
    if suite:
        out += ["This repo's full suite: `%s`. Do not re-run it." % suite, ""]

    if rng:
        commits = [[c, s] for c, s in (l.split("\t", 1) for l in git(cr, "log", "--reverse", "--format=%H%x09%s", rng).splitlines() if l)]
        diff = git(cr, "diff", "--unified=3", rng, "--", ".", *EXCLUDE_ALL)
    else:
        commits = commits_for(cr, [feat_id] + tasks)
        if not commits:
            fail("no commit in %s reachable from HEAD names %s or its tasks; pass --range A..B, or --code-root if the code is in another repo" % (cr, feat_id))
        diff = "".join(source_diff_of(cr, c) for c, _ in commits)

    shas = [c for c, _ in commits] if not rng else []
    left_out = set()
    for c in shas:
        left_out |= set(git(cr, "show", "--format=", "--name-only", c, "--", *[":(glob)%s" % g for g in GENERATED]).split())
    if rng:
        left_out |= set(git(cr, "diff", "--name-only", rng, "--", *[":(glob)%s" % g for g in GENERATED]).split())
    files = changed_files(diff)
    test_files = [f for f in files if TEST_PATH.search(f)]
    out += ["## Commits", ""] + ["- `%s` %s" % (c[:10], s) for c, s in commits] + [""]
    out += ["## Files changed (source only)", ""] + ["- `%s`%s" % (f, "  (test)" if f in test_files else "") for f in files]
    if left_out:
        out += ["", "Generated or translated, changed but left out of the diff:"] + ["- `%s`" % f for f in sorted(left_out)]
    out += ["", "## Source diff", ""] + diff_block(diff, diff_path, "(these commits change no source outside docs/)")
    return "\n".join(out), diff


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("feature")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--code-root", default=None,
                    help="Repo holding the code, when the notes live elsewhere (project-os-dev is the notes repo for template code)")
    ap.add_argument("--allow-empty-diff", action="store_true",
                    help="Accept a packet with no source diff, for a feature whose work really is documentation")
    ap.add_argument("--range", dest="rng")
    ap.add_argument("--claim", action="append", default=[])
    ap.add_argument("--round", type=int, choices=(1, 2), default=1)
    ap.add_argument("--since")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"FEAT-\d+", args.feature):
        fail("expected a feature ID such as FEAT-0001, got %r" % args.feature)
    if len(args.claim) > MAX_CLAIMS:
        fail("at most %d author claims; the review checks the acceptance criteria first" % MAX_CLAIMS)
    if args.round == 2 and not args.since:
        fail("--round 2 needs --since <commit>, the commit round one reviewed")
    root = Path(args.repo_root).resolve()
    code_root = Path(args.code_root).resolve() if args.code_root else None
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / (
        "review-packet-%s-r%d.md" % (args.feature, args.round))
    diff_path = out.with_suffix(".diff")
    packet, diff = build(root, args.feature, args.rng, args.claim, args.round, args.since, diff_path, code_root)
    if not diff.strip() and not args.allow_empty_diff:
        fail("the packet has no source diff, so a reviewer told to treat it as the scope would have nothing to read.\n"
             "  If this feature's code lives in another repo, pass --code-root <that repo>.\n"
             "  If its work really is documentation only, pass --allow-empty-diff and say so in the brief.\n"
             "  A silent empty diff sent four reviewers to read prose in place of code (project-os-dev FEAT-0034, 2026-09-20).")
    out.write_text(packet, encoding="utf-8")
    if diff.count("\n") > INLINE_DIFF_LINES:
        diff_path.write_text(diff, encoding="utf-8")
    elif diff_path.exists():
        diff_path.unlink()
    lines = diff.count("\n")
    if lines > LARGE_DIFF_LINES:
        sizes = {}
        for f, body in re.findall(r"^diff --git a/\S+ b/(\S+)\n(.*?)(?=^diff --git |\Z)", diff, re.M | re.S):
            sizes[f] = sizes.get(f, 0) + body.count("\n")
        top = ", ".join("%s (%d)" % kv for kv in sorted(sizes.items(), key=lambda kv: -kv[1])[:5])
        print("review-packet: warning: the diff is %d lines (over %d). Largest: %s. Split the review or accept the size."
              % (lines, LARGE_DIFF_LINES, top), file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
