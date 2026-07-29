---
type: "[[test]]"
id: TST-0001
aliases: ["TST-0001"]
title: "Docs validation gate: the repo's own invariants hold"
status: passing
owner: user:edwin
created: 2026-07-25
updated: 2026-07-28
source: []
scope: system
kind: automated
level: system
entrypoint: "tools/scripts/validate-docs.sh"
command: "bash tools/scripts/validate-docs.sh --quiet"
last_run: "2026-07-28T17:11Z"
exit_code: 0
requirements: [REQ-0022]
features: []
issues: []
tasks: [TASK-0067]
artifacts: []
evidence: []
adequacy: ""
related: [ADR-0010]
---

# Docs validation gate

## Purpose

The first executable test note in the fleet, and the end-to-end proof that [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] works: this note's `status` is written by `tools/scripts/run-tests.py` from the exit code of `command:`, never by an author.

## Procedure

Automated. `run-tests.py` executes `bash tools/scripts/validate-docs.sh --quiet` at the repo root and stamps `passing` (exit 0), `failing` (non-zero), or leaves the status alone if the command could not run at all.

## Expected results

- Exit 0 while the repo's snapshot↔notes invariants hold.
- Non-zero the moment they do not — which is what makes this a gate rather than a label.

## Adequacy (who verifies this test?)

A test that cannot fail does not guard. Verified by inversion on 2026-07-25: a sibling note pointed at a deliberately non-zero command was stamped `failing` by the same runner, and a note pointed at a non-existent binary was correctly classified `unrunnable` and left untouched rather than being stamped `failing`. Evidence recorded in [[TASK-0067-Test-Runner|TASK-0067]].
