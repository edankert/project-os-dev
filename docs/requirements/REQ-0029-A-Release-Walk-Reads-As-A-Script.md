---
type: "[[requirement]]"
id: REQ-0029
aliases: ["REQ-0029"]
title: "A release walk reads as a script: the changed screens with a rider-facing sentence and before and after captures, then one procedure per sitting that a validator holds to the owed set"
status: implemented
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "Edwin, 2026-09-14: approved goal wording for the v2.2.0 walk"]
priority: high
scope: "The project-os template: tools/instructions/TAXONOMY.md and TESTING.md, docs/__templates__/surface.md, change.md, walk.md and SCHEMAS.md, tools/scripts/walk-sheet.py and its fixture test, the procedure validator, and the change-note, close-out, release-prep and new procedure skills. The cockpit page and each consumer's surfaces, change notes, captures and procedures are downstream."
acceptance:
  - "TAXONOMY.md says a surface is a screen by default and states four rules once: a state is not a surface; a dialog, sheet or panel is a child with parent:; a check that walks several screens names their parent; a screen placed differently per platform is one surface."
  - "change.md's Impact section lists SUR-* ids, each with one rider-facing sentence, and the change-note and close-out skills ask an LLM to draft it from the diff."
  - "The survey lists every surface named in the Impact section of a change note merged since the last release tag, with its sentences, and shows before and after captures where the gallery maps a capture key to that surface. It prints no test id. Without a reachable release tag it says so."
  - "A procedure for a sitting lives in one file under docs/tests/acceptance/walk/, linked from WALK.md, and states the setup once, then numbered steps that each name a surface, with expectation lines that quote the check's Expect text word for word and carry ASCII tags such as TST-0648.4."
  - "The validator fails on an owed part no step cites, an owed part two steps cite, a tag naming a retired check, a tag naming a step the check does not have, and a quoted expectation that does not match the check's Expect text; it passes when none of these holds. A fixture test proves each failure and the pass."
  - "For a sitting with a procedure the sheet prints the setup and only the steps citing an owed part; a sitting without one prints per-check rows as REQ-0028 describes."
  - "A skill regenerates a sitting's procedure when its owed checks change and keeps the result only if the validator passes."
  - "TESTING.md 'The walk' states these rules once; the templates, skills, generator and validator link to it without restating."
implements: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
verifies: []
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]"]
tests: ["[[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]", "[[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]"]
reviewed_by: "model:claude-opus-5"
review_date: 2026-09-14
review_verdict: approved
---

# A release walk reads as a script

## Statement

When a release is walked, the walk sheet shall open with the screens the release changed, each with one sentence a rider would understand and before and after captures where they exist, and shall present each sitting that has a written procedure as that procedure: the setup once, then numbered steps naming the screen, with each expectation tagged by the check it satisfies. A validator shall refuse a procedure that leaves an owed part uncited, cites one twice, or cites a retired check or a missing step.

Words used here. A **procedure** is a written script for one sitting. An **owed part** is one numbered step of a check the release still owes; a check with no numbered steps is one part. An **expectation tag** is a label such as `TST-0648.4` on a procedure line.

This requirement rests on two decisions Edwin accepted on 2026-09-14, [[ADR-0044-A-Surface-Is-A-Screen-By-Default|ADR-0044]] and [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]], together with the goal wording he approved the same day. It went `draft` → `implemented` at FEAT-0031's close-out without resting at `approved`, because the acceptance it would have been approved against is the wording already quoted in [[PHASE-0005-The-Walk-Reads-As-A-Script|PHASE-0005]] and the two ADRs' decision records. Said here rather than left as a gap in the history.

It is owned by FEAT-0031 because a requirement has at most one owning feature (ADR-0007). The first three criteria are built by [[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens|FEAT-0030]].

## Acceptance Criteria

