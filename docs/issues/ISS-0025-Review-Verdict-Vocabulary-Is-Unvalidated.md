---
type: "[[issue]]"
id: ISS-0025
aliases: ["ISS-0025"]
title: "The validator checks that review_verdict is PRESENT but never that it is a DEFINED value, so any string reads as a satisfied review — 10 notes in one repo carried `CLOSE`, which QUALITY.md does not define"
status: open
severity: medium
owner: user:edwin
created: 2026-07-30
updated: 2026-07-30
component: docs
source: ["project-os-cockpit ISS-0069, 2026-07-30 — surfaced by RENDERING the corpus, not by validating it"]
phase: "[[PHASE-999-Parking-Lot]]"
related: []
depends: []
tests: []
---

# `review_verdict` has no validated vocabulary

## The finding

`QUALITY.md` defines the close-out review verdict as `approved` | `changes-requested`. The validator checks two things about the field, and neither is its value:

- **ADR-0011's `REVIEW` rule** warns when a terminal note carries **no** `review_verdict`.
- The `REVIEW` **error** fires on the specific string `changes-requested`.

An arbitrary value satisfies both. It is not absent, so no warning. It is not `changes-requested`, so no error. **It reads as a satisfied review gate.**

Measured in `project-os-cockpit` on 2026-07-30:

```
approved            65
CLOSE               10
accepted             2
```

The ten `CLOSE` notes are all `CHG-*` from a three-day window (2026-07-21..23) — one session's convention that nothing rejected. All ten carry `reviewed_by: "opus-independent-review"` and a date, so a review demonstrably happened; what is unrecoverable is what the word meant.

## Why it belongs upstream

`QUALITY.md`, the review fields, and `validate-docs.py` are all **template-owned**. Every adopting repo inherits the same gap, and the failure is silent by construction: a repo drifts into a private verdict vocabulary and its close-out gates keep reporting satisfied.

It also makes any count of "how much of the corpus is reviewed" wrong by an unknown amount in an unknown direction — a number that is load-bearing whenever a repo argues that its review process is working.

## The shape of the fix, and the part that is not obvious

There is more than one legitimate vocabulary, and they must not be interchangeable:

| Context | Values | Written by |
|---|---|---|
| close-out review (QUALITY.md) | `approved`, `changes-requested` | the independent review pass |
| plan acceptance at a review desk | `accepted`, `accepted-amended`, `rejected` | a human accepting a plan |
| design acceptance | `accepted` | a design decide-transition |

A union check is **not** sufficient and this is the trap: `project-os-cockpit` implemented one, its own note claimed the sets were "split by context", and an independent review demonstrated by mutation that stamping a close-out change note with `accepted` — a plan-acceptance value — still passed. The whole point of keeping the sets distinct is that a plan-acceptance stamp must not satisfy a close-out gate.

So the check must know **which context a note is in**, and the third context (design) has to be one of them or design acceptances get classified as desk acceptances.

## Expected

An unrecognised `review_verdict` fails validation. A recognised one that belongs to the wrong context also fails.

## Next Actions

- [ ] Decide the per-context vocabulary in `QUALITY.md` — it currently documents only the first row
- [ ] Add the check to `validate-docs.py`, keyed on context rather than a union
- [ ] Decide what adopting repos do with values already in the field. `project-os-cockpit` **cleared** its ten while keeping `reviewed_by` and `review_date` — a verdict nobody can interpret is not a verdict, but the evidence that a review happened is real information and destroying it would be worse

## Notes

Found by **rendering** the corpus, not by validating it: a `verdict-chip` in the cockpit UI showed grey — the fallback for a value its vocabulary does not recognise. The chip degrading rather than mis-colouring is correct behaviour, and it is the only reason this was visible at all. Worth keeping, because it inverts this system's usual lesson: here the surface caught what the validator could not.

`project-os-cockpit` carries a local guard (`test_review_verdicts_use_a_defined_value`) that catches the undefined-value case. It cannot be the answer for the fleet — it lives in one repo's suite, and `validate-docs.py` is byte-identity-checked against the template there, so it deliberately was not edited downstream.
