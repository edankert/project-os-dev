---
type: "[[feature]]"
id: FEAT-0037
title: "Every repo can take the template again"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["Edwin, 2026-09-18: 'Can you enumerate the changes needed for the template files in the different projects and suggest how to resolve?', then 'Implement as suggested.'", "[[TASK-0131-Roll-Out-And-Measure-Five-Reviews]] hand-merge list"]
goal: "The template sync fast-forwards every file that has no local edits. Files that belong to a project stop being reported. Work that was built in a project first reaches the template. So a sync reports only files that really need a person."
requirements: []
tasks: [TASK-0134, TASK-0135, TASK-0136, TASK-0137, TASK-0142, TASK-0147]
issues: [ISS-0068]
release: ""
acceptance_exception: "Tooling for the template's own sync; it is checked by the sync's fixture test and by the fleet's dry-run results, which the tasks record."
reviewed_by: ["model:claude-opus-5 (reviewer A)", "model:claude-opus-5 (reviewer B)", "model:claude-opus-5 (round 2)"]
review_date: "2026-09-19"
review_round: 2
review_verdict: approved
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]"]
---

# Every repo can take the template again

## Goal

Rolling PHASE-0007 out to the fleet on 2026-09-18 turned up about 100 template-owned files that the sync would not update. They fall into four groups:
- **51 are stale.** Each is exactly an older template version, left behind because an earlier sync skipped it and then recorded a later baseline.
- **14 hold content that belongs to the project**, such as a filled-in `LLM_BRIEF.md` or a CI workflow that differs on purpose.
- **About 12 are template work that was built in a project first.**
- **The rest are older local variants.**

This feature makes the sync handle the first two groups by itself, and clears the rest by hand.

## Scope

- [[TASK-0134-The-Sync-Fast-Forwards-Stale-Copies|TASK-0134]] (step 1): the sync fast-forwards any file that equals an older template version. `LLM_BRIEF.md`, `SECURITY.md`, `docs/INDEX.md` and `docs/README.md` become seed files. Workflows other than `validate-docs.yml` become project-owned. A repo can list files it keeps on purpose. Then the fleet is re-synced.
- [[TASK-0135-Older-Local-Variants-Take-The-Template|TASK-0135]] (step 2): the older local variants take the template, after a check each.
- [[TASK-0136-The-Cockpits-Validator-Checks-Reach-The-Template|TASK-0136]] (step 3): the cockpit's four validator checks move to the template, and the cockpit takes the template's validator.
- [[TASK-0137-Three-Repos-Reach-The-Current-Validator|TASK-0137]] (step 5): edankert.com, your-applications.com and yourtrainer-mcp clear the debt that stops the current validator, then take it.
- [[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template|TASK-0142]] (2026-09-19): a `merge` file that is exactly an older template version takes the template, build output is never synced, and the sync stops listing a repo's own files as no longer shipped.

## Out of Scope

- The walk-preparation files (`walk-sheet.py`, `test-walk-sheet.sh`, `procedure.md`, the walk-procedure skill, `walk_readiness_for:`). They reach the template when [[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup|TASK-0125]] closes, in its own session.
- project-os-cockpit's `tools/adapters/codex/ADAPTER.md`, which another session is editing.

## Acceptance

- A fleet dry-run lists no template-owned file that equals an older template version.
- Every file still reported is written up in a task note, with the reason it needs a person.

## Verification

- 2026-09-19, in `~/Dev/repos/project-os` at `01031af`: `for t in tools/scripts/test-*.sh; do bash "$t"; done`, `python3 -B tools/scripts/test-retention.py`, `python3 -B tools/scripts/test-walk-preparation.py`, `python3 tools/scripts/generate-adapters.py --check` and `bash tools/scripts/validate-docs.sh`. Every script passed: 16 shell test scripts with 0 failures, retention 26 assertions, walk preparation OK, all 65 generated artifacts current, validator OK. The same code is synced to all twelve fleet repos, each passing `validate-docs.sh --as-committed`.

## Review

**Round 1, 2026-09-19: changes-requested.** Two clean-context reviewers on one packet (template `9da6c83`, `d2f78bc`, `a978752`, `4b5fa83` and the sync half of `01031af`), combined here.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | A fleet dry-run lists no template-owned file that equals an older template version | **refuted** (reviewer A) / holds (reviewer B) | Refutation wins: `GONE` still listed `docs/__templates__/dashboard.md` in your-trainer and the cockpit, each an exact old template copy. |
| 2 | Every file still reported is written up in a task note | **refuted** | About 150 `GONE` lines, mostly a repo's own scripts, `ROADMAP.md` and `PHASES.md` `MERGE`, the cockpit's `test-walk-preparation.py` `SUBSET`: no task note. |
| 3a–e | TASK-0134's parts | holds | Guards broken by both reviewers each failed TST-0016. |
| 4–6 | TASK-0135, TASK-0136, TASK-0137 | holds | `cmp` against the template in each repo. |
| 7 | TST-0016 fails when its behaviour is broken | holds, one vacuous assertion | "a project's own workflow is left alone" could not fail: the fixture template shipped no `own-ci.yml`. |
| 8 | TST-0017 fails when its behaviour is broken | **refuted** (reviewer B) | Replacing the calls to `validate_frontmatter_parses` and `validate_ledgers` in `main` left it passing. |

**Fixed before round 2** (template `badc195`, cockpit `0e0fb0c`, this repo's notes): the sync no longer reports a file the template never shipped, removes an exact old copy of a dropped template file, and reports only an edited one; `template_history` reads `HEAD`; the cockpit takes the template's `test-walk-preparation.py` and keeps `feature.md` under `keep_local:`; TASK-0142 writes up every file a fleet sync still reports; TST-0016 covers the new rules and its workflow assertion can fail; TST-0017 runs the whole validator end to end. Out-of-date sentences in TASK-0134, TASK-0136 and the TST `adequacy:` fields are corrected, and TASK-0142 is in the Scope.

**Round 2, 2026-09-19: approved.** One reviewer, fix diff only, 10 of 15 calls. Claims 1, 2 and 8: *fixed*. A dry run over the twelve repos printed no `GONE` and no `REMOVED`, lists exactly what TASK-0142 writes up, and every listed file matches no template version. Removing either call in `main` fails `test-ledger-checks.sh`. Its caveat: the NOTE-FRONTMATTER end-to-end case runs only where PyYAML is installed, as the check itself does.

## Links
- Tests: [[TST-0016-The-Sync-Fast-Forwards-Only-What-Nobody-Edited|TST-0016]], [[TST-0017-Ledger-And-Frontmatter-Checks-Hold-Their-Rules|TST-0017]]
- Filed: [[ISS-0068-The-Cockpits-Validator-Carries-Rules-The-Template-Lacks|ISS-0068]]