- [x] TAXONOMY.md says a surface is a screen by default and states the four rules once — evidence: `tools/instructions/TAXONOMY.md`, "`kind` (surfaces)" opens with the rule and "The four rules" states them, one paragraph each with a your-trainer example. `docs/__templates__/surface.md` and `SCHEMAS.md`'s new `surface.md` entry link there and restate none of them. `TASK-0116`.
- [x] change.md's Impact section lists `SUR-*` ids with one rider-facing sentence each, and the change-note and close-out skills ask an LLM to draft it from the diff — evidence: `docs/__templates__/change.md`'s `## Impact` is one `[[SUR-####]]` line per screen plus the `No screen changed` form; `SCHEMAS.md` describes the shape a parser reads and records the removal of `## Acceptance checks reopened` with its reason; `change-note/SKILL.md` step 2 and `close-out/SKILL.md` step 6 both say to draft it with an LLM from the diff and the surface notes, then check every id resolves. `TASK-0117`.
- [x] The survey lists the surfaces named by change notes since the last release tag, with sentences and before and after captures, no test ids, and says so when no tag is reachable — evidence: `walk-sheet.py`'s `build_survey()` over `load_changes(only=changes_since(tag))`, `load_surfaces()` and `capture_finder()`; the tag comes from the newest released `REL-*` note for the platform. [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After|TST-0011]] asserts it on a real git fixture: the screens named after the tag and not the one before, each sentence with its change's title, the dialog nested under its parent, one screen before-and-after and one marked new, no `TST-` string anywhere in the survey, and the three ways it can have no anchor. `TASK-0118`.
- [x] A procedure lives in one file per sitting under `docs/tests/acceptance/walk/`, states the setup once, then numbered steps naming a surface, with expectation lines quoting the check's Expect text and ASCII tags — evidence: `docs/__templates__/procedure.md` with a worked example (a data-only trainer sitting whose third step is one action tagged for three checks); `SCHEMAS.md`'s `procedure.md` entry gives the parser's table; `TESTING.md`, "The walk", rule 9 is the normative text and defines an owed part. `TASK-0119`.
- [x] The validator fails on each of the five defects (uncited, doubly cited, retired check, missing step, quote mismatch) and passes otherwise, proven by a fixture test — evidence: `walk-sheet.py --check`, `audit_procedure()` and `_audit_tag()`. [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]] proves each of the five on its own one-line fixture, plus a tag naming a check another sitting claims, a bare tag on a numbered check, an unknown check, a missing `sitting:`, a `sitting:` matching no heading and two procedures for one sitting. 28 mutations, none survived. `TASK-0120`.
- [x] The sheet prints only the procedure steps citing an owed part, and per-check rows for a sitting without a procedure — evidence: `attach_procedure()` filters the steps and `render_procedure()` prints them; asserted on the fixture sheet — the setup printed exactly once, the step whose only tag is a passed check absent, the count of left-out steps, the passed tag marked on a mixed step, one tick box per owed check, no per-check row for that sitting, and the second sitting's rows unchanged. A procedure the validator refuses prints its message and then the rows, so nothing owed is hidden. `TASK-0121`.
- [x] A skill regenerates a procedure when its sitting's owed checks change, and keeps it only if the validator passes — evidence: `tools/skills/walk-procedure/SKILL.md`, step 7 keeps the result only on a passing `--check`; its refusals name the five things an LLM writing from check notes actually gets wrong. `release-prep` step 2a and `release-verification` step 3a run the check before a sheet is handed over. Registered in the skill list and the adapters regenerated. `TASK-0122`.
- [x] TESTING.md "The walk" states the rules once — evidence: rule 2 replaced, rules 5 and 8 narrowed, rule 9 added, and the section heading now reads "Nine rules". `walk.md`, `procedure.md`, `surface.md`, `SCHEMAS.md`, `TAXONOMY.md`, `walk-sheet.py`'s docstring and `--help`, and the change-note, close-out, release-prep, release-verification and walk-procedure skills all link to it by section name and restate none of it.

## Traceability

- Implements: [[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]
- Verified by: [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]], [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]

## Independent review, round one (2026-09-14)

`model:claude-opus-5`, fresh context, separate session from the author. Same model family as the author, which is recorded in `reviewed_by` and is not the gate (`tools/instructions/QUALITY.md`, "Independent review (clean-context)"). Round one verdict: **changes-requested**. Round two closed it: the frontmatter reads `approved`.

The harness is real: `bash tools/scripts/test-walk-sheet.sh` prints "139 assertions, 0 failure(s)", and eight mutations applied one at a time to `walk-sheet.py` were each killed by it. Three of the eight criteria are refuted by inputs the reviewer constructed.

**Criterion 5 is refuted twice.** The rule the criterion names — an owed part cited by two steps is refused — is defeated by two steps that share a step number, because `audit_procedure` keys the count on `step.number` rather than on the step. Markdown's ordinary "every item is `1.`" style makes every step share a number, and nothing in TESTING.md or `procedure.md` forbids it. And a tag inside a fenced code block is read as a real citation, because `parse_steps` skips fences when finding step boundaries but not when collecting expectation lines — which both satisfies coverage with a fenced example (when the cited check states no `## Expect`, the dominant corpus shape per ISS-0064) and refuses a correct procedure with a spurious "cited by steps 1, 4".

