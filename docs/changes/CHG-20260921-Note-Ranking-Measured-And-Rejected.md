---
type: "[[change]]"
id: CHG-20260921-Note-Ranking-Measured-And-Rejected
title: "Three scripts measure whether a note ranker earns its place; it does not"
status: merged
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[PHASE-0008-Measured-Note-Ranking]]"]
related: ["[[FEAT-0038-Note-Relevance-Harness]]", "[[REQ-0032-Ranking-Claims-Measured]]", "[[Note-Ranking-Measured-2026-09-21]]"]
---

# Three scripts measure whether a note ranker earns its place; it does not

## What changed

The template gains three scripts under `tools/scripts/`, standard library only:

- `rank-notes.py` — ranks the repo's notes against a plain-language query. `rank-notes.py "the review keeps running past its budget" -k 10`, with `--json` and `--scores`.
- `rank-bench.py` — scores a ranker against commits that touched 2–12 notes, with the cold-start snapshot baseline and a recency floor as rows in the same table. No arguments needed. Runs `rank-bench-sessions.py` afterwards so one command reports both.
- `rank-bench-sessions.py` — scores a ranker against what real sessions read: opening prompt as query, notes opened as labels, corpus pinned to the commit the session started from.

Nothing calls them. They are not in `validate-docs.sh` or the pre-commit hook, and adding them there is refused by [[REQ-0032-Ranking-Claims-Measured]]'s fifth criterion.

## Impact

No existing behaviour changes. No note format, path, gate or command that anything depended on is altered. A repo that ignores these three files is unaffected.

What changes is what can be claimed. [[REQ-0032-Ranking-Claims-Measured]] now forbids any mechanism that hands an agent a subset of the notes unless it states its recall against ground truth already in the repo, at the budget it proposes, beside the baseline it replaces. `rank-bench.py` is how that is satisfied, and `--ranker` scores a candidate other than the bundled one.

## The finding

A BM25 ranker does not beat sorting the notes by last-modified date. Commits: 0.340 against 0.450 at a 24-note budget. Real sessions, 87 across 7 repos: 0.253 against 0.275, a gap of 1.1 standard errors. Figures and caveats in [[Note-Ranking-Measured-2026-09-21]].

Earlier figures claiming the opposite came from indexing the working tree while scoring labels from past commits — a train/test leak, which `rank-bench.py --worktree` now measures rather than describes.
