---
type: "[[task]]"
id: TASK-0152
aliases: ["TASK-0152"]
title: "The transcript benchmark reads more than four tool fields, so more than 9 of 96 sessions count"
status: done
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]", "prototype: scratchpad/bench.py bench_transcripts TODO(widen), 2026-09-21"]
parent: "[[FEAT-0038-Note-Relevance-Harness]]"
effort: L
due: ""
depends: ["[[TASK-0150-Git-History-Benchmark]]"]
blocks: ["[[TASK-0155-First-Run-Recorded]]"]
related: ["[[REQ-0032-Ranking-Claims-Measured]]", "[[RISK-0004-Transcript-Privacy]]"]
tests: ["[[TST-0021-Caveat-With-Every-Row]]"]
---

# The transcript benchmark reads more than four tool fields

## What this delivers

The benchmark that compares the ranker to a real session. Stored transcripts are aligned to the commits in their time window; the ranker is given the same note budget the session used, and both are scored against the same labels.

Measured on nine sessions: the session read a mean of 25.6 notes and reached recall 0.75; the ranker at that budget reached **0.54**, with IDs stripped from the query. A finished session reads better than the ranker ranks, and that gap is the point — the ranker is worth something at the cold start, before any of that reading has happened, and is not a substitute for a session doing its work.

## The defect this task fixes

The parser reads four tool-input fields: `file_path`, `command`, `pattern`, `path`. A note opened by a subagent, or reached from a glob result, is invisible to it. 86 of 96 transcripts drop out for having too few identifiable reads to score, so the benchmark runs at n=9 and no figure from it is a sample of anything.

Widening the extraction is also the route to the fix for the whole measurement: once reads are recovered reliably, the gold set can be **the notes a session read** rather than the notes its commits wrote, which is the bias that qualifies every git-history row (TASK-0150).

## Definition of Done

- [x] The extraction covers tool results and nested inputs, not four top-level fields, and the note lists what it now reads.
- [x] The count of transcripts that survive is printed with the result, with the reason the rest drop out.
- [x] Substantially more than 9 of the 96 sessions score; if the widened parser still loses most of them, the note says what is actually in the dropped files rather than reporting a bigger number.
- [x] The session row and the ranker row are scored against the same labels at the same budget, and both are printed, never the ranker alone.
- [x] The output carries no transcript content — no prompt text, no file contents, no path outside the repo — only counts, recalls and a session identifier. See [[RISK-0004-Transcript-Privacy]].
- [x] Whether a read-derived gold set is now feasible is recorded here, with the evidence, as the input to whoever revisits TASK-0150's caveat.


## Result, 2026-09-21

Built as `tools/scripts/rank-bench-sessions.py` in the template. Query: the session's opening prompt. Labels: the notes that session opened. Corpus: the repo's notes at the commit the session started from. Budget: however many notes the session actually read.

Pooled over **87 scored sessions in 7 project-os repos**:

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

Per session the ranker wins 32, ties 7 and loses 48. The mean delta is −0.022 with a standard deviation of 0.179, so the standard error over 87 sessions is 0.019 and the gap is 1.1 standard errors. **On the task a ranker exists for, BM25 relevance is indistinguishable from sorting by last-modified date, with the point estimate slightly behind.**

That agrees with `rank-bench.py`'s commit benchmark (0.340 against 0.450) from an independent label source, which is the strongest thing about it.

### The premise in this task's title was wrong

It assumed 87 of 96 project-os-dev sessions were lost to a narrow parser. Widening the scan from four tool-input fields to the whole record found **4x more note references and zero additional sessions**: 11 of 96 either way. The other 85 never opened a note — they were questions, shell work, or sessions about code. The sample was not being under-read; it is that size. Scale came from other repos instead, 11 to 87.

### A read-derived gold set is feasible, and is what this benchmark uses

The input TASK-0150's caveat was waiting on. These labels are notes **read**, not notes written, so the "outputs not inputs" caveat does not apply to this benchmark at all. `rank-bench.py`'s caveat still stands for its own rows.

## Notes

Transcripts live under `~/.claude/projects/<repo-path>/` and are the user's own session records. They are read, never copied into the repo.