**Criterion 3 is refuted.** A change note whose `## Impact` line names two screens loses the second one from the survey, and the first screen's rider-facing sentence prints as `and [[SUR-0002]]: both gained a lap counter.` — raw wikilink markup. An `## Impact` list written inside a fenced block is read as a real changed screen.

**Criterion 8 is refuted.** `docs/__templates__/walk.md` restates rule 9's "Where it lives" bullet, its `sitting:` convention and its reason, in a file the criterion's own evidence names as restating none of it.

Separately, a check whose `## Steps` repeat a number collapses to one owed part, so the release owes less than rule 9 says it does; and the cockpit's `walk_payload` refuses any procedure citing an already-passed check, which is a disagreement between the two readers that rule 7 says cannot happen. The reproductions, the commands and the non-blocking findings are in the reviewer's report.

## Review response — round one addressed, 2026-09-14

All eight blocking findings are fixed with a fixture each, and five of the nine non-blocking ones. Two are filed as issues at `triage` because they need a decision rather than a change. The harness is 155 assertions and 36 mutations, none surviving.

**1. Two steps sharing a written number defeated the doubly-cited rule.** A step's number is now its **position in the list**, not the digit written, because markdown renumbers an ordered list and "every item is `1.`" is the style most people write. `written` is kept so the validator can report a note whose own numbering will not match the sheet. Rule 9 and SCHEMAS.md say so. Fixture: a procedure written `1.` on every item passes; two steps citing one owed part are refused naming "steps 1, 2".

**2. A tag inside a fenced block counted as a citation.** Expectations are now collected while the fence state is known, in the same pass that finds the step boundaries, so a worked example inside ``` claims nothing. Both directions have a fixture: a fenced repeat no longer refuses a correct procedure, and a fenced tag no longer covers an owed part.

**3. A check whose `## Steps` repeat a number owed one part instead of three.** `numbered_steps` counted distinct digits and now counts positions, the same rule as above. Fixture: a check written `1.` three times still owes three parts, and dropping one is still refused.

**4. The cockpit and the generator disagreed about one procedure.** `audit_procedure` takes `known` — every check a tag may legally name — defaulting to `checks`. A procedure covers its whole sitting and prints the owed part of itself, so its tags name checks that have already passed; a caller that passed only the owed set reported every such tag as naming no check. `walk_payload` now builds `known` from the checks its procedures actually cite, so a repo with 431 of them pays for the handful its scripts name. Two new cockpit tests write a procedure file — the reviewer found that none did — and both fail when the fix is reverted. The template harness asserts the same contract through `build_walk`, because the generator always passes the full set and cannot reach it alone.

**5. `walk.md` restated rule 9.** It now says a sitting may be walked from a written script and points at rule 9 for everything else: one sentence, no facts of its own.

**6. A change note naming two screens on one Impact line lost one of them,** and printed the other's sentence as raw wikilink markup. The parser reads the whole run of ids at the head of an item, joined by `and`, `,`, `&` or `+`, and gives each of them the one sentence that follows. SCHEMAS.md documents the shape. Fixture asserts both screens and that neither sentence carries the markup between them.

**7. An `## Impact` list inside a fenced block was read as a real changed screen.** `parse_impact` tracks fences now. Fixture: a change note whose Impact section is "No screen changed" above a fenced example surveys nothing.

**8. `--check` failed forever in a repo with a ledger and no live acceptance check.** `read_repo`'s refusals reached the exit code, so a repo whose checks had all been retired failed its own pre-commit hook. Nothing to check is not a failure: it returns 0, and says why only when not `--quiet`. Fixture: every check retired, `--check --quiet` exits 0 and prints nothing.

**Non-blocking, fixed:** `--check` now reads every change note whatever the tag says, so a repo with no released `REL-*` note is still told which notes have no Impact list (the CHG note claimed this and the code did not do it); a retired citation gets the same message from the sheet as from `--check`, because `retired` is threaded into `attach_procedure`; a procedure whose written numbers do not match their positions is reported; `.svg` is a capture format; and rule 2 now says the survey reads what git says was **added**, so an uncommitted note and a back-filled Impact list are both outside it.

