---
type: "[[test]]"
id: TST-0010
aliases: ["TST-0010"]
title: "A procedure covers every owed part exactly once, the validator refuses one that does not, and the sheet prints only the owed steps"
status: active
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[TASK-0120-The-Procedure-Validator]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-walk-sheet.sh"
command: "bash ../project-os/tools/scripts/test-walk-sheet.sh"
last_verified: ""
covers: ["[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
issues: []
tasks: ["[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
artifacts: []
adequacy: "36 mutations over walk-sheet.py, none survived (2026-09-14, after the independent review added eight); the list is in this note's Adequacy section"
mutation_score: "36/36 killed"
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
area: "the walk"
after: []
---

# A procedure covers every owed part exactly once

## Setup

The template repo checked out beside this one. The harness is `tools/scripts/test-walk-sheet.sh` there, and it is this note's `command:`, so the note records no verdict (ADR-0025): a red run is a red build.

The procedure fixtures it builds: one repo with two sittings, seven acceptance checks (three with numbered steps, one with unheaded prose, one retired, one already passed, one stating no expected result), a ledger, a `WALK.md`, and one procedure covering every owed part once. Each defect below is that repo copied with **one line of the procedure changed**, so an assertion that passes is pinned to the rule it names rather than to a fixture broken in several ways at once.

## Steps

1. Run the harness against the fixture whose procedure cites every owed part once.
2. Run it against the fixture where one owed part is cited by no step.
3. Run it against the fixture where one owed part is cited by two steps.
4. Run it against the fixture where a tag names a retired check.
5. Run it against the fixture where a tag names step 9 of a check with 4 steps.
5a. Run it against the fixture where one expectation line's quote differs from its check's Expect text by one word.
5b. Run it against the fixture where a tag names a check the other sitting claims.
5c. Run it against the fixture where a bare `TST-####` tag cites a check that numbers its steps, the fixture where a tag names no check at all, the fixture whose procedure has no `sitting:`, the fixture whose `sitting:` matches no heading in WALK.md, and the repo carrying two procedures for one sitting.
6. Generate the sheet for the first fixture, where one of its checks has already passed.
7. Generate the sheet for a fixture sitting that has no procedure.
8. Run it against the fixture whose step 2 names no screen.

## Expect

- Step 1 passes, and says which sittings still have no procedure. Citing a part that is **not** owed does not fail it, and neither does quoting a check that states no expected result — there is nothing to compare against, so there is no evidence of a mismatch.
- Steps 2 to 5c each exit 1, and each message names the file and the check or step involved.
- Step 6 prints the setup once, leaves out the step whose only tag is for the passed check, says one step was left out, and marks the passed tag on the step it keeps. It prints no per-check row for that sitting, and ends with one tick box per owed check.
- Step 7 prints the per-check rows the sheet prints today, unchanged.
- Step 8 exits 0 and reports "step 2 names no screen". A step that says where it happens is a rule; a step that does not costs no owed part its walk, so it is reported rather than refused.

## Not this check

- Whether a procedure's own step wording (outside the quoted expectations) describes the check well. The validator checks coverage and the quotes, not the prose around them.
- The survey. That is [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After|TST-0011]].

## Adequacy

155 assertions over nine fixture repos, two of them real git checkouts. **36 mutations applied to `walk-sheet.py` one at a time on 2026-09-14, none survived.** One per rule:

the uncited-owed-part rule · the doubly-cited rule · the retired-check rule · the unknown-check rule · the other-sitting rule · the missing-step rule · the bare-tag-on-a-numbered-check rule · the quote comparison · "silence is not a mismatch" · the owed filter on printed steps · one part per numbered step · reading a check's step numbers · nesting a child screen under its parent · restricting the survey to notes added since the tag · verifying the tag is in this checkout · which capture is before and which is now · marking a screen captured only now as new · stripping the wikilink before the sentence · a released note must carry a tag · the report of sittings with no procedure · the step-names-no-screen remark · the owed predicate the sheet shares with the gate · the fall-back to rows when a procedure is refused · a second procedure for one sitting · a procedure naming a sitting WALK.md does not have · the exit code `--check` reports a problem with · anchoring the Impact id at the start of its item · the list-item shape an Impact line must have · a step's number is its position rather than the digit written · a tag inside a fenced block is not a citation · a check's parts are its step positions rather than its distinct digits · every screen an Impact item names · a fenced Impact list is an example · nothing to check is not a failing commit · a tag may cite a check that has already passed · `--check` reads every change note whatever the tag says.

**Two survived the first pass and both were closed rather than excused**, which is the part worth keeping:

- *Anchoring the Impact id.* The pattern carried `^` and the call used `.match`, so removing the `^` changed nothing and the rule could not be got wrong — or tested. The `^` came out, and the fixture gained the exact sentence shape from the real corpus ("eleven checks now point at SUR-0002, which is where the old label went"), which only a `.search` reads as a screen.
- *The fall-back when a procedure is refused.* `attach_procedure`'s early return is invisible on a sheet, because the renderer decides from `problems`. It is not invisible to the cockpit, which renders `steps` from the payload. The harness now imports the module and asserts `problems=1 steps=0 owed_checks=0 walked=False` directly.

**Eight of the 36 came from the independent review of 2026-09-14**, which refuted three of REQ-0029's criteria against the 139-assertion suite. Every one of those eight is a defect the suite passed over, and the pattern in them is worth naming: **five were about a shape the corpus writes and the fixtures did not.** Markdown's "every item is `1.`", a worked example inside a fence, two screens on one Impact line, an `## Impact` list shown inside a fence, a repo whose checks have all been retired. The fixtures were written from the rule rather than from the corpus, and the rule is what the author already believed.

The two that were not about shape are the two worth remembering. One was a **disagreement between two readers of one corpus** that neither repo's suite could see, because no cockpit test wrote a procedure file at all. The other was a rule the author had written so that it could not be got wrong, and therefore could not be tested — `.match` with a redundant `^`.
