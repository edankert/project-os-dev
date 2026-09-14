---
type: "[[feature]]"
id: FEAT-0031
aliases: ["FEAT-0031"]
title: "A sitting is walked from a written procedure: setup once, a screen on every step, each expectation tagged with its check, and a validator that holds it to the owed set"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["Edwin, 2026-09-14, approved goal: 'Then it gives one procedure per sitting (checks sharing one setup): the setup stated once, each step naming the screen it happens on, and each expectation tagged with the check it satisfies.'", "Edwin, 2026-09-14: 'an LLM can always be integrated in these solutions'"]
goal: "A person walks a sitting from one procedure instead of from each check in turn: the setup is stated once, every step names its screen, every expectation line says which check step it satisfies, and a script refuses the procedure if it misses or double-counts anything the release owes."
requirements: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tasks: ["[[TASK-0119-The-Procedure-Format]]", "[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]", "[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure]]", "[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
release: ""
acceptance_exception: ""
reviewed_by: "model:claude-opus-5"
review_date: 2026-09-14
review_verdict: approved
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]]", "[[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect]]"]
---

# A sitting is walked from a written procedure

## Goal

A person walking a sitting reads one procedure. It states the setup once. Each numbered step names the screen it happens on. Each line saying what should be seen quotes the check's own Expect text word for word and carries an ASCII tag such as `TST-0648.4`, meaning it satisfies step 4 of check TST-0648. The procedure lives in one file per sitting under `docs/tests/acceptance/walk/`, linked from WALK.md, and is written once for the whole product, not per release. The walk sheet prints only the steps that cite something the release still owes. A validator refuses the procedure if an owed step is cited by nothing, cited twice, or cited from a retired check or a step that does not exist, or if a quoted expectation does not match the check.

Today the sheet prints each check separately inside a sitting. On your-trainer's v2.2.0 sheet the fake-trainer setup is printed four times in one sitting and the drivable-trainer comparison four times across checks ([[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]], Context).

## Scope

In, all in the template repo:

1. **The format** ([[TASK-0119-The-Procedure-Format|TASK-0119]]): where a procedure lives, its headings, the tag spelling, and the TESTING.md text.
2. **The validator** ([[TASK-0120-The-Procedure-Validator|TASK-0120]]) and its fixture test, which is the command on [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].
3. **The sheet** ([[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure|TASK-0121]]): `walk-sheet.py` prints a procedure's owed steps, and per-check rows where a sitting has no procedure.
4. **The skill** ([[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure|TASK-0122]]): an LLM regenerates a sitting's procedure when its owed checks change, and keeps it only when the validator passes.
5. **Downstream** ([[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit|TASK-0123]]): sync to your-trainer and project-os-cockpit, and REQ-0028's amendment recorded.

Out:

- Automatic merging of steps without a written procedure.
- Any ledger change. A verdict is still one event per check.
- Writing any consumer's procedures. your-trainer's are its TASK-0906.
- The cockpit's per-step ticks (project-os-cockpit FEAT-0150).

## What an owed part is

The validator needs a unit to count. Decided by Edwin on 2026-09-14: an **owed part** is one numbered item under a check's `## Steps` heading (or `## Procedure` where Steps is absent), for a check the ledger says this platform owes. A check whose steps are not numbered is one part, cited by its bare id. This matches the way the review counted repetition ("TST-0648 steps 12 to 15").

It depends on how many owed checks have numbered steps. [[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect|ISS-0064]] measured that most your-trainer rows keep their procedure in unheaded prose, so many will be one part each. The LLM writing a sitting's procedure numbers those steps in the check note when it gets to them, and the check then has one part per step.

## Acceptance

- The fixture test fails the validator on each of the five defects (the four coverage defects and a quoted expectation that does not match), one fixture each, and passes a procedure that cites every owed part once. [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].
- On a fixture sitting with a procedure and some checks already passed, the sheet prints the setup once and only the steps that cite an owed part.
- On a fixture sitting with no procedure, the sheet prints exactly what it prints today.
- The procedure skill exists and tells the agent to rerun the validator before keeping a regenerated procedure.

## Risk scan

No new external dependency, environment variable or credential. One new authored file shape per consumer (the procedure) and one new validator entry point. The LLM that drafts a procedure runs inside the agent session, not inside the generator or validator, so neither script gains a network call or a model dependency. No `RISK-*`.

## Links

- Decision: [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]].
- Requirement: [[REQ-0029-A-Release-Walk-Reads-As-A-Script]].
- Downstream: your-trainer FEAT-0121 (v2.2.0 procedures), project-os-cockpit FEAT-0150 (the page and step ticks).

## Independent review, round one (2026-09-14)

`model:claude-opus-5`, fresh context, separate session from the author; same model family, recorded in `reviewed_by` and not the gate (`tools/instructions/QUALITY.md`, "Independent review (clean-context)"). Round one verdict: **changes-requested**. Round two closed it: the frontmatter reads `approved`.

