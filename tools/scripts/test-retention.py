#!/usr/bin/env python3
"""TST-0003: sync-snapshot's derivation and retention hold their invariants.

Inversion suite. Every condition is violated in turn and the entry must SURVIVE;
a check that only ever tests the happy path cannot tell a working rule from a
missing one.

Deferred protection is structural rather than a separate condition: (5)
requires the note's status to equal the collection's terminal status, and
`deferred` never is. `cond3 deferred survives` therefore asserts the OUTCOME
(a deferred note is never pruned) rather than a particular line, which is what
should be guarded -- an assertion tied to a line passes for the wrong reason
the moment the line moves.

Stdlib only. Exit 0 = all pass. Usage: test-retention.py
"""

from __future__ import annotations

import importlib.util as ilu
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = ilu.spec_from_file_location("ss", HERE / "sync-snapshot.py")
ss = ilu.module_from_spec(_spec)
_spec.loader.exec_module(_spec and ss)

FAILURES = []
ASSERTIONS = [0]


def check(name, got, want):
    ASSERTIONS[0] += 1
    if got != want:
        FAILURES.append("%s: got %r, want %r" % (name, got, want))


def fixture(tmp, entries, notes, retention=""):
    root = Path(tmp)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    for the_id, (typ, fm) in notes.items():
        body = ["---", 'type: "[[%s]]"' % typ, "id: %s" % the_id]
        body += ["%s: %s" % (k, v) for k, v in fm.items()]
        body += ["---", "", "# %s" % the_id, ""]
        (root / "docs" / ("%s-note.md" % the_id)).write_text("\n".join(body), encoding="utf-8")
    lines = ["version: 1", "retention:", "  policy: active-and-recent"]
    lines += ["  " + r for r in retention.splitlines() if r.strip()]
    lines += ["counters:", "  TASK: 999", "focus:", '  task: ""', "items:", "  tasks:"]
    for the_id, fields in entries.items():
        lines.append("    %s:" % the_id)
        for k, v in fields.items():
            lines.append("      %s: %s" % (k, v))
    lines += ["metrics:", "  counts:", "    tasks_total: 0"]
    (root / "SNAPSHOT.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def prunable(root):
    snap = ss.load_yaml((root / "SNAPSHOT.yaml").read_text(encoding="utf-8")) or {}
    statuses, index, _cl = ss.note_statuses(root)
    _, window = ss.retention_config(snap)
    return {i for _, i in ss.prunable_ids(snap, index, window or 0, statuses)}


def base(extra_entry=None, extra_note=None, retention="prune_window: 0"):
    entries = {"TASK-0001": {"status": "done", "file": "docs/TASK-0001-note.md"}}
    notes = {"TASK-0001": ("task", {"status": "done", "title": "One"})}
    if extra_entry:
        entries["TASK-0001"].update(extra_entry)
    if extra_note:
        notes["TASK-0001"][1].update(extra_note)
    return entries, notes, retention


def run_case(name, expect_pruned, **kw):
    entries, notes, retention = base(**kw)
    with tempfile.TemporaryDirectory() as tmp:
        root = fixture(tmp, entries, notes, retention)
        check(name, "TASK-0001" in prunable(root), expect_pruned)


def main():
    # Happy path: a terminal entry outside the window, with nothing outstanding.
    run_case("baseline prunes", True)

    # (1) not terminal
    run_case("cond1 non-terminal survives", False, extra_entry={"status": "backlog"},
             extra_note={"status": "backlog"})
    # (2) inside the retention window
    run_case("cond2 recent survives", False, retention="prune_window: 5")
    # (3) deferred: asserted as an OUTCOME -- a deferred note is never pruned.
    #     There is no separate condition 3; (5) requires the note's TERMINAL
    #     status and `deferred` never is, so the protection is structural.
    #     Tying the assertion to the outcome rather than to a line is why it
    #     survived that refactor, and why it now also catches a reverted (5).
    # The entry is terminal in the snapshot and deferred in its note, which is
    # the shape that reaches furthest into the rule before being stopped.
    entries, notes, _ = base()
    entries["TASK-0001"]["status"] = "done"
    notes["TASK-0001"][1]["status"] = "deferred"
    with tempfile.TemporaryDirectory() as tmp:
        root = fixture(tmp, entries, notes, "prune_window: 0")
        snap = ss.load_yaml((root / "SNAPSHOT.yaml").read_text(encoding="utf-8")) or {}
        statuses, index, _cl = ss.note_statuses(root)
        ids = {i for _, i in ss.prunable_ids(snap, index, 0, statuses)}
        check("cond3 deferred survives", "TASK-0001" in ids, False)
    # (5) note missing entirely
    with tempfile.TemporaryDirectory() as tmp:
        root = fixture(tmp, {"TASK-0001": {"status": "done"}}, {}, "prune_window: 0")
        check("cond5 noteless survives", "TASK-0001" in prunable(root), False)
    # (5b) a note that EXISTS but cannot supply a status. This is the case the
    # first fix was written for and the first suite never covered: `index`
    # contains zero-byte and unparseable files, so a membership test passes
    # them. Three real entries were deleted this way.
    for label, body in (("zero-byte", ""),
                        ("unparseable", "---\nid: TASK-0001\nstatus: [unclosed\n"),
                        ("no status", "---\ntype: \"[[task]]\"\nid: TASK-0001\ntitle: T\n---\n")):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp, {"TASK-0001": {"status": "done",
                                               "file": "docs/TASK-0001-note.md"}},
                           {}, "prune_window: 0")
            (root / "docs" / "TASK-0001-note.md").write_text(body, encoding="utf-8")
            check("cond5 %s note survives" % label, "TASK-0001" in prunable(root), False)

    # (6) note: prose holds -- and clearing it RELEASES the hold
    run_case("cond6 note: holds", False, extra_entry={"note": '"context"'})
    run_case("cond6 cleared releases", True)
    # (7) outstanding verification business holds
    run_case("cond7 waiver holds", False, extra_entry={"verification_waiver": '"docs only"'})

    # Fail-safe on derivation: a note with no usable title must leave the
    # snapshot value ALONE rather than blanking it. 3 REGISTERED notes are in this
    # state fleet-wide, all zero-byte (6 unregistered ones also supply no title); files whose frontmatter PyYAML rejects
    # are NOT among them, because load_yaml falls back to parse_yaml_subset.
    with tempfile.TemporaryDirectory() as tmp:
        root = fixture(tmp, {"TASK-0001": {"status": "done", "title": '"Snapshot value"'}},
                       {"TASK-0001": ("task", {"status": "done"})}, "derive_fields: true")
        (root / "docs" / "TASK-0002-note.md").write_text("", encoding="utf-8")  # zero-byte
        lines = (root / "SNAPSHOT.yaml").read_text(encoding="utf-8").splitlines(keepends=True)
        changes = ss.sync_derived_fields(lines, ss.note_fields(root), True)
        check("failsafe: titleless note leaves value alone", changes, [])
        check("failsafe: value intact", 'title: "Snapshot value"' in "".join(lines), True)

    # Scanner: titles containing commas, braces and escaped quotes survive a
    # round-trip through an inline flow mapping.
    tricky = 'He said "go", {maybe}, or not'
    line = '    TASK-0001: { file: "x.md", title: %s, status: done }\n' % ss._yaml_quote(tricky)
    span = ss._scalar_span(line, "title")
    got = ss.load_yaml("v: " + line.rstrip("\n")[span[0]:span[1]]).get("v")
    check("scanner round-trips a hostile title", got, tricky)
    check("scanner finds status after it", ss._scalar_span(line, "status") is not None, True)

    # End-to-end through BOTH destructive writers. Without this the suite
    # passes against an implementation whose writers do nothing at all.
    with tempfile.TemporaryDirectory() as tmp:
        # TASK-0009 exercises derivation (it is not prunable, so the rewritten
        # value survives to be asserted); TASK-0001 exercises the prune.
        entries = {"TASK-0001": {"status": "done", "file": "docs/TASK-0001-note.md"},
                   "TASK-0009": {"status": "backlog", "file": "docs/TASK-0009-note.md",
                                 "title": '"stale snapshot title"'}}
        notes = {"TASK-0001": ("task", {"status": "done", "title": "One"}),
                 "TASK-0009": ("task", {"status": "backlog", "title": "note title"})}
        # A BLOCK-style entry whose value contains a brace: reverting the
        # branch selection to find("{") sends this down the inline path, where
        # the key is invisible, and derivation silently stops.
        entries["TASK-0007"] = {"status": "backlog", "file": "docs/TASK-0007-note.md",
                                "title": '"stale {brace} value"'}
        notes["TASK-0007"] = ("task", {"status": "backlog", "title": "derived {brace} value"})
        root = fixture(tmp, entries, notes, "derive_fields: true\nprune_window: 0")
        text = (root / "SNAPSHOT.yaml").read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        statuses, index, _cl = ss.note_statuses(root)
        ss.sync_derived_fields(lines, ss.note_fields(root), True)
        snap = ss.load_yaml("".join(lines)) or {}
        removed = ss.prune_entries(lines, ss.prunable_ids(snap, index, 0, statuses))
        out = "".join(lines)
        check("writer: derivation actually rewrote the value", '"note title"' in out, True)
        # Assert the DERIVED value, not merely that a brace survives: the stale
        # value contains one too, so "{brace} in out" passes even when
        # derivation never ran. That weaker assertion let the round-one defect
        # revert green.
        check("writer: braced block value was derived", "derived {brace} value" in out, True)
        check("writer: braced block stale value is gone", "stale {brace} value" in out, False)
        check("writer: stale value is gone", "stale snapshot title" in out, False)
        check("writer: prune actually removed the entry", removed, ["TASK-0001"])
        check("writer: the untouched entry survives", "TASK-0009:" in out, True)
        check("writer: result still parses", bool(ss.load_yaml(out)), True)
        check("writer: no over-deletion", "metrics:" in out and "counters:" in out, True)

    if FAILURES:
        print("test-retention: FAIL (%d)" % len(FAILURES))
        for f in FAILURES:
            print("   " + f)
        return 1
    print("test-retention: OK (%d assertions)" % ASSERTIONS[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
