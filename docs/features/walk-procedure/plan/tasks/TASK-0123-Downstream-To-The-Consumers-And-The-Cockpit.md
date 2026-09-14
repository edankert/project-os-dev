---
type: "[[task]]"
id: TASK-0123
aliases: ["TASK-0123"]
title: "Sync the surface rules, the Impact field, the survey, the procedure format, validator and skill into your-trainer and project-os-cockpit, and confirm their plans carry the rest"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: M
due: ""
depends: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]", "[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]", "[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure]]"]
blocks: []
related: ["[[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit]]", "[[PHASE-0005-The-Walk-Reads-As-A-Script]]"]
tests: []
---

# Downstream: the consumers and the cockpit

## What

The template changes from FEAT-0030 and FEAT-0031 reach the two repos that use them. This task syncs and confirms. It does not do either repo's work: your-trainer's is its PHASE-024 (FEAT-0120, FEAT-0121) and the cockpit's is its PHASE-044 (FEAT-0150).

## Definition of Done

- [x] `tools/scripts/sync-project-os.sh` has run in your-trainer. Its diverged `validate-docs.py` is hand-merged, not overwritten, as in TASK-0115. This is your-trainer TASK-0905.
- [x] The same sync has run in project-os-cockpit, and `walk_sheet_bundled.py` is byte-identical to the template's `walk-sheet.py` again (its `tests/test_walk_bundle.py` passes).
- [x] The other repos with an acceptance suite (project-os-deck, your-sudoku) are synced, and `bash tools/scripts/validate-fleet.sh` shows no new errors against the pre-sync table.
- [x] REQ-0028's Amendments section records the survey change. *(ADR-0029's pointer to ADR-0045 was added on 2026-09-14 when ADR-0045 was accepted.)*
- [x] This repo's vendored `tools/` is synced or its deferral is recorded.
- [x] Adapters regenerated in every synced repo.

## Notes

- your-trainer's TASK-0902 (the `area:` rewrite) does not wait for this sync; its TASK-0906 (procedures) does.

## What the sync found, and what it took

**The baseline was stale, which made the report frightening and the work small.** `.project-os-sync` in every consumer records a baseline from before PHASE-0004 landed upstream, so `walk-sheet.py` and `test-walk-sheet.sh` came back UNKNOWN and `TESTING.md`, `change.md` and `close-out/SKILL.md` came back CONFLICT. Checking each downstream copy against the previous template commit settled it: **in your-trainer, project-os-deck, your-sudoku and this repo, every one of them was byte-identical to the old template.** They were overwritten, which is provably right.

Only **project-os-cockpit** had real divergence, in `TAXONOMY.md` and `TESTING.md` — its copies still carry 2026-07-17 prose elsewhere in the file. Those two were hand-merged by region: the new "The walk" section and the new `kind`/`gallery` surface sections replaced their old ones, and the rest of each file was left exactly as it was. `SCHEMAS.md` is merge-owned in every repo and got its three new entries by hand.

**`walk_sheet_bundled.py` is byte-identical again** and `tests/test_walk_bundle.py` passes.

**validate-fleet is unchanged before and after.** Thirteen repos, the same four pre-existing failures with the same counts (edankert.com 47, your-applications.com 63, your-trainer 1, yourtrainer-mcp 16), the same warnings, the same waivers. No new error anywhere.

## The cockpit needed more than a file copy

A sync that leaves a downstream suite red is not a sync. The new module changed `build_walk`'s signature and replaced `SurveyEntry`, so `acceptance.walk_payload` raised on the first call and 37 of the cockpit's tests went red.

Three things landed there with the sync, and they are recorded on that repo's TASK-0622 so its PHASE-044 starts from them:

- `walk_payload` speaks the new API, and `_walk_notes` returns the index in the shape upstream's readers take so `load_surfaces` runs there rather than being written a second time. The payload carries the survey's screens, sentences and captures, and each sitting's procedure with its owed flags.
- `tests/test_walk_survey.py` was rewritten to the new rule — 11 tests over git fixtures with a real tag. The old file asserted the invalidation join upstream retired, and a downstream test of a retired rule is stale rather than failing.
- `buildSurveySection` draws the new shape plainly. The **card layout, the side-by-side widths and the framed-viewer route are still project-os-cockpit TASK-0622**, and its boxes stay unticked.

Suites after: `pytest` 2121 passed / 6 skipped, `node --test desktop/tests/*.mjs` 146 passed, `test-walk-sheet.sh` 139 assertions in all five repos, `validate-docs.sh` OK in all six.

## Two deliberate departures

**This repo's vendored `SCHEMAS.md` got only the `change.md` body shape.** It is a trimmed copy — no `walk.md`, `release.md`, `plan.md` or `check.md` entries — because project-os-dev keeps no surfaces, no releases and no ledger. Adding `surface.md` and `procedure.md` entries here would document note types this repo does not have.

**A tracked `tools/scripts/__pycache__/validate-docs.cpython-313.pyc` was deleted** in your-trainer and the copies removed elsewhere. The sync manifest globs `tools/scripts/`, so it had been copying compiled bytecode between repos. Removing it is right; teaching the manifest not to is not this task's, and is worth an `ISS-*` if it comes back.

## What is still downstream's

your-trainer TASK-0900 (the surface mapping Edwin approves), TASK-0902 (the `area:` rewrite), TASK-0904 (where captures live), TASK-0906 (the v2.2.0 procedures) and TASK-0907; project-os-cockpit TASK-0622 to TASK-0626. Nothing here waits on them.
