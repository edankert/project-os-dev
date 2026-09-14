---
type: "[[feature]]"
id: FEAT-0030
aliases: ["FEAT-0030"]
title: "A surface is a screen, a change note names the screens it changed, and the survey shows those screens before and after"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["Edwin, 2026-09-14, approved goal: 'It opens with the app screens this release changed: what each one now shows, with before and after screenshots.'", "Edwin, 2026-09-14: no new screens concept; update the surfaces to be the real screens"]
goal: "The walk sheet's survey lists the app screens a release changed, each with a sentence a rider would understand and a before and after capture, because surfaces are screens and every change note says which screens it changed."
requirements: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tasks: ["[[TASK-0116-TAXONOMY-States-What-A-Surface-Is]]", "[[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed]]", "[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
release: ""
acceptance_exception: ""
reviewed_by: "model:claude-opus-5"
review_date: 2026-09-14
review_verdict: approved
related: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them]]"]
---

# A surface is a screen, and a change names its screens

## Goal

The survey at the top of a walk sheet lists the app screens a release changed. Each screen carries the sentence every change wrote about it, in words a rider would understand, and a capture of the screen at the last release beside a capture of the release candidate. No test id appears.

Today the survey groups invalidated checks by `area:` and quotes "Acceptance checks reopened" sections. On your-trainer that prints "Hardware" and "Riding — structured", which are test categories, above text that justifies reopening a check rather than describing a screen.

## Scope

In, all in the template repo:

- **What a surface is** ([[TASK-0116-TAXONOMY-States-What-A-Surface-Is|TASK-0116]]). TAXONOMY.md and `surface.md` say a surface is a screen by default and state ADR-0044's four rules: states, dialogs as children, checks that cross screens, and per-platform placement. Plus the `gallery:` field on a surface note: a list of `key` or `key:state` entries (decided 2026-09-14).
- **What a change note records** ([[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed|TASK-0117]]). `change.md`'s Impact section lists `SUR-*` ids, each with one rider-facing sentence. The change-note and close-out skills ask an LLM to draft it from the diff.
- **How the survey is built** ([[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures|TASK-0118]]). TESTING.md rule 2 and `walk-sheet.py`: change notes merged since the last release tag, grouped by the surfaces they name, with before and after captures.

Out:

- Rewriting any consumer's surfaces or `area:` values. your-trainer does that in its PHASE-024.
- Taking screenshots. The template names where captures are found; each consumer's gallery tool produces them.
- The cockpit's screen cards (project-os-cockpit FEAT-0150).

## Acceptance

- TAXONOMY.md carries the four rules once, and `surface.md` points there.
- A change note written from the template has an Impact section that lists `SUR-*` ids with one sentence each, and the close-out skill tells the agent to draft it with an LLM from the diff.
- On a fixture repo with a release tag, two change notes after it and a capture map, the sheet's survey lists exactly the surfaces those notes name, with their sentences and both captures, and contains no `TST-` string. [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After|TST-0011]] holds this.

## Risk scan

The survey gains one runtime input: the most recent release tag in git. A shallow clone has none, so the survey says it cannot find the tag rather than printing an empty list. No new external dependency, environment variable or credential. Captures are image files in each consumer repo; their size in git is that repo's risk (your-trainer RISK-0010), not the template's. No `RISK-*` here.

## Links

- Decision: [[ADR-0044-A-Surface-Is-A-Screen-By-Default]], and ADR-0045 decisions 1 and 2.
- Requirement: [[REQ-0029-A-Release-Walk-Reads-As-A-Script]] criteria 1 to 3.
- Downstream: your-trainer FEAT-0120 (its surfaces become screens, its change notes name them), project-os-cockpit FEAT-0150 (screen cards).

## Independent review, round one (2026-09-14)

`model:claude-opus-5`, fresh context, separate session from the author; same model family, recorded in `reviewed_by` and not the gate (`tools/instructions/QUALITY.md`, "Independent review (clean-context)"). Round one verdict: **changes-requested**. Round two closed it: the frontmatter reads `approved`.

