---
type: "[[adr]]"
id: ADR-0005
aliases: ["ADR-0005"]
title: "Deferral is a descoping operation, not a status flip"
status: accepted
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
decision: "A parent's tasks list is its current scope; done/cancelled resolve scope, deferred may not remain in it — deferring an item detaches it from the parent (origin keeps provenance) and re-homes it to a future phase or the PHASE-999 parking lot"
context: "Deferred items were being counted as complete: parents closed over them and parked work vanished from retention, metrics, and the cockpit with no re-surfacing mechanism (ISS-0002)"
alternatives:
  - "Keep parent linkage and exempt deferred in every completeness check — rejected: status-based exemptions leak into every consumer (validator, dashboards, metrics) and keep the fake-done incentive alive"
  - "Treat deferred as terminal like cancelled — rejected: deferred work is still wanted; terminal status guarantees it is never revisited"
  - "Force every deferred item into a concrete future phase — rejected: projects without phase gating need a home too; the PHASE-999 parking-lot sentinel is the fallback"
consequences:
  - "The mechanical completeness rule stays brutally simple: everything in tasks: must be done or cancelled — no status exemptions"
  - "Deferring gains ceremony (descope, origin, forward home) — deliberate: parking work is a scope decision and should cost one explicit step"
  - "Deferred tasks are the one exception to the task-must-have-parent rule: origin + phase replace parent until re-adoption"
related: [FEAT-0011, REQ-0013, ISS-0002, ADR-0004]
---

# Deferral is a descoping operation, not a status flip

## Context

`deferred` was defined only as "parked", with no rule for what a deferred child means for its parent. Agents closing features read deferred children as "not required", the validator only checked IDs still present in the `tasks:` list, and cancelled children (which *should* allow parent closure) were blocked — together incentivising fake-`done` flips. Parked work then vanished from every active surface ([[ISS-0002-Deferred-Items-Satisfy-Parent-Completeness|ISS-0002]]).

## Decision

A parent's `tasks:` list is its **current scope**:

- `done` and `cancelled` **resolve** scope — a parent can complete over them.
- `deferred` does **not** resolve scope and may not remain in a scope list. Deferring an item is a descoping operation: remove it from the parent's `tasks:` list, record it in the parent's `deferred:` list, set the item's single-word `origin:` field to the former parent (provenance), clear `parent:`, and give it a forward home — `phase:` pointing at a real future phase when one exists, else the `PHASE-999` parking-lot sentinel.
- Deferred items stay **active**: never pruned from the snapshot, counted in metrics, reviewed on every backlog-grooming pass, until re-adopted (new parent, status back to `backlog`/`open`/`draft`) or cancelled.

All of this is enforced mechanically by `validate-docs.py` (feature-done scope rule + DEFER-* checks), not by convention.

## Consequences

See frontmatter. The naming choice: `origin` (one word) rather than `deferred_from`, and it deliberately complements the existing `source` field (import provenance) without overlapping it.
