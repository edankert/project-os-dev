---
type: "[[phase]]"
id: PHASE-999
aliases: ["PHASE-999"]
title: "Parking lot — future and unplanned work"
status: planned
order: 999
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
goal: "Forward home for work that is wanted but unscheduled: deferred items descoped from a parent, and tracked-but-unplanned issues that belong to no active phase"
features: []
requirements: []
tasks: []
issues: [ISS-0003, ISS-0005]
related: [ADR-0005, REQ-0013]
tags: [phase, parking-lot]
---

# Parking lot

## Goal

The sentinel phase every project-os repo uses as the destination for work that is real, tracked, and not scheduled. It has two distinct populations, and the distinction matters:

1. **Deferred items** — descoped from a parent under the deferral procedure ([[ADR-0005-Deferral-As-Descoping|ADR-0005]], [[REQ-0013-Deferral-Semantics|REQ-0013]]). Deferral *requires* a forward home; where no real future phase exists, this is it. None currently in this repo.
2. **Tracked-but-unplanned items** — open, low-severity, belonging to no active phase. Two currently.

## Scope

| Item | Status | Why parked |
|---|---|---|
| [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing\|ISS-0003]] | open, low | Stale vendored hooks; fragile focus parsing and wrong-repo gating already fixed upstream. One unfixed case remains (non-repo path) |
| [[ISS-0005-Feature-Less-Requirement-Triage\|ISS-0005]] | open, low | ADR-0007 follow-up. 14 of 23 feature-less requirements resolved mechanically; 9 are a real residue — 5 policies, 3 conventions, 1 unscheduled deliverable |

## Out of scope

- Anything with an owner and a date. If work is scheduled, it belongs to a real phase.
- Cancelled or abandoned work. That is `cancelled`/`wont-fix` with the note preserved, not parking. **Parking means still wanted.**

## Exit criteria

This phase does not complete. Items leave it by being adopted into a real phase, or by being cancelled — both of which are decisions, not a phase transition. It is reviewed every backlog-grooming pass (`tools/skills/backlog-grooming/SKILL.md`), which exists partly to stop the parking lot becoming a place things go to be forgotten.

## Notes

**On the ID.** The note is `PHASE-999`, not `PHASE-0999`. The all-9s form is a documented sentinel that `validate-docs.py` exempts from counter integrity (`if set(str(num)) == {"9"}`), so it needs no `counters.PHASE` allocation and never collides with a real phase number. `PHASE-0999` would contain a `0` and lose that exemption, requiring `counters.PHASE` to be raised to 999 — which would then silently permit any phase ID up to 999 without counter discipline. The three-digit form is named explicitly in `STATUSES.md` and in `status-transition/SKILL.md` as the parking lot, so it is also the ID every other repo and skill already expects.

**On not letting it fill up.** A parking lot is only honest if things leave it. Both current items are ADR-0007 and template-sync residue; if either is still here after two grooming passes, the right answer is likely `wont-fix` with a recorded rationale rather than indefinite parking.
