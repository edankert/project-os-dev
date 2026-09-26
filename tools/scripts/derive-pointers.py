#!/usr/bin/env python3
"""Stamp the back-pointer on a superseded or amended note (ADR-0048, ISS-0096).

Superseding used to mean editing two notes: the new one got `supersedes:`,
and the old one got `superseded:` and a new status by hand. ADR-0045 was
amended by ADR-0046 on 2026-09-16 and carried no pointer until 2026-09-25, so
a reader who reached it by a link read a rule that no longer held. Now the
author writes the new note only, and this script writes the old one:

  new note `supersedes: X`   X gets `superseded: "[[new]]"` and status `superseded`
  new note `amends: X`       X gets `amended_by:` listing every note that amends it

The field keeps the old note's own spelling: `superseded_by:` where the note
or its type already uses it (designs, tasks, phases), else `superseded:`.
The status changes only where the old note's type has a `superseded` status.
A successor still `proposed` or `draft` stamps nothing: until it is decided,
nothing has been replaced.

Idempotent: a note already carrying the right pointer is left alone.

Usage:
    derive-pointers.py [--repo-root .]      # dry run
    derive-pointers.py --apply
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNDECIDED = {"proposed", "draft"}
#: Types whose back-pointer field is spelled `superseded_by:` when the note
#: carries neither spelling yet.
BY_SPELLING = {"design", "design-system", "task", "phase", "plan", "surface"}

_vd = None


def validator():
    global _vd
    if _vd is None:
        spec = importlib.util.spec_from_file_location("_vd_pointers", HERE / "validate-docs.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _vd = mod
    return _vd


def plan(root):
    """[{old, field, want, status, path}] for every old note that needs a pointer."""
    vd = validator()
    index, claimants = vd.build_note_index(root / "docs")
    notes = {i: (p, fm or {}) for i, (p, fm) in index.items() if claimants.get(i) == [p]}
    superseders, amenders = {}, {}
    for nid, (_p, fm) in sorted(notes.items()):
        if str(fm.get("status", "")).strip() in UNDECIDED:
            continue
        for old in vd.extract_ids(fm.get("supersedes")):
            if old != nid and old in notes:
                superseders.setdefault(old, []).append(nid)
        for old in vd.extract_ids(fm.get("amends")):
            if old != nid and old in notes:
                amenders.setdefault(old, []).append(nid)
    out = []
    for old, news in sorted(superseders.items()):
        path, fm = notes[old]
        ntype = vd.note_type(fm)
        field = ("superseded_by" if "superseded_by" in fm
                 else "superseded" if "superseded" in fm
                 else "superseded_by" if ntype in BY_SPELLING else "superseded")
        have = vd.extract_ids(fm.get(field))
        want = sorted(set(news))
        allowed = vd.ALLOWED_STATUS.get(ntype, set())
        status = "superseded" if "superseded" in allowed and str(fm.get("status", "")) != "superseded" else None
        if set(have) != set(want) or status:
            out.append({"old": old, "path": path, "field": field, "want": want, "have": have,
                        "status": status, "kind": "superseded"})
    for old, news in sorted(amenders.items()):
        path, fm = notes[old]
        have = vd.extract_ids(fm.get("amended_by"))
        want = sorted(set(news) | set(have))
        if set(have) != set(want):
            out.append({"old": old, "path": path, "field": "amended_by", "want": want, "have": have,
                        "status": None, "kind": "amended"})
    return out


def _set_field(lines, end, field, value):
    key = re.compile(r"^%s:" % re.escape(field))
    for i in range(1, end):
        if key.match(lines[i]):
            j = i
            while j + 1 < end and re.match(r"^\s+-", lines[j + 1]):
                j += 1
            lines[i:j + 1] = ["%s: %s\n" % (field, value)]
            return
    lines.insert(end, "%s: %s\n" % (field, value))


def apply(root, changes, write):
    for ch in changes:
        text = ch["path"].read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\n") == "---"), None)
        if not lines or not lines[0].startswith("---") or end is None:
            continue
        links = ['"[[%s]]"' % n for n in ch["want"]]
        value = links[0] if ch["kind"] == "superseded" and len(links) == 1 else "[%s]" % ", ".join(links)
        _set_field(lines, end, ch["field"], value)
        if ch["status"]:
            end = next(i for i in range(1, len(lines)) if lines[i].rstrip("\n") == "---")
            _set_field(lines, end, "status", ch["status"])
        if write:
            ch["path"].write_text("".join(lines), encoding="utf-8")
    if write and changes:
        validator().invalidate_note_index()
    return changes


def derive(root, write=False):
    root = Path(root).resolve()
    changes = apply(root, plan(root), write)
    return [{"id": c["old"], "path": str(c["path"].relative_to(root)), "field": c["field"],
             "want": c["want"], "status": c["status"], "kind": c["kind"]} for c in changes]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    changes = derive(args.repo_root, write=args.apply)
    if args.json:
        print(json.dumps(changes, indent=2))
        return 0
    print("derive-pointers: %s %d note(s)" % ("stamped" if args.apply else "would stamp", len(changes)))
    for c in changes:
        print("   %-10s %s: %s%s" % (c["id"], c["field"], ", ".join(c["want"]),
                                     "; status superseded" if c["status"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