The first two acceptance bullets hold. TAXONOMY.md carries the four rules and says they are stated there and nowhere else; `surface.md` points at them and restates none of them; `change-note/SKILL.md` step 2 and `close-out/SKILL.md` step 6 both ask an LLM to draft the `## Impact` list from the diff and the surface notes and to check that every id resolves.

The third bullet — "the sheet's survey lists exactly the surfaces those notes name" — is refuted on two inputs the reviewer built on a real git fixture.

**Two screens on one `## Impact` line lose one of them.** `parse_impact` anchors `_SUR_RE` at the start of the list item and reads one id per line, so `- [[SUR-0001]] and [[SUR-0002]]: both gained a lap counter.` puts SUR-0001 in the survey, drops SUR-0002 entirely, and prints SUR-0001's rider-facing sentence as `and [[SUR-0002]]: both gained a lap counter.` — raw wikilink markup in the one line a walker is meant to read. `walk-sheet.py --check` says nothing about it. `change.md` does say one line per screen, so the input is off-template; the sentence it prints is still broken markdown and the dropped screen is still silent.

**An `## Impact` list inside a fenced code block is read as a real changed screen.** A change note whose Impact section says "No screen changed: it is documentation" above a fenced example naming SUR-0002 puts SUR-0002 on the survey. `section()` and `parse_steps` both skip fences; `parse_impact` does not.

Neither is covered by [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After|TST-0011]]. Commands and output are in the reviewer's report, together with the non-blocking survey findings: an uncommitted change note is silently absent, an `## Impact` list back-filled onto a pre-tag note is invisible, and git's default rename detection can pair a deleted pre-tag note with a new post-tag one so that the new one never reaches the survey.

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

Both survey findings are fixed and pinned, verified against the same git fixtures that found them. An `## Impact` line naming two screens now lists both, each with the sentence "both gained a lap counter." and no wikilink markup; an `## Impact` list inside a fenced block adds no screen. Mutating either fix back — `parse_impact` stopping at the first id, or ignoring fences — turns `test-walk-sheet.sh` red by three and one assertions. Round two's full record is on [[REQ-0029-A-Release-Walk-Reads-As-A-Script|REQ-0029]].

## Round two's one finding, fixed rather than filed, 2026-09-14

Round two approved all three notes and verified every one of the eight fixes against the fixture that found it. It also found **a regression the eighth fix introduced**, reported in the note rather than held against the gate because no acceptance criterion claims anything about it. It is fixed here anyway, because parking a regression as an issue is not the same as living with a known limitation.

**What was wrong.** Round one's eighth finding was that `--check` failed forever in a repo with a ledger and no live acceptance check. The fix caught `WalkError` in `run_check` and carried on — and `WalkError` is also what `read_repo` raises for a **broken ledger**. So a ledger whose filename names no platform, and a ledger entry dated `2026-13-45`, both stopped being reported anywhere: the generator still refused them with exit 2, and `validate-docs.sh`, which is the only thing that reads a ledger on every commit, said nothing. Measured by the reviewer at `0f1b673` against `6a513ff`: both cases went from exit 2 to exit 0.

**What was done.** `NothingToWalk` is a subclass of `WalkError`, raised only when a repo has no acceptance check at a live status. `run_check` is silent about that one and reports everything else with exit 2. The redundant second early return went with it — the reviewer noted no test pinned it, and with the narrow exception in place it would have skipped the ledger check in a repo that happens to keep no `walk/` or `changes/` directory.

Two assertions pin it: a ledger named `testbed.json` and an entry dated `2026-13-45` each fail `--check --quiet` with exit 2 and their own message, while the all-retired fixture still exits 0 in silence. The suite is 157 assertions and 38 mutations.

**Why this one is worth naming.** It is the second time in this phase that making something quieter made it blind, and both times the blindness was invisible to the suite because the fixtures tested the case that was being fixed and not the case next to it. The first was `--quiet` on the walk remarks, where the narrowing was deliberate and recorded; this one was accidental and took a second reviewer to see.
