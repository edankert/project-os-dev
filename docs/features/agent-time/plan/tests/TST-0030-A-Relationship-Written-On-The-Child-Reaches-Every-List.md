---
type: "[[test]]"
id: TST-0030
aliases: ["TST-0030"]
title: "A task written once, on the child, reaches the feature's list, the phase's list, both snapshot lists and a snapshot entry"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0172]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-derive-lists.sh"
command: "bash ../project-os/tools/scripts/test-derive-lists.sh"
covers: ["[[ISS-0095-One-Relationship-Is-Written-In-Six-Places]]"]
tasks: ["[[TASK-0172]]"]
issues: ["[[ISS-0095-One-Relationship-Is-Written-In-Six-Places]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 19 assertions. Six mutations in a scratch copy: M1 any other parent makes an entry stale, 1 failure; M2 no fact moves onto the child, 2; M3 new entries ignore the slug form, 1; M4 the pre-commit hook does not stage the notes it wrote, 1 (it survived until the assertion stopped treating an empty result as a pass); M5 no snapshot entry added, 1; M6 the validator ignores derive_lists, 1. Pristine 19 of 19."
related: []
---

# A task written once, on the child, reaches the feature's list, the phase's list, both snapshot lists and a snapshot entry

## Purpose

ISS-0095: adding a task to a feature in a phase wrote one fact in six places. With `retention.derive_lists`, the author writes the task note only and the sync writes the rest. This test builds a git repo, stages two new task notes, and commits through the real pre-commit hook.

## Procedure

`bash tools/scripts/test-derive-lists.sh` in `~/Dev/repos/project-os`.

- The dry run (`derive-lists.py`) reports the conflict, naming both sides, and writes nothing.
- The feature's block list gains the new task, in the list's own slug form, and stays a block list; the field after it survives.
- A task written only in the feature's list keeps its place, and the fact moves onto the task: its empty `parent:` becomes the feature.
- A task whose `parent:` is another feature leaves this feature's list, in the note and in the snapshot.
- The issue lists its own task and keeps the task that fixes it, whose parent is a feature.
- The phase note's empty list gains its tasks; its bare-id list keeps its form. The snapshot's inline phase list follows, as bare ids.
- A live task under a live entry gets a snapshot entry.
- The hook stages every note the sync wrote, and SNAPSHOT.yaml; a second `--check` finds nothing.
- Opted in, the validator does not report PARENT-BACKLINK for a task the sync has not listed yet. Not opted in, it does, nothing is written, and the sync says how many lists would follow.

## Expected results

- Exit 0: 19 of 19, 2026-09-26.
