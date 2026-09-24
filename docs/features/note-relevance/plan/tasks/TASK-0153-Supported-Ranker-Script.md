---
type: "[[task]]"
id: TASK-0153
aliases: ["TASK-0153"]
title: "The script ranker becomes a supported script: BM25, no dependencies, no network"
status: cancelled
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]", "prototype: scratchpad/rank.py, 2026-09-21"]
parent: "[[FEAT-0038-Note-Relevance-Harness]]"
effort: M
due: ""
depends: ["[[TASK-0150-Git-History-Benchmark]]"]
blocks: ["[[TASK-0154-Parameter-Sweep]]"]
related: ["[[REQ-0032-Ranking-Claims-Measured]]"]
tests: []
---

# The script ranker becomes a supported script

## What this delivers

`rank-notes.py`: given a sentence describing the job, it names the notes most likely to matter. BM25 over note bodies, then four adjustments — a length normalisation, a boost when the note's status is one of the active ones, a boost when `updated:` is recent, and a large boost when the query names an item ID outright. Standard library only, no network, no API key. 0.9 ms per query once the index is warm, against 5.31 s for `validate-docs.sh`.

The prototype already works. This task is what turns 120 lines of scratchpad into something another script and another repo can rely on.

## Definition of Done

- [ ] Lives in the template as `tools/scripts/rank-notes.py` and works in any project-os repo from its root, with no path hard-coded to project-os-dev.
- [ ] A CLI: a query, a budget, and `--json`, matching the convention every other script in `tools/scripts/` follows.
- [ ] Importable by `rank-bench.py` through the interface TASK-0150 defines.
- [ ] Imports nothing outside the standard library, opens no socket, and reads no environment variable for credentials.
- [ ] Notes under `docs/__templates__/` are excluded, and a note whose ID appears twice resolves to one entry.
- [ ] An executable `TST-*` with a `command:` covers it, per ADR-0010 and ADR-0025: at minimum, a query naming an item ID returns that note first, and a known-good prose query returns its labelled notes within the budget.
- [ ] Not called from the pre-commit hook or from `validate-docs.sh`.

## Why this was cancelled

Cancelled 2026-09-21 when PHASE-0008 closed on its finding. This task would have made `rank-notes.py` a supported script with its own executable test. The measurement it was waiting on says the ranker is indistinguishable from sorting by last-modified date (pooled 0.253 against 0.275 over 87 sessions, [[Note-Ranking-Measured-2026-09-21]]). Supporting a script that matches `ls -t` is cost with no return. The script stays in the template as the thing the harness scores, not as a supported entry point.

## Notes

The one substantive change already made to the prototype is worth keeping visible: an over-aggressive length normalisation had buried the corpus's largest note at rank 44 of 360 for a near-verbatim title query. Removing it lifted recall at every depth. Nothing else in the scoring has been justified by measurement yet — that is TASK-0154.
