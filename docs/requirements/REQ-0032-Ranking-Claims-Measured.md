---
type: "[[requirement]]"
id: REQ-0032
aliases: ["REQ-0032"]
title: "A claim about which notes to read carries the measurement that backs it"
status: implemented
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["Edwin, 2026-09-21: 'make it so'", "measurement session 2026-09-21 against project-os-dev: 467 notes, 2,321,813 bytes"]
priority: high
scope: "Any mechanism that hands an agent a subset of the notes"
acceptance: ["One command scores a ranker against ground truth already in the repo", "Every reported recall names the ground truth and the budget it was scored at", "The snapshot baseline is reported beside the ranker at the same budget", "A number whose ground truth is known to be biased carries that caveat wherever it is printed", "The harness runs on the standard library alone and is never added to the commit gate"]
implements: "[[FEAT-0038-Note-Relevance-Harness]]"
verifies: []
related: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]", "[[RISK-0004-Transcript-Privacy]]"]
tests: ["[[TST-0021-Caveat-With-Every-Row]]"]
---

# A claim about which notes to read carries the measurement that backs it

## Statement

Anything in project-os that tells an agent *these are the notes you need* must say how often it is right, measured against ground truth that already exists in the repo, at the budget it proposes, beside the baseline it would replace. Today nothing does. `SNAPSHOT.yaml` is described as the canonical active context and is the largest single artefact in every repo, and no number anywhere says how much of what a session needed it actually names.

A recall figure on its own is not a measurement. Ground truth drawn from git history records the notes a commit *wrote*, not the notes the work *read*, so a figure taken from it is comparable across rankers and is not a statement about how much of the reading a ranker covers. The requirement is that the caveat travels with the number, in the harness output, not only in a note somebody may open.

## Approved, 2026-09-21

Edwin approved these acceptance criteria on 2026-09-21 ("approve REQ-0032"), which releases [[FEAT-0038-Note-Relevance-Harness|FEAT-0038]] from the requirement-approval gate (`tools/instructions/STATUSES.md` `[[feature]]`). Approval means these five criteria are the ones the work builds against; a departure is amended here rather than reconciled at close-out.

Which document says the approval is his was itself unclear: `tools/skills/feature-scaffold/SKILL.md` step 7 addresses the scaffolding agent and names no human, while `tools/instructions/OWNERSHIP.md` makes a requirement's owner its stakeholder and approver. [[ISS-0077-Who-Approves-Requirements|ISS-0077]] carries that disagreement.

## Acceptance Criteria

- [x] One command scores a ranker against ground truth already in the repo — evidence: `python3 tools/scripts/rank-bench.py` from any project-os repo root, no arguments; runs the commit benchmark then the session benchmark. Two consecutive runs on an unchanged checkout gave byte-identical figure rows, 2026-09-21.
- [x] Every reported recall names the ground truth and the budget it was scored at — evidence: the harness header names the labelled set, the corpus range and the selection rule; every row is printed at budgets of 5, 10, 24 and 50, and the session benchmark scores each session at the number of notes it actually read. [[Note-Ranking-Measured-2026-09-21]].
- [x] The snapshot baseline is reported beside the ranker at the same budget — evidence: `first N items SNAPSHOT.yaml lists` and `the snapshot's focus block alone` are rows in the same table at the same budgets; a whole-snapshot read is printed beneath it as unbudgeted. [[Note-Ranking-Measured-2026-09-21]], Benchmark 1.
- [x] A number whose ground truth is known to be biased carries that caveat wherever it is printed — evidence: the commit benchmark prints the notes-written-not-read caveat in its header and closes with "Every row above carries the caveat printed in the header"; the reference note repeats it verbatim beside the table. The session benchmark states separately that its labels are notes read, so that caveat does not apply to it.
- [x] The harness runs on the standard library alone and is never added to the commit gate — evidence: the three scripts import only argparse, collections, dataclasses, datetime, importlib, json, math, os, pathlib, re, statistics, subprocess, sys and time; `grep -rn 'rank-notes\|rank-bench'` over `validate-docs.sh` and `install-git-hooks.sh` returns nothing, checked 2026-09-21.

## Outcome

Implemented 2026-09-21. The harness exists and the measurement it forced came back against the thing being built: the ranker scores 0.253 where sorting by last-modified date scores 0.275, pooled over 87 real sessions. This requirement was written so that a ranking claim could not stand without that comparison, and the comparison refuted the claim. [[Note-Ranking-Measured-2026-09-21]] carries the run.

## Traceability

- Implements: [[FEAT-0038-Note-Relevance-Harness]].
- Verified by: [[TST-0021-Caveat-With-Every-Row]], and the executable check TASK-0153 adds when the ranker becomes a supported script.
