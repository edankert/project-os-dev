---
type: "[[adr]]"
id: ADR-0045
aliases: ["ADR-0045"]
title: "A sitting may be walked from an LLM-written procedure that a script holds to the owed set, and the survey comes from change notes and screenshots rather than invalidated checks"
status: proposed
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["Edwin, 2026-09-14, approving the goal: 'Then it gives one procedure per sitting (checks sharing one setup): the setup stated once, each step naming the screen it happens on, and each expectation tagged with the check it satisfies.'", "Edwin, 2026-09-14: 'an LLM can always be integrated in these solutions'", "Review of your-trainer's REL-0017 walk sheet, 2026-09-14: 1,331 lines, 39 owed rows, 10 sittings, one setup printed four times in Sitting 2, 25 rows with no Setup"]
decision: "Option 3 proposed. Amends ADR-0029 rules 2, 5 and 8 and leaves rules 1, 3, 4, 6 and 7 as they are. The survey is built from change notes since the last release tag, grouped by the SUR-* ids their Impact section names, with before and after captures. A sitting may carry a procedure: setup once, numbered steps each naming a surface, and expectation lines tagged with TST-id and step number. A validator fails when an owed part is cited by no step or by two, or when a tag names a retired check or a step that does not exist. The sheet prints only the steps that cite an owed part. A sitting without a procedure prints per-check rows as today."
context: "The walk sheet removes the hand-written run plan but still prints each check separately, so shared setup repeats and the survey lists invalidated test categories rather than changed screens."
alternatives: ["Keep per-check rows", "Merge steps automatically in the generator, with no written procedure"]
consequences: ["ADR-0029 rule 8's 'no new obligation at close-out' no longer holds: a change note's Impact section must name the screens it changed, drafted by an LLM", "A procedure is authored text that cites checks, so the validator, not a person, keeps it honest against the owed set", "The procedure and the check note both describe a step; the check note stays the definition and the procedure is the script", "The generator reads git tags and change notes, so a shallow clone loses the survey"]
supersedes: ""
superseded: ""
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]]", "[[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect]]"]
---

# A sitting is walked from a written procedure

## Context

The walk sheet from [[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once|ADR-0029]] works, and a real release shows what it still lacks. your-trainer's REL-0017 Android sheet is 1,331 lines for 39 owed checks in 10 sittings. The sheet groups the checks but prints each one's Setup, Steps and Expect separately:

- Sitting 2 prints "Fake a connected trainer … do not use Failure mode" in TST-0648, 0649, 0653 and 0656, and again in TST-0651 in Sitting 6.
- "Start a Power workout on the data-only trainer" appears in TST-0648 steps 1 and 4, TST-0649 step 1, TST-0653 step 2 and TST-0656's setup.
- The comparison against a drivable KICKR recurs in TST-0648 steps 12 to 15, TST-0649 step 13, TST-0650 step 10 and TST-0656 step 7.
- 25 rows print "Setup: not stated".

The survey has a second problem. ADR-0029 rule 2 builds it from the ledger's invalidation events, grouped by the invalidated check's `area:`, quoting each change's "Acceptance checks reopened" section. That section exists to justify reopening a check, and half of them say "None". None of them says what changed on the screen. The screens themselves are captured by your-trainer's parity gallery, but the images have not been committed since 2026-06-17, so no before and after exists.

Edwin approved the goal on 2026-09-14 and added that the procedure may be written by an LLM.

## Options

1. **Keep per-check rows.** Nothing to build. The repetition above stays, and it grows with every check added to a sitting.
2. **Merge steps automatically in the generator.** The generator would detect shared setup and shared steps from the text. This is the kind of inference from prose that project-os-cockpit TASK-0449 was cancelled for, and it cannot tell two differently worded steps apart from two different steps. Out of scope by Edwin's goal.
3. **A written procedure per sitting, held to the owed set by a script.** An LLM drafts the procedure from the sitting's checks. A validator fails the procedure when it and the owed set disagree. The sheet prints the procedure, filtered to owed parts. Costs a format, a validator, a skill and a change to the survey.

## Decision

**Option 3.** This amends ADR-0029 rules 2, 5 and 8. Rules 1, 3, 4, 6 and 7 stand. The normative text will be `tools/instructions/TESTING.md`, "The walk" (TASK-0118, TASK-0119), and TESTING.md governs where the two differ (ADR-0024).

1. **Rule 2 is replaced: the survey comes from change notes and captures.** The survey lists every surface named in the Impact section of a change note merged since the last release tag, with the one rider-facing sentence each change wrote for it. Where the repo's gallery maps a capture key to that surface, the survey shows the capture from the last release tag beside the capture from the release candidate. The survey prints no test id.
2. **A change note names the screens it changed.** The Impact section of `change.md` lists `SUR-*` ids, each with one sentence a rider would understand. The close-out and change-note skills ask an LLM to draft it from the diff. This replaces rule 8's "the walk asks nothing new at close-out" for change notes only. The reason is the measurement above: the one input the survey needs is not recorded anywhere else.
3. **A sitting may carry a procedure.** It states the setup once, then numbered steps. Each step names the surface it happens on. Each expectation line carries one or more tags of the form `TST-####·N`, meaning it satisfies step N of that check. A check with no numbered steps is cited by its bare id. The exact spelling of the tag and where the procedure file lives are settled in TASK-0119.
4. **A validator holds the procedure to the owed set.** It fails when an owed part is cited by no step, when an owed part is cited by more than one step, when a tag names a retired check, or when a tag names a step the check does not have. It does not judge whether the wording is faithful; the check note stays the definition.
5. **Rule 5 is extended: the sheet prints the procedure's owed parts.** For a sitting with a procedure, the sheet prints the setup and only the steps that cite at least one owed part. For a sitting without one, it prints per-check rows exactly as rule 5 says today.
6. **A skill regenerates a sitting's procedure when its owed checks change**, and a regenerated procedure is kept only if the validator passes.

## Alternatives

- Option 1, per-check rows. Rejected because the repetition is the complaint.
- Option 2, automatic merging. Rejected as inference from prose, and out of scope.
- Keeping the survey on invalidation events and adding screenshots. Rejected because an invalidation names a check, not a screen, and a change that reopens nothing but alters a screen would be missed.

## Consequences

- ADR-0029 needs a one-line pointer to this amendment once it is accepted. The pointer is not added while this is proposed.
- REQ-0028's survey criterion is amended, with the reason recorded in its Amendments section.
- ADR-0029 option 2 rejected "a per-release authored run plan" as a second list of the checks for a release. A procedure is not per release: it belongs to a sitting and survives releases, and the validator decides which of its steps print. It does cite check ids. If the owner reads that as a second list, this decision should be declined.
- A pass recorded from a procedure step attests the procedure's wording, not the check's own Expect text. The validator checks coverage, not faithfulness. Whether a procedure line must quote the check's expectation verbatim is an open question for the owner.
- The generator must find the last release tag. In a shallow clone it cannot, and the survey then says so rather than printing an empty list.

## Acceptance

- [ ] **Where a procedure lives is decided**: inside WALK.md under each sitting, or one file per sitting beside it.
- [ ] **What a procedure covers is decided**: every live check in its sitting, or only the checks owed when it was last regenerated.
- [ ] **Whether an expectation line quotes the check's own Expect text is decided.**
- [ ] **REQ-0028's Amendments section records the survey change.**
