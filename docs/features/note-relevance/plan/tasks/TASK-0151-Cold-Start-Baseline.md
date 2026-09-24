---
type: "[[task]]"
id: TASK-0151
aliases: ["TASK-0151"]
title: "The cold-start baseline: what a session holds after reading the snapshot, scored against the same labels"
status: done
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]", "prototype: scratchpad/bench.py bench_snapshot, 2026-09-21"]
parent: "[[FEAT-0038-Note-Relevance-Harness]]"
effort: M
due: ""
depends: ["[[TASK-0150-Git-History-Benchmark]]"]
blocks: ["[[TASK-0154-Parameter-Sweep]]"]
related: ["[[REQ-0032-Ranking-Claims-Measured]]", "[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]"]
tests: ["[[TST-0021-Caveat-With-Every-Row]]"]
---

# The cold-start baseline from the snapshot

## What this delivers

The row the ranker has to beat. For each of the 86 benchmark commits the harness reads `SNAPSHOT.yaml` **as it stood at that commit's parent** — the file a session would actually have opened — and scores what it names against the same labels.

Four rows, measured in the prototype:

| what the session holds | items | recall |
|---|---:|---:|
| the `focus` block only | 3–5 | 0.257 |
| the first 24 items the snapshot lists | 24 | 0.233 |
| the ranker's top 24, prose query | 24 | 0.340 |
| floor: the 24 most recently updated notes | 24 | **0.450** |
| every item the snapshot lists | 168 | 0.535 |

The median snapshot across those commits was 100,016 bytes, about 26.3k tokens, listing 168 items.

## Why this row and not a token count

`SNAPSHOT.yaml` is described as the canonical machine-readable active context, and how much of a job's notes it actually names has never been measured. [[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs|ISS-0031]] says as much in its own note: whether an agent that greps instead of reading is left oriented is unmeasured. This task does not settle that — it measures the index, not the agent — but it is the first number anyone has put against the snapshot's retrieval quality, and it is cheap.

## Definition of Done

- [x] The baseline reads the snapshot at each commit's **parent**, never at the commit itself, and the harness says so in the output.
- [x] All four rows print together, against one set of labels, at one budget where the budget applies.
- [x] The median snapshot size and item count over the benchmark commits print with the table.
- [x] Commits whose parent has no `SNAPSHOT.yaml` are skipped and counted, not silently dropped.
- [x] The figures above reproduce, or the note records what changed and why.

## Notes

This row is evidence for two items already in the backlog. [[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]] TASK-0080 proposes the `SessionStart` hook emit the in-flight slice; the `focus`-block row, 0.257, is the closest measurement anyone has of what that slice would be worth as retrieval. `project-os-bench` TASK-0008 proposes a two-arm experiment on the same question. Neither is this task's to settle.
