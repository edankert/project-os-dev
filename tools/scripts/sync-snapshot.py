#!/usr/bin/env python3
"""Sync SNAPSHOT.yaml's derived fields from note frontmatter (ADR-0009).

97% of the commits that touch SNAPSHOT.yaml also touch a note in the same
commit: every status change is written twice, by hand. A further 494 commits
changed a note *without* touching the snapshot -- that population is where drift
comes from, and three validator checks (ITEM-STATUS, COUNTER, METRICS) exist for
no purpose except detecting the two copies disagreeing.

This makes the note authoritative for the fields that can be derived.

WHY A SURGICAL UPDATER, NOT A GENERATOR
---------------------------------------
The first implementation regenerated the whole file. A shadow run against all 10
repos rejected that design, and the rejection is worth recording: a snapshot is
not a pure function of `docs/`. It is duplication *plus curation* --

  * ~80 lines of hand-written comments with no frontmatter home
    ("# Pruned: FEAT-0001..0006 (all done)", rationale beside a counter);
  * a curated retention set that no count-based rule reproduces (153 items
    would have been dropped, 180 added);
  * editorial `goal:` / `note:` prose that lives nowhere else.

Regenerating destroys the curated half to fix the duplicated half. So this
script rewrites only the fields that are genuinely derived, in place, and leaves
every byte it does not own:

  UPDATED IN PLACE   an entry's `status` (from the note), `counters`, `metrics`
  LEFT ALONE         comments, ordering, retention, goal/note prose, focus,
                     project, team, and every entry the snapshot does not list

Unregistered notes are REPORTED, never auto-added -- which items a snapshot
carries is the curation decision this script deliberately does not make.

Exit codes: 0 = clean/updated, 1 = --check found drift, 2 = usage error.

Stdlib only. Usage:
    sync-snapshot.py [--repo-root PATH] [--check] [--quiet]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "_vd", Path(__file__).resolve().parent / "validate-docs.py")
    _vd = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_vd)  # type: ignore[union-attr]
except Exception as exc:  # pragma: no cover
    print("sync-snapshot: cannot load validate-docs.py (%s)" % exc, file=sys.stderr)
    raise

# Reuse the validator's parsers. Two frontmatter readers that disagree would be a
# whole new class of drift, and removing one is the point of this script.
load_yaml = _vd.load_yaml
build_note_index = _vd.build_note_index
note_type = _vd.note_type
compute_metric_counts = _vd.compute_metric_counts
ID_RE = _vd.ID_RE

COLLECTION_OF = {
    "feature": "features", "task": "tasks", "issue": "issues",
    "requirement": "requirements", "phase": "phases", "risk": "risks",
    "test": "tests", "workflow": "workflows", "change": "changes",
    "adr": "decisions", "decision": "decisions", "release": "releases",
    "design": "designs",
}

_ITEM_RE = re.compile(r"^(\s+)([A-Z]+-[\w-]+):\s*(\{.*\})?\s*$")
_STATUS_BLOCK_RE = re.compile(r"^(\s+status:\s*)(.+?)(\s*)$")
_STATUS_INLINE_RE = re.compile(r"(\bstatus:\s*)([A-Za-z][\w-]*)")


def note_statuses(root):
    """id -> frontmatter status, using only notes that genuinely CLAIM that id.

    The validator's `index` matches IDs as substrings, so composite names
    legitimately resolve to the wrong note: `CHG-20260525-FEAT-0009-Chrome-Polish`
    is indexed under FEAT-0009 and sorts first, which would have propagated a
    change note's `merged` onto a feature. `claimants` holds only real claims
    (frontmatter id, or an ID-prefixed filename), which is what authority requires.
    """
    index, claimants = build_note_index(root / "docs")
    out = {}
    for the_id, paths in claimants.items():
        if len(paths) != 1:
            continue  # ambiguous: NOTE-DUP-ID reports it; do not guess
        entry = index.get(the_id)
        if not entry or entry[0] != paths[0]:
            fm = _vd.parse_frontmatter(paths[0]) or {}
        else:
            fm = entry[1] or {}
        st = str(fm.get("status", "") or "").strip()
        if st:
            out[the_id] = st
    return out, index


def sync_statuses(lines, statuses):
    """Rewrite each item entry's status to match its note. Returns list of changes."""
    changes, current_id, in_items = [], None, False
    for i, line in enumerate(lines):
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            in_items = False
        if not in_items:
            continue

        m = _ITEM_RE.match(line)
        if m:
            current_id = m.group(2)
            inline = m.group(3)
            if inline and current_id in statuses:
                want = statuses[current_id]

                def _sub(mm, want=want, cid=current_id):
                    if mm.group(2) != want:
                        changes.append((cid, mm.group(2), want))
                        return "%s%s" % (mm.group(1), want)
                    return mm.group(0)

                new = _STATUS_INLINE_RE.sub(_sub, line)
                if new != line:
                    lines[i] = new
            continue

        m = _STATUS_BLOCK_RE.match(line)
        if m and current_id and current_id in statuses:
            have = m.group(2).strip().strip("\"'")
            want = statuses[current_id]
            if have != want:
                changes.append((current_id, have, want))
                lines[i] = "%s%s\n" % (m.group(1), want)
    return changes


