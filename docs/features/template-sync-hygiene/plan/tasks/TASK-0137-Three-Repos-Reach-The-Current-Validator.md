---
type: "[[task]]"
id: TASK-0137
aliases: ["TASK-0137"]
title: "Three repos reach the current validator"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
effort: "Medium"
due: ""
depends: [TASK-0134]
blocks: []
related: []
verification_waiver: "Grooming of three repos' notes; the evidence is each repo validating with the template's validator, recorded below"
waiver_expires: 2026-12-18
tests: []
---

# Three repos reach the current validator

## Definition of Done
- [x] edankert.com (40 PARENT-BACKLINK and 7 SNAPSHOT-MEMBERSHIP errors), your-applications.com (50 and 13) and yourtrainer-mcp (6 SNAPSHOT-MEMBERSHIP and 10 VERIFY) validate with the template's current validator.
- [x] Stale manual tests (VERIFY) are walked again or given a dated waiver. Either is Edwin's call and is asked, not assumed.
- [x] Each repo takes the template's `validate-docs.py`.

## Outcome, 2026-09-18
- **edankert.com is done** (`4bbd09c`). Seven feature notes gained the tasks that name them as parent, 39 tasks and 1 issue, and it runs the template's current validator.
- **your-applications.com** (`1842e40`). Eleven notes and nineteen snapshot entries gained their tasks. Two are held for Edwin: TASK-0161 (parent FEAT-0028) and TASK-0162 (parent FEAT-0026) are `doing` under features marked `done`.
- **yourtrainer-mcp** (`da0ed06`). Six snapshot entries gained their tasks. Nine tests (TST-0001, 0005 to 0010, 0012, 0013) are marked manual and `passing`, with `last_verified` 2026-05-29. Each is a pytest suite that names its command in `entrypoint:` but has no `command:`.
- **Both repos keep their current validator** until Edwin decides these. The fixes came from facts the notes already record, and no `updated:` date moved.

## Closed, 2026-09-18

Edwin decided both open points: "mark the tasks finished, add the command field".
- **your-applications.com** (`0d8ef0b`). TASK-0161 and TASK-0162 were checked against the code, then marked done with a note separating what was checked from what rests on his word. Both joined their features' lists, and the repo took the template's validator. The ADR counter change in its SNAPSHOT.yaml is someone else's uncommitted work and stays out of every commit.
- **yourtrainer-mcp** (`de1e128`). The nine pytest suites carry `command:` equal to their `entrypoint:` and are `active` (ADR-0025). `ci.suite_command: "pytest -q"` runs them once on CI, locally 226 passed. The repo took the template's validator.
- **A template change this needed** (project-os `0ba6102`). The docs workflow installs a Python project before `run-tests.py --ci`, or every pytest command is unrunnable on CI. It reached the fleet in one more sync.
- **All three repos now run the template's current validator.**
