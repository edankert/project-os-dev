---
type: "[[requirement]]"
id: REQ-0006
title: "Verification gating must block status transitions when linked tests are not passing"
status: approved
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
priority: high
implements: [FEAT-0005]
acceptance:
  - "Close-out skill checks linked test statuses as its first step"
  - "Status-transition skill includes a verification gate before done/closed/verified transitions"
  - "Agent must STOP if any linked test is not passing"
related: [ADR-0004]
---

# Verification gating must block status transitions when linked tests are not passing

## Acceptance Criteria

- [ ] Close-out skill (`tools/skills/close-out/SKILL.md`) checks linked test statuses as step 1
- [ ] Status-transition skill (`tools/skills/status-transition/SKILL.md`) includes a verification pre-transition gate
- [ ] Gate applies before transitions to: `done`, `closed`, `verified`
- [ ] Agent must STOP and report if any linked test is not `status: passing`
