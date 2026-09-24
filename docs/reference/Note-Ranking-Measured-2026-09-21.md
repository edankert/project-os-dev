---
type: "[[reference]]"
id: REF-NOTE-RANKING-2026-09-21
title: "What a note ranker scored, measured 2026-09-21"
status: active
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
scope: "The measurement behind PHASE-0008; the figures the feature and task notes point at"
source: ["tools/scripts/rank-bench.py run against project-os-dev at 74dbf38, 2026-09-21"]
related: ["[[FEAT-0038-Note-Relevance-Harness]]", "[[REQ-0032-Ranking-Claims-Measured]]", "[[PHASE-0008-Measured-Note-Ranking]]", "[[TASK-0152-Transcript-Benchmark]]"]
---

# What a note ranker scored, measured 2026-09-21

## Purpose

The dated record of the only full run PHASE-0008 produced, so the figures in [[FEAT-0038-Note-Relevance-Harness]] and its tasks point somewhere rather than standing alone. It exists because REQ-0032 forbids a note-ranking claim that carries no measurement, and this is that measurement.

**The finding: a BM25 ranker does not beat sorting the notes by last-modified date.** Two label sources built from different evidence agree on it.

## The command

```
python3 tools/scripts/rank-bench.py
```

Run from a project-os repo root, no arguments. Runs the commit benchmark, then the session benchmark. 8.5s over 86 commits in project-os-dev. Two consecutive runs on an unchanged checkout produced byte-identical figure rows, checked 2026-09-21.

Scripts live in the template at `~/Dev/repos/project-os/tools/scripts/`: `rank-notes.py` (the ranker), `rank-bench.py` (commit labels), `rank-bench-sessions.py` (session labels). Standard library only. Neither `validate-docs.sh` nor the pre-commit hook calls them.

## Benchmark 1 — commit labels

86 commits in project-os-dev that touched 2–12 notes, from the last 300. The commit message is the query; the notes that commit touched are the labels. Each commit is scored against the note corpus **at its own parent**, 46–359 notes depending on the commit. `SNAPSHOT.yaml` at those parents was a median of 100,198 bytes listing 169 items.

| recall at | 5 | 10 | 24 | 50 |
|---|---:|---:|---:|---:|
| ranker, commit message as written | 0.339 | 0.384 | 0.459 | 0.522 |
| ranker, IDs stripped from query (the honest row) | 0.209 | 0.257 | **0.340** | 0.427 |
| baseline: first N items `SNAPSHOT.yaml` lists | 0.064 | 0.127 | 0.235 | 0.290 |
| baseline: the snapshot's `focus` block alone | 0.257 | 0.257 | 0.257 | 0.257 |
| floor: the N most recently updated notes | 0.221 | 0.341 | **0.450** | 0.536 |
| baseline: every item the snapshot lists (168, ~26.3k tokens) | — | — | **0.535** | — |

> **The caveat these rows carry, in the words the harness prints.** Labels are the notes each commit WROTE, not the notes its author read. Close-out mechanically touches the task note and the snapshot, so part of every label set is output rather than input. The bias falls on every row equally: compare rows, and do not read a row as "N% of what you needed to read".

The stripped-ID row is the honest one. A query naming `FEAT-0034` hands the answer to the ranker's exact-ID boost and measures nothing.

## Benchmark 2 — session labels

The task a ranker exists for. Query: a session's opening prompt. Labels: the notes that session opened. Corpus: the repo's notes at the commit the session started from. Budget: however many notes the session actually read.

| repo | sessions | ranker | recency floor | delta |
|---|---:|---:|---:|---:|
| project-os-dev | 11 | 0.335 | 0.450 | −0.115 |
| your-trainer | 27 | 0.127 | 0.142 | −0.015 |
| project-os-cockpit | 18 | 0.097 | 0.185 | −0.088 |
| project-os-deck | 11 | 0.616 | 0.524 | +0.091 |
| your-health | 10 | 0.221 | 0.203 | +0.018 |
| articles | 6 | 0.452 | 0.434 | +0.018 |
| your-sudoku | 4 | 0.359 | 0.349 | +0.010 |
| **pooled** | **87** | **0.253** | **0.275** | **−0.022** |

Per session the ranker wins 32, ties 7, loses 48. Standard deviation of the per-session delta is 0.179, so over 87 sessions the standard error is 0.019 and the gap is 1.1 standard errors. **Indistinguishable from recency, with the point estimate slightly behind.**

> **The caveat these rows carry.** These labels are notes *read*, so the outputs-not-inputs caveat above does not apply to them. What does apply: only sessions that opened two or more notes can be scored, which is a minority — 11 of 96 transcripts in project-os-dev. The other 85 never touched a note. That is what the sample is, not a parser that needs widening.

No transcript content appears in this note or in the harness output. Counts, note IDs and recalls only ([[RISK-0004-Transcript-Privacy]]).

## What this run does **not** establish

- **That the ranker beats a session's own reading.** It does not, and that was never the comparison. A session that has worked for an hour has read, grepped and followed links; the ranker is a cold-start aid and is measured against what a session holds *before* any of that.
- **That BM25 is the ceiling.** The parameters were never swept (TASK-0154, cut when the phase closed). A tuned ranker might close 0.022. Nothing here says it cannot.
- **That recency is a good answer in absolute terms.** It wins at 0.275. Three notes in four that a session opens are still not in front of it. The finding is comparative, not a recommendation to be satisfied.
- **That this generalises beyond project-os repos.** Seven repos, one author, one working style.

## The superseded figures, and why they were wrong

Earlier revisions of these notes recorded the ranker at 0.620 against a 0.152 floor, and concluded it won. Those came from indexing the **working tree** while scoring labels from past commits: a note's present text was written partly by the commit being scored and partly by commits after it, so the query matched text that did not exist when the label was created. A train/test leak.

`rank-bench.py --worktree` measures it, holding the ranker fixed and changing only where notes are read from:

| recall at 24 | corpus pinned per commit | corpus from the working tree |
|---|---:|---:|
| ranker, as written | 0.459 | 0.768 |
| ranker, IDs stripped | 0.340 | 0.629 |
| snapshot, first 24 items | 0.235 | 0.235 |
| snapshot `focus` block | 0.257 | 0.257 |
| floor, most recently updated | 0.450 | 0.093 |

The two snapshot rows are identical across both runs because neither reads the note corpus. That is the control: the ranker's near-doubling is the leak and nothing else.

## The residue worth more than tuning

The per-repo spread. project-os-deck at +0.091 and project-os-cockpit at −0.088 are the same ranker on the same kind of corpus. Whatever distinguishes a repo where relevance helps from one where recency dominates is a better question than the right value of `k1`, and nobody has looked at it.
