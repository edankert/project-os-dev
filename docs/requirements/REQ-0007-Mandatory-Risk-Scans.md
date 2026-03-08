---
type: "[[requirement]]"
id: REQ-0007
title: "Risk scans must be mandatory with explicit trigger checklist"
status: approved
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
priority: high
implements: [FEAT-0005]
acceptance:
  - "Close-out, feature-scaffold, and issue-intake skills include mandatory risk scan steps"
  - "Each risk scan step has an explicit trigger checklist"
  - "Agent must create RISK-* note if any trigger applies, or record 'No new risks identified'"
related: [ADR-0004]
---

# Risk scans must be mandatory with explicit trigger checklist

## Acceptance Criteria

- [ ] Close-out skill includes mandatory risk scan with trigger checklist
- [ ] Feature-scaffold skill includes mandatory risk scan with trigger checklist
- [ ] Issue-intake skill includes mandatory risk scan with trigger checklist
- [ ] Trigger checklist covers: new dependencies, env vars, path changes, performance impacts, security exposure
- [ ] Agent must either create a RISK-* note or explicitly record "No new risks identified"
