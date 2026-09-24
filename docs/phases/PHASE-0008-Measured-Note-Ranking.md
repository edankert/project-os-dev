---
type: "[[phase]]"
id: PHASE-0008
aliases: ["PHASE-0008"]
title: "A ranking of the notes is measured before it is trusted"
status: done
order: 8
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
goal: "Nothing in project-os may claim to know which notes a session needs until a harness has scored that claim against the repo's own history, beside the cold-start baseline it would replace. Build the harness, then score the cheapest candidate."
features: [FEAT-0038]
requirements: [REQ-0032]
tasks: [TASK-0150, TASK-0151, TASK-0152, TASK-0153, TASK-0154, TASK-0155]
issues: []
related: [TST-0021, RISK-0004, FEAT-0021, ISS-0031]
tags: [retrieval, measurement]
---

# A ranking of the notes is measured before it is trusted

## Goal

A session that starts cold has to guess which of this repo's 467 notes matter to the job in front of it, and the instructed answer — read `SNAPSHOT.yaml` — has never been measured. This phase builds the instrument that settles such questions, and only then the first answer to it.

The order is the whole point. The harness outlives whichever ranker wins; a ranker without a harness is a preference with a script attached.

## Scope

- [[FEAT-0038-Note-Relevance-Harness|FEAT-0038]] and its six tasks: the harness and the git-history benchmark, the cold-start baseline, the transcript benchmark with a widened extraction, the ranker as a supported script, the parameter sweep, and the reference note recording the first full run.
- [[REQ-0032-Ranking-Claims-Measured|REQ-0032]], which states the rule the phase exists to install.
- [[TST-0021-Caveat-With-Every-Row|TST-0021]] and [[RISK-0004-Transcript-Privacy|RISK-0004]].

**Where the code lands.** The notes live here; the code lands in the template, `~/Dev/repos/project-os`, as `tools/scripts/rank-notes.py` and `tools/scripts/rank-bench.py`, and is dogfooded in this repo through the vendored copy. Settled by Edwin on 2026-09-21, and it is what `CLAUDE.md` already says this repo is for.

## Out of Scope

- **A semantic reranker (Jev / TypeSafe).** Deferred to evidence this phase produces, not to a later date: TASK-0154 reads the misses and records whether a rerank stage is worth pricing. No reranker work is scaffolded before that line is ticked.
- **Wiring the ranker into the `SessionStart` hook.** That surface and its token budget belong to [[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]]. This phase produces the script and the evidence; who gets the hook is decided afterwards, with numbers in hand.
- **Changing what `SNAPSHOT.yaml` is for.** Measuring the snapshot's ordering as a retrieval index says nothing about its role as the canonical active context.
- **`project-os-bench`'s payoff study.** FEAT-0007 and its TASK-0008 orientation probe ask an adjacent question with a different instrument — a two-arm experiment on a live agent, where this is an offline score of a retrieval function. Edwin settled on 2026-09-21 that bench does not implement this; the overlap is recorded in FEAT-0038 and nowhere becomes a new item.

## Exit Criteria

