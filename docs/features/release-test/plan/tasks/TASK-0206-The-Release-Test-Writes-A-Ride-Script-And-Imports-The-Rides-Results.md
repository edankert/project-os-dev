---
type: "[[task]]"
id: TASK-0206
aliases: ["TASK-0206"]
title: "release-test.py writes the owed steps as a ride script an app can run, and imports the app's results file into the working ledger"
status: done
phase: ""
owner: user:edwin
created: 2026-10-21
updated: 2026-10-21
source: ["[[ISS-0109-The-Release-Test-Should-Be-A-Script-An-App-Can-Run]]", "your-trainer TASK-1127 and FEAT-0140, plan section \"Formats\""]
parent: "[[ISS-0109-The-Release-Test-Should-Be-A-Script-An-App-Can-Run]]"
effort: "M"
due: ""
depends: ["[[TASK-0205-A-Command-Covers-One-Platform-Hand-Steps-Stay-Owed-And-The-Sheet-Prints-The-Budget]]"]
blocks: []
related: ["[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]"]
tests: []
---

# The release test writes a ride script and imports the ride's results

A person testing a release reads a sheet and records each result by hand. your-trainer wants its app to show the owed steps one at a time during a ride and record the answers itself. This task gives the app something to load and gives the answers a way back into the ledger. The formats are fixed in your-trainer FEAT-0140's plan, "Formats"; this task implements them and does not change them.

## Definition of Done

- [x] `release-test.py --release R --platform P --ride-script FILE` writes the ride script (`release-ride-script/1`) with the steps in the sheet's order, `setup` from the procedure's `setup_for`, `screens` from the what-changed list and `commit` from the repo's git HEAD. Evidence: `ride_script` in project-os a76657d; the test asserts the format, release, platform and commit, the step ids in the sheet's order, the section, group and setup names of a step, and the changed screen with its line.
- [x] `release-test.py --import-ride FILE --platform P` adds one entry per check to `WORKING-P.json`: `pass` when every owed step passed, `fail` with the step notes as the reason when any failed, and nothing when a step was skipped. Entries carry `method: "ride"` and `build`. Evidence files are copied beside the ledger and listed in its `evidence`. Changed screens marked failed are printed. `--dry-run` writes nothing. Evidence: `plan_ride_import`, `apply_ride_import` and `report_ride_import`; the test asserts each outcome, the copied evidence and its ledger item, the failed screen printed, a second import adding nothing, another platform's file refused, and `--dry-run` leaving the ledger byte for byte.
- [x] The ledger checks accept `method: ride` and require a `build` on it; `TAXONOMY.md` and the ledger README say so. Evidence: `LEDGER_METHODS` and the `build` rule in `validate_ledgers`; the test asserts an imported ledger draws no error, and a ride entry with no or an empty build is refused.
- [x] The template's tests cover the script and the import and pass (`test-release-ride.py`, 64 assertions with TASK-0205's).

## Decisions inside the fixed formats

The formats say one script step per owed part and nothing about steps that record nothing. Three choices follow, all within the formats, and SCHEMAS.md states them:

- A preparation step, and a group's `Start:` line, become the first lines of the next owed step's `do`, so the rider still does them in order.
- When one procedure step tests several owed parts, the first carries the action and the others say "Nothing new to do. Check this from what the step before showed."
- A setup item scoped `all` is named on every step of its section.

## Notes

Not in this task, and still open under ISS-0109: cutting the script to a time target by priority, grouping steps so the setup changes as rarely as possible, and the cockpit showing imported results.

## Result

Built in project-os a76657d. Run read-only against your-trainer, REL-0017 on Android writes 240 steps from 37 owed checks, 28 changed screens, 127 KB. A dry-run import of a sample results file reports one entry it would add and writes nothing. Before a repo imports a ride, project-os-cockpit has to accept `method: ride` and keep `build` when it rewrites a ledger; its `ledger.py` refuses the first and drops the second today.
