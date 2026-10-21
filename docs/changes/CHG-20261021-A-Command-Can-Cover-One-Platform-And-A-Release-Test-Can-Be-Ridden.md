---
type: "[[change]]"
id: CHG-20261021-A-Command-Can-Cover-One-Platform-And-A-Release-Test-Can-Be-Ridden
title: "A check's command can cover one platform, hand steps stay owed, each sheet prints a hand-run budget, and release-test.py writes a ride script and imports its results"
status: merged
owner: user:edwin
created: 2026-10-21
updated: 2026-10-21
source: ["[[TASK-0205-A-Command-Covers-One-Platform-Hand-Steps-Stay-Owed-And-The-Sheet-Prints-The-Budget]]", "[[TASK-0206-The-Release-Test-Writes-A-Ride-Script-And-Imports-The-Rides-Results]]"]
commit: "project-os a76657d"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/scripts/validate-docs.py", "tools/scripts/test-release-ride.py", "tools/instructions/TESTING.md", "tools/instructions/TAXONOMY.md", "docs/__templates__/SCHEMAS.md", "docs/__templates__/release-test.md", "docs/releases/ledgers/README.md", ".github/workflows/validate-docs.yml"]
platforms: []
issues: ["[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]", "[[ISS-0109-The-Release-Test-Should-Be-A-Script-An-App-Can-Run]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# A command can cover one platform, and a release test can be ridden

## Summary

After its next template sync, a repo can give an acceptance check a test on one platform only, and that platform's release test stops asking for it. A check can also keep just the steps a person must run, such as the one that needs the real trainer. Each release test sheet now says how many hand-run checks the platform owes against a limit of ten. And `release-test.py` can write the owed steps as a script an app shows one at a time, then read the app's results back into the ledger.

## Impact

- **New check fields:** `commands: {android: "..."}` makes a check automated on that platform only. `hand_steps: [3, 5]` keeps those steps owed where a command covers the check. The validator checks both (`CHECK-COMMANDS`), and a check with `hand_steps:` stays under `docs/tests/acceptance/` even with a `command:` (`ACCEPT-LOCATION`).
- **`release-test.py --check`** refuses a procedure that cites a step a command covers on the platform it checks. A procedure that serves another platform limits that step with `step_platforms`.
- **Every sheet** prints a "Hand-run budget" line near the top, and `--json` carries `budget`. `hand_run_limit:` in `RELEASE-TEST.md` sets the limit; the default is ten. The line does not block anything.
- **New flags:** `--ride-script FILE` writes `release-ride-script/1`. `--import-ride FILE --platform P [--dry-run]` reads `release-ride-results/1` and adds entries to `WORKING-P.json` with `method: "ride"` and `build`. Evidence is copied to `docs/releases/ledgers/evidence/<release>-<platform>-<started>/`.
- **Ledger checks:** `ride` is a valid `method`, and a ride entry must name its `build`.
- **Not changed yet:** project-os-cockpit reads ledgers with its own method list, so it refuses a `ride` entry and drops `build` when it rewrites a ledger. It also counts owed checks by `command:` alone. Both need a cockpit change before a repo imports a ride.

## Verification

`python3 -B tools/scripts/test-release-ride.py` in the template: 64 assertions, all pass. Four deliberate mutations each make it fail: owed checks counted by `command:` alone, the procedure rule removed, hand steps ignored, and a ride entry with no build accepted. `test-release-test.sh` (273), `test-release-test-preparation.py` (39) and `test-ledger-checks.sh` still pass. Run read-only against your-trainer, REL-0017 on Android: `--check` passes on both platforms, and the validator reports no error.
