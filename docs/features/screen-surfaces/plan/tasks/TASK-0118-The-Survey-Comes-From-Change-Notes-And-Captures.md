---
type: "[[task]]"
id: TASK-0118
aliases: ["TASK-0118"]
title: "TESTING.md rule 2 and walk-sheet.py build the survey from change notes merged since the last release tag, grouped by the screens they name, with before and after captures and no test ids"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 1"]
parent: "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"
effort: L
due: ""
depends: ["[[TASK-0116-TAXONOMY-States-What-A-Surface-Is]]", "[[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed]]"]
blocks: ["[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
tests: ["[[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]"]
---

# The survey comes from change notes and captures

## What

The first section of the walk sheet lists the screens changed since the last release. For each screen it prints the sentences from every change note that named it, then the capture from the last release tag beside the capture from the release candidate, where the repo maps a capture key to that screen. It prints no test id.

## Definition of Done

- [ ] TESTING.md "The walk" rule 2 is rewritten to ADR-0045 decision 1, and rule 8's close-out sentence is narrowed to say change notes now carry the Impact list.
- [ ] `walk-sheet.py` finds the last release tag for the platform, lists `docs/changes/CHG-*` notes added since it, reads each Impact list, and groups by surface with children under their parent screen.
- [ ] Before and after captures are resolved through the capture-key map TASK-0116 settles. Where only the after capture exists (a new screen or state), the survey says "new". Where neither exists, it prints the sentence alone.
- [ ] Without a reachable tag (a shallow clone, or no released `REL-*`), the survey prints one line saying so. It never prints an empty survey silently.
- [ ] The survey contains no `TST-` string. Asserted.
- [ ] `test-walk-sheet.sh` gains a fixture repo with a git tag, change notes before and after it, and a capture map. Its survey assertions become TST-0011's command. The old invalidation-event survey assertions in TST-0009 are rewritten, not deleted silently.
- [ ] REQ-0028's criterion 2 is amended in its `## Amendments` section with the reason (ADR-0045).

## Steps

- [ ] Settle the tag lookup (PLAN.md open question 2) before writing code.
- [ ] Write the fixture first, watch the survey assertions fail, then change the generator.
- [ ] Rerun the 28 existing TST-0009 mutations that touch the survey; record which ones no longer apply.

## Notes

- The cockpit bundles this module byte for byte (project-os-cockpit `walk_sheet_bundled.py`). A git call inside it runs inside the cockpit's sidecar too. Check that the sidecar's working directory makes the tag lookup work.
