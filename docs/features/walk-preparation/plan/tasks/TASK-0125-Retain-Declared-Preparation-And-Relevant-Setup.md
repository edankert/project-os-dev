---
type: "[[task]]"
id: TASK-0125
aliases: ["TASK-0125"]
title: "Retain declared preparation and relevant setup in the walk"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-16
updated: 2026-09-24
source: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
parent: "[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"
effort: "Large"
depends: []
blocks: []
related: ["[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]", "[[REQ-0031-Preparation-Is-Declared-And-Validated]]"]
tests: ["[[TST-0023]]", "[[TST-0011]]"]
---

# Retain declared preparation and relevant setup in the walk

## Definition of Done

- [x] The authored syntax declares prerequisite step numbers, setup entries and platform variants without prose inference.
- [x] The validator reports missing and cyclic prerequisites, invalid setup references, contradictory state and invalid platform coverage — evidence: missing, future and cyclic prerequisites and absent setup steps were already refused; added 2026-09-24, in the structural sense set out below: one step or setup id declared twice in a map, a setup, readiness or action declaration that can never apply on its step's platforms, and a platform name with no ledger. TST-0023, 16 of 16. Corpus audit below: 0 problems on both platforms.
- [x] The generator retains required preparation in authored order, filters irrelevant setup and leaves the owed check set unchanged.
- [x] Child screen survey entries keep their true parent even when the parent has no change note.
- [x] Fixture tests prove the expected output and a deliberately broken implementation causes those tests to fail — evidence: eight mutations, recorded on TST-0023. One survived (every setup item printed); the test that catches it was added, and it now fails.
- [x] The template, instructions and both consumer copies are synced after upstream validation. *(Corrected 2026-09-18: this was ticked on 2026-09-17, but the work reached only this repo, and your-trainer and project-os-cockpit got partial hand copies. It reached the template on 2026-09-18 as project-os c71dbb7 and every repo was synced from it; see the section below.)*

## Steps

- [x] Amend ADR-0045's filtering rule through ADR-0046 and update TESTING.md.
- [x] Implement parsing, validation, generation and rendering in walk-sheet.py.
- [x] Add focused fixture tests, then run the upstream test suite and documentation validator.

## Screen name finding, 2026-09-16

The generator previously set a procedure step's visible screen to its `SUR-*` id when that id appeared in the action. The cockpit showed `SUR-0033` instead of Quick Ride cockpit. The generator now resolves known ids to their surface titles, retains the id for linking, and leaves unknown ids visible. Its 157 sheet assertions and eight preparation fixture tests pass, and both consumer copies are byte-identical with upstream.

Your Trainer's `TST-0657.9a` citation exposed an invalid-tag gap: the numeric tag parser ignored it, and a valid tag beside it could still pass coverage. The shared validator now names a malformed backticked `TST-` token even when a valid tag is beside it. The procedure falls back to complete per-check rows. The focused fixture has nine passing tests, the sheet script has 157 passing assertions, and the generator is byte identical in project-os-dev, project-os-cockpit's script and bundle, and Your Trainer. State contradiction and full corpus coverage checks remain open.

`state_for:` now carries its authored reminder to later applicable steps on the same platform until another declaration replaces it. A declaration on an omitted step still changes the later reminder; a declaration on a platform-only step does not affect the other platform. The focused preparation fixture has ten passing cases and the shared sheet has 157 passing assertions. Contradictory-state validation and a full corpus audit remain open.

Unscripted acceptance checks can now declare a platform-specific preparation or decision reason. The generator validates the map, retains the owed row and prints the reason on the matching platform's sheet. The focused fixture now has twelve passing cases and the shared sheet script passes. Both consumers received the same generator. [[CHG-20260917-Declare-readiness-for-unscripted-walk-checks]] records this contract addition; the task remains open for its broader validation and mutation evidence.

## Reaching the template, 2026-09-18

Found while hand-merging TESTING.md (FEAT-0036): the template's `walk-sheet.py` was last changed on 2026-09-14, so the sync reported this task's files as local content in every repo that had them, and four repos carried four different TESTING.md files. project-os c71dbb7 moved this repo's set into the template: `walk-sheet.py`, `test-walk-sheet.sh`, `test-walk-preparation.py`, the procedure and test templates, the walk-procedure skill and TESTING.md. Every line the other copies had that the template did not was checked and found to be older template wording.

