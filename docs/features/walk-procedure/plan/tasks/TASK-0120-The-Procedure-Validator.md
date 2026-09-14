---
type: "[[task]]"
id: TASK-0120
aliases: ["TASK-0120"]
title: "The procedure validator fails on an owed part no step cites, an owed part two steps cite, a tag naming a retired check and a tag naming a missing step, with a fixture test for each"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 4"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: L
due: ""
depends: ["[[TASK-0119-The-Procedure-Format]]"]
blocks: ["[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure]]", "[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]]", "[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]"]
tests: ["[[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]"]
---

# The procedure validator

## What

A script reads a sitting's procedure, the check notes and the ledger, and fails with a message naming the check and step when the procedure and the owed set disagree. It is how an LLM-written procedure is trusted without a person re-reading every check.

## Definition of Done

- [x] For a release and platform, the validator computes owed parts from the same owed set `walk-sheet.py` uses (one implementation, ADR-0029 rule 7).
- [x] It fails, naming the check and step, when: an owed part is cited by no step; an owed part is cited by more than one step; a tag names a check at `status: retired`; a tag names a step number the check does not have; a quoted expectation does not match the check's Expect text (the check's own wording, compared after normalising whitespace only).
- [x] It also fails when a tag names a check that belongs to a different sitting, or say in this task why that is allowed.
- [x] It passes a procedure that cites every owed part exactly once, even when it also cites parts that are not owed, and does not fail on live checks the procedure does not yet cover. Coverage of every live check is the aim, reported as a count, not a failure.
- [x] A fixture harness proves each failure with its own fixture and proves the pass. It is the `command:` on [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]], and each assertion is shown to fail when its rule is removed (record the mutations in TST-0010's `adequacy:`).
- [x] Where it runs is decided (PLAN.md, open questions): `walk-sheet.py --check`, a `validate-docs.sh` rule, or both. Record why.

## Steps

- [x] Write the five failing fixtures first (four coverage defects and one quote mismatch).
- [x] Put the code where the cockpit's byte-identical bundle picks it up (PLAN.md soft dependency).

## Notes

- A procedure goes stale without being edited: a ledger event can make a new part owed. The regenerate skill (TASK-0122) is the answer; the validator is what tells you.
- [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]: the template's CI runs none of its harnesses. This harness would be the eighth. Do not fix that here, but say in the change note that it has the same exposure.

## Where it runs, which was this task's open question

**Both, and for one reason each.** `python3 tools/scripts/walk-sheet.py --check [--platform <p>]` is the command a person runs and the one the release skills call. `validate-docs.sh` calls it too, for every platform with a ledger, because a procedure goes stale when a **ledger event** lands and a ledger event is a commit to `docs/releases/ledgers/*.json` — so pre-commit and CI are exactly where the staleness arrives. A check that only ran when somebody remembered to generate a sheet would find out at the worst moment.

The code lives in `walk-sheet.py`, not in `validate-docs.py`, so project-os-cockpit keeps one byte-identical bundle instead of needing a second. `validate-docs.py` is what `walk-sheet.py` imports; the reverse would be a cycle.

**`validate-docs.sh` passes `--quiet`.** The check also reports things that are nobody's mistake — a sitting nobody has scripted yet, a change note written before the Impact rule existed. Unsuppressed, your-trainer printed seven of those and the cockpit twelve on every commit, which is how validator output stops being read. A real disagreement still speaks and still fails the commit.

## Why a tag from another sitting's procedure fails

The task asked for a decision or a reason. **It fails**, and the reason is rule 3: the first sitting in `WALK.md` that claims a check keeps it, so a check belongs to exactly one sitting. A tag from another sitting's procedure either walks that check twice or hides it from the sitting that owns it, and coverage is counted per sitting so neither shows up as a coverage error. The message names the sitting that does claim it. No consumer has a procedure yet, so this lands as an error from day one with a violation count of zero (ADR-0011).

## Two more failures than the five, and one deliberate silence

Beyond the five ADR-0045 lists, the validator also refuses a tag naming a check that matches no note at all (a typo would otherwise read as "an owed part nobody cited", pointing at the wrong file), a bare `TST-####` tag on a check that does number its steps, a procedure with no `sitting:`, a `sitting:` matching no heading, and a second procedure for one sitting.

**It stays silent on one thing on purpose.** Where a tagged check's note states no expected result, there is nothing to compare the quote against, so it reports nothing rather than a mismatch it has no evidence for. Fifty-seven of your-trainer's sixty-one rows looked like that on 2026-09-13 ([[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect|ISS-0064]]); calling all of them mismatches would be a false claim at scale.

## Adequacy

`test-walk-sheet.sh` is 157 assertions over ten fixture repos, two of them real git checkouts. **36 mutations, none survived** — one per rule, including the six the ADR names, the printing filter, the owed predicate, the tag verification and the Impact anchoring. Recorded on [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].

Two mutations survived the first pass and both were closed rather than excused, and the independent review of 2026-09-14 then added eight more defects with a fixture each (see the review response on FEAT-0031). One showed that `.match` with a redundant `^` made the anchoring rule impossible to get wrong and therefore impossible to test; the `^` came out and the fixture gained the sentence shape from the real corpus. The other showed that a refused procedure's fall-back was only observable on the sheet, not in the payload the cockpit renders — so the harness now imports the module and asserts the payload directly.

## The exposure this shares with the rest

[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]] still stands and this harness is the eighth. Not fixed here; said in the change note.
