---
type: "[[issue]]"
id: ISS-0084
aliases: ["ISS-0084"]
title: "An in-flight task can be missing from SNAPSHOT.yaml, even as the focus task, and the validator passes"
status: fixed
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["FEAT-0039, 2026-09-24: five new tasks were never added to the snapshot and every check passed", "Edwin, 2026-09-24: 'file the validator gap as an issue and fix'"]
reported_by: agent
question: ""
severity: medium
component: "tools/scripts/validate-docs.py"
parent: ""
related: ["[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]", "[[TASK-0160]]"]
tests: ["[[TST-0022]]"]
---

# An in-flight task can be missing from SNAPSHOT.yaml, even as the focus task, and the validator passes

## Problem

A task that is being worked can be absent from `SNAPSHOT.yaml`, and `validate-docs.sh` still says OK. It said OK even when that task was `focus.task`. Anything that reads the snapshot then loses the task: the session-start orientation leaves it out, and the close-out Stop hook cannot find its note, so it gives its plain reason instead of naming the open boxes.

> [!quote] As reported — 2026-09-24 (user:edwin)
> file the validator gap as an issue and fix.

## Repro

On 2026-09-24, FEAT-0039's five tasks (TASK-0156 to TASK-0160) were written as notes, and the feature's snapshot entry listed them in `tasks:`. The insert that should have added their own `items.tasks` entries matched nothing. `validate-docs.sh` passed through the whole feature, including with `focus.task: TASK-0160`. The gap only showed when the Stop hook quoted nothing for TASK-0160.

## Expected

The validator reports a focus item that has no snapshot entry, and a `doing` or `backlog` task that an in-flight feature or phase lists in the snapshot but that has no snapshot entry of its own.

## Actual

- `FOCUS` accepts a focus ID that resolves to a note, even with no snapshot item.
- `SNAPSHOT-MEMBERSHIP` compares a feature's `tasks:` list in the note with the same list in the snapshot. Both lists were right; nothing checks that each listed task has an entry of its own.

## Evidence

- `tools/scripts/validate-docs.py`, "focus resolution" (`resolves()` accepts a note) and "ISS-0117 SNAPSHOT-MEMBERSHIP" (compares the two lists only). The comment on SNAPSHOT-MEMBERSHIP describes the same cause, a string replace whose pattern no longer matched.

## Resolution

[[TASK-0161]], template commit `d93d847`: FOCUS-MEMBERSHIP and TASK-MEMBERSHIP. Both warn until 2026-12-23, because the fleet already carries 22 such findings in five repos; each repo clears its own before then. Tested by [[TST-0022]].
