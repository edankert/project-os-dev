---
type: "[[test]]"
id: TST-0021
aliases: ["TST-0021"]
title: "The harness prints every row with its ground truth, its budget and its caveat"
status: active
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]", "[[REQ-0032-Ranking-Claims-Measured]]"]
scope: system
level: acceptance
entrypoint: "tools/scripts/rank-bench.py"
command: ""
last_verified: ""
covers: ["[[FEAT-0038-Note-Relevance-Harness]]"]
issues: []
tasks: ["[[TASK-0150-Git-History-Benchmark]]", "[[TASK-0151-Cold-Start-Baseline]]", "[[TASK-0152-Transcript-Benchmark]]"]
artifacts: []
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0032-Ranking-Claims-Measured]]"]
area: "note retrieval"
after: []
---

# The harness prints every row with its caveat

## Purpose

A recall figure read without its caveat is worse than no figure: it invites the reader to believe the ranker covers that share of what a session needed, which these labels cannot show. This check is walked by someone who did not build the harness, reading only what it prints.

> **Status is evidence, not intent.** Who writes a test's status, and what a `command:` changes, is stated once in `tools/instructions/STATUSES.md` `[[test]]`.

## Setup

A project-os repo with at least a few dozen notes and a git history of commits that touched them — project-os-dev itself is the cheapest such repo — and the template's `tools/scripts/rank-bench.py` and `rank-notes.py` present. No API key, no network, no configuration.

## Steps

1. From the repo root, run the harness with no arguments.
2. Read the output from the top, as someone who has not seen this feature.
3. Run it a second time without changing anything.

## Expect

- The run finishes in seconds and prints a table, without being given a query, a path or a key.
- The git-history section states how many commits it scored and the rule that selected them.
- Each git-history row is labelled with the query form it used, and the row using commit messages as written is not the only one shown; the stripped-ID row is there and is marked as the honest one.
- A sentence printed with those rows says the labels are notes the commits **wrote**, not notes the work read.
- The cold-start section shows the `focus` block, the first 24 items, every item, and the ranker at 24, against one set of labels, and states the snapshot size and item count it read.
- The transcript section states how many sessions it scored and how many it dropped, and prints the session's own recall beside the ranker's.
- No prompt text, file content or path from outside the repo appears anywhere in the output.
- The second run prints the same figures as the first.

## Not this check

- Whether the ranker is *good*. That is what the figures say, and this check asserts only that they are reported honestly and reproducibly.
- Whether the harness's numbers match the ones quoted in FEAT-0038. TASK-0155's reference note is where a dated run is recorded.
- Anything about the `SessionStart` hook. Nothing here wires the ranker into a session.
