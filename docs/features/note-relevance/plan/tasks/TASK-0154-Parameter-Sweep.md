---
type: "[[task]]"
id: TASK-0154
aliases: ["TASK-0154"]
title: "The ranker's parameters come from a recorded sweep, and the misses are read"
status: cancelled
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]"]
parent: "[[FEAT-0038-Note-Relevance-Harness]]"
effort: M
due: ""
depends: ["[[TASK-0151-Cold-Start-Baseline]]", "[[TASK-0153-Supported-Ranker-Script]]"]
blocks: ["[[TASK-0155-First-Run-Recorded]]"]
related: ["[[REQ-0032-Ranking-Claims-Measured]]"]
tests: []
---

# The parameters are swept instead of guessed

## What this delivers

`k1`, `b`, the status weight and the recency weight currently hold the values convention suggests. Nobody has searched them. This task searches them against the harness and records what moved.

It also answers the question that decides whether any further ranking work is worth starting: **what do the misses look like?** The ranker is lexical, so it cannot match a query whose words are absent from the note. Whether that is what costs the missing recall is unknown, and reading the misses is the only way to find out.

## The trap to avoid

A sweep run on the same 86 commits it is scored against will report a number that is partly the sweep fitting the benchmark. Split the labelled set before searching, tune on one half and report on the other, and print both figures. A tuned result that does not survive the held-out half is a finding, not a failure to hide.

## Definition of Done

- [ ] The labelled set is split before any search; the split rule is recorded and is not a hand-picked partition.
- [ ] `k1`, `b`, the status weight and the recency weight are searched over a stated grid, and the grid is in the note.
- [ ] Both figures are reported: recall on the tuning half and on the held-out half, before and after.
- [ ] Any parameter the sweep leaves effectively unchanged is named as such, rather than quietly re-stated as a tuned value.
- [ ] **The twenty highest-ranked misses are read**, and the note says, for each, whether the query's wording overlapped the note's at all.
- [ ] From that reading, one line stating whether a semantic rerank stage is worth pricing. This line is the trigger the feature's Out of scope section defers to; no reranker work is scaffolded before it exists.

## Why this was cancelled

Cancelled 2026-09-21 when PHASE-0008 closed on its finding. The sweep would have tuned `k1`, `b` and the status/recency weights against a held-out split, and read the twenty highest-ranked misses to say whether a semantic rerank was worth pricing. Both remain unanswered and the gap it would need to close is 0.022, not the 0.115 the earlier leaked figures implied — so this is cut as not-now rather than refuted. Re-adopt it by creating a successor task; the harness it needs already exists and takes `--ranker`. See [[Note-Ranking-Measured-2026-09-21]], "What this run does not establish".

## Notes

The reranker candidate under discussion is Jev / TypeSafe. The plugin is installed and the key is in the shell profile. Neither has been used, and this task's output is what decides whether either should be.
