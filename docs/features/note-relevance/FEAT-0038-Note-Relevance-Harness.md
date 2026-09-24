---
type: "[[feature]]"
id: FEAT-0038
aliases: ["FEAT-0038"]
title: "A harness scores which notes a session should read, and a script ranker is the first thing it scores"
status: done
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["Edwin, 2026-09-21: 'make it so'", "measurement session 2026-09-21, project-os-dev: 467 notes, 86 labelled commits, 9 transcripts"]
goal: "Build the thing that can tell a good answer from a bad one first: a harness that scores any note ranker against ground truth already in the repo, with the snapshot's own ordering as the baseline. Then ship the cheapest candidate — a BM25 ranker with no dependencies — and let the harness say what it is worth."
requirements: ["[[REQ-0032-Ranking-Claims-Measured]]"]
tasks: ["[[TASK-0150-Git-History-Benchmark]]", "[[TASK-0151-Cold-Start-Baseline]]", "[[TASK-0152-Transcript-Benchmark]]", "[[TASK-0153-Supported-Ranker-Script]]", "[[TASK-0154-Parameter-Sweep]]", "[[TASK-0155-First-Run-Recorded]]"]
release: ""
acceptance_exception: ""
related: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]", "[[ISS-0030-Retention-Is-Policy-Nothing-Performs]]", "[[ADR-0017-Claims-About-Working-Software-Are-Derived]]", "[[RISK-0004-Transcript-Privacy]]"]
tests: ["[[TST-0021-Caveat-With-Every-Row]]"]
---

# A harness scores which notes a session should read

## Goal

A session that starts cold has to guess which of this repo's 467 notes matter to the job in front of it. Reading `SNAPSHOT.yaml` is the instructed answer and nobody has ever measured what it buys. This feature builds the measuring instrument first and the answer second: a harness that scores any ranker against ground truth the repo already holds, and then one ranker — plain BM25 over the note bodies, no dependencies and no network — as the first candidate to be scored.

The order matters. A ranker with no harness is a preference. The harness is the part that stays useful even if this particular ranker is thrown away.

## What was measured before any of this was written

Measured 2026-09-21 against this repo, with a prototype at `scratchpad/rank.py` and `scratchpad/bench.py`. Every figure below is a real run, not an estimate.

**The corpus.** 467 notes, 2,321,813 bytes, mean note 4,988 bytes. `SNAPSHOT.yaml` is 131,680 bytes today and was a median of 100,016 bytes across the 86 benchmark commits — about 26.3k tokens listing 168 items.

**Benchmark 1, git history.** 86 commits that touched between 2 and 12 notes. The commit message is the query; the notes the commit touched are the labels. Every commit is scored against the note corpus **as it stood at that commit's parent**.

| row, recall at 24 notes | score |
|---|---:|
| ranker, commit message as written | 0.459 |
| ranker, item IDs stripped from the query (the honest row) | 0.340 |
| baseline: the first 24 items `SNAPSHOT.yaml` lists | 0.235 |
| baseline: the snapshot's `focus` block alone (3-5 ids) | 0.257 |
| floor: the 24 most recently updated notes | **0.450** |
| baseline: every item the snapshot lists (~26.3k tokens, 168 items) | **0.535** |

**The claim this feature was built on does not survive its own measurement.** At a 24-note budget the ranker's honest row scores 0.340. Doing nothing but reading the 24 most recently updated notes scores 0.450. Reading the whole snapshot scores 0.535. The ranker loses to both, and REQ-0032 exists precisely so that a ranking claim cannot stand without this comparison.

**Why the earlier figures said the opposite.** The prototype indexed the *working tree* while scoring labels from past commits. A note's present text was written partly by the commit being scored and partly by commits after it, so the query matched text that did not exist when the label was created. That is a train/test leak, and `rank-bench.py --worktree` measures it by holding the ranker fixed and changing only where the notes are read from:

| recall at 24 | corpus pinned per commit | corpus from the working tree |
|---|---:|---:|
| ranker, as written | 0.459 | 0.768 |
| ranker, IDs stripped | 0.340 | 0.629 |
| snapshot, first 24 items | 0.235 | 0.235 |
| snapshot `focus` block | 0.257 | 0.257 |
| floor, most recently updated | 0.450 | 0.093 |

The two snapshot rows are identical across both runs because neither reads the note corpus. That is the control: the difference in the ranker's rows is the leak and nothing else. The superseded figures of 0.768 / 0.620 / 0.152 were all measured under it.

**Benchmark 2, the cold-start baseline.** Folded into the table above; it is the same run, scored at the same budgets against the same labels, which is what REQ-0032 asks for.

**Benchmark 3, real sessions against real commits.** Nine stored transcripts aligned to the commits in their time window, with the ranker given the same note budget the session used.

| | notes | recall |
|---|---:|---:|
| what the session actually read | 25.6 mean | 0.75 |
| the ranker at the same budget | 25.6 | 0.54 |

**So the ranker does not replace a session doing its work.** A finished session reads better than the ranker ranks, 0.75 against 0.54. What the ranker beats is the cold start — the moment before any of that reading has happened. That is the claim this feature is allowed to make.

