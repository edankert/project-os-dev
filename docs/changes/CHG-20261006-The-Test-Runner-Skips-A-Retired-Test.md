---
type: "[[change]]"
id: CHG-20261006-The-Test-Runner-Skips-A-Retired-Test
title: "The test runner no longer runs the command of a retired test"
status: merged
owner: user:edwin
created: 2026-10-06
updated: 2026-10-06
source: ["[[ISS-0105-The-Test-Runner-Runs-A-Retired-Tests-Command]]"]
commit: "project-os e9b7744"
pr: ""
impacts: ["tools/scripts/run-tests.py", "tools/scripts/test-verdict-model.sh", "tools/instructions/HOOKS.md"]
platforms: []
issues: ["[[ISS-0105-The-Test-Runner-Runs-A-Retired-Tests-Command]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# The test runner no longer runs the command of a retired test

## Summary

A push is no longer refused because of a retired test. Before, `run-tests.py` ran the `command:` of every `TST-*` note whatever its status. A test retired because its subject was deleted usually still named the deleted file, so the pre-push hook failed on it. That happened in project-os-deck on 2026-10-06 with TST-0061. Now a note at `status: retired` is skipped, even when `--filter` names it, and the report does not list it.

## Impact

- **`run-tests.py`**: a retired note is left out of the run, the report and the passing and failing counts. Under `--ci` it is left out of the "covering N test note(s)" count.
- **`HOOKS.md`**, HC-009: a fourth line of check logic says so.
- **Downstream repos**: nothing changes until each one syncs the template. A repo that removed the `command:` from a retired note, as project-os-deck did, can leave it removed.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable (tracked as ISS-0105)
- issues: updated (ISS-0105 fixed)
- tests: updated (test-verdict-model.sh, three new checks, each failing when the skip is removed)
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable (no new dependency, variable, path or credential)
- changes: new
- snapshot: updated
