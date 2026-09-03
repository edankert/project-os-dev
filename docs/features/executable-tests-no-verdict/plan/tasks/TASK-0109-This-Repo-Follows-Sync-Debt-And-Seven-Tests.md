---
type: "[[task]]"
id: TASK-0109
aliases: ["TASK-0109"]
title: "This repo follows: sync its tools, clear its validation debt, strip the seven verdicts"
status: backlog
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
- [ ] The 47 errors the template's validator reports here are cleared: 41 PARENT-BACKLINK (feature notes name the tasks that name them), 3 SNAPSHOT-MEMBERSHIP, 2 METRICS, 1 DECISION-OPTIONS (ADR-0024's options as a numbered list).
- [ ] `tools/` is synced from the template and the adapters regenerated; pre-commit passes.
- [ ] TST-0001 to TST-0007 carry `status: active` and no `last_run:` or `exit_code:`; their prose says CI is the verdict.
