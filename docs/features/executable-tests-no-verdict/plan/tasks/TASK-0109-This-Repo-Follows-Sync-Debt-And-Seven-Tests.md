---
type: "[[task]]"
id: TASK-0109
aliases: ["TASK-0109"]
title: "This repo follows: sync its tools, clear its validation debt, strip the seven verdicts"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
parent: "[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"
effort: M
depends: ["[[TASK-0106]]", "[[TASK-0107]]", "[[TASK-0108]]"]
related: []
tests: ["[[TST-0008]]"]
---

# This repo follows: sync its tools, clear its validation debt, strip the seven verdicts

## Definition of Done
- [x] The 47 errors the template's validator reports here are cleared: 41 PARENT-BACKLINK (feature notes name the tasks that name them), 3 SNAPSHOT-MEMBERSHIP, 2 METRICS, 1 DECISION-OPTIONS (ADR-0024's options as a numbered list).
- [x] `tools/` is synced from the template and the adapters regenerated; pre-commit passes.
- [x] TST-0001 to TST-0007 carry `status: active` and no `last_run:` or `exit_code:`; their prose says CI is the verdict.

## Notes

Done 2026-09-03 in this repo's close-out commit: the 47 errors cleared (nine feature notes gained the `tasks:` field they never had, two cancelled tasks added to the snapshot lists, ADR-0024's options as a numbered list, metrics repaired), tools synced from template commit 09ae4dc with `--force` for the eight files that had diverged (AGENTS.md checked by diff: only the template's own changes), the eight command: tests at `active` with no verdict fields, `run-tests.py` 8 of 8, validator clean.