**Speed.** 0.9 ms per query once the index is warm. `validate-docs.sh` takes 5.31 s for comparison. The git and snapshot benchmarks take a few seconds; the transcript benchmark takes 2.1 s.

## What the numbers do not say

Four limits, each of which is somebody's task below rather than a footnote.

1. **The git-history labels measure the wrong thing.** A commit records the notes the work *wrote*. Close-out mechanically touches the task note and the snapshot, so some labels are outputs of the work rather than inputs to it. The bias is the same in every row, so row-to-row comparison survives; the absolute figure does not mean "N% of what you needed to read". The fix is to take the gold set from what sessions actually read, which is TASK-0152.
2. **Nine transcripts is not a sample.** The parser reads four tool-input fields (`file_path`, `command`, `pattern`, `path`), so a note reached through a subagent or from a glob result is invisible, and 86 of 96 transcripts drop out for having too little to score. TASK-0152 widens it.
3. **The ranker is untuned.** `k1`, `b` and the status and recency weights were set by convention, not by search. One change already mattered: an over-aggressive length normalisation had buried the corpus's largest note at rank 44 of 360 for a near-verbatim title query, and removing it lifted recall at every depth. TASK-0154 runs the sweep.
4. **The ranker is lexical only.** It cannot match a query whose words do not appear in the note. Whether that gap is what costs the missing recall is unknown until somebody reads the misses, which is a Definition-of-Done line on TASK-0154.

## Scope

- A harness, `rank-bench.py`, with three benchmarks and the cold-start baseline, scoring any ranker through one small interface.
- Every number it prints carries the caveat that qualifies it, in the output itself.
- A ranker, `rank-notes.py`: BM25 over note bodies, a length normalisation, a boost for an active status, a boost for a recent `updated:` date, and a large boost for an item ID named in the query. Standard library only.
- A parameter sweep, on a split that keeps the sweep from simply fitting the benchmark.
- One reference note recording the first full run, so the figures in this note have a dated source.

## Out of scope

- **A semantic reranker (Jev / TypeSafe).** The `typesafe@typesafe-ai` plugin is installed and `TYPESAFE_API_KEY` is in the shell profile, and neither is used here. No call has been made and none is planned in this feature. The decision waits on evidence this feature produces: TASK-0154 inspects the highest-ranked misses and records whether the query wording overlapped the note. If the misses are mostly wording gaps, a rerank stage is worth pricing; if they are not, it would buy nothing. **Do not scaffold that work before that line is ticked.**
- **Wiring the ranker into the `SessionStart` hook.** The hook's output is [[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]]'s subject and its token budget is already contested. This feature produces a script and the evidence about what it is worth; who gets the hook is decided afterwards, with the numbers in hand.
- **Changing what `SNAPSHOT.yaml` is for.** Nothing here makes the snapshot less canonical. The measurement says the snapshot's ordering is a weak retrieval index, which is a different claim from what the snapshot is for.

## Where the code lands

**The notes live here; the code lands in the template.** `~/Dev/repos/project-os`, as `tools/scripts/rank-notes.py` and `tools/scripts/rank-bench.py`, dogfooded in this repo through the vendored copy. Settled by Edwin on 2026-09-21, and it is what this repo's `CLAUDE.md` already says: project-os-dev is the planning and tracking layer, and the template repo is the implementation target. A session picking up TASK-0150 should not have to work this out again.

**The overlap with `project-os-bench` is recorded, not acted on.** That repo's FEAT-0007 payoff study owns the adjacent question — is the snapshot worth its tokens — and its TASK-0008 orientation probe proposes to answer it by running a fresh agent in two arms, with and without `SNAPSHOT.yaml`. This feature's cold-start baseline (TASK-0151) is a cheaper, offline, partial answer to the same question: it scores the snapshot's ordering as a retrieval index rather than watching an agent use it. Edwin settled on 2026-09-21 that bench does not implement this work and that the overlap needs a line here rather than a new item. This is that line.

## Acceptance

- One command scores a ranker against all three benchmarks and the cold-start baseline, and re-running it on an unchanged repo reproduces the same figures.
- Every row of the output names its ground truth and its budget, and each row taken from git-history labels prints the caveat that those labels are notes written rather than notes read.
- The cold-start table reports the `focus` block, the first 24 items, the whole snapshot and the ranker at 24, all against one set of labels.
- The transcript benchmark keeps more than the 9 sessions the four-field parser survives, and its note says how many of the 96 it now reads and why the rest still drop out.
- The ranker's parameters come from a recorded sweep with a held-out split, and the note says what the sweep moved and what it did not.
- Neither script imports anything outside the standard library, and neither is called from the pre-commit hook or `validate-docs.sh`.

## Verification

Not yet run. [[TST-0021-Caveat-With-Every-Row]] is the walked check; TASK-0153 adds an executable check when the ranker becomes a supported script.

## Links

- Plan: [[features/note-relevance/plan/PLAN|PLAN]]
- Requirement: [[REQ-0032-Ranking-Claims-Measured]]
- Risk: [[RISK-0004-Transcript-Privacy]]