`bash tools/scripts/test-walk-sheet.sh` prints "139 assertions, 0 failure(s)". The harness guards: eight mutations applied one at a time to `walk-sheet.py` — including the doubly-cited rule, the uncited rule, the quote comparison, the bare-tag rule, the omitted count and `attach_procedure`'s early return on a refused procedure — were each killed. The skill exists and step 7 keeps a regenerated procedure only on a passing `--check`. Renumbering a check's steps behaves exactly as rule 9 says.

Four findings refute claims about behaviour.

**Two steps that share a number defeat the doubly-cited rule.** `audit_procedure` records `cited[tag].add(step.number)` and then fails on `len(steps) > 1`, so two distinct steps written `1.` and `1.` collapse to one entry and a procedure citing one owed part from both passes. Markdown's ordinary "every item is `1.`" style triggers it for every step at once, and the sheet then prints four headings all reading "Step 1".

**A check whose `## Steps` repeat a number owes fewer parts than rule 9 says.** `numbered_steps` deduplicates, so a check with three steps written `1. 1. 1.` is one owed part; a procedure citing `.1` alone passes and the other two steps are never walked. No corpus in the fleet does this today — the reviewer scanned all four repos' acceptance checks and found none.

**A tag inside a fenced code block is a citation.** `parse_steps` skips fences when finding step boundaries and then collects expectation tags from every line of the step, fences included. A fenced example satisfies coverage for a check that states no `## Expect` (57 of 61 rows on the corpus that needs this, per ISS-0064), and a fenced example that repeats a real expectation line refuses a correct procedure with "cited by steps 1, 4".

**The cockpit and the generator disagree about the same procedure.** `walk_payload` builds its `checks` map from the owed rows only, so every tag citing a check that has already passed resolves to nothing and is reported as "matches no acceptance check in this repo". On the harness's own fixture the generator exits 0 and walks the sitting from its script; `acceptance.walk_payload` returns `problems` of two and `steps` of zero and falls back to per-check rows. `TESTING.md`, "The walk", rule 7 says bundling the module is what makes that impossible. No cockpit test writes a procedure file at all, so nothing downstream guards it.

Commands, outputs and the non-blocking findings are in the reviewer's report.

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

All four procedure findings are fixed and pinned. A step's number is now its position, so two steps written `1.` are two steps and the doubly-cited rule fires on them; a check whose `## Steps` repeat a digit owes one part per item again; a tag inside a fenced block is neither a citation that satisfies coverage nor one that causes a false refusal. On the fixture where the page and the sheet disagreed, `acceptance.walk_payload` now returns `problems: []` and four steps, matching the generator's "4 steps to walk", and both new tests in the cockpit's `tests/test_walk_payload.py` fail when `known=known` comes off the `build_walk` call. Round two's full record, including one non-blocking side effect in `run_check`, is on [[REQ-0029-A-Release-Walk-Reads-As-A-Script|REQ-0029]].

## Round two's one finding, fixed rather than filed, 2026-09-14

Round two approved all three notes and verified every one of the eight fixes against the fixture that found it. It also found **a regression the eighth fix introduced**, reported in the note rather than held against the gate because no acceptance criterion claims anything about it. It is fixed here anyway, because parking a regression as an issue is not the same as living with a known limitation.

**What was wrong.** Round one's eighth finding was that `--check` failed forever in a repo with a ledger and no live acceptance check. The fix caught `WalkError` in `run_check` and carried on — and `WalkError` is also what `read_repo` raises for a **broken ledger**. So a ledger whose filename names no platform, and a ledger entry dated `2026-13-45`, both stopped being reported anywhere: the generator still refused them with exit 2, and `validate-docs.sh`, which is the only thing that reads a ledger on every commit, said nothing. Measured by the reviewer at `0f1b673` against `6a513ff`: both cases went from exit 2 to exit 0.

**What was done.** `NothingToWalk` is a subclass of `WalkError`, raised only when a repo has no acceptance check at a live status. `run_check` is silent about that one and reports everything else with exit 2. The redundant second early return went with it — the reviewer noted no test pinned it, and with the narrow exception in place it would have skipped the ledger check in a repo that happens to keep no `walk/` or `changes/` directory.

Two assertions pin it: a ledger named `testbed.json` and an entry dated `2026-13-45` each fail `--check --quiet` with exit 2 and their own message, while the all-retired fixture still exits 0 in silence. The suite is 157 assertions and 38 mutations.

**Why this one is worth naming.** It is the second time in this phase that making something quieter made it blind, and both times the blindness was invisible to the suite because the fixtures tested the case that was being fixed and not the case next to it. The first was `--quiet` on the walk remarks, where the narrowing was deliberate and recorded; this one was accidental and took a second reviewer to see.
