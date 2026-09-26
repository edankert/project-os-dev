---
type: "[[test]]"
id: TST-0035
aliases: ["TST-0035"]
title: "An edit to a ticket that was finished at the last release warns, and the tools' own writes and renames do not"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0178]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-frozen-edit.sh"
command: "bash ../project-os/tools/scripts/test-frozen-edit.sh"
covers: ["[[ISS-0097-Nothing-Stops-A-Released-Ticket-Being-Edited]]"]
tasks: ["[[TASK-0178]]", "[[TASK-0184]]"]
issues: ["[[ISS-0097-Nothing-Stops-A-Released-Ticket-Being-Edited]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 11 assertions. Four mutations in a scratch copy: M1 tool-written fields count as edits, 1 failure; M2 the status at the tag is ignored, 1; M3 staged edits are not seen, 1; M4 the superseded status counts as an edit, 1. Pristine 11 of 11. TASK-0184 added 3 assertions and 3 mutations (no released filter, 1 failure; the status at the tag ignored, 1; FROZEN-EDIT hidden too, 4); pristine 14 of 14."
related: []
---

# An edit to a ticket that was finished at the last release warns, and the tools' own writes and renames do not

## Purpose

ISS-0097, ADR-0048: a ticket whose release is out is a record, and editing it is a warning so an unforeseen correction stays possible and visible.

## Procedure

`bash tools/scripts/test-frozen-edit.sh` in `~/Dev/repos/project-os`: a copy of the template in a git repo, tagged `v1.0`, with a `released` REL note naming that tag.

- Nothing edited: no FROZEN-EDIT.
- An edit to a task that was `done` at `v1.0` warns, naming the release; so does an edit to a change note.
- A task still `doing` at `v1.0` is not frozen.
- A reverse list the tools write, the sync's supersession stamp (pointer and status), and a rename are not edits.
- It is a warning: the validator still passes.
- A staged edit warns (the pre-commit case); once committed, nothing is reported.
- With no release note, the newest git tag is the boundary.

## Expected results

- Exit 0: 14 of 14, 2026-09-26. The last three assertions are TASK-0184's: a released task's content finding is hidden and counted while FROZEN-EDIT on it still shows, and the same finding on a task finished since the release is shown.
