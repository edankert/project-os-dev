---
type: "[[requirement]]"
id: REQ-0023
aliases: ["REQ-0023"]
title: "Manual verification and verification waivers must carry a date and expire; staleness is a finding, not a status"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: medium
scope: verification
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0016]
related: [ADR-0010, ADR-0011, REQ-0006]
tests: []
acceptance:
  - "A test with no `command:` must carry `last_verified:`; a missing date is a validator error."
  - "A manual test whose `last_verified:` is older than the project's configured window is reported as stale and does not satisfy the VERIFY gate."
  - "Staleness is reported as a validator finding; no `stale` status value is added to the taxonomy."
  - "`verification_waiver` requires `waiver_expires:`; an expired waiver is an error while an in-date one remains a warning."
  - "The 48 existing waivers and the existing manual tests are dated during migration, with the chosen baseline and its rationale recorded."
---

# Manual verification expires

## Statement

Verification that cannot be executed shall carry the date it was last performed, and shall cease to satisfy the verification gate once that date falls outside the project's configured window. Verification waivers shall carry an expiry date. Staleness shall be reported as a validator finding rather than represented as a status value.

## Acceptance Criteria

- [x] Test without `command:` must carry `last_verified:` — evidence: `validate-docs.py` TEST-FIELDS; 80 manual tests backfilled before promotion
- [x] Stale manual test does not satisfy `VERIFY` — evidence: VERIFY rejects passing-but-stale; it caught FEAT-0001 in obsidian-supernote-sync on the first run
- [x] Staleness is a finding; no `stale` status added — evidence: TEST-STALE warning; the test taxonomy is still `{ready, passing, failing}`
- [x] `waiver_expires:` required; expired errors, in-date warns — evidence: `validate-docs.py` WAIVER; 49 waivers dated 2026-10-23
- [x] Baseline dated and rationale recorded — evidence: the Amendment; `last_verified` taken from each note's `updated:`

## Why not a `stale` status

Adding `stale` would regrow the taxonomy that [[REQ-0016-Declared-Statuses-Observed-In-Use|REQ-0016]] is cutting, and — decisively — it would be a value an agent could write by hand. That reintroduces the assertion problem [[REQ-0022-Test-Status-Stamped|REQ-0022]] exists to remove, at exactly the point where the system is trying to distinguish "verified recently" from "claimed once". Staleness is computed from a date; it is not a claim anyone makes.

## Why waivers need an end

`QUALITY.md` calls a waiver "a logged artifact" and forbids the silent skip, which is right. But a log entry with no end date is a rule deletion written in the passive voice, and there are 48 of them across the fleet with no expiry and no review. [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] grants `VERIFY-WAIVED` a standing exemption from promotion precisely *because* the waiver is meant to be logged — an exemption that only holds if the waiver itself is temporary.

## Impact analysis (2026-07-25)

- [[REQ-0006-Verification-Gating|REQ-0006]] — **extended.** REQ-0006 gates on test status; this adds a freshness condition to what counts as a satisfying status. Manual verification that was true a year ago and has not been repeated is not evidence about today's system.
- [[REQ-0022-Test-Status-Stamped|REQ-0022]] — same feature, complementary: REQ-0022 covers what can be executed, this covers what cannot. Together they close the gap without forcing manual checks into fake automation.
- [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] — aligned and mutually dependent: the `VERIFY-WAIVED` exemption is only defensible because waivers expire under this requirement.
- [[REQ-0016-Declared-Statuses-Observed-In-Use|REQ-0016]] — respected: no new status value is introduced.
- **Migration hazard, recorded not resolved:** dating existing manual tests from their creation date marks most of the fleet stale immediately; dating from migration is kinder and less truthful. The choice and its rationale are an acceptance criterion so the decision is visible rather than defaulted.

**No conflicts found.**

## Traceability

- Feature: [[FEAT-0016-Executable-Verification|FEAT-0016]]
- Decision: [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]]

## Amendment (2026-07-25) — backfill baseline chosen

The open question was where to start the clock for 80 existing manual tests. **Dated from each note's `updated:`**, not from migration day.

Migration-day dating would have given the whole fleet a clean 90 days and asserted that verification happened when it did not — the same fiction ADR-0010 exists to remove, one layer along. Dating from `updated:` immediately marks 13 tests stale across two repos, which is the true state and the point.

The 49 waivers were dated uniformly to **2026-10-23** (90 days), letting renewal be the forcing function: a waiver nobody renews was not load-bearing.
