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

## After the FEAT-0037 review, 2026-09-19

Both reviewers refuted FEAT-0037's second criterion: the sync listed about 150 files as `GONE` (the template no longer ships them), and no note said why. Most were a repo's own scripts under `tools/scripts/`. Two were exact old template copies. Fixed in the sync:
- A file the template never shipped is the project's own, and is not reported.
- A file that is exactly an old template version is removed and reported `REMOVED`. That removes `docs/__templates__/dashboard.md` from your-trainer and project-os-cockpit at the next sync.
- Only a template file someone edited is still reported `GONE`.
- `template_history` reads the template's `HEAD` history, not `--all`, so a version that only lived on an unmerged branch no longer counts.

Also in the cockpit: `tools/scripts/test-walk-preparation.py` took the template's copy (every line of the cockpit's copy was in it), and `docs/__templates__/feature.md` went under `keep_local:` with its reason.

## What a fleet sync still reports, and why each needs a person

Measured with a dry run of the fixed sync over the twelve repos on 2026-09-19:
- **`docs/PHASES.md` (`MERGE`), in eleven repos.** It holds the project's own planning history beside the template's explanation of phases. A template change to that explanation has to be merged by hand into prose the project wrote, so it is shown at every sync on purpose.
- **`ROADMAP.md` (`MERGE`), in articles and project-os-bench.** The same reason: it is the project's roadmap, laid out on the template's headings.
- **`docs/__templates__/SCHEMAS.md` (`MERGE`), in your-sudoku and project-os-cockpit.** Older template wording mixed with lines that may be the project's own. It needs one hand-merge each, after which the rule above keeps it current.
- **`tools/adapters/codex/ADAPTER.md` (`LOCAL-CONTENT`), in project-os-cockpit.** Another session is editing it. Out of scope in FEAT-0037.
- **`KEPT` lines** (the cockpit's `run-tests.py` and `feature.md`, and `validate-docs.yml` in project-os-dev and your-trainer). Each is kept on purpose, with its reason in that repo's `.project-os-sync`.
