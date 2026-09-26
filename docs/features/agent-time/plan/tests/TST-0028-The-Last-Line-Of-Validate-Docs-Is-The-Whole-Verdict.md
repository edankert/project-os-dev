---
type: "[[test]]"
id: TST-0028
aliases: ["TST-0028"]
title: "The last line of validate-docs.sh is the verdict for every step, and walk problems are marked ERROR [WALK]"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0170]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-validate-verdict.sh"
command: "bash ../project-os/tools/scripts/test-validate-verdict.sh && bash ../project-os/tools/scripts/test-walk-sheet.sh"
covers: ["[[ISS-0089-The-Validator-Said-OK-And-The-Commit-Was-Refused]]"]
tasks: ["[[TASK-0170]]"]
issues: ["[[ISS-0089-The-Validator-Said-OK-And-The-Commit-Was-Refused]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 11 assertions in test-validate-verdict.sh and 2 in test-walk-sheet.sh. Four mutations in a scratch copy: M1 the script as committed before the change, 6 failures; M2 the verdict ignores the walk step, 4; M3 the validator ignores PROJECT_OS_VALIDATE_STEP, 2; M4 walk problems without the ERROR prefix, 1 (test-walk-sheet.sh). Pristine 11 of 11 and 161 of 161."
related: []
---

# The last line of validate-docs.sh is the verdict for every step, and walk problems are marked ERROR [WALK]

## Purpose

In your-trainer a session read `validate-docs: OK` from `validate-docs.sh` while the walk check, which runs after the validator, had failed (ISS-0089). This test pins down that the last line answers for every step, and that a walk problem is found by filtering for `ERROR`.

## Procedure

`bash tools/scripts/test-validate-verdict.sh` in `~/Dev/repos/project-os`. It copies the template and replaces `walk-sheet.py` with a stub that fails on demand; the template's own notes pass.

- Everything passes: exit 0, the last line is `validate-docs: OK (<root>: notes and walk procedures)`, and the validator's own line reads `validate-docs [notes]: OK`.
- The your-trainer case, notes pass and the walk fails: exit 1, the last line is `validate-docs: FAIL (notes: OK; walk procedures: FAIL)`, no line reads `validate-docs: OK`, and a grep for `^ERROR` finds the walk problem.
- A walk check that cannot run (exit 2) is named as such.
- Failing notes with a passing walk name the notes; `--quiet` still prints a failing verdict, and prints nothing when all pass.
- `validate-docs.py` run on its own keeps its plain `validate-docs: OK` line.

`test-walk-sheet.sh` asserts that every `--check` disagreement, and a broken ledger, starts with `ERROR [WALK]`.

## Expected results

- Exit 0: 11 of 11 and 161 of 161, 2026-09-26.