Before moving it, the sheets were compared: project-os-deck's and project-os-cockpit's are byte-identical under the old and new code, and your-trainer's differ only because it uses the new fields. The template's CI now also runs `test-walk-preparation.py`.

Still open here: the validator's reports for missing or cyclic prerequisites, the mutation check, and the feature's two-reviewer review.

## Finishing, 2026-09-24

Edwin asked for this task to be finished: the validator's contradictory-state and coverage checks, ADR-0045 and TESTING.md rule 9 made to allow retained preparation, FEAT-0033's acceptance boxes ticked with evidence, and the generator synced to project-os-cockpit and your-trainer.

**What "contradictory state" means here.** ADR-0046 and rule 9 forbid the generator from reading action prose, so it cannot judge whether "any tier" contradicts "PRO" (Your Trainer FEAT-0122 A3). That conflict is resolved by the author, or labelled with `readiness_for: {kind: decision}`. What the validator can see is structural, and that is what it will report:

- **Two instructions for one thing.** The same step or setup id declared twice in one declaration map. The frontmatter parser keeps the last value and silently drops the first; measured 2026-09-24, `state_for` with step 2 declared as both FREE and PRO kept only PRO.
- **A declaration that can never apply.** A setup item limited to platforms on which none of its steps run; a `readiness_for` or `action_for` platform on a step unavailable on that platform.

**What "invalid platform coverage" and "full coverage" mean here.** A platform name the repo keeps no ledger for, in any declaration: `andriod` in `step_platforms` is accepted today. And a corpus-wide audit: `walk-sheet.py --check` on every platform of every consumer repo, recorded below.

**ADR-0045 and rule 9.** ADR-0046 (accepted 2026-09-16) already amends ADR-0045's filtering rule, and rule 9 already has the declared-preparation bullets. What is missing is ADR-0045's own pointer to the amendment, whose decision still says only cited steps print, and ADR-0046 in rule 9's list of decisions.

## Results, 2026-09-24

**The checks.** `walk-sheet.py` now refuses three structural contradictions. Each makes the sitting fall back to its per-check rows, as every other refused declaration does:

- `duplicate_declarations`: one step or setup id declared twice in the same declaration map. It reads the frontmatter text, because the parser keeps the last value.
- In `validate_preparation`: a setup item limited to platforms that none of its steps runs on, and a `readiness_for` platform or `action_for` variant on a step that does not run on that platform.
- `unknown_platforms`: a platform name in any declaration that the repo keeps no ledger for. Skipped in a repo with no ledgers.

TESTING.md rule 9, "What is checked", names them, and says that prose which disagrees is the author's to settle.

**Full coverage.** Your Trainer is the only repo in the fleet with procedures. `walk-sheet.py --check`, run with the new generator on both platforms, reports 0 problems and no coverage remark. So every owed part is cited, every live check in each sitting is reached, and no sitting with owed checks lacks a procedure. It evaluated 14 procedures and 866 steps: 359 `state_for` declarations, 108 scoped setup items and 6 platform-limited steps. The old generator also reports 0 problems. The new checks found nothing to correct in the corpus.

**Current sheets, REL-0017 Android, 2026-09-24.** Sitting 5 (FREE rides) keeps step 1 ("start Sweet Spot Base") and step 3 ("ride on to the programmed end"), both labelled preparation, around the owed summary step, and leaves out 82 steps. Sitting 13 (the final sweep) prints no AI key, email account or redirect browser. The procedure's `state_for` declares all three, for steps that are left out.

**Mutation check.** Recorded on [[TST-0023]]. Printing every setup item passed every test, because the one negative setup assertion was met by the platform filter. A walk owing only TST-1001 now proves that a same-platform item scoped to a left-out step is not printed.

**ADR-0045 and rule 9.** ADR-0045 now carries a callout naming ADR-0046 as the amendment to its decision 5, as ADR-0029 does for ADR-0045. Rule 9's list of decisions names ADR-0046.

**Synced.** Template working tree to project-os-dev, project-os-cockpit (the script and both bundled copies) and your-trainer, byte-identical. Tests there: cockpit 81 walk tests pass, and its full Python suite has 3 failures, all in desktop build and renderer code with uncommitted work by another session; your-trainer `--check` passes on both platforms and its validator passes. Your Trainer's `test-walk-corpus.py` fails 12 of 57, and the same 12 fail on its HEAD with the old generator. They come from the procedure its PHASE-025 close-out added (`a78f55c7`), and fixing them means rewriting its procedures, which is Your Trainer TASK-0960.
