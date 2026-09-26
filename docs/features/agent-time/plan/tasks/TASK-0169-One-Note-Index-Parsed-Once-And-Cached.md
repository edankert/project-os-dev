---
type: "[[task]]"
id: TASK-0169
aliases: ["TASK-0169"]
title: "Every note is parsed once, cached by path, size and mtime, and shared as a note index"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0093-The-Checks-Parse-Every-Note-Several-Times]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0093-The-Checks-Parse-Every-Note-Several-Times]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0027-The-Note-Cache-Never-Changes-What-The-Checks-Say]]"]
---

# Every note is parsed once, cached by path, size and mtime, and shared as a note index

## Definition of Done
- [x] `validate-docs.py`, `walk-sheet.py` and `sync-snapshot.py` parse each note at most once per run, and reuse a disk cache across runs that re-reads only changed notes. All three parse through `validate-docs.py`'s `parse_frontmatter`, cached in the system temp folder per repository.
- [x] NOTE-FRONTMATTER uses libyaml where present (`_yaml_loader()`), with the pure-Python loader and then the subset parser as fallbacks.
- [x] A note index (id, path, type, status, phase, parent, links, headings, frozen, superseded) is built from the cache and readable by other tools: `tools/scripts/note-index.py`, with `build()`, `backlinks()` and `--links-to`. The `frozen` and `superseded_by` fields are filled by TASK-0178 and TASK-0173.
- [x] Output with and without the cache is identical on every fleet repo; a test asserts cache invalidation on edit and fails when the key ignores mtime (TST-0027).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0027: four mutations, all caught).

## Result, measured on your-trainer 2026-09-26

| Step | Before | After, cold cache | After, warm cache |
|---|---|---|---|
| `validate-docs.py` | 28.6 s | 3.4 s | 0.96 s |
| `walk-sheet.py --check` | 1.27 s | 0.60 s | 0.60 s |
| `sync-snapshot.py` | 14.9 s | 0.95 s | 0.44 s |
| Pre-commit hook | 54.9 s | 3.11 s | 2.01 s |
| Stop hook | 39.9 s | 2.10 s | 1.51 s |

The validator's output was identical before and after the change on all 13 fleet repos (1,140 lines on your-trainer).
