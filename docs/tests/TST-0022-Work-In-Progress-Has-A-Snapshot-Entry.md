---
type: "[[test]]"
id: TST-0022
aliases: ["TST-0022"]
title: "The validator reports a focus item or an in-flight task that has a note but no snapshot entry"
status: active
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-snapshot-membership.sh"
command: "bash ../project-os/tools/scripts/test-snapshot-membership.sh"
covers: ["[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"]
tasks: [TASK-0161]
issues: ["[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"]
artifacts: []
evidence: []
adequacy: "2026-09-24, template at d93d847, 9 assertions. Three mutations, each reverted from a scratchpad copy: (Q) the focus check disabled, 1 failure (focus.task with a note but no entry); (R) the task check made to skip every task, 2 failures (the missing backlog task; reported once); (S) settled parents no longer skipped, 1 failure (a done feature's list is history). Pristine 9 of 9."
related: ["[[TST-0001]]", "[[TST-0020]]"]
---

# The validator reports a focus item or an in-flight task that has a note but no snapshot entry

## Purpose

`FOCUS-MEMBERSHIP` and `TASK-MEMBERSHIP` exist because five of FEAT-0039's tasks, one of them `focus.task`, were missing from `SNAPSHOT.yaml` while every other check passed ([[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot|ISS-0084]]). The harness builds a small fixture repo and runs the template's validator over it, reading only these two gates.

## Procedure

`bash tools/scripts/test-snapshot-membership.sh` in `~/Dev/repos/project-os`. Cross-repo, like [[TST-0020]].

1. A correct snapshot: neither gate fires.
2. The 2026-09-24 case (the feature lists the tasks, the tasks have no entries): `focus.task` is FOCUS-MEMBERSHIP; the missing backlog task is TASK-MEMBERSHIP, reported once; a done task the feature lists is not reported, because retention may prune it; a task no snapshot entry lists is not this check's concern.
3. A done feature's list is history: nothing is reported.
4. Both gates carry a date in `PROMOTIONS`, so they warn until 2026-12-23 and then fail.

## Expected results

- Exit 0: 9 of 9, first run 2026-09-24.
- Exit 1: each failure printed as `FAIL <name>: <detail>`.
