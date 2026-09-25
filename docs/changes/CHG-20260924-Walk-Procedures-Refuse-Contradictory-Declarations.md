---
type: "[[change]]"
id: CHG-20260924-Walk-Procedures-Refuse-Contradictory-Declarations
title: "A walk procedure that declares one thing twice, or declares something that can never apply, now falls back to per-check rows"
status: merged
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
commit: ""
pr: ""
impacts: ["tools/scripts/walk-sheet.py", "tools/scripts/test-walk-preparation.py", "tools/scripts/test-walk-sheet.sh", "tools/instructions/TESTING.md", "docs/decisions/ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure.md"]
issues: ["[[ISS-0085-Parallel-Reviewers-Mutate-The-Same-Working-Tree]]"]
features: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TST-0023]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]"]
---

# A walk procedure that declares one thing twice, or declares something that can never apply, now falls back to per-check rows

## Summary

`walk-sheet.py --check` and the walk sheet now refuse a procedure whose declarations contradict each other. That covers one step or setup id declared twice in the same map, a setup, readiness or action declaration for a platform its step never runs on, and a platform name with no ledger. A check's `walk_readiness_for` with a platform that has no ledger is refused too. A refused procedure prints its per-check rows, as any other refused procedure does. Your Trainer's 14 procedures pass on both platforms, so no walk changes today.

## Impact

- No screen changed: the walk generator and its validator. A procedure that trips a new check shows the existing "no longer matches what the release owes" notice and its per-check rows in the sheet and the cockpit.

Also: a problem that holds on every platform prints once from `--check`; ADR-0045 carries a callout naming ADR-0046 as its amendment; TESTING.md rule 9 lists the new refusals. The generator is synced byte-identical to project-os-dev, project-os-cockpit (its script and both bundled copies) and your-trainer.

## Documentation Coverage (All Types Considered)

- features: updated (FEAT-0033)
- requirements: updated at close (REQ-0031)
- tasks: updated (TASK-0125, done)
- issues: new (ISS-0085, from the review)
- tests: new (TST-0023)
- workflows: not-applicable
- decisions: updated (ADR-0045 amendment callout)
- risks: not-applicable (no new dependency, variable or path)
- changes: new (this note)
- snapshot: updated

## Follow-ups

- [ ] Your Trainer's `test-walk-corpus.py` fails 12 of 57, with or without this change, because of the procedure its PHASE-025 close-out added; its TASK-0960.
- [ ] Edwin: sheet step numbering against procedure prose, and criterion 5's "actual parent" for screens three levels deep.
