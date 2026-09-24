---
type: "[[task]]"
id: TASK-0161
aliases: ["TASK-0161"]
title: "The validator reports a focus item or an in-flight task that has no snapshot entry"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"]
parent: "[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"
effort: S
due: ""
depends: []
blocks: []
related: ["[[FEAT-0015-Derived-State]]"]
tests: ["[[TST-0022]]"]
---

# The validator reports a focus item or an in-flight task that has no snapshot entry

## Definition of Done
- [x] A focus ID that resolves to a note but has no `items.*` entry is reported — FOCUS-MEMBERSHIP
- [x] A task whose note status is `backlog` or `doing`, listed in `tasks:` by a snapshot feature or phase whose own status is not terminal, is reported when it has no `items.tasks` entry — TASK-MEMBERSHIP; issues' `tasks:` lists count too
- [x] Both checks are measured over every fleet repo first; each ships as an error only if it finds nothing, and otherwise warns with a promotion date (ADR-0011 clause 3) — measured 2026-09-24 over 13 repos: TASK-MEMBERSHIP 20 (your-health 8, project-os-cockpit 7, your-trainer 5), FOCUS-MEMBERSHIP 2 (your-applications.com 1, yourtrainer-mcp 1), this repo 0. Spot-checked: your-trainer's TASK-0132 has a note, FEAT-0027 lists it, and the snapshot has no entry. Both warn until 2026-12-23; every repo validates OK with the template's validator
- [x] A harness asserts both findings and their absence on a correct snapshot, and fails when either check is removed — `test-snapshot-membership.sh`, TST-0022, 9 of 9; mutations recorded on TST-0022
- [x] The template is synced here and this repo validates — template `d93d847`, `cmp` identical; `validate-docs.sh` OK

## Steps
- [x] Add the checks to `validate-docs.py` in the template.
- [x] Measure over the fleet.
- [x] Write the harness and link it from a test note.

## Notes
Placed under FEAT-0015 (derived state) because the check is about the snapshot and the notes agreeing; the parent is the issue.
