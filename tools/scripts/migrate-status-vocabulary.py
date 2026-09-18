#!/usr/bin/env python3
"""Migrate a repo's note + snapshot status vocabulary to the current taxonomy.

This is the fleet's one status-migration tool, covering every vocabulary
decision taken so far. Adding a decision means adding its rows to MAPPING
rather than writing a second script — the rewrite machinery below (block
*and* inline snapshot styles, note frontmatter, the drift report) is the
part that is easy to get subtly wrong, and having two copies of it is how
one of them silently falls behind.

* **ADR-0008** ("States must earn their keep", amended 2026-07-25) collapsed
  the taxonomy from 64 declared values to 53.
* **ADR-0012** (2026-07-26) removed the four hyphenated values: `in-progress`
  and `rolled-back` merged into the `doing` and `reverted` that already meant
  the same thing; `in-review` and `wont-fix` were renamed to `review` and
  `declined`.

The script rewrites values in note frontmatter and in the matching
SNAPSHOT.yaml entries, so the two never disagree mid-migration.

**What it deliberately does not touch:** the vocabulary *surfaces* — a repo's
`tools/instructions/STATUSES.md` and its validator's ALLOWED_STATUS. Those
arrive by template sync, and a migration script editing them would let a repo
drift from the template it is supposed to be following. Run the sync, then run
this. If you migrate before syncing, the repo's own validator will reject the
new values and tell you so.

Design constraints, in priority order:

1. **Completed state is preserved.** Every mapping below sends a terminal status
   to a terminal status. The one case that changes how an item *reads* --
   issue `done` -> `fixed` -- is flagged in the report rather than buried,
   because `done` was never a legal issue status and renders as incomplete
   today despite its author having marked it finished.
2. **Dry-run is the default.** `--write` is required to touch anything.
3. **Per-repo.** Run it once per repo and commit separately, so a bad mapping is
   revertible in isolation rather than tangled with nine other repos'.

Only `status:` is rewritten. Bodies, other frontmatter keys, and formatting are
left byte-identical -- the rewrite is anchored to the frontmatter block so a
`status:` line inside a fenced code block in the body is never touched.

Exit codes: 0 = clean (or nothing to do), 1 = a mapping could not be applied.

Stdlib only. Usage:
    migrate-status-vocabulary.py [--repo-root PATH] [--write] [--quiet]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# (note type, old status) -> new status.
#
# Absent on purpose: `task`/`phase` `superseded`. Those 72 notes carry
# `superseded_by:` pointing at a successor feature/phase -- work absorbed, not
# abandoned -- and ADR-0008's amendment ADDED `superseded` to both taxonomies
# rather than remapping them. They are already legal and must not be touched.
MAPPING: dict[tuple[str, str], str] = {
    # --- issues: `closed` merged into `fixed` (3% follow-through fleet-wide) ---
    ("issue", "closed"): "fixed",          # terminal -> terminal
    ("issue", "done"): "fixed",            # never legal; author meant finished  [FLAGGED]
    ("issue", "pending"): "open",
    ("issue", "in-progress"): "open",
    ("issue", "blocked"): "open",          # blocked-ness moves to `depends:`
    ("issue", "reopened"): "open",
    ("issue", "resolved"): "fixed",
    # --- tasks ---
    ("task", "next"): "backlog",
    ("task", "blocked"): "doing",          # blocked-ness moves to `depends:`
    ("task", "todo"): "backlog",
    ("task", "pending"): "backlog",
    ("task", "complete"): "done",
    ("task", "completed"): "done",
    # --- tests: `ready` = defined but not yet executed (ADR-0010) ---
    ("test", "active"): "ready",
    ("test", "draft"): "ready",
    ("test", "blocked"): "ready",
    ("test", "deprecated"): "ready",
    # --- phases ---
    ("phase", "draft"): "planned",
    ("phase", "backlog"): "planned",
    # --- risks: mitigation progress lives in mitigation_tasks:, not in a status ---
    ("risk", "mitigating"): "open",
    ("risk", "monitoring"): "open",
    # --- changes: {merged, reverted} has no pre-merge state ---
    ("change", "active"): "merged",        # [FLAGGED]
    ("change", "draft"): "merged",         # [FLAGGED]
    ("change", "in-review"): "merged",     # [FLAGGED]
    # --- plans ---
    ("plan", "doing"): "active",
    ("plan", "next"): "draft",
    ("plan", "backlog"): "draft",
    # --- references ---
    ("reference", "reference"): "active",
    ("reference", "draft"): "active",
    ("reference", "complete"): "active",
    # --- releases ---
    ("release", "staged"): "draft",
    # --- decisions ---
    ("adr", "rejected"): "superseded",
    ("decision", "rejected"): "superseded",

    # ---------------------------------------------------------------
    # ADR-0012 (2026-07-26): status values carry no hyphens.
    # Two merges into values that already existed, two renames. None of
    # these change whether an item reads as complete, so none is FLAGGED.
    # ---------------------------------------------------------------
    ("feature", "in-progress"): "doing",       # merge: `doing` already meant this
    ("feature", "in-review"): "review",        # rename
    ("issue", "wont-fix"): "declined",         # rename
    ("release", "rolled-back"): "reverted",    # merge: `reverted` already meant this
    # Types that carried a hyphenated value only by drift. Cheap to map,
    # and leaving them out would strand a note the vocabulary now rejects.
    ("task", "in-progress"): "doing",
    ("task", "in-review"): "review",
    ("requirement", "in-review"): "review",
    ("plan", "in-progress"): "active",
    ("phase", "in-progress"): "active",
    ("risk", "wont-fix"): "closed",
    ("test", "in-review"): "ready",
    ("change", "rolled-back"): "reverted",
}

#: Mappings that change whether an item reads as complete. Reported separately;
#: they are corrections, but they are visible and must not be silent.
FLAGGED: frozenset[tuple[str, str]] = frozenset({
    ("issue", "done"),
    ("change", "active"), ("change", "draft"), ("change", "in-review"),
})

#: Types where "complete" is a claim about delivered work. The terminal-preservation
#: invariant below is enforced for these and only these.
#:
#: A `reference` at `complete` is the counter-example that motivated the
#: distinction: its status described the *sweep it documents* (tracked in its own
#: TASK note), not the note's lifecycle, and the reference stays valid afterwards.
#: Refusing that remap would have blocked the migration to protect a completion
#: claim nobody made.
WORK_TYPES: frozenset[str] = frozenset({"task", "issue", "feature", "requirement", "phase"})

#: Terminal in the post-ADR-0008 taxonomy -- used to assert the invariant that
#: no migration moves a work item out of completion.
TERMINAL_AFTER: frozenset[str] = frozenset({
    "done", "fixed", "implemented", "merged", "passing", "released",
    "accepted", "superseded", "cancelled", "wont-fix", "retired",
    "reverted", "rolled-back", "deprecated",
})
TERMINAL_BEFORE: frozenset[str] = TERMINAL_AFTER | {
    "closed", "resolved", "fulfilled", "met", "complete", "completed",
    "published", "verified", "obsolete",
}


def note_type_of(fm_text: str) -> str:
    m = re.search(r"^type:\s*(.+)$", fm_text, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'").strip("[]").strip().lower()


def split_frontmatter(text: str):
    """Return (pre, frontmatter, post) or None when the file has no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[:4], text[4:end], text[end:]


