---
type: "[[task]]"
id: TASK-0106
aliases: ["TASK-0106"]
title: "The runner reports and exits; it no longer writes"
status: done
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
- [x] `tools/scripts/run-tests.py` has no `--write`; it runs every `command:`, prints the outcome per test, and exits 1 on any failure.
- [x] Its docstring and help say CI is the verdict.
- [x] The CI seed `.github/workflows/validate-docs.yml` runs it after the validator, so a red executable test is a red build.

## Steps
- [x] Remove the stamping branch; keep discovery, the timeout and the unrunnable handling.

## Notes

Landed as template commit `3d67f11` on 2026-09-03. The runner keeps discovery, the timeout and the unrunnable handling; the CI seed runs it after the validator.
