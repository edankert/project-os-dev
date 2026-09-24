---
type: "[[task]]"
id: TASK-0155
aliases: ["TASK-0155"]
title: "The first full run is written down where a reader will find it"
status: done
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]"]
parent: "[[FEAT-0038-Note-Relevance-Harness]]"
effort: S
due: ""
depends: ["[[TASK-0152-Transcript-Benchmark]]", "[[TASK-0154-Parameter-Sweep]]"]
blocks: []
related: ["[[REQ-0032-Ranking-Claims-Measured]]"]
tests: []
---

# The first full run is written down

## What this delivers

A `reference` note under `docs/reference/` holding the first complete run: the corpus size, the three benchmarks, the cold-start table, the sweep result and the date. The figures quoted in [[FEAT-0038-Note-Relevance-Harness|FEAT-0038]] today come from a session that will not be readable later, and a number whose source is a chat transcript cannot be checked by the next reader.

## Definition of Done

- [x] A `reference` note exists, created from `docs/__templates__/reference.md`, carrying every figure with the command and the date that produced it.
- [x] Each number sits beside the caveat that qualifies it, in the same words the harness prints.
- [x] The feature note's tables point at this note rather than standing alone.
- [x] It records what the run does **not** establish: that the ranker does not beat a session's own reading, and that the git-history labels are notes written rather than notes read.
- [x] No transcript content appears in it — counts and recalls only.