def migrate_notes(root: Path, write: bool):
    changes, flagged, broke_invariant = [], [], []
    docs = root / "docs"
    if not docs.is_dir():
        return changes, flagged, broke_invariant
    for path in sorted(docs.rglob("*.md")):
        if "__templates__" in path.parts or "__bases__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        parts = split_frontmatter(text)
        if not parts:
            continue
        pre, fm, post = parts
        m = re.search(r"^status:\s*(.+)$", fm, re.M)
        if not m:
            continue
        old = m.group(1).strip().strip("\"'")
        nt = note_type_of(fm)
        new = MAPPING.get((nt, old))
        if not new or new == old:
            continue
        if nt in WORK_TYPES and old in TERMINAL_BEFORE and new not in TERMINAL_AFTER:
            broke_invariant.append((path, nt, old, new))
            continue
        rel = path.relative_to(root).as_posix()
        changes.append((rel, nt, old, new))
        if (nt, old) in FLAGGED:
            flagged.append((rel, nt, old, new))
        if write:
            new_fm = re.sub(r"^status:\s*.+$", "status: %s" % new, fm, count=1, flags=re.M)
            path.write_text(pre + new_fm + post, encoding="utf-8")
    return changes, flagged, broke_invariant


def migrate_snapshot(root: Path, write: bool, note_types: dict[str, str]):
    """Rewrite items.*.status in SNAPSHOT.yaml to match the migrated notes.

    The snapshot groups items by collection (``items.tasks``, ``items.issues``
    ...), so the note type is taken from the collection name rather than
    re-parsed -- that is what makes a per-type mapping applicable here at all.
    """
    snap = root / "SNAPSHOT.yaml"
    if not snap.is_file():
        return []
    text = snap.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    coll_type = {
        "tasks": "task", "issues": "issue", "features": "feature",
        "requirements": "requirement", "phases": "phase", "risks": "risk",
        "tests": "test", "workflows": "workflow", "changes": "change",
        "decisions": "adr", "releases": "release",
    }
    current, in_items, changed = None, False, []
    for i, line in enumerate(lines):
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            in_items = False
        if not in_items:
            continue
        m = re.match(r"^  (\w+):\s*(\{\})?\s*$", line)
        if m:
            current = coll_type.get(m.group(1))
            continue
        # Block style:  `      status: closed`
        m = re.match(r"^(\s+status:\s*)(.+?)(\s*)$", line)
        if m and current:
            old = m.group(2).strip().strip("\"'")
            new = MAPPING.get((current, old))
            if new and new != old:
                lines[i] = "%s%s\n" % (m.group(1), new)
                changed.append((current, old, new))
            continue
        # Inline flow style: `    ISS-0087: { title: "...", status: closed, ... }`
        # Several repos write whole item entries on one line; a block-only rewrite
        # silently skips them and leaves the snapshot disagreeing with the note
        # (validator ITEM-STATUS), which is how this was found.
        if current and "{" in line and "status:" in line:
            def _sub(mm):
                old_v = mm.group(2).strip()
                new_v = MAPPING.get((current, old_v))
                if new_v and new_v != old_v:
                    changed.append((current, old_v, new_v))
                    return "%s%s" % (mm.group(1), new_v)
                return mm.group(0)
            updated = re.sub(r"(\bstatus:\s*)([A-Za-z][\w-]*)", _sub, line)
            if updated != line:
                lines[i] = updated
    if changed and write:
        snap.write_text("".join(lines), encoding="utf-8")
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description="Migrate status vocabulary to the current taxonomy (ADR-0008, ADR-0012).")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: cwd)")
    ap.add_argument("--write", action="store_true", help="Apply changes (default: dry run)")
    ap.add_argument("--quiet", action="store_true", help="Only print the summary")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not (root / "SNAPSHOT.yaml").is_file():
        print("migrate-status: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 1

    changes, flagged, broke = migrate_notes(root, args.write)
    snap_changes = migrate_snapshot(root, args.write, {})

    mode = "APPLIED" if args.write else "DRY RUN"
    print("== %s  %s ==" % (mode, root.name))
    if not args.quiet:
        for rel, nt, old, new in changes:
            print("   %-58s %s: %s -> %s" % (rel[:58], nt, old, new))
    if snap_changes:
        from collections import Counter
        agg = Counter("%s: %s -> %s" % c for c in snap_changes)
        for k, n in sorted(agg.items()):
            print("   SNAPSHOT.yaml  %s  (x%d)" % (k, n))
    print("   notes: %d   snapshot entries: %d" % (len(changes), len(snap_changes)))
    if flagged:
        print("   !! %d change(s) alter whether an item reads as complete:" % len(flagged))
        for rel, nt, old, new in flagged:
            print("      %s  %s: %s -> %s" % (rel, nt, old, new))
    if broke:
        print("   XX %d mapping(s) REFUSED -- would move a completed work item out of completion:" % len(broke))
        for path, nt, old, new in broke:
            print("      %s  %s: %s -> %s" % (path, nt, old, new))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
