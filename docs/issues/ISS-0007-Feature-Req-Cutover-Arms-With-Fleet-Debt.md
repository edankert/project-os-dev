---
type: "[[issue]]"
id: ISS-0007
aliases: ["ISS-0007"]
title: "FEATURE-REQ / REQ-BOXES cutover arms on 2026-07-25 with ~325 unresolved findings still in the fleet"
status: fixed
phase: "[[PHASE-0002-State-Model-Simplification]]"
severity: high
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
component: tooling
source: ["review:2026-07-25-fleet-state-audit"]
related: [ADR-0007, ADR-0011, FEAT-0017, REQ-0024]
tasks: []
tests: []
---

# The ADR-0007 cutover arms today, over undismantled debt

## Problem

`validate-docs.py` carries:

```python
FEATURE_REQ_GATE_FROM = "2026-07-25"
```

That date is **today**. From now on, `FEATURE-REQ` and terminal `REQ-BOXES` are errors rather than warnings for any note whose `updated:` is on or after the cutover.

The gate is keyed on the note's `updated:` date, not on when the item actually closed — the code says so explicitly, and names the consequence:

> editing a grandfathered note for any reason re-arms the gate on it (bring it into compliance, or leave the note alone)

The fleet is carrying roughly **325** findings of exactly these two kinds. Every one of them becomes a build failure the moment its note is touched for any reason at all — a typo fix, a link update, a template sync.

## Evidence

Current findings, from `validate-docs.py` per repo:

| Repo | REQ-BOXES | FEATURE-REQ |
|---|---|---|
| your-trainer | 121 | 30 |
| your-sudoku | 74 | 15 |
| your-health | 39 | 1 |
| your-applications.com | 21 | 6 |
| edankert.com | 10 | 1 |
| obsidian-supernote-sync | 4 | — |
| project-os-cockpit | 1 | 1 |
| **Total** | **271** | **54** |

ADR-0007's own outcome section records the design intent: *"53 grandfathered features carrying ~900 unresolved criteria between them report as warnings, not errors, so no repo's CI broke."* Grandfathering was chosen deliberately. What was not decided is what happens when a grandfathered note is next edited — and the answer, mechanically, is that the build breaks at an arbitrary future moment, in whichever repo happens to touch a stale note first.

## Expected

Either the debt is cleared before the gate arms, or the cutover moves to a date the backfill can meet.

## Actual

The cutover arms today with the debt intact. Nothing fails yet — failure is deferred until the next unrelated edit to any of ~325 notes, which makes it look like a regression introduced by whatever change happens to touch one.

## Impact

- **Unpredictable failure timing.** The break is triggered by an edit, not by a date, so it will surface during unrelated work in a repo whose owner has no context on ADR-0007.
- **A perverse incentive.** The cheapest way to keep a repo green is to not touch stale notes — the opposite of what the gate is for.
- **Template sync is a mass trigger.** `sync-project-os.sh` updates `updated:` across many notes at once; a routine sync could arm the gate on a large fraction of the debt in a single commit.

## Next Actions

- [ ] **Decide today**, one of: (a) clear the debt first and keep the cutover; (b) move `FEATURE_REQ_GATE_FROM` to a date the backfill can meet; (c) accept edit-triggered failure as the forcing function, deliberately and in writing.
- [ ] If (a) or (b): run the fleet backfill ([[TASK-0070-Fleet-Backfill-Before-Cutover|TASK-0070]]).
- [ ] Record the choice as an amendment to [[ADR-0007-Requirement-Terminality-And-Ownership|ADR-0007]].
- [ ] Generalise the ordering rule — debt cleared *before* promotion — via [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] clause 3, so the next promotion does not repeat this.
