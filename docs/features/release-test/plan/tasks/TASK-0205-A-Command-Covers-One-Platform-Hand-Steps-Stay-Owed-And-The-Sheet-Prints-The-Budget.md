---
type: "[[task]]"
id: TASK-0205
aliases: ["TASK-0205"]
title: "A check's command can cover one platform, its hand steps stay owed there, and each release test sheet prints the hand-run budget"
status: done
phase: ""
owner: user:edwin
created: 2026-10-21
updated: 2026-10-21
source: ["[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]", "your-trainer TASK-1127 and FEAT-0140, plan section \"Formats\"", "Edwin, 2026-10-21, in your-trainer: 'I will go with the recommendations, implement as suggested (but implement this for 2.2.0 since this will reduce the testing time significantly).'"]
parent: "[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]"
effort: "M"
due: ""
depends: []
blocks: []
related: ["[[TASK-0206-The-Release-Test-Writes-A-Ride-Script-And-Imports-The-Rides-Results]]", "[[ISS-0109-The-Release-Test-Should-Be-A-Script-An-App-Can-Run]]"]
tests: []
---

# A command can cover one platform, hand steps stay owed, and the sheet prints the budget

Today a `command:` on an acceptance check takes it off every platform's release test at once, and a check with one step that needs a person stays whole on the sheet. your-trainer found nine checks whose test exists on Android only, and its v2.2.0 release is Android only. This task lets a check name a command per platform, lets it keep only the steps a person must run, and prints how many hand-run checks a platform owes against a limit. The formats are fixed in your-trainer FEAT-0140's plan, "Formats".

## Definition of Done

- [x] `release-test.py` treats a check as automated on platform P when it has `command:` or `commands.P`, and leaves it off P's sheet and owed count. Evidence: `Check.automated_on` and `owed_checks(..., platform)` in project-os a76657d; `test-release-ride.py` asserts TST-0003 (`commands: {android}`) is off Android and owed on iOS, and TST-0005 (`command:`) is off both.
- [x] On a platform with a command, `hand_steps:` keeps the check owed for those steps only. The sheet prints only those steps, and `--check` refuses a procedure that cites a step the command covers on that platform. Evidence: `Check.hand_parts`, `hand_steps_text` and the new rule in `_audit_tag`; the test asserts the procedure prints only `TST-0002.2` on Android and all three steps on iOS, a per-check row prints only step 3 and its Expect line, and `--check` refuses the procedure once its step 3 is no longer limited to iOS.
- [x] `validate-docs.py` checks that `commands:` maps ledger platforms to non-empty commands, and that each `hand_steps:` number is a step under the note's `## Steps`. Evidence: `validate_check_commands` (CHECK-COMMANDS); eight cases in the test, plus one through the validator's own run.
- [x] Each sheet prints a budget line near the top: the owed hand-run checks and hand steps against a limit, ten by default, set by `hand_run_limit:` in the section order file. `--json` carries it. Evidence: `budget_line` and `payload()["budget"]`; the test asserts the default line, a limit of 2 read from RELEASE-TEST.md with "3 over it", and `--check` refusing `hand_run_limit: ten`.
- [x] `TESTING.md`, "Release gating", states the three rules in plain words; `SCHEMAS.md` defines the new fields (`commands`, `hand_steps`, `hand_run_limit`).
- [x] The template's tests cover each rule and pass. Evidence: `test-release-ride.py`, 64 assertions, 0 failures, run in CI beside the other Python tests. `test-release-test.sh` (273), `test-release-test-preparation.py` and `test-ledger-checks.sh` still pass. The three template tests that fail (`test-word-budgets.sh`, `test-review-budget.sh`, `test-stop-sync.sh`) fail the same way at d813929, before this change.

## Notes

Not in this task, and still open under ISS-0108: refusing to seal a ledger that is over the limit, and making the cockpit's `ledger.owed()` count the same way.

## Result

Built in project-os a76657d, with TASK-0206. Run read-only against your-trainer, REL-0017 on Android prints "**Hand-run budget:** 37 checks with 240 steps are owed by hand on Android. The limit is 10 checks. This release is 27 over it." No your-trainer check has `commands:` or `hand_steps:` yet, so its owed set is unchanged and `--check` passes on both platforms. Not synced into any repo yet.
