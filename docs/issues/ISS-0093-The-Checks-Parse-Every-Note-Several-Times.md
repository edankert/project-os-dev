---
type: "[[issue]]"
id: ISS-0093
aliases: ["ISS-0093"]
title: "Every commit and every stop waits about a minute while the checks parse the same notes again and again"
status: open
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: high
component: "tools/scripts/validate-docs.py; walk-sheet.py; sync-snapshot.py; the pre-commit and Stop hooks"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: []
---

# Every commit and every stop waits about a minute while the checks parse the same notes again and again

## Problem

In your-trainer (3,150 notes) a commit spends about 54 s in the pre-commit hook and every stop after a write about 40 s in the Stop hook. The time is parsing: `parse_frontmatter` runs 16,402 times per validator run, about five times per note, and `sync-snapshot.py` and `walk-sheet.py` each parse every note again.

## Evidence (2026-09-26)

- cProfile of `validate-docs.py` on your-trainer: 43.6 s total, 34.5 s in `parse_frontmatter`/`load_yaml`, 6.9 s in `validate_frontmatter_parses` (a second, PyYAML parse of every note).
- Caching `parse_frontmatter` by path, size and mtime within one run: 28.6 s to 10.3 s, identical output (1,140 lines).
- PyYAML's C loader parses all notes in 0.32 s (pure-Python 4.2 s); `stat` on every note takes 8 ms.

## Expected

Each note is parsed once per run, with libyaml where present and the current parser as fallback, and the parse is cached on disk by path, size and mtime so the validator, `walk-sheet.py` and `sync-snapshot.py` share it and a second run re-reads only what changed. A test asserts that the cached and uncached runs give identical output on a fixture, and a measurement on your-trainer records the before and after.

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

## Widened, 2026-09-26: the cache becomes the note index

Edwin asked whether a database of the links, built before a session starts, would make things faster and reduce reliance on grep. Searching is not the slow part (0.06 to 0.3 s on your-trainer); reading what comes back is. So the parse cache this issue asks for should also be the index the other tools use, rather than a second system:

- **Per note:** id, path, type, status, phase, parent, released or frozen, superseded by, outgoing links (wikilinks and bare ids), and headings. Backlinks are derived from the outgoing links.
- **Always current, never committed.** Keyed by path, size and mtime, so a run re-reads only changed notes (`stat` on every note: 8 ms; a full rebuild with libyaml: about 0.3 s). It is built on first use; the SessionStart hook may warm it. A missing or unreadable cache is rebuilt, never trusted.
- **JSON first.** At about 3,000 notes a JSON file is enough; SQLite (standard library) only if the queries grow.
- **Its readers:** the validator, `walk-sheet.py`, `sync-snapshot.py`, the derived lists and back-pointers (ISS-0095, ISS-0096), and the search in ISS-0101.
