---
type: "[[task]]"
id: TASK-0142
aliases: ["TASK-0142"]
title: "A merge file nobody edited takes the template, and build output is never synced"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["[[ISS-0071-A-Merge-Owned-File-Nobody-Edited-Never-Receives-Template-Updates]]", "project-os-cockpit ISS-0257", "Edwin, 2026-09-19: 'Do all 5 steps in the suggested order'"]
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[TASK-0134-The-Sync-Fast-Forwards-Stale-Copies]]"]
tests: ["[[TST-0016-The-Sync-Fast-Forwards-Only-What-Nobody-Edited]]"]
---

# A merge file nobody edited takes the template, and build output is never synced

## Definition of Done
- [x] `sync-project-os.py` fast-forwards a `merge` file that is byte-for-byte an older template version, as TASK-0134 already does for template files. A `merge` file with any local edit is still left alone and reported `MERGE`. ([[ISS-0071-A-Merge-Owned-File-Nobody-Edited-Never-Receives-Template-Updates|ISS-0071]])
- [x] The sync never copies `__pycache__`, `*.pyc`, `.pytest_cache` or `.DS_Store` from the template's working copy (project-os-cockpit ISS-0257).
- [x] `test-sync-stale.sh` asserts both, and fails without each fix.
- [x] The fleet is synced, and `SCHEMAS.md` is current in every repo that never edited it.

## Decision
Edwin's recommendation, accepted with "Do all 5 steps in the suggested order" (2026-09-19): yes, fast-forward a `merge` file that exactly equals an older template version. Such a copy holds no project content, so nothing can be lost.

## Done, 2026-09-19
Template `01031af`; synced to all twelve fleet repos, each checked with `validate-docs.sh --as-committed`. The new assertions in `test-sync-stale.sh` fail on the old code (1 for the merge rule, 2 for build output) and pass on the new. How far the rule reached, and the seven copies brought current by hand, are in [[ISS-0071-A-Merge-Owned-File-Nobody-Edited-Never-Receives-Template-Updates|ISS-0071]].

**Still a hand-merge:** `docs/__templates__/SCHEMAS.md` in your-sudoku and project-os-cockpit. Each mixes older template wording with lines that may be the project's own, so it needs a person to read it. Not done here.
