---
type: "[[task]]"
id: TASK-0185
aliases: ["TASK-0185"]
title: "The Stop and pre-commit hooks run the validator whatever its file mode"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0103-The-Stop-Hook-Skips-Validation-When-The-Script-Is-Not-Executable]]"]
parent: "[[ISS-0103-The-Stop-Hook-Skips-Validation-When-The-Script-Is-Not-Executable]]"
effort: S
due: ""
depends: []
blocks: []
related: []
tests: ["[[TST-0029-The-Stop-Hooks-Sync-Before-They-Validate]]"]
---

# The Stop and pre-commit hooks run the validator whatever its file mode

## Definition of Done
- [x] `close-out-check.sh` and `hooks/pre-commit` run `validate-docs.sh` with `bash` when the file exists.
- [x] The template's scripts are stored as executable in git (`git update-index --chmod=+x`, since the repo keeps `core.fileMode` off).
- [x] A test fails when the Stop hook skips a validator that is not executable; CI is green (project-os `136a065`).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0029: the hook back on `-x` fails 1 assertion).
