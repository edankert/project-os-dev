---
type: "[[change]]"
id: CHG-20260919-A-Broken-Snapshot-Fails-And-Merge-Files-Take-The-Template
title: "A snapshot that does not parse now fails, and merge files nobody edited take the template"
status: merged
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["PHASE-0007 step 2, Edwin, 2026-09-19: 'Do all 5 steps in the suggested order'"]
commit: "project-os 01031af"
pr: ""
impacts: []
issues: ["[[ISS-0069-A-Regression-Check-A-Change-Overlaps-Cannot-Be-Reopened]]", "[[ISS-0070-A-Snapshot-That-Does-Not-Parse-Still-Passes-Validation]]", "[[ISS-0071-A-Merge-Owned-File-Nobody-Edited-Never-Receives-Template-Updates]]", "[[ISS-0072-PHASES-Md-Repeats-Every-Phase-Status-And-Drifts-From-The-Phase-Notes]]"]
features: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]", "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template]]", "[[TASK-0143-Template-Fixes-Found-By-The-Cleanup]]"]
---

# A snapshot that does not parse now fails, and merge files nobody edited take the template

## Summary
From template `01031af`, synced to all twelve fleet repos on 2026-09-19, five things behave differently:

- **A `SNAPSHOT.yaml` that does not parse fails.** The validator reports `SNAP-PARSE`, and `sync-snapshot.py` prints the parser's message and exits 1 without writing. Before, both read the broken file with the lenient fallback parser and passed. A commit whose snapshot does not parse is now refused by the pre-commit hook and by CI.
- **The sync updates a `merge` file that nobody edited.** If the repo's copy is exactly an older template version, it takes the current one. A `merge` file with any local edit is still left alone and reported `MERGE`.
- **The sync never copies build output** (`__pycache__`, `*.pyc`, `.pytest_cache`, `.DS_Store`) from the template's working copy.
- **`TESTING.md` says to split a regression check** that also states current behaviour, when a change overlaps it.
- **Cursor sessions get the writing rules**, as `.cursor/rules/writing.mdc`.

The template's `PHASES.md` also no longer ships an example table, and says a phase's status lives only in its note.

## Impact

- No screen changed: these are the documentation system's own scripts and rules.
- project-os-deck's committed snapshot did not parse, and was repaired in its sync commit `1de5526`.
- articles' working copy of `SNAPSHOT.yaml` does not parse, because of another session's uncommitted edit. That session's next commit will be refused until the snapshot is fixed.

## Documentation Coverage (All Types Considered)
- features: updated
- requirements: not-applicable
- tasks: new
- issues: updated
- tests: not-applicable
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups
- [ ] Hand-merge `docs/__templates__/SCHEMAS.md` in your-sudoku and project-os-cockpit (TASK-0142).
- [ ] Tell the session working in articles that its snapshot does not parse.