**Non-blocking, filed rather than fixed:** [[ISS-0066-An-Expectation-Line-May-Quote-Any-Expect-Line-Of-Its-Check|ISS-0066]] (a line tagged `.1` may quote the check's step-3 expectation; three options costed, Edwin's call) and [[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]] (deleting a change note can make git pair it as a rename and hide a new one; reachable only by breaking LIFECYCLE's "never delete a completed note").

**Not reproduced by the reviewer either, and left alone:** a path traversal through a `gallery:` key. Appending an extension and the fixed directory depth defeated every escape tried. Worth a bounded key one day; not a defect anybody can demonstrate today.

`docs/PHASES.md` listing both phases as `planned` was an uncommitted working-tree edit of mine that the review caught before it was committed. It is committed now.

### Round two (2026-09-14): approved

Same reviewer, same clean context, verifying the fixes to round one's eight blocking findings and nothing else (ADR-0028; `tools/instructions/QUALITY.md`, "Independent review (clean-context)"). Fixes are `project-os` `6a513ff` and `project-os-cockpit` `a168006`. **All eight are fixed**, each re-run against the reproduction that found it, and the good fixture still passes.

`bash tools/scripts/test-walk-sheet.sh` prints "155 assertions, 0 failure(s)", and the new fixtures pin the fixes: mutating each of the five code fixes back — the step number returning to the written digit, expectation tags collected inside a fence again, `numbered_steps` counting distinct digits, `parse_impact` stopping at the first id, `parse_impact` ignoring fences — turns the suite red, by one to three assertions each. So does removing `run_check`'s `WalkError` handler. In the cockpit, both new tests in `tests/test_walk_payload.py` fail when `known=known` comes off the `build_walk` call, and `walk_sheet_bundled.py` is still byte-identical to the template's `walk-sheet.py`.

Criterion 3 now lists both screens a two-id Impact line names, each with the clean sentence and no raw markup, and a fenced Impact list adds no screen. Criterion 5's doubly-cited rule fires on two steps that share a written digit, and a fenced tag neither satisfies coverage nor causes a false refusal. Criterion 8's restatement in `walk.md` is gone, replaced by one sentence that names what rule 9 states without stating it.

**One side effect, reproduced, not blocking.** `run_check` now swallows every `WalkError`, not only the three its docstring names. A ledger file whose name does not name a platform, and a ledger entry whose date is unparseable, both made `--check` exit 2 at `0f1b673` and both return 0 at `6a513ff`. `validate-docs.py` has no ledger check of its own, so nothing in `validate-docs.sh` reports either one any more. The generator still refuses both with exit 2, and no acceptance criterion here claims otherwise, so this is worth an `ISS-*` rather than a third round. Two lines are also unpinned by any test: `run_check`'s second early return (removing it leaves the suite green — it is redundant with the `WalkError` handler) and `walk.md`'s trimmed paragraph, which no harness can check.

## Round two's one finding, fixed rather than filed, 2026-09-14

Round two approved all three notes and verified every one of the eight fixes against the fixture that found it. It also found **a regression the eighth fix introduced**, reported in the note rather than held against the gate because no acceptance criterion claims anything about it. It is fixed here anyway, because parking a regression as an issue is not the same as living with a known limitation.

**What was wrong.** Round one's eighth finding was that `--check` failed forever in a repo with a ledger and no live acceptance check. The fix caught `WalkError` in `run_check` and carried on — and `WalkError` is also what `read_repo` raises for a **broken ledger**. So a ledger whose filename names no platform, and a ledger entry dated `2026-13-45`, both stopped being reported anywhere: the generator still refused them with exit 2, and `validate-docs.sh`, which is the only thing that reads a ledger on every commit, said nothing. Measured by the reviewer at `0f1b673` against `6a513ff`: both cases went from exit 2 to exit 0.

**What was done.** `NothingToWalk` is a subclass of `WalkError`, raised only when a repo has no acceptance check at a live status. `run_check` is silent about that one and reports everything else with exit 2. The redundant second early return went with it — the reviewer noted no test pinned it, and with the narrow exception in place it would have skipped the ledger check in a repo that happens to keep no `walk/` or `changes/` directory.

Two assertions pin it: a ledger named `testbed.json` and an entry dated `2026-13-45` each fail `--check --quiet` with exit 2 and their own message, while the all-retired fixture still exits 0 in silence. The suite is 157 assertions and 38 mutations.

**Why this one is worth naming.** It is the second time in this phase that making something quieter made it blind, and both times the blindness was invisible to the suite because the fixtures tested the case that was being fixed and not the case next to it. The first was `--quiet` on the walk remarks, where the narrowing was deliberate and recorded; this one was accidental and took a second reviewer to see.
