---
type: "[[requirement]]"
id: REQ-0000
title: ""
status: draft
phase:
owner: unassigned
created: 2026-01-26
updated: 2026-07-21
source: []
priority: medium
scope: ""
acceptance: []
implements: ""   # at most one [[FEAT-...]] (ADR-0007); empty = no owning feature
verifies: []
related: []
tests: []
---

# <Requirement>

## Statement
<Must/should/shall statement>

## Acceptance Criteria
<One checkbox per entry in the frontmatter `acceptance:` list. Tick only with an evidence pointer, at feature close-out. Every criterion must be ticked or reconciled before this requirement reaches `implemented` (its terminal status) — and an unresolved criterion blocks the owning feature from `done`.>
- [ ] <criterion> — evidence: <path, path:line, command, or note ID>

## Traceability
- Implements: a single `[[FEAT-####-...]]` link (at most one feature owns a requirement)
- Verified by: repo paths (e.g. `tests/run_regressions.sh`) or workflow links
