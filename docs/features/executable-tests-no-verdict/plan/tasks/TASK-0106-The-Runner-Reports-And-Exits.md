---
type: "[[task]]"
id: TASK-0106
aliases: ["TASK-0106"]
title: "The runner reports and exits; it no longer writes"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
parent: "[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"
effort: S
depends: ["[[TASK-0107]]"]
related: []
tests: ["[[TST-0008]]"]
---

# The runner reports and exits; it no longer writes

## Definition of Done
- [ ] `tools/scripts/run-tests.py` has no `--write`; it runs every `command:`, prints the outcome per test, and exits 1 on any failure.
- [ ] Its docstring and help say CI is the verdict.
- [ ] The CI seed `.github/workflows/validate-docs.yml` runs it after the validator, so a red executable test is a red build.

## Steps
- [ ] Remove the stamping branch; keep discovery, the timeout and the unrunnable handling.
