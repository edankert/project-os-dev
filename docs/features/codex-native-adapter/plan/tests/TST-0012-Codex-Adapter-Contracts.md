---
type: "[[test]]"
id: TST-0012
title: "Codex adapter contracts"
status: active
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["[[FEAT-0032-Codex-Native-Project-Adapter]]"]
scope: feature
level: system
entrypoint: "../project-os/tools/scripts/test-codex-adapter.sh"
command: "bash ../project-os/tools/scripts/test-codex-adapter.sh"
last_verified: ""
covers: ["[[FEAT-0032-Codex-Native-Project-Adapter]]", "[[REQ-0030-Codex-Receives-Native-Project-OS-Integration]]"]
issues: []
tasks: ["[[TASK-0124-Implement-And-Verify-Codex-Native-Adapter]]"]
artifacts: []
adequacy: "Test denied and allowed fixtures, generated-file drift, and hook-install preservation."
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# Codex adapter contracts

## Purpose
The fixture suite catches changes to Codex hook payload handling, generated artifacts, and installation behavior.

## Procedure
- Run `bash ../project-os/tools/scripts/test-codex-adapter.sh` from project-os-dev.

## Expected results
- The suite exits zero and reports all assertions passing.

## Evidence (fill after running)
- `python3 tools/scripts/run-tests.py --filter TST-0012` reported `passing=1 failing=0 unrunnable=0` on 2026-09-16. The executable test remains `status: active`; CI supplies its verdict.

## Adequacy (who verifies this test?)
- A denied document-first fixture and an allowed exemption must produce different decisions; a stale generated file must make `--check` fail.
