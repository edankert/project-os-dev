---
type: "[[issue]]"
id: ISS-0066
title: "An expectation line may quote any Expect line of the check it cites, not the one its step is about"
status: fixed
phase: "[[PHASE-999-Parking-Lot]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-18
source: ["Independent review of PHASE-0005, 2026-09-14 (model:claude-opus-5)"]
question: "Must a walk step quote the Expect line that belongs to it? Recommendation: no. Leave the check as it is and add a sentence to TESTING.md rule 9: the quote proves the words are the check's own, not which step they belong to."
severity: medium
component: tooling
parent: ""
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[TASK-0120-The-Procedure-Validator]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tests: []
---

# An expectation line may quote the wrong Expect line and still pass

## Problem

A procedure step tagged `TST-0401.1` may quote any line of TST-0401's `## Expect` section, including the one that belongs to step 3. The validator compares the quote against the check's Expect lines as a **set**, so swapping two of them changes nothing it can see. A walker then reads, at step 1, the thing that should be observed at step 3, ticks it, and the ledger records a pass on TST-0401.

> [!quote] As reported — 2026-09-14 (model:claude-opus-5, independent review of PHASE-0005)
> **A quote may come from any `## Expect` line of the cited check, not the cited step's.** Swapping the quotes on `TST-0401.1` and `TST-0401.3` passes (`.../scratchpad/wrongline`, exit 0). Rule 9's letter allows it; its justification ("a tick ... stands as a verdict on the check itself") assumes otherwise.

## Repro

Take the procedure fixture in `tools/scripts/test-walk-sheet.sh`, swap the quoted text on the lines tagged `TST-0401.1` and `TST-0401.3`, and run `python3 tools/scripts/walk-sheet.py --check --platform testbed`. It exits 0.

## Expected

Either the validator holds a line tagged `.N` to the Nth line of the check's Expect section, or `TESTING.md` rule 9 says plainly that it does not and why.

## Actual

Neither. Rule 9 says the line "quotes one line of the check's own `## Expect` section word for word", which is true of the wrong line too.

## Why this is a decision and not a bug

**A check's Expect lines are not numbered and do not correspond to its steps.** Most checks state three or four assertions against five or six steps; some state one assertion for the whole walk. Pairing the Nth expectation with the Nth step would be an invention about a corpus that never had that structure, and it would refuse most correct procedures. The honest options are:

1. **Leave it.** A procedure is written by an agent that read the check in full and is reviewed by the person walking it. The quote still has to be the check's own words, which is what keeps the tick inside project-os-cockpit ADR-0041.
2. **Require each of a check's Expect lines to be quoted exactly once across the procedure.** Catches the swap, costs nothing when a check has one assertion, and refuses a procedure that quotes one assertion twice for two different steps — which may be legitimate.
3. **Number a check's Expect lines** and tag them `TST-0401.1e3`. A new field shape on 581 notes in the largest consumer, for a defect nobody has hit.

Option 2 is the one worth costing. It is Edwin's call, and nothing is blocked while it waits: the procedures that would exercise it are your-trainer's TASK-0906 and none is written yet.

## Next Actions

- [ ] Decide between the three options above, or a fourth.
- [ ] If option 2: measure how many of your-trainer's 39 owed checks state more Expect lines than their procedure would naturally quote.

## Checked against the template, 2026-09-18: a question for Edwin

`walk-sheet.py` checks the quote against all of the check's Expect lines; TESTING.md says only that it quotes one line of the check's own Expect section.

Checked as part of FEAT-0036 (TASK-0140).

## Answered and fixed, 2026-09-18

Edwin, 2026-09-18: as recommended. Template 7595361: TESTING.md rule 9 says a quoted Expect line proves the words are the check's own, and the tag says which step. `walk-sheet.py` is unchanged.