- [~] One command reports the benchmarks and the cold-start baseline together, and a second run reproduces every figure — **reconciled: two benchmarks, not three.** `python3 tools/scripts/rank-bench.py` runs the commit benchmark then the session benchmark, with the cold-start baseline as rows in the first. The third, a link-graph proxy that labelled a note with its own outbound links, was dropped as too noisy to inform anything — the labels include parent backlinks and boilerplate citations. Two consecutive runs gave byte-identical figure rows, 2026-09-21. Evidence: [[Note-Ranking-Measured-2026-09-21]].
- [x] Every printed recall names its ground truth and its budget, and every row built on git-history labels prints that those labels are notes the commits **wrote** — evidence: the harness header carries the caveat and the table closes with "Every row above carries the caveat printed in the header"; [[Note-Ranking-Measured-2026-09-21]] repeats it verbatim beside the figures. [[TST-0021-Caveat-With-Every-Row|TST-0021]] stays `active` and unwalked, which is where an acceptance test rests (`STATUSES.md`); the walk is owed by someone who did not build the harness and is not a condition of this phase.
- [x] The ranker's recall is reported beside the cold-start baseline at the same note budget, and the phase records which won — **recency won.** The claim this criterion was written against, 0.620 against 0.233 at 24 notes, did not reproduce and is recorded rather than dropped: it came from indexing the working tree while scoring labels from past commits, a train/test leak that `rank-bench.py --worktree` now measures. Pinned, the ranker scores 0.340 against a recency floor of 0.450 and a whole-snapshot read of 0.535. On session labels, pooled over 87 sessions in 7 repos, 0.253 against 0.275 — a gap of 1.1 standard errors. Evidence: [[Note-Ranking-Measured-2026-09-21]].
- [x] The transcript benchmark states how many of the stored sessions it scores and why the rest drop out — evidence: [[TASK-0152-Transcript-Benchmark|TASK-0152]]. It scores 11 of 96 in project-os-dev and says so in its header. The number is not larger because widening the scan from four tool-input fields to the whole record found 4x more note references and **zero** additional sessions: the other 85 never opened a note. Scale came from six further repos instead, 11 to 87.
- [~] The ranker's parameters come from a recorded sweep — **cut when the phase closed on its finding.** [[TASK-0154-Parameter-Sweep|TASK-0154]] is `cancelled`, not deferred: tuning was to close a gap the leaked figures put at 0.115, and the real gap is 0.022 against a floor that costs nothing. Whether a tuned BM25 or a semantic rerank could close it is unanswered and recorded as unanswered in [[Note-Ranking-Measured-2026-09-21]], "What this run does not establish".
- [x] Neither script imports anything outside the standard library, and neither is called from the pre-commit hook or `validate-docs.sh` — evidence: the three scripts import only argparse, collections, dataclasses, datetime, importlib, json, math, os, pathlib, re, statistics, subprocess, sys and time; `grep -rn 'rank-notes\|rank-bench'` over both gates returns nothing, checked 2026-09-21.
- [x] REQ-0032's five acceptance criteria are ticked with evidence — evidence: [[REQ-0032-Ranking-Claims-Measured|REQ-0032]], now `implemented`, each criterion carrying the command or the check that satisfies it.

## What this phase found

A BM25 ranker over the note corpus does not beat sorting the notes by last-modified date. Two label sources built from different evidence agree: commits say 0.340 against 0.450, real sessions say 0.253 against 0.275. The phase closes on that finding rather than on the feature it opened to build.

REQ-0032 is the reason the finding exists. It forbade the claim without the comparison, the comparison was run, and it refuted the claim. A requirement that stops its own feature is the requirement working.

What is left unanswered, and recorded as unanswered: whether tuning closes 0.022, and why the same ranker helps in project-os-deck (+0.091) and hurts in project-os-cockpit (-0.088). The second is the better question.

## Notes

**This is a third active phase.** PHASE-0003 (prompting-guide conformance) and PHASE-0006 (Codex, parked until Codex is back) are both still `active`, and neither absorbs this work. Nothing in `STATUSES.md` or `PHASES.md` limits how many phases are active at once; what is singular is `focus.phase`, which names the milestone being worked and now names this one. If Edwin would rather close or park PHASE-0003 before a third opens, that is his to say.

**It passes the size test** in `tools/skills/phase-planning/SKILL.md`, "When a phase is too small". Its goal states an outcome without listing its parts, and its exit criteria say more than "the tasks are done" — three of them name a number or a reading that no task list implies. It carries nine linked items, against the three-or-fewer mark the skill warns about.

**Sequencing.** TASK-0150 first; TASK-0151, TASK-0152 and TASK-0153 all depend on the interface it defines. TASK-0154 needs both a supported ranker and the baseline, because a sweep with nothing to beat is a number going up. TASK-0155 is worth the most last.
