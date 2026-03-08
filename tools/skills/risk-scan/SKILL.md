---
type: skill
id: SKILL-RISK-SCAN
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, risks]
---

# Skill: Risk scan

## When to use
- Before starting implementation for a new feature or a change that alters behavior/contracts.
- When an issue indicates brittle assumptions or external dependencies.

## Inputs
- Planned changes (feature/tasks/issues) and impacted repo paths.

## Outputs
- Optional new/updated `RISK-*` note(s) under `../../../docs/risks/`.
- `../../../SNAPSHOT.yaml` updated (`items.risks` + links from impacted features/tasks/issues).

## Checklist
1. Check triggers:
   - new external dependency/toolchain/runtime
   - new required env var/config surface
   - directory layout/artifact path changes
   - runtime/performance cost increase
   - security/license/credential exposure
2. If any trigger applies, create/update a `RISK-*`:
   - set likelihood/impact and concrete mitigations
   - link mitigations to tasks when work is planned
3. Update `../../../SNAPSHOT.yaml` to link the risk from impacted items.
