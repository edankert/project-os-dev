---
type: "[[issue]]"
id: ISS-0069
aliases: ["ISS-0069"]
title: "A regression check whose claim describes current behaviour is never reopened when that behaviour changes"
status: "open"
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: "2026-09-19"
source: ["your-trainer ISS-0414, decided by Edwin on 2026-09-18: 'Take your recommendations'"]
reported_by: user:edwin
question: ""
severity: medium
component: "testing"
parent: ""
related: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"]
tests: []
---

# A regression check whose claim describes current behaviour is never reopened when that behaviour changes

## Problem

A walker can be shown a check as settled that no longer holds. TESTING.md routes a check that `covers:` an `ISS-*` into the regression section, and a regression check is never invalidated by a change. Some regression checks, though, state how the app behaves now, not only that a fixed defect stays fixed. When a later change alters that behaviour, the check stays ticked. your-trainer's TST-0642 (`covers: ISS-0387`) is the case that raised it ([[your-trainer#ISS-0414]]).

## Decided

Edwin chose option 2 on 2026-09-18. **When a change overlaps a regression check whose claim describes current behaviour, split the check in two:**
- a regression check that keeps only the defect's own assertion;
- a feature check for the behaviour, which a change can invalidate.

## Next Actions
- [ ] State the split in TESTING.md in project-os, at the rule about regression checks never being invalidated.
- [ ] Sync to the fleet. Then your-trainer's ISS-0414 closes, and TST-0642 is split as the first case.
