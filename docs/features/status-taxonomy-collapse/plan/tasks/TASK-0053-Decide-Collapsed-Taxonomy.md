---
type: "[[task]]"
id: TASK-0053
aliases: ["TASK-0053"]
title: "Decide the collapsed taxonomy per type and rewrite STATUSES.md, templates and SCHEMAS.md"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0013-Status-Taxonomy-Collapse]]"
effort: M
due: ""
depends: []
blocks: [TASK-0054, TASK-0055, TASK-0056]
related: [ADR-0008, REQ-0016, REQ-0017]
tests: []
---

# Decide the collapsed taxonomy

## Definition of Done

- [ ] Per-type vocabulary settled and written into `tools/instructions/STATUSES.md`, with a one-line retention justification for any value kept despite low usage.
- [ ] **The `approved` question is decided and recorded as an amendment to [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]]**, including its consequence for ADR-0006's approval-precedes-implementation clause and for REQ-0014's third acceptance criterion.
- [ ] The `superseded`-on-tasks mapping question is answered per repo (see Notes) and recorded, so TASK-0055 executes a decision rather than making one.
- [ ] Note templates under `docs/__templates__/` updated for any changed default status.
- [ ] `SCHEMAS.md` status sections updated.
- [ ] `failing` retained on tests with its ADR-0010 exception stated in `STATUSES.md`, not left implicit.

## Steps

- [ ] Draft the per-type table from ADR-0008 and re-verify each deletion against the fleet counts before committing to it.
- [ ] Resolve `approved` — the one genuine trade-off. Options, to be chosen explicitly:
  1. **Keep it.** Costs nothing; leaves a value with 99 writes whose gate (`REQ-PREMATURE`) fires 3 times fleet-wide.
  2. **Delete it and delete the approval gate.** Simplest; reopens ADR-0006's "approval precedes implementation" and invalidates REQ-0014's third criterion, which would need reconciling per ADR-0006's own reconcile-never-tick rule.
  3. **Delete it and move the gate onto the feature.** A feature may not enter `in-progress` while a linked requirement has no agreed criteria — expressed as "criteria present and non-empty" rather than as a status word. Keeps the checkpoint, loses the vocabulary.
- [ ] Decide `wont-fix` versus `cancelled` for issues — two descoping words for one concept across types, worth collapsing while the file is open.
- [ ] Write the amendment onto ADR-0008 and, if option 2 or 3 is chosen, the reconciliation onto REQ-0014.

## Notes

**The `superseded`-on-tasks decision is the load-bearing one for migration risk.** 71 tasks carry it; it has never been legal, so no convention records what it meant. It maps to either `cancelled` (abandoned) or `done` (absorbed into work that shipped) — opposite sides of the delivery line. Establish the mapping per repo from note bodies and git context; a global guess will be wrong for one of the two populations and invisible afterwards ([[RISK-0001-Fleet-Status-Migration|RISK-0001]]).

This task blocks all three siblings: nothing can be enforced, migrated or counted before the target vocabulary exists.
