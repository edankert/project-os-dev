---
type: "[[requirement]]"
id: REQ-0030
title: "Codex receives native project-os integration"
status: approved
phase: "[[PHASE-0006]]"
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["[[FEAT-0032-Codex-Native-Project-Adapter]]"]
priority: high
scope: "Codex adapter generation, hook installation, and lifecycle coverage"
acceptance: ["Canonical skills and agents are generated in Codex native locations", "Lifecycle hooks handle Codex event payloads and preserve existing configuration", "Fixture tests and the generated-artifact check detect regression", "Adapter documentation states activation and remaining limits"]
implements: "[[FEAT-0032-Codex-Native-Project-Adapter]]"
verifies: []
related: [RISK-0003]
tests: [TST-0012]
---

# Codex receives native project-os integration

## Statement
The project-os template must expose canonical playbooks and lifecycle checks through Codex native skills, agents, and hooks.

## Acceptance Criteria
- [ ] Canonical skills and agents are generated in Codex native locations — evidence: `tools/scripts/generate-adapters.py --check`.
- [ ] Lifecycle hooks handle Codex event payloads and preserve existing configuration — evidence: `tools/scripts/test-codex-adapter.sh`.
- [ ] Fixture tests and the generated-artifact check detect regression — evidence: `tools/scripts/test-codex-adapter.sh`.
- [ ] Adapter documentation states activation and remaining limits — evidence: `tools/adapters/codex/ADAPTER.md`.

## Traceability
- Implements: [[FEAT-0032-Codex-Native-Project-Adapter]]
- Verified by: [[TST-0012-Codex-Adapter-Contracts]]
