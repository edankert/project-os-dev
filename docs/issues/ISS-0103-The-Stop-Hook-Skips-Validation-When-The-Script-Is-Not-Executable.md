---
type: "[[issue]]"
id: ISS-0103
aliases: ["ISS-0103"]
title: "On a fresh clone the Stop hook never validates, because git stores validate-docs.sh as not executable"
status: fixed
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["CI run for project-os 751d9e1 and project-os-dev 1448e60, 2026-09-26: test-stop-sync.sh failed 'a note error the sync cannot fix still blocks the stop'"]
reported_by: agent
question: ""
severity: high
component: "tools/adapters/claude-code/hooks/close-out-check.sh; tools/scripts/hooks/pre-commit; the executable bit of the template's scripts"
parent: ""
tests: ["[[TST-0029-The-Stop-Hooks-Sync-Before-They-Validate]]"]
related: ["[[ISS-0090-The-Stop-Hook-Validates-Without-Syncing-The-Snapshot]]", "[[TST-0029-The-Stop-Hooks-Sync-Before-They-Validate]]"]
tasks: ["[[TASK-0185]]"]
---

## Problem

The Claude Code Stop hook runs `validate-docs.sh` only when the file is executable (`[ -x "$VALIDATOR" ]`), and otherwise lets the stop through without checking anything. The template repo has `core.fileMode = false`, so git stores `validate-docs.sh`, both git hooks and every other script as mode 100644. A fresh clone, such as CI's, gets them without the executable bit. The pre-commit hook has the same test and refuses to commit instead.

## Evidence

- `git ls-files -s tools/scripts/validate-docs.sh` in project-os: `100644`. 31 scripts under `tools/scripts/` are stored that way.
- CI on 2026-09-26: `test-stop-sync.sh`, which copies the checkout, found that an invalid status no longer blocked the stop. It passed locally, where the file happens to be executable.

## Expected

Both hooks run the script with `bash` whenever the file exists, as the Codex hook already does, so the executable bit no longer decides whether a stop or a commit is checked. The scripts are also stored as executable.

## Fixed, 2026-09-26

TASK-0185. Both hooks run the validator with `bash` whenever the file exists, the scripts are stored as executable, and `test-stop-sync.sh` removes the bit as a fresh clone would, so TST-0029 fails if the Stop hook skips validation again.
