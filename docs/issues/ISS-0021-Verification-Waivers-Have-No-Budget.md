---
type: "[[issue]]"
id: ISS-0021
aliases: ["ISS-0021"]
title: "Verification waivers expire individually but nothing bounds how many are outstanding, and a batch stamped with one date is indistinguishable from waivers considered one at a time — all 19 in this repo expire 2026-10-23, the migration default no waiver has diverged from since"
status: open
severity: low
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: tooling
source: ["intake 2026-07-29: articles repo, quality-without-reading thesis, finding 8 (narrowed after verification)"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0017, ADR-0010, ADR-0011, REQ-0023, ISS-0019]
depends: [ISS-0019]
tests: []
---

# Verification waivers have no budget

## What the intake claimed, and what is actually true

The intake reported that `verification_waiver` has *"no budget, expiry, or ageing"* — that *"manual tests go stale via `last_verified`; waivers never do."*

**The expiry half is stale.** Waivers do expire, and it is an error, not a nudge. `validate-docs.py:1380-1393`:

- no `waiver_expires:` → `WAIVER` error, *"an open-ended waiver is a rule deletion written in the passive voice (ADR-0010)"*
- malformed date → `WAIVER` error
- `expires < today` → `WAIVER` error, *"renew it with a reason or satisfy the gate"*
- otherwise → `VERIFY-WAIVED` warning carrying the reason and the date

[[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] decided it (*"`verification_waiver` gains an expiry date"*) and `TASK-0068` shipped it. The intake's `:1377` pointer is accurate — that is where the waiver is read — but the expiry logic is on the next three lines and was missed.

Recording the correction because the intake asked for stale findings to be discarded, and half of this one is stale.

## The half that survives

**Nothing bounds the population.** Each waiver is checked in isolation: does it have a date, is the date well-formed, has it passed. No check asks how many exist, whether the count is rising, or whether one item's waiver is the fifth in its feature.

That distinction matters because a waiver is the sanctioned exit from the verification gate. An exit with a per-use check and no aggregate limit is a gate whose throughput is unbounded — every individual use is legitimate, dated and logged, and the sum is unexamined.

## Measured in this repo, 2026-07-29

19 `VERIFY-WAIVED` warnings. **Every one expires `2026-10-23`.** (An earlier draft of this note said 15 — a miscount from truncated validator output, caught by the ADR-0017 independent review.)

The provenance of the shared date matters and softens the naive reading: `2026-10-23` is the **migration default** — the FEAT-0017/TASK-0070 backfill dated 49 waivers fleet-wide with that single date when `WAIVER` was promoted to error, and that batch is documented in the promotion record. So this is not stealth batch-stamping at close-out.

What remains is the finding the per-waiver check structurally cannot see: **no waiver has diverged from the migration default since.** The field exists to force a per-item judgement about how long each item's verification gap should be tolerated; nineteen items carrying the migration's one-size date months later means that judgement has not happened once, and nothing will notice if it never does — until all nineteen expire on the same day, as one cliff.

The population also concentrates: `FEAT-0010` through `FEAT-0017` and `TASK-0041` through `TASK-0052` — i.e. two features' worth of program work closed almost entirely under waiver. Each waiver reason is substantive and mechanically specific (*"validate-docs 0 errors on 10 repos, sync-snapshot --check 0 drift on 10 repos, cockpit suite 253 passed"*), which is the system working as intended at the per-item level, and exactly why the aggregate is worth a look: this is what a well-behaved waiver population looks like, and it is still 19-for-19 on one date.

## Relationship to ADR-0017 and ISS-0019

Under [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]] clause 2, the waiver is the correct mechanism — an unexecutable claim, labelled and perishable. This issue is not an argument against waivers.

It pairs with [[ISS-0019-Verify-Is-Blind-To-Tests-That-Were-Never-Linked|ISS-0019]], and the two must be considered together or the fix to one worsens the other. ISS-0019 found 52 items closing with *neither* test nor waiver. The obvious disposition for many of them is a waiver — which would take this repo from 19 outstanding waivers to something nearer 71. Arming ISS-0019 without a view on the budget converts an invisible problem into a large visible one and calls that progress.

## Fix sketch, and the reason to be cautious

The cheap version is a derived count in `metrics.counts` (`waivers_outstanding`, and perhaps `waivers_expiring_30d`), which needs no rule and gates nothing — the same shape as [[ISS-0020-Nothing-Requires-A-Test-To-Be-Executable|ISS-0020]]'s metric, and cheap for the same reason.

A **budget** — a hard cap on outstanding waivers — is a much larger claim and should not be adopted on this evidence. Two objections to answer first:

- **A cap creates pressure to pick the invisible exit.** While ISS-0019 stands, closing with no waiver at all is cheaper than closing with one. A cap on the honest path, with the dishonest path unpoliced, is worse than no cap. ISS-0019 must land first; this is a sequencing constraint, not a preference.
- **A cap is a permanent warning by another name unless it can be satisfied.** [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] requires every rule to be an error or deleted. A waiver cap that no repo can meet is a rule that is always violated, which is the tier ADR-0011 abolished.

A more promising direction than a cap: make the *batch* visible rather than the count. A check that reports N waivers sharing one `waiver_expires` date addresses the actual finding here, is satisfiable by doing the per-item thinking the field already asks for, and cannot be gamed except by doing that thinking.

## Blast radius

Metrics are additive and fleet-safe. Any check is not: the fleet's waiver population is unmeasured, and `ISS-0007` is the standing precedent for what arming a check over an unmeasured population costs.

## Next Actions

- [ ] Correct the record: `waiver_expires` exists and errors. Done above; noted so no one re-files the expiry half.
- [ ] Add derived `waivers_outstanding` to `metrics.counts` — no rule, no gate.
- [ ] Measure the fleet-wide waiver population and the distribution of `waiver_expires` dates. The one-date pattern here may be fleet-wide or local to this repo's program closes; that changes the finding.
- [ ] Evaluate a shared-expiry-date check as the narrow alternative to a cap.
- [ ] Do not arm anything until ISS-0019 has landed — a cap on the visible exit while the invisible one is open is a regression.
