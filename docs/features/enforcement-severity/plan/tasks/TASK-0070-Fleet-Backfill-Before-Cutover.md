---
type: "[[task]]"
id: TASK-0070
aliases: ["TASK-0070"]
title: "Clear ~325 REQ-BOXES/FEATURE-REQ findings across the fleet, and resolve the live ADR-0007 cutover"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0017-Enforcement-Severity]]"
effort: XL
due: ""
depends: []
blocks: []
related: [ISS-0007, REQ-0024, ADR-0007, ADR-0011]
tests: []
---

# Fleet backfill before cutover

## Definition of Done

- [ ] **[[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] decided and recorded as an ADR-0007 amendment** — this is the time-sensitive half and does not wait for the rest.
- [ ] The backfill strategy is chosen and written down **before** work starts (see Notes) — a half-finished backfill leaves the fleet worse than the warning did.
- [ ] `REQ-BOXES` and `FEATURE-REQ` findings resolved, or an explicit documented grandfather set defined with its rationale.
- [ ] Per-repo commits; each repo validates clean afterwards.
- [ ] No criterion is ticked without an evidence pointer — ADR-0006's reconcile-never-tick-to-fit rule governs this backfill absolutely.

## Steps

- [ ] **First**: decide ISS-0007 — clear the debt / move `FEATURE_REQ_GATE_FROM` / accept edit-triggered failure. Record it.
- [ ] Sample ~20 findings across repos to establish how many are genuinely tickable versus needing reconciliation. The sample determines whether the strategy below is viable at all.
- [ ] Choose the strategy and record it.
- [ ] Execute per repo, validating after each.

## The size of this

271 `REQ-BOXES` findings represent roughly **900 unresolved acceptance criteria** (ADR-0007's own corrected figure) across 53 grandfathered features. Ticking a box requires an evidence pointer per criterion, and ADR-0006 forbids ticking to fit. So this is not a script — it is ~900 individual judgements about work that closed months ago.

Strategies, to be chosen explicitly rather than drifted into:

1. **Reconcile in bulk by superseding.** Where a requirement's criteria no longer describe the system, supersede the whole requirement with one that does. Fewer, larger judgements; preserves the audit trail; ADR-0006 explicitly permits it.
2. **Tick with evidence, criterion by criterion.** Most faithful, and ~900 judgements — realistically months.
3. **Documented permanent grandfather set.** Freeze the current debt as explicitly exempt, enforce forward only. Honest and cheap, but under [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] clause 1 this is a *deletion* of the rule for that set, not an exemption, and should be recorded as such.

A hybrid — (1) where requirements are stale, (3) for the residue, (2) only where a criterion genuinely matters — is the likely answer. Decide before starting.

## Notes

**Do not start the backfill before ISS-0007 is decided.** Editing these notes is exactly what re-arms the gate; a backfill run over a repo mid-decision converts warnings into build failures as a side effect of the work meant to prevent them.

Effort is `XL` deliberately. Estimating this as a normal task is how it ends up half-done, which is the worst available outcome: partial ticking destroys the signal that the remaining findings are untriaged.
