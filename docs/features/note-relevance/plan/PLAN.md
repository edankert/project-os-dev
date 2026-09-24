---
type: "[[plan]]"
title: "Delivery plan: a harness scores which notes a session should read"
status: draft
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]"]
implements: ["[[FEAT-0038-Note-Relevance-Harness]]"]
related: ["[[REQ-0032-Ranking-Claims-Measured]]", "[[FEAT-0021-Serve-Orientation-Answer-Lookup]]"]
---

# Delivery plan: a harness scores which notes a session should read

## Delivery sequence

1. **The harness and the git-history benchmark** (TASK-0150). The ranker interface, the labelled set built from 86 commits, recall at 5, 10, 24 and 50, the stripped-ID row, the most-recently-updated floor, and the caveat printed beside every row that uses these labels. The prototype at `scratchpad/rank.py` is the first thing it scores, so the harness has a candidate from its first run.
2. **The cold-start baseline** (TASK-0151). The same labels, scored against what `SNAPSHOT.yaml` held at each commit's parent: the `focus` block, the first 24 items, every item, and the ranker at 24. This is the row that makes the whole exercise mean something, so it comes before any tuning.
3. **The transcript benchmark, widened** (TASK-0152). Aligning stored sessions to the commits in their window, and widening the tool-input extraction past four fields so more than 9 of 96 transcripts survive. This is also the path to a gold set of notes *read* rather than notes *written*.
4. **The ranker becomes a supported script** (TASK-0153). The prototype moves into the template as `tools/scripts/rank-notes.py` with a CLI, `--json` like every other script there, and an executable check.
5. **The sweep** (TASK-0154). `k1`, `b` and the status and recency weights, searched on a split that keeps the search from fitting the benchmark, plus a read of the twenty highest-ranked misses.
6. **The reference note** (TASK-0155). The first full run, dated, so the figures quoted in the feature note have a source that is not a chat transcript.

## Dependencies

- **Hard:** TASK-0151, TASK-0152 and TASK-0153 all need the ranker interface from TASK-0150. TASK-0154 needs both the ranker (TASK-0153) and the baseline (TASK-0151), because a sweep with nothing to beat is just a number going up.
- **Soft:** TASK-0155 is worth the most after TASK-0152 and TASK-0154, when the figures it records are the ones that will be quoted.

## Settled, 2026-09-21

- **Which repo implements this.** The template, `~/Dev/repos/project-os`, `tools/scripts/`, dogfooded here. Edwin's decision. `project-os-bench` does not implement it; the overlap with its FEAT-0007 payoff study is recorded in the feature note.
- **Whether this opens a phase.** It does: [[PHASE-0008-Measured-Note-Ranking|PHASE-0008]], which this feature is the whole scope of.

## Open questions

- **REQ-0032 is still `draft`, and that still holds the feature out of `doing`.** `tools/instructions/OWNERSHIP.md` makes a requirement's owner its approver, and this one's owner is Edwin. The repo question that originally justified the draft status is answered; the approval itself has not been given.
- **What the misses are made of.** TASK-0154 reads them. Until it has, nothing here decides whether a semantic rerank stage is worth pricing, and no Jev work is scaffolded.
