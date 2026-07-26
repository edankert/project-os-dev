---
type: "[[issue]]"
id: ISS-0010
aliases: ["ISS-0010"]
title: "Plan notes never advance: 31 plans sit at draft/active under a done feature, and 16 carry no status at all"
status: fixed
severity: medium
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
component: lifecycle-rules
source: ["user-report:2026-07-26"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0006, REQ-0018]
tests: []
---

# Plans never advance

## Problem

A `PLAN.md` is created with its feature and then never touched again. Across the fleet:

| Plan status | Parent feature | Count |
|---|---|---|
| `active` | `done` | 21 |
| *(no status field)* | `done` | 10 |
| `draft` | *(unresolved)* | 29 |
| *(no status field)* | — | 16 total |

**31 plans sit at `draft`/`active`/nothing under a feature that is `done`.**

## Cause

Two distinct gaps.

**1. Nothing in the lifecycle advances a plan.** `close-out/SKILL.md` updates task, issue, feature, requirement and phase. Plans are not mentioned. `STATUSES.md` actively excuses it:

> Plans follow their parent feature; most projects leave plans at `draft`/`active`.

That sentence describes the behaviour and then licenses it, so no reader treats it as drift.

**2. Plans are invisible to every mechanical check.** `build_note_index` registers a note by its frontmatter `id` or an ID-prefixed filename. `PLAN.md` has neither — and it *must not* have an `id:` of the template's `PLAN-FEAT-0000` form, because `extract_ids` would resolve `PLAN-FEAT-0012` to `FEAT-0012` and the plan would masquerade as its own feature (the same composite-ID collision that made a change note resolve as `FEAT-0009` in ISS-0026). So plans fall outside `NOTE-STATUS`, `ITEM-STATUS` and every status-keyed metric.

Being unregistered is what let 16 plans lose their `status:` field entirely without a single check noticing — including plans created earlier in this same session, from an in-repo example that had already dropped the field.

## Impact

A plan is the delivery sequence for a feature. One reading `active` under a shipped feature says work is in flight that finished weeks ago — the same class of lie about state that PHASE-0002 removed everywhere else, surviving in the one note type no check could see.

## Fix

1. **Rule:** close-out advances the plan with its feature (`active` while building, `done` at close-out, `superseded` if the plan was replaced).
2. **Check:** a `PLAN-STATE` validator rule comparing a plan's status against its `parent:` feature — plans are found by `type: [[plan]]`, not by ID, since they deliberately have none.
3. **Backfill:** the 31 stale plans and the 16 missing `status:` fields.
4. Delete the excusing sentence from `STATUSES.md`.

## Resolution (2026-07-26)

1. **Rule** — `close-out/SKILL.md` now advances the plan with its feature (`active` → `done`, or `superseded`).
2. **Check** — new `PLAN-STATE` validator rule, finding plans by `type: [[plan]]` rather than by ID, since a plan deliberately has none. It reports a missing `status:` and a plan left non-terminal under a terminal feature.
3. **Backfill** — **17 plans given a `status:`**, **21 advanced** to match their feature. Fleet distribution is now 32 `done` / 9 `active` / 25 `draft`, and `PLAN-STATE` reports **0 findings across all 10 repos**.
4. `STATUSES.md`'s excusing sentence ("most projects leave plans at `draft`/`active`") replaced with the rule, plus the reason plans carry no `id:`.

The interesting part is *why* it went unnoticed: plans are the one note type outside `build_note_index`, so no status check has ever seen them. 16 had silently lost their `status:` field entirely — including plans created earlier in this same session, copied from an in-repo example that had already dropped it. An unregistered note type is an unchecked one.
