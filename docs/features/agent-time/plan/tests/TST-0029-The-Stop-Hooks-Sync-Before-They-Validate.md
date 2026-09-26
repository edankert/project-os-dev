---
type: "[[test]]"
id: TST-0029
aliases: ["TST-0029"]
title: "Both Stop hooks sync the snapshot before they validate, and the sync never writes over another writer's edit"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0171]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-stop-sync.sh"
command: "bash ../project-os/tools/scripts/test-stop-sync.sh"
covers: ["[[ISS-0090-The-Stop-Hook-Validates-Without-Syncing-The-Snapshot]]"]
tasks: ["[[TASK-0171]]", "[[TASK-0185]]"]
issues: ["[[ISS-0090-The-Stop-Hook-Validates-Without-Syncing-The-Snapshot]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 7 assertions. Four mutations in a scratch copy: M1 the Claude Code hook without the sync, 2 failures; M2 the Codex dispatch without the sync, 2; M3 the sync writes whatever it read, 1; M4 the hook skips validation, 1. Pristine 7 of 7."
related: []
---

# Both Stop hooks sync the snapshot before they validate, and the sync never writes over another writer's edit

## Purpose

In your-trainer a background planner created REQ-0221 while `counters.REQ` was 220, and the main session's stop was blocked on `COUNTER`, an error the next commit's sync would have fixed by itself (ISS-0090). This test runs both Stop hooks on a copy of the template with a new note the counter does not yet cover.

## Procedure

`bash tools/scripts/test-stop-sync.sh` in `~/Dev/repos/project-os`.

- Unsynced, the validator fails on `COUNTER`, which reproduces the case.
- The Claude Code hook (`close-out-check.sh`) lets the stop through and has raised `counters.ISS` to 1.
- The Codex `dispatch.py` Stop handler does the same.
- A note error the sync cannot fix (an invalid status) still blocks the stop.
- `write_if_unchanged` leaves a snapshot alone when it changed since the sync read it, replaces an unchanged one, and leaves no temporary file.

## Expected results

- Every fixture removes the executable bit from `validate-docs.sh`, as a fresh clone of a repo with `core.fileMode` off has it, so a hook that only runs an executable validator fails the invalid-status case (ISS-0103).

- Exit 0: 7 of 7, 2026-09-26.
