---
type: "[[issue]]"
id: ISS-0029
aliases: ["ISS-0029"]
title: "LIFECYCLE says when a phase note is needed and never when one is too small, so an agent under the document-first rule mints a phase per request — measured at nine in a day against nine in the preceding twelve weeks"
status: open
severity: medium
owner: user:edwin
created: 2026-07-30
updated: 2026-07-30
component: docs
source: ["project-os-cockpit ISS-0077, 2026-07-30 — counted after Edwin asked to review phase granularity"]
phase: "[[PHASE-999-Parking-Lot]]"
related: []
depends: []
tests: []
---

# Nothing says a phase can be too small

## The finding

`LIFECYCLE.md` step 4 says to create a phase note "when phase-gated work needs durable scope/exit criteria". That is the *lower* bound. There is no upper bound and no guidance on when work should **join** an existing phase instead.

Measured in `project-os-cockpit` on 2026-07-30:

| Era | Phases | Items per phase |
|---|---|---|
| PHASE-001…009, ~12 weeks | 9 | median **21** |
| PHASE-011…019, **one day** | 9 | median **4** |

Same count as the preceding twelve weeks, at a fifth of the size.

## Why an agent in particular hits this

**The document-first rule needs a focus item before code changes, and an open phase is the cheapest way to get one.** A `UserPromptSubmit` hook blocks edits until `SNAPSHOT.yaml` names something; a closed phase cannot host new work; so each new request produces a new phase rather than finding a home.

That is a structural incentive, not carelessness — which is why "be more careful" will not fix it, and why the rule belongs in the instruction rather than in a habit.

The split in that repo's own data shows it: `PHASE-011/012/013` were **planned together in one commit** when the user asked for a phase proposal, and are normally sized. `PHASE-014` through `019` were each created reactively, one per request, and are not.

## Why it matters

- A phase's gate stops meaning anything. `PHASE-CHILDREN` over four notes is not a gate.
- The cockpit's overview groups by phase; twenty rows each saying almost nothing is the opposite of what that strip is for.
- `docs/PHASES.md` stops being a map and becomes a log.

## Proposed rule

**Open a phase when both hold:**

1. Its goal can be stated **without listing its parts**.
2. Its exit criteria are something other than **"the tasks are done"** — criteria that restate the task list are a task list with a heading.

**Do not** open one for a single request, a single issue, or work finishing in the same session.

**Add the standing phase as a first-class idea.** One long-lived phase per durable surface, which small fixes join, closing only if the surface is retired. This is the missing mechanism: without somewhere to *put* a small thing, minting a phase is the only move that satisfies document-first.

**A phase closing with ≤3 items is a signal**, checkable before close-out.

## Next Actions

- [ ] Add the upper bound and the standing-phase idea to `LIFECYCLE.md`
- [ ] Consider a `PHASE-THIN` **warning** at close-out — a phase resolving with very few items. A warning, not an error: small phases are sometimes right, and the point is to make the author look
- [ ] Document the merge procedure. `superseded` already expresses it ([[ADR-0008]]); what is missing is the order — **re-home the children before superseding the parent**, or `PHASE-CHILDREN` fires

## Notes

Running downstream since 2026-07-30 in that repo's `CLAUDE.md`, with a worked example: PHASE-016 absorbed PHASE-017/018/019, nineteen phases to sixteen. Two guards there hold the merge invariants — no note may name a superseded phase, and a superseded phase must say what absorbed it.

Fourth in the same family as [[ISS-0025]], [[ISS-0027]] and [[ISS-0028]]: a close-out or planning obligation the template states half of.
