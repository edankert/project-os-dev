---
type: "[[issue]]"
id: ISS-0027
aliases: ["ISS-0027"]
title: "Nothing re-homes an item's phase at close-out, so work delivered without a plan stays in the PHASE-999 parking lot forever — 16 of 19 notes naming it in one repo are terminal, and the phase strip draws 16 `delivered` squares inside a phase titled 'Future'"
status: open
severity: medium
owner: user:edwin
created: 2026-07-30
updated: 2026-07-30
component: docs
source: ["project-os-cockpit, 2026-07-30 — Edwin: 'if a feature is complete but it was never planned, it will for always stay in the unplanned/future phase'"]
phase: "[[PHASE-999-Parking-Lot]]"
related: []
depends: []
tests: []
---

# Terminal items never leave the parking-lot phase

## The finding

`PHASE-999` is a sentinel for work with no delivery phase yet. Its own note describes exactly one exit: *"When the item gets serious planning, re-phase it into the concrete phase that will deliver it."*

That is the **forward** exit. The exit that actually happens most — the item gets *built* — was never written down, and nothing re-asks the question at close-out. `LIFECYCLE.md`'s close-out updates status, links, metrics and change notes; it never says re-home the phase.

Measured in `project-os-cockpit` on 2026-07-30:

```
19 notes name PHASE-999
16 are TERMINAL   (done / fixed / implemented / passing)
 3 are actually parked
```

The parking lot is **84% graveyard**. And the cockpit renders it exactly as absurdly as that sounds: the phase strip draws **16 `delivered` squares inside a phase titled "Future / Unphased"**.

Fleet-wide, notes naming the sentinel: `your-trainer` 72, `project-os-dev` 42, `project-os-cockpit` 19.

## Two details that sharpen it

**One feature's tasks ended up in two different phases.** `FEAT-0044` closed in `PHASE-013` with `TASK-0231` beside it; its sibling `TASK-0230` is still in `PHASE-999`. Same feature, same close-out, same day. Six of the sixteen are stranded children whose parent already lives in a real phase.

**The parking lot does not know its own residents left.** `PHASE-999`'s `features:` list still named `FEAT-0018` and `FEAT-0028` after both went `done` and were re-phased elsewhere — the membership list and the members disagree, and nothing compares them.

## Why it happens

`phase:` answers two different questions at two different times, and only the first is ever asked.

| When | Question | Is "not planned yet" an answer? |
|---|---|---|
| before the work | which phase plans to deliver this? | **yes** — that is what the sentinel is for |
| after the work | which push actually shipped this? | **no** — it is a category error, not a stale value |

So the field keeps a plan-time answer forever. The item is stuck **by construction**, not by neglect, which is why "be more careful" is not a fix.

## Proposed handling, ordered by how little discipline each needs

**1. Enforce it — the mirror of `PHASE-CHILDREN`.** A note whose status is in `PHASE_RESOLVED[type]` may not name the parking-lot phase. One predicate, reusing a table `validate-docs.py` already self-checks via `STATUS-TABLE`. This is the part that makes it stick: in this system, what was enforced held and what was merely documented drifted — sixteen times, here.

**2. Derive it where a parent exists.** A task's phase follows its feature's. Removes the stranded-children class structurally, needing no discipline at all. Same shape as [[ADR-0009]]: one authored value, the rest computed.

**3. Document it.** Close-out gains "re-home the phase to the one that delivered it". Worth adding and worth ranking last — an unenforced step is how the sixteen got there.

Also worth deciding: whether a phase's `features:` list should be **derived** from the notes naming it, rather than hand-kept alongside them. It is the same dual-write [[ADR-0009]] removed for statuses, and it drifted the same way.

## The objection, and the answer

Retro-stamping work with a phase that never planned it is fabrication, and the discipline exists to keep the record honest.

So the rule is **not** "stamp the currently-active phase" — it is *"name a phase that actually delivered you"*. In fifteen of the sixteen cases in `project-os-cockpit` one demonstrably did, resolvable from `parent:`, `fixed_by:` or `implements:` without judgement. The sixteenth genuinely shipped outside every phase, and the honest handling there is to **write the phase note** — a retrospective phase is a normal artifact, and cheaper than a second sentinel meaning "delivered, but unphased".

That is the shape of the escape hatch: not an exemption, a record.

## Next Actions

- [ ] Add the `PHASE_RESOLVED`-mirror rule to `validate-docs.py`
- [ ] Decide whether a child's phase is derived from its parent or merely checked against it
- [ ] Add the close-out step to `LIFECYCLE.md`, and the delivered-exit to the `PHASE-999` template note, which currently documents only the forward one
- [ ] Decide whether `features:` on a phase note should be derived
- [ ] Adopting repos will each have a backlog; `your-trainer` (72) and `project-os-dev` (42) are the large ones. The rule should probably land with grandfathering, as gates here have before

## Notes

Found by a user reading the surface, not by validation — the phase strip rendering shipped work under "Future" is what made it visible, and no check anywhere reports it. That is the third time in one week in this fleet that a rendering caught what the validator could not ([[ISS-0025]], and `project-os-cockpit`'s ISS-0072 and ISS-0073).