def sync_counters(lines, index):
    """counters.<PREFIX> = max observed ID. All-9s sentinels are exempt, as in the validator."""
    observed = {}
    for the_id in index:
        m = ID_RE.match(the_id)
        if not m:
            continue
        prefix, digits = m.group(1), m.group(2)
        if _vd.is_sentinel_id(digits):
            continue  # PHASE-999 / PHASE-0999 parking lot -- see validator
        observed[prefix] = max(observed.get(prefix, 0), int(digits))

    changes, in_counters = [], False
    for i, line in enumerate(lines):
        if re.match(r"^counters:\s*$", line):
            in_counters = True
            continue
        if in_counters and re.match(r"^\S", line):
            in_counters = False
        if not in_counters:
            continue
        m = re.match(r"^(  ([A-Z]+):\s*)(\d+)(\s*(?:#.*)?)$", line.rstrip("\n"))
        # Counters only ever RISE. An ID is allocated, not owned: lowering a counter
        # because its note was deleted would hand the same ID to the next item.
        if m and m.group(2) in observed and observed[m.group(2)] > int(m.group(3)):
            changes.append((m.group(2), m.group(3), observed[m.group(2)]))
            lines[i] = "%s%d%s\n" % (m.group(1), observed[m.group(2)], m.group(4))
    return changes


def sync_metrics(lines, snap, index):
    computed = compute_metric_counts(snap.get("items") or {}, index)
    changes, in_metrics, in_counts = [], False, False
    for i, line in enumerate(lines):
        if re.match(r"^metrics:\s*$", line):
            in_metrics = True
            continue
        if in_metrics and re.match(r"^\S", line):
            break
        if in_metrics and re.match(r"^\s+counts:\s*$", line):
            in_counts = True
            continue
        if not in_counts:
            continue
        m = re.match(r"^(\s*)([\w-]+):\s*(-?\d+)\s*(#.*)?$", line.rstrip("\n"))
        if m and m.group(2) in computed and int(m.group(3)) != computed[m.group(2)]:
            changes.append((m.group(2), m.group(3), computed[m.group(2)]))
            trailing = (" " + m.group(4)) if m.group(4) else ""
            lines[i] = "%s%s: %d%s\n" % (m.group(1), m.group(2), computed[m.group(2)], trailing)
    return changes


def unregistered(snap, index):
    registered = set()
    for coll in (snap.get("items") or {}).values():
        if isinstance(coll, dict):
            registered.update(coll.keys())
    out = []
    for the_id, (path, fm) in sorted(index.items()):
        if the_id in registered or not COLLECTION_OF.get(note_type(fm)):
            continue
        out.append((the_id, path))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync SNAPSHOT.yaml derived fields from docs/.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--check", action="store_true", help="Exit 1 on drift; write nothing")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--report-unregistered", action="store_true",
                    help="List notes with no snapshot entry (advisory; never auto-added)")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    snap_path = root / "SNAPSHOT.yaml"
    if not snap_path.is_file():
        print("sync-snapshot: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 2

    text = snap_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    statuses, index = note_statuses(root)

    st_changes = sync_statuses(lines, statuses)
    ct_changes = sync_counters(lines, index)
    snap_after = load_yaml("".join(lines)) or {}
    mt_changes = sync_metrics(lines, snap_after, index)
    new_text = "".join(lines)

    total = len(st_changes) + len(ct_changes) + len(mt_changes)
    if total == 0:
        if not args.quiet:
            print("sync-snapshot: %s up to date" % root.name)
    else:
        verb = "would update" if args.check else "updated"
        print("sync-snapshot: %s %s %d field(s)" % (root.name, verb, total))
        if not args.quiet:
            for cid, old, new in st_changes:
                print("   status  %-14s %s -> %s" % (cid, old, new))
            for pfx, old, new in ct_changes:
                print("   counter %-14s %s -> %s" % (pfx, old, new))
            for key, old, new in mt_changes:
                print("   metric  %-14s %s -> %s" % (key, old, new))
        if not args.check:
            snap_path.write_text(new_text, encoding="utf-8")

    if args.report_unregistered:
        missing = unregistered(load_yaml(new_text) or {}, index)
        if missing:
            print("   %d note(s) with no snapshot entry (curation decision -- not auto-added):" % len(missing))
            for the_id, path in missing[:20]:
                print("      %-14s %s" % (the_id, path.relative_to(root).as_posix()))

    return 1 if (args.check and total) else 0


if __name__ == "__main__":
    sys.exit(main())
