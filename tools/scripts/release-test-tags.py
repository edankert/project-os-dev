#!/usr/bin/env python3
"""Rewrite quoted procedure expectation lines as tag-only lines (ADR-0049, ISS-0088).

A procedure step used to quote a check's `## Expect` line word for word, so
rewriting the check broke every procedure that quoted it. A line may now be only
its tags, `` - `TST-0480` ``, and `release-test.py` prints the check's current
Expect lines in its place. This script makes that change where it loses
nothing, and leaves every other line as written:

  one line whose quote is exactly what its tag would print
      -> the tags alone. That is a check with one Expect line, or `.N` on a
      check that pairs step N with Expect line N (`release-test.py`,
      `expect_for`), quoting line N
  one step quoting every Expect line of a check, all with the same tags
      -> one tag-only line where the first of them was

Any other line stays quoted: its tag-only form would print more than the
author wrote. A line whose
tags name several checks stays quoted too, for the same reason. Each kept line
is reported with its reason.

"What its tag would print" is counted on every platform the step runs on: a
check may mark an Expect line `[android]` or `[ios]` (project-os-dev
REQ-0034), and a quote is only lossless when each of those platforms' pages
would print exactly the quoted words.

--all converts the rest as well, because a procedure line is its tags alone
(project-os-dev ADR-0050 D2; `release-test.py --check` warns about every
quoted line). Each quoted line becomes its tags; a tag already given earlier in
the same step is not given again, and a line left with none is removed. An
action line that carries tags keeps its words and gets its tags on a line of
their own under it. Every line whose page text changes is reported with what
it will print instead.

--refresh does the other half, for a line that must stay quoted. When a check's
Expect line has been reworded, every procedure quoting the old words fails. For each
such quote, it finds the check's last version in git (the working tree's edit
against HEAD, then older commits) whose Expect had the quoted line, and
rewrites the quote with the current line at the same position. It does so only
when the Expect section has as many lines as it had then; otherwise it reports
the line for a person to re-quote.

Usage:
    release-test-tags.py [--repo-root .]      # dry run: what would change, and what stays
    release-test-tags.py --apply
    release-test-tags.py --refresh [--apply]  # re-quote lines a reworded check broke
    release-test-tags.py --all [--apply]      # every quoted line to tags alone
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def release_test_module():
    spec = importlib.util.spec_from_file_location("_release_test_for_tags", HERE / "release-test.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _wants(rt, check, tags, platforms) -> list[list[str]]:
    """What the tags would print, once per platform the step runs on."""
    out = []
    for platform in platforms:
        want: list[str] = []
        for _c, n in tags:
            want += [x for x in rt.expect_for(check, n, platform) if x not in want]
        out.append(want)
    return out


def plan(repo_root: Path, everything: bool = False):
    rt = release_test_module()
    docs = repo_root / "docs"
    checks = rt.load_checks(docs, repo_root=repo_root)
    known = rt.platforms(docs) or [""]
    out = []
    for procedure in rt.load_procedures(docs, repo_root):
        path = repo_root / procedure.path
        edits, kept = [], []
        for step in procedure.steps:
            if everything:
                convert_all(rt, step, checks, sorted(step.platforms) or known, edits, kept)
                continue
            runs_on = sorted(step.platforms) or known
            quoted = [e for e in step.expectations if e.quote and e.raw != step.body[0]]
            by_check: dict[tuple, list] = {}
            for e in quoted:
                owners = {c for c, _n in e.tags}
                if len(owners) != 1:
                    kept.append((step.number, e.raw, "its tags name %d checks" % len(owners)))
                    continue
                by_check.setdefault((next(iter(owners)), tuple(e.tags)), []).append(e)
            for (cid, tags), lines in by_check.items():
                check = checks.get(cid)
                if check is None:
                    kept.append((step.number, lines[0].raw, "%s is not an acceptance check here" % cid))
                    continue
                wants = _wants(rt, check, tags, runs_on)
                have = [e.quote for e in lines]
                if not rt.expect_text(check):
                    for e in lines:
                        kept.append((step.number, e.raw, "%s states no Expect text to print" % cid))
                    continue
                if any(q not in rt.expect_text(check) for q in have):
                    for e in lines:
                        kept.append((step.number, e.raw, "it does not quote %s's current Expect" % cid))
                    continue
                differs = [(p, w) for p, w in zip(runs_on, wants) if sorted(set(have)) != sorted(w)]
                if differs:
                    platform, want = differs[0]
                    for e in lines:
                        kept.append((step.number, e.raw, "%s's tags print %d Expect line(s)%s, %s, and "
                                     "this step quotes %d" % (cid, len(want),
                                                              " on %s" % platform if platform else "",
                                                              "; ".join(repr(w) for w in want),
                                                              len(set(have)))))
                    continue
                first = lines[0].raw
                m = rt._MARKER_RE.match(first)
                prefix = first[:m.end()] if m else first[:len(first) - len(first.lstrip())]
                tag_text = " ".join("`%s%s`" % (c, "." + n if n else "") for c, n in tags)
                edits.append((first, prefix + tag_text, [e.raw for e in lines[1:]]))
        if edits or kept:
            out.append({"path": path, "shown": procedure.path, "edits": edits, "kept": kept})
    return out


def convert_all(rt, step, checks, runs_on, edits, kept) -> None:
    """Every quoted line of one step to its tags alone (`--all`).

    ``kept`` receives, for each converted line whose page text changes, what
    the page will print instead, so the author can see what the conversion
    did; nothing is left quoted.
    """
    head = step.body[0] if step.body else ""
    given: set = set()
    for e in step.expectations:
        if not e.quote:
            given.update(e.tags)
            continue
        new_tags = [tag for tag in e.tags if tag not in given]
        given.update(e.tags)
        tag_text = " ".join("`%s%s`" % (c, "." + n if n else "") for c, n in new_tags)
        if e.raw == head:
            found = rt._STEP_RE.match(head)
            indent = " " * (head.index(found.group(2)) if found else 3)
            action = rt._TAG_RE.sub("", head).rstrip()
            new = action + ("\n%s- %s" % (indent, tag_text) if new_tags else "")
            edits.append((head, new, []))
            kept.append((step.number, head, "the action line's tags moved to a line of their own"))
            continue
        if not new_tags:
            edits.append((e.raw, None, []))
            continue
        m = rt._MARKER_RE.match(e.raw)
        prefix = e.raw[:m.end()] if m else e.raw[:len(e.raw) - len(e.raw.lstrip())]
        edits.append((e.raw, prefix + tag_text, []))
        for platform in runs_on:
            shown: list[str] = []
            for c, n in new_tags:
                check = checks.get(c)
                shown += [x for x in (rt.expect_for(check, n, platform) if check else []) if x not in shown]
            if shown != [e.quote]:
                kept.append((step.number, e.raw, "%sprints %s instead" % (
                    "on %s " % platform if platform else "",
                    "; ".join(repr(x) for x in shown) or "the line as written, because no check states Expect text for it")))


def _git(repo_root: Path, *args: str) -> str:
    import subprocess
    try:
        return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True).stdout
    except OSError:
        return ""


def refresh_plan(repo_root: Path):
    """Stale quotes, each with the current line at the position it used to quote."""
    rt = release_test_module()
    docs = repo_root / "docs"
    checks = rt.load_checks(docs, repo_root=repo_root)
    history: dict[str, list[list[str]]] = {}

    def versions(check) -> list[list[str]]:
        if check.id in history:
            return history[check.id]
        rel = str(Path(check.path)) if not Path(check.path).is_absolute() else str(Path(check.path).relative_to(repo_root))
        out = []
        for rev in [h for h in _git(repo_root, "log", "--format=%H", "--", rel).split() if h]:
            text = _git(repo_root, "show", "%s:%s" % (rev, rel))
            body = text.split("\n---", 1)[1] if text.startswith("---") and "\n---" in text[3:] else text
            lines = []
            for line in rt.under_heading(body, "Expect", "Expected results").splitlines():
                n = rt.normalise(line)
                if n and n not in lines:
                    lines.append(n)
            out.append(lines)
        history[check.id] = out
        return out

    out = []
    for procedure in rt.load_procedures(docs, repo_root):
        edits, kept = [], []
        for step in procedure.steps:
            for e in step.expectations:
                owners = {c for c, _n in e.tags}
                if not e.quote or len(owners) != 1:
                    continue
                check = checks.get(next(iter(owners)))
                now = rt.expect_text(check) if check else []
                if not now or e.quote in now:
                    continue
                found = None
                for old in versions(check):
                    if e.quote in old:
                        found = old
                        break
                if found is None:
                    kept.append((step.number, e.raw, "no earlier version of %s has these words" % check.id))
                    continue
                if len(found) != len(now):
                    kept.append((step.number, e.raw, "%s's Expect had %d lines and has %d; re-quote by hand"
                                 % (check.id, len(found), len(now))))
                    continue
                new_text = now[found.index(e.quote)]
                m = rt._MARKER_RE.match(e.raw)
                prefix = e.raw[:m.end()] if m else e.raw[:len(e.raw) - len(e.raw.lstrip())]
                tag_text = " ".join("`%s%s`" % (c, "." + n if n else "") for c, n in e.tags)
                edits.append((e.raw, prefix + new_text + " " + tag_text, []))
        if edits or kept:
            out.append({"path": repo_root / procedure.path, "shown": procedure.path, "edits": edits, "kept": kept})
    return out


def apply(item) -> None:
    lines = item["path"].read_text(encoding="utf-8").split("\n")
    for first, new, drop in item["edits"]:
        i = lines.index(first)
        for raw in drop:
            j = lines.index(raw, i + 1)
            del lines[j]
        if new is None:
            del lines[i]
        else:
            lines[i:i + 1] = new.split("\n")
    item["path"].write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="re-quote lines whose check's Expect was reworded")
    ap.add_argument("--all", action="store_true",
                    help="rewrite every quoted line as its tags alone, and move tags "
                         "off action lines (project-os-dev ADR-0050 D2)")
    args = ap.parse_args(argv)
    if args.all and args.refresh:
        ap.error("--all and --refresh do opposite things; choose one")
    root = Path(args.repo_root).resolve()
    items = refresh_plan(root) if args.refresh else plan(root, everything=args.all)
    if args.apply:
        #: Write first, report after: a reader that closes the pipe early
        #: (`| head`) must not stop the rewrite half way (TASK-0186).
        for item in items:
            if item["edits"]:
                apply(item)
    n_edit = sum(len(i["edits"]) for i in items)
    n_kept = sum(len(i["kept"]) for i in items)
    if args.refresh:
        print("release-test-tags: %s %d stale quote(s) from the check's current Expect; %d need a person"
              % ("re-quoted" if args.apply else "would re-quote", n_edit, n_kept))
    elif args.all:
        print("release-test-tags: %s %d line(s) to tags only; %d of them print different words"
              % ("rewrote" if args.apply else "would rewrite", n_edit, n_kept))
    else:
        print("release-test-tags: %s %d line(s) to tags only; %d quoted line(s) stay quoted"
              % ("rewrote" if args.apply else "would rewrite", n_edit, n_kept))
    for item in items:
        for first, new, drop in item["edits"]:
            print("   %s: %s%s" % (item["shown"], "(removed: its tags are given above it)"
                                   if new is None else new.strip().replace("\n", " / "),
                                   " (replaces %d lines)" % (1 + len(drop)) if drop else ""))
        for number, raw, why in item["kept"]:
            print("   %s  %s step %d: %s" % ("note" if args.all else "keep",
                                           item["shown"], number, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
