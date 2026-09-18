---
type: "[[task]]"
id: TASK-0125
aliases: ["TASK-0125"]
title: "Retain declared preparation and relevant setup in the walk"
status: doing
phase: ""
owner: user:edwin
created: 2026-09-16
updated: 2026-09-18
source: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
parent: "[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"
effort: "Large"
depends: []
blocks: []
related: ["[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]", "[[REQ-0031-Preparation-Is-Declared-And-Validated]]"]
tests: []
---

# Retain declared preparation and relevant setup in the walk

## Definition of Done

- [x] The authored syntax declares prerequisite step numbers, setup entries and platform variants without prose inference.
- [ ] The validator reports missing and cyclic prerequisites, invalid setup references, contradictory state and invalid platform coverage.
- [x] The generator retains required preparation in authored order, filters irrelevant setup and leaves the owed check set unchanged.
- [x] Child screen survey entries keep their true parent even when the parent has no change note.
- [ ] Fixture tests prove the expected output and a deliberately broken implementation causes those tests to fail. The output assertions pass; a mutation check is still pending.
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

