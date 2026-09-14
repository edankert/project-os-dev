---
type: "[[plan]]"
title: "Delivery plan — surfaces are screens, change notes name them, and the survey shows them"
status: draft
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"]
implements: ["[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"]
related: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[PHASE-0005-The-Walk-Reads-As-A-Script]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — surfaces are screens

## Where the work lands

Every file changes in `~/Dev/repos/project-os`. This repo holds the record. your-trainer and project-os-cockpit receive the result through TASK-0123.

## Delivery sequence

1. **[[TASK-0116-TAXONOMY-States-What-A-Surface-Is|TASK-0116]]: the rules.** TAXONOMY.md and `surface.md`. First, because the Impact field and the survey both name surfaces by these rules.
2. **[[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed|TASK-0117]]: the input.** `change.md`'s Impact section, `SCHEMAS.md`, and the change-note and close-out skills.
3. **[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures|TASK-0118]]: the output.** TESTING.md rule 2, `walk-sheet.py`'s survey, the capture map, and TST-0011's fixture.

## Dependencies

- **Hard:** ADR-0044 accepted before TASK-0116; ADR-0045 accepted before TASK-0117 and TASK-0118 change TESTING.md.
- **Soft:** TASK-0121 in FEAT-0031 edits the same `render()` in `walk-sheet.py`; land TASK-0118 first or rebase deliberately.

## Open questions

- Where the capture-key map lives: a `captures:` field on each surface note, or one file owned by the gallery tool (ADR-0044 acceptance box 2).
- How the generator finds "the last release tag": the newest `REL-*` note at `status: released` and its `tag:`, or the newest git tag matching a pattern. your-trainer tags Android as `v2.1.8` and iOS as `ios/v0.1.0`, so it has to be per platform.
