---
type: "[[phase]]"
id: PHASE-999
aliases: ["PHASE-999"]
title: "Parking lot — future and unplanned work"
status: planned
order: 999
owner: user:edwin
created: 2026-07-25
updated: 2026-09-22
goal: "Forward home for work that is wanted but unscheduled: deferred items descoped from a parent, and tracked-but-unplanned issues that belong to no active phase"
features: []
requirements: []
tasks: []
issues: [ISS-0005, ISS-0079, ISS-0080, ISS-0081, ISS-0082, ISS-0083, ISS-0085, ISS-0086, ISS-0087, ISS-0088, ISS-0089, ISS-0090, ISS-0091, ISS-0092]
related: [ADR-0005, REQ-0013]
tags: [phase, parking-lot]
---

# Parking lot

## Goal

The sentinel phase every project-os repo uses as the destination for work that is real, tracked, and not scheduled. It has two distinct populations, and the distinction matters:

1. **Deferred items** — descoped from a parent under the deferral procedure ([[ADR-0005-Deferral-As-Descoping|ADR-0005]], [[REQ-0013-Deferral-Semantics|REQ-0013]]). Deferral *requires* a forward home; where no real future phase exists, this is it. Five arrived on 2026-09-22 — the borrows from the Spec Kit read, filed then triaged and parked the same day.
2. **Tracked-but-unplanned items** — open, belonging to no active phase. One currently. The 2026-09-03 prompting-guide review's items were parked here for a few hours and then adopted into [[PHASE-0003-Prompting-Guide-Conformance|PHASE-0003]] the same day, together with ISS-0003, whose remaining fix is scheduled there. ISS-0047, found the same day, followed the same route within hours.

## Scope

| Item | Status | Why parked |
|---|---|---|
| [[ISS-0005-Feature-Less-Requirement-Triage\|ISS-0005]] | open, low | ADR-0007 follow-up. 14 of 23 feature-less requirements resolved mechanically; 9 are a real residue — 5 policies, 3 conventions, 1 unscheduled deliverable |
| [[ISS-0079-Converge-Pass\|ISS-0079]] | deferred, medium | Nothing checks the code against the requirement text. The one Spec Kit borrow project-os has no partial answer to; weigh against ADR-0016 before building |
| [[ISS-0080-Ambiguity-Markers\|ISS-0080]] | deferred, medium | An ambiguity an agent judged tolerable leaves no trace. The seven-category clarify taxonomy is the cheap half and needs no schema change |
| [[ISS-0081-Observable-Criteria\|ISS-0081]] | deferred, low | Acceptance criteria mix system behaviour with observable outcome. Weakest of the five; sample a dozen REQ notes before building, and decide it with EARS |
| [[ISS-0082-Reviewer-Owned-Notes\|ISS-0082]] | deferred, medium | `review_verdict` is someone else's judgement written by the author. ADR-0009's argument applied to verdicts; ISS-0077 is the same defect on requirement approval |
| [[ISS-0083-Override-Layering\|ISS-0083]] | deferred, medium | A repo that edits a template-owned skill diverges and hand-merges forever. July's unfiled groomable; count the real divergences before designing |

## Decided 2026-09-03 — a phase, not parking

Twenty-six items arrived here from one review and left the same day. The parking lot is for work with no owner and no date; a coherent body of work with an order and a plan is a phase. Edwin: "I would use a real phase instead of having them in phase-999." They are now [[PHASE-0003-Prompting-Guide-Conformance|PHASE-0003]]. [[ISS-0027-Terminal-Items-Are-Stranded-In-The-Parking-Lot-Phase]] is the cost of getting this wrong in one direction, and ISS-0029 is the cost of getting it wrong in the other.

## Out of scope

- Anything with an owner and a date. If work is scheduled, it belongs to a real phase.
- Cancelled or abandoned work. That is `cancelled`/`wont-fix` with the note preserved, not parking. **Parking means still wanted.**

## Exit criteria

This phase does not complete. Items leave it by being adopted into a real phase, or by being cancelled — both of which are decisions, not a phase transition. It is reviewed every backlog-grooming pass (`tools/skills/backlog-grooming/SKILL.md`), which exists partly to stop the parking lot becoming a place things go to be forgotten.

## Notes

**On the ID.** The note is `PHASE-999`, not `PHASE-0999`. The all-9s form is a documented sentinel that `validate-docs.py` exempts from counter integrity (`if set(str(num)) == {"9"}`), so it needs no `counters.PHASE` allocation and never collides with a real phase number. `PHASE-0999` would contain a `0` and lose that exemption, requiring `counters.PHASE` to be raised to 999 — which would then silently permit any phase ID up to 999 without counter discipline. The three-digit form is named explicitly in `STATUSES.md` and in `status-transition/SKILL.md` as the parking lot, so it is also the ID every other repo and skill already expects.

**On not letting it fill up.** A parking lot is only honest if things leave it. ISS-0005 is ADR-0007 residue; if it is still here after two grooming passes, the right answer is likely `wont-fix` with a recorded rationale rather than indefinite parking.

**On the 2026-09-22 arrivals.** Five items entered together from one read of an external system ([[Comparable-Systems-Spec-Kit-2026-09-22]]), which is the pattern the 2026-09-03 entry above warns about: twenty-six items arrived from one review and became [[PHASE-0003-Prompting-Guide-Conformance|PHASE-0003]] the same day. These five are different in the way that matters — they have no order, no dependency between them, and three of them recommend measuring before building. They are candidates, not a body of work. If two or more survive the next grooming pass, that is the signal to make them a phase rather than leave them here.
