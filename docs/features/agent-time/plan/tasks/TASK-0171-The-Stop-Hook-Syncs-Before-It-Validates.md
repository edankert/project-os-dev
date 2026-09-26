---
type: "[[task]]"
id: TASK-0171
aliases: ["TASK-0171"]
title: "The Stop hook syncs the snapshot before it validates"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0090-The-Stop-Hook-Validates-Without-Syncing-The-Snapshot]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0090-The-Stop-Hook-Validates-Without-Syncing-The-Snapshot]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0029-The-Stop-Hooks-Sync-Before-They-Validate]]"]
---

# The Stop hook syncs the snapshot before it validates

## Definition of Done
- [x] `close-out-check.sh` and the Codex stop handler run `sync-snapshot.py` before the validator, as the pre-commit hook does. The sync now writes through `write_if_unchanged`: it re-reads SNAPSHOT.yaml first and leaves it alone if another writer changed it, and it replaces the file in one step.
- [x] A test: a note whose status changed outside the session no longer blocks the stop (TST-0029, with a new note the counter does not cover).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0029: four mutations, all caught).

## Result, measured on a copy of your-trainer 2026-09-26

The Stop hook, now sync plus validation, takes 2.0 s with a warm cache and 2.9 s cold (three cold runs: 2.99, 2.89 and 2.88 s). It was 39.9 s. A cold cache happens once after each validator update. To stay under 3 s cold, NOTE-FRONTMATTER now reuses the frontmatter parse when PyYAML read the same text, which cut 0.6 s; TST-0027 covers that.
