---
type: "[[issue]]"
id: ISS-0062
aliases: ["ISS-0062"]
title: "A review's round count is recorded nowhere, so an eight-round review and a one-round review both read `approved` and the cost of the gate is invisible to every measurement"
status: fixed
phase: ""
severity: medium
owner: user:edwin
created: 2026-09-10
updated: 2026-09-18
source: ["[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]] acceptance criterion 2", "The 10% changes-requested rate ADR-0026 used to leave the review gate unchanged"]
component: docs
parent: ""
related: ["[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ISS-0061-A-Review-Gate-Has-No-Round-Cap-And-No-Severity-Bar]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[ISS-0025-Review-Verdict-Vocabulary-Is-Unvalidated]]"]
tests: [TST-0015]
---

# A review's round count is recorded nowhere

## Problem

A reviewed note records `reviewed_by`, `review_date` and `review_verdict`, and nothing anywhere records how many rounds the review took. An eight-round review and a first-time approval produce identical frontmatter. That blindness already changed a decision: [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] left the review gate alone on a `changes-requested` rate of about 10%, computed from final verdicts, which cannot see a round.

## Repro

```bash
# The eight-round review reads exactly like a first-pass approval:
grep -n "^review_verdict:" docs/changes/CHG-20260804-Retention-And-Field-Derivation.md
# 19:review_verdict: approved
sed -n '88p' docs/changes/CHG-20260804-Retention-And-Field-Derivation.md   # "...eight times"

# The five-round review contributes no row at all:
grep -n "^review_verdict:" docs/changes/CHG-20260726-Phase-Resolved-Declined.md
# 19:review_verdict: ""

# The whole population the 10% was computed from:
grep -rh "^review_verdict: " docs/ | sort | uniq -c
#   16 ""
#   16 approved
#    3 changes-requested
```

## Expected

The number of rounds a gate took is recorded on the reviewed note, so that ADR-0028's two-round cap can be checked rather than remembered, and so a later question about what review costs has data to answer it.

## Actual

Only the last verdict survives. Rounds are visible solely as hand-written prose in a note's body ("Reviewed clean-context **eight times**") or reconstructed from the issues each round happened to file. Neither is queryable and neither is required, so a ninth round would pass every check in the system.

## Evidence

- `docs/changes/CHG-20260804-Retention-And-Field-Derivation.md:19` and `:88` — `approved` in frontmatter, eight rounds in the body.
- `docs/changes/CHG-20260726-Phase-Resolved-Declined.md:19` — five rounds, empty verdict.
- `docs/__templates__/SCHEMAS.md` — declares `reviewed_by`, `review_date`, `review_verdict`; no round field.
- ADR-0026's Context, which cites "18 recorded verdicts ... 16 approved, 2 changes-requested" as the reason not to change the gate.

**Sibling search: a sibling exists** (searched: `review_verdict`, `review round`, `reviewed_by` over `docs/issues/`). [[ISS-0025-Review-Verdict-Vocabulary-Is-Unvalidated|ISS-0025]] is the same field failing a different way — the validator checks that `review_verdict` is present but never that it holds a defined value, so ten notes in one repo carried `CLOSE`. Two issues about the review frontmatter is the harvest trigger for a rule about what a review record must contain; ADR-0028 already stands over the gate, so the rule belongs there once this lands rather than in a third ADR.

## Next Actions

- [ ] **Decide how a round is recorded.** The open question, and it is the reason this note sits at `triage` rather than `open`. A counter field (`review_rounds: 2`) is cheap and hand-maintained, which is the [[ISS-0026-Coverage-Registers-Are-Hand-Maintained|ISS-0026]] shape. A per-round list is honest and verbose. Deriving it from the issues each round filed needs no new field and only works when a round files one.
- [ ] Declare the chosen field in `docs/__templates__/SCHEMAS.md`; a field a check reads must appear there ([[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]]'s recurring-class table).
- [ ] Add the validator check that ADR-0028's cap needs, warning-first with a dated promotion if any existing note violates it.
- [ ] Backfill the two known multi-round reviews (`CHG-20260804`, eight; `CHG-20260726`, five) so the first measurement is not all zeroes.
- [ ] Then promote ADR-0028 to a rule-ADR — this check is the `## Conformance` it is currently missing.

## Fixed, 2026-09-18
Fixed by PHASE-0007 in `~/Dev/repos/project-os` commit `3c979ee` (TASK-0129: `review_round` is recorded, and the validator refuses any value but 1 or 2).
