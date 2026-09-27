---
type: "[[test]]"
id: TST-0041
aliases: ["TST-0041"]
title: "migrate-release-test-names.py moves a consumer's files to the release test names once, and the validator names every old name until it has"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0187-Rename-The-Walk-To-The-Release-Test-Everywhere]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-migrate-release-test-names.sh"
command: "bash ../project-os/tools/scripts/test-migrate-release-test-names.sh"
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
tasks: ["[[TASK-0187]]"]
requirements: ["[[REQ-0037-The-Walk-Is-Called-The-Release-Test-Everywhere]]"]
issues: []
artifacts: []
evidence: []
adequacy: "2026-09-27, 27 assertions. Ten mutations of migrate-release-test-names.py and validate-docs.py in a scratch copy of the template: M1 sealed ledgers rewritten, 1 failure; M2 open ledgers not rewritten, 1; M3 no conflict check, 2; M4 a key rewritten in the note body as well, 2 (survived until the fixture had a body line starting with the old key); M5 a plain rename instead of git mv, 2 (survived until the moves were read before staging); M6 a conflict exiting 0, 1; M7 the validator's OLD-NAME check not called, 5; M8 the old folder left behind, 2; M9 the old skill path left in other CLAUDE.md lines, 2 (survived until the fixture had such a line); M10 the skill line's label not rewritten, 1. Pristine 27 of 27."
related: ["[[TST-0016]]", "[[TST-0009]]"]
---

# A consumer's walk files move to the release test names once, and the validator names every old name until they have

## Purpose

ADR-0050 renamed the walk to the release test with no period in which both names work. A consumer's own files keep the old names until it runs the migration, so the migration must move everything once and lose nothing, and the validator must refuse whatever is left.

## Procedure

`bash tools/scripts/test-migrate-release-test-names.sh` in `~/Dev/repos/project-os`, on a git repo holding a copy of the template's notes and scripts plus the files a consumer wrote under the old names.

- Before migrating, the validator reports WALK.md, the walk/ folder, a check's `walk_readiness_for:` and CLAUDE.md's old skill line as OLD-NAME, each naming its new name and the migration command.
- A dry run and `--check` change nothing; `--check` exits 1.
- `--apply` moves WALK.md and walk/ with `git mv`, rewrites `sitting:` and `walk_readiness_for:` in frontmatter only, rewrites CLAUDE.md's skill line, and rewrites `mark` to `result` in the open ledger with one entry per line as before. The sealed ledger is byte for byte unchanged.
- After migrating, the validator reports no old name, and `release-test.py --check` finds the section by its new key.
- A second run says there is nothing to do and changes nothing.
- WALK.md beside RELEASE-TEST.md is a conflict: exit 2, and neither file is touched.

The sync's side, deleting renamed template files and printing the migration command, is in [[TST-0016]]'s harness, `test-sync-stale.sh`.

## Expected results

- Exit 0: 27 of 27, 2026-09-27.
