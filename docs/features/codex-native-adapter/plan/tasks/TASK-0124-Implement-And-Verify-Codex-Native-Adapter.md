---
type: "[[task]]"
id: TASK-0124
title: "Implement and verify the Codex native adapter"
status: done
phase: "[[PHASE-0006]]"
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["[[FEAT-0032-Codex-Native-Project-Adapter]]"]
parent: "[[FEAT-0032-Codex-Native-Project-Adapter]]"
effort: L
due: ""
depends: []
blocks: []
related: [RISK-0003]
tests: [TST-0012]
---

# Implement and verify the Codex native adapter

## Definition of Done
- [x] Generator emits Codex skills, agents, and hook configuration from canonical sources.
- [x] Hook runner checks lifecycle events using Codex payloads, with tested failures and exemptions.
- [x] Adapter guidance and hook contract map match implementation.
- [x] Template and tracking validators pass.

## Steps
- [x] Add generated native Codex artifacts and safe hook installation.
- [x] Add hook logic and a fixture test.
- [x] Update adapter guidance and contract documentation.
- [x] Run tests, drift check, and docs validation; record any limits.

## Notes
The upstream template is `/Users/Edwin/Dev/repos/project-os`. This note is its development record because the template snapshot is intentionally a placeholder.

## Verification 2026-09-16
- `bash ../project-os/tools/scripts/test-codex-adapter.sh`: 12 fixtures passed, including a failing linked test denial, cross-repository target gating, shell redirection, trust-safe hook installation, and stale generated output detection.
- `python3 ../project-os/tools/scripts/generate-adapters.py --check`: all 64 generated artifacts current after marking the new files intent-to-add.
- `bash ../project-os/tools/scripts/test-hooks.sh`: 74 Claude hook assertions passed.
- `bash ../project-os/tools/scripts/test-verdict-model.sh`: 31 assertions passed.
- `bash ../project-os/tools/scripts/validate-docs.sh` and this repository's validator: zero errors.
- Codex's repository hook trust still requires a user `/hooks` review; the fixture suite tests the runner directly and does not claim a live trusted Codex session.
- The template changes were committed locally as `336d5f9 Add native Codex project adapter`. Push, CI confirmation, and an independent feature/requirement review remain for FEAT-0032 close-out.
