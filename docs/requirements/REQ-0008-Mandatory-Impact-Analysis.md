---
type: "[[requirement]]"
id: REQ-0008
title: "Impact analysis must run as mandatory preflight for new requirements"
status: approved
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
priority: high
implements: [FEAT-0005]
acceptance:
  - "Feature-scaffold skill includes impact analysis as a mandatory step"
  - "Issue-intake skill includes impact analysis as a mandatory step"
  - "Impact analysis skill exists with explicit STOP gate on conflict detection"
  - "LIFECYCLE.md includes impact analysis in preflight for new requirements"
related: [ADR-0004]
---

# Impact analysis must run as mandatory preflight for new requirements

## Acceptance Criteria

- [ ] Feature-scaffold skill includes impact analysis as a mandatory step
- [ ] Issue-intake skill includes impact analysis as a mandatory step
- [ ] `tools/skills/impact-analysis/SKILL.md` exists with structured playbook
- [ ] Impact analysis skill includes mandatory STOP when conflicts are detected
- [ ] LIFECYCLE.md preflight includes impact analysis step for new requirements
