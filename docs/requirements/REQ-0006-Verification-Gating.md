---
type: "[[requirement]]"
id: REQ-0006
aliases: ["REQ-0006"]
title: "Verification gating must block status transitions when linked tests are not passing"
status: implemented
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
owner: user:edwin
created: 2026-03-08
updated: 2026-07-24
priority: high
implements: ["[[FEAT-0005]]"]
acceptance:
  - "Close-out skill checks linked test statuses as its first step"
  - "Status-transition skill includes a verification gate before done/closed/verified transitions"
  - "Agent must STOP if any linked test is not passing"
related: [ADR-0004]
tests: []
---

# Verification gating must block status transitions when linked tests are not passing

## Acceptance Criteria

- [x] Close-out checks linked test statuses as its first step — evidence: `tools/skills/close-out/SKILL.md` checklist item 1 "Verification gating (mandatory first)": lists `TST-*` IDs, verifies each is `status: passing`, stops and reports the blocker otherwise.
- [x] Status-transition includes a verification gate before terminal transitions — evidence: `tools/skills/status-transition/SKILL.md` step 2 "Pre-transition gates" → "Verification gate", covering task `done`, issue `closed`, requirement `verified`, feature `done` and phase `done` (a superset of the three named here).
- [x] The agent must STOP if a linked test is not passing — evidence: close-out "stop before applying terminal statuses and report the blocker"; mechanically enforced by `tools/scripts/validate-docs.py` (VERIFY error) and the blocking `hooks/verification-gate.py` PreToolUse deny. The stop is escapable only by a recorded `verification_waiver:`, which the validator reports as a logged warning (`QUALITY.md`).


## Amendments (2026-07-21)

The note body previously carried four checkboxes against three frontmatter criteria — the extra one named the transition set (`done`, `closed`, `verified`) that the frontmatter only implied. Per `SCHEMAS.md` (frontmatter `acceptance:` is the criteria of record, one body box per criterion), the body was reconciled to three and the transition set folded into criterion 2's evidence, where the shipped gate is in fact broader (it also covers feature `done` and phase `done`). No criterion was weakened or dropped.
