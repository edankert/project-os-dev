---
type: "[[change]]"
id: CHG-20260927-The-Walk-Is-Renamed-The-Release-Test
title: "The walk is renamed the release test in every project-os template file, and consumers move their own files with one command"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0187-Rename-The-Walk-To-The-Release-Test-Everywhere]]"]
commit: "project-os 66cee10, bff690e, 88d0c8b, cb01d0a"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/scripts/release-test-tags.py", "tools/scripts/test-release-test.sh", "tools/scripts/test-release-test-preparation.py", "tools/scripts/migrate-release-test-names.py", "tools/scripts/test-migrate-release-test-names.sh", "tools/scripts/validate-docs.py", "tools/scripts/validate-docs.sh", "tools/scripts/sync-project-os.py", "tools/sync/MANIFEST.yaml", "tools/skills/release-test-procedure/", "docs/__templates__/release-test.md", "tools/instructions/TESTING.md", "tools/instructions/TAXONOMY.md", "docs/__templates__/SCHEMAS.md", "docs/tests/acceptance/RELEASE-TEST.md (consumers)", "docs/tests/acceptance/release-test/ (consumers)", "docs/releases/ledgers/WORKING-*.json (consumers)"]
issues: []
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "[[REQ-0037-The-Walk-Is-Called-The-Release-Test-Everywhere]]", "[[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths]]", "[[TST-0009]]", "[[TST-0010]]", "[[TST-0011]]", "[[TST-0023]]", "[[TST-0028]]", "[[TST-0033]]"]
---

# The walk is renamed the release test in every project-os template file, and consumers move their own files with one command

## Summary

Testing a release by hand is now called the release test in every project-os template file, as ADR-0050 decided. A tester sees it first on the generated page: it is headed "Release test sheet", starts with "What changed" instead of "Survey", and numbers "Section 1" instead of "Sitting 1". Anyone who runs the scripts or writes the files notices the new names below, and a consumer that has not moved its own files gets an OLD-NAME error from the validator that names the command to run.

The page's content is unchanged. On a scratch clone of your-trainer the Android and iOS sheets are line for line the same as before once the words are swapped, and `--check` prints the same 420 lines.

## Impact

- No screen changed: project-os has no surface notes. The generated release test sheet in each consumer uses the new words, as the Summary says.

What changed for someone running or writing these files:

- **Scripts.** `walk-sheet.py` is `release-test.py`, `walk-tags.py` is `release-test-tags.py`, `test-walk-sheet.sh` is `test-release-test.sh`, and `test-walk-preparation.py` is `test-release-test-preparation.py`. The old names are not kept as aliases.
- **A consumer's own files.** `docs/tests/acceptance/WALK.md` is `RELEASE-TEST.md`, and the `walk/` folder of procedures is `release-test/`. A procedure's `sitting:` key is `section:`. A check's `walk_readiness_for:` is `readiness_for:`, the key procedures already used. `python3 tools/scripts/migrate-release-test-names.py --apply` makes all of these changes once, with `git mv`, and a second run changes nothing.
- **Ledger entries.** A new entry stores its result under `result`. Every reader still accepts `mark`, because a sealed ledger is never rewritten. The migration rewrites `mark` to `result` in each unsealed `WORKING-*.json` ledger, one entry per line as before. An entry whose `result` and `mark` disagree is a LEDGER-ENTRY error.
- **Validator.** OLD-NAME is a new error. It names the new name for each old file, folder or key it finds, and the migration command. `validate-docs.sh` ends with "notes and release test procedures", and procedure problems start with `ERROR [RELEASE-TEST]`.
- **Sync.** The manifest has a `renamed:` table and a `migrations:` list. The sync deletes each renamed path, edited or not, and prints the migration command when the migration has work. A sync runs the consumer's own copy of `sync-project-os.py`, so the first sync that brings this in does neither; the validator's OLD-NAME errors cover that sync.
- **Words.** `TESTING.md`'s "The walk" is "The release test", with section, what changed, section order, tester and result in its glossary. "The three sections" (feature, regression, automated) is "The three test kinds", so "section" has one meaning. The `walk-procedure` skill is `release-test-procedure`.
- **Code names**, for project-os-cockpit's bundle (FEAT-0155): `Walk` is `ReleaseTest`, `Sitting` is `Section`, `build_walk` is `build_release_test`, `WalkError` is `ReleaseTestError`, `NothingToWalk` is `NothingToTest`, `parse_walk_order` is `parse_section_order`, `ReleaseTest.survey` is `what_changed`, the `survey_*` fields are `what_changed_*`, `Placed.sitting` and `Procedure.sitting` are `.section`, `walked_from_procedure` is `tested_from_procedure`, `Event.mark` is `Event.result`, `Check.section` (the test kind) is `Check.kind`, and the markdown heading reader `section()` is `under_heading()`.

## Documentation Coverage (All Types Considered)

- features: not-applicable (FEAT-0040 stays planned; its other tasks follow)
- requirements: not-applicable (REQ-0037 is advanced at the feature's close-out)
- tasks: updated (TASK-0187)
- issues: not-applicable
- tests: updated (TST-0009, TST-0010, TST-0011, TST-0023, TST-0028, TST-0033 run the renamed harnesses)
- workflows: not-applicable
- decisions: not-applicable (ADR-0050 already records it)
- risks: updated (RISK-0005)
- changes: new
- snapshot: updated

## Follow-ups

- [ ] project-os-cockpit re-bundles `release-test.py` under the new code names (FEAT-0155).
- [ ] project-os-cockpit and your-trainer take the template sync and run the migration (TASK-0195). project-os-dev takes the same sync.
