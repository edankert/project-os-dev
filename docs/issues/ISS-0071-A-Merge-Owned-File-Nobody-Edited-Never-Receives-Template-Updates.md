---
type: "[[issue]]"
id: ISS-0071
aliases: ["ISS-0071"]
title: "A merge-owned file nobody edited never receives template updates, so 10 of 12 repos read field definitions months out of date"
status: open
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["your-health, 2026-09-19: Edwin asked why SCHEMAS.md differed from the template after a clean sync"]
reported_by: user:edwin
question: ""
severity: medium
component: "sync"
parent: ""
related: []
tests: []
---

# A merge-owned file nobody edited never receives template updates

## Problem

An agent in a downstream repo reads the note field definitions in `docs/__templates__/SCHEMAS.md` and gets a version months out of date. For example, it is told a feature lists its `tests:`, which ADR-0032 removed. It is not told about `reported_by`, which is required on an open issue from 2026-09-19. It is also not told about the `## Acceptance`, `## Verification` and `## Impact` sections that `review-packet.py` and `walk-sheet.py` parse.

This happens because `tools/sync/MANIFEST.yaml` marks `SCHEMAS.md` as `merge` (the project may add its own content). The sync never writes a `merge` file. It only prints `MERGE` and a note to merge by hand, which nobody does. So a repo that never touched the file keeps its first copy forever. `test-sync-stale.sh` asserts this behaviour ("a merge-owned stale file is not overwritten"). The sync reports such a repo as fully up to date, and the dry run lists `SCHEMAS.md` beside `docs/PHASES.md`, a file that really does hold project content. So a reader takes the difference to be deliberate. On 2026-09-19 an agent in your-health told Edwin exactly that, before it checked.

> [!quote] As reported — 2026-09-19 (user:edwin)
> Why would schemas.md be different

## Evidence

Compared with project-os `4b5fa83` on 2026-09-19. The number is the count of template lines each repo's copy lacks:

| Repo | Lines missing |
|---|---|
| edankert.com, obsidian-supernote-sync, your-applications.com, yourtrainer-mcp | 153 |
| project-os-dev | 149 |
| articles, project-os-bench | 114 |
| project-os-cockpit | 60 |
| your-sudoku | 28 |
| project-os-deck | 13 |
| your-health, your-trainer | 0 |

your-health had 153 missing lines, and none of its own. Its only lines the template lacks were older wordings of the same fields. It was replaced with the template copy on 2026-09-19. The smaller counts (cockpit, sudoku, deck) may hold genuine local additions and need looking at before anything overwrites them.

## Expected

A `merge` file the project never edited updates like a template-owned file. The sync already keeps a baseline (`baseline_sha` in `.project-os-sync`): if the repo's copy equals the file at the baseline commit, nobody edited it, and it can be fast-forwarded. Only a copy that differs from both the baseline and the new template needs a hand merge.

## Next Actions
- [ ] Decide whether `SCHEMAS.md` needs `merge` at all. If no repo adds project content to it, make it `template`.
- [ ] Otherwise, fast-forward a `merge` file when the repo's copy matches the baseline version. Change the `test-sync-stale.sh` case to expect that.
- [ ] In the dry run, say which `MERGE` files have local edits and which are only behind.
- [ ] Bring the ten repos above up to date, checking cockpit, sudoku and deck for local additions first.
