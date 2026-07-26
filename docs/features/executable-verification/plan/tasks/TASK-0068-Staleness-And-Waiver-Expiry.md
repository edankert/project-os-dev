---
type: "[[task]]"
id: TASK-0068
aliases: ["TASK-0068"]
title: "Staleness finding for manual tests and expiry for verification waivers"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0016-Executable-Verification]]"
effort: M
due: ""
depends: [TASK-0066]
blocks: []
related: [REQ-0023, ADR-0010, ADR-0011]
tests: []
---

# Staleness and waiver expiry

## Definition of Done

- [ ] A test with no `command:` and no `last_verified:` is a validator error.
- [ ] A manual test past the configured window reports as stale and **does not satisfy** the `VERIFY` gate.
- [ ] Staleness is a finding; **no `stale` status value is added**.
- [ ] `verification_waiver` requires `waiver_expires:`; an expired waiver is an error, an in-date one stays a warning.
- [ ] The window is configurable in `SNAPSHOT.yaml` with a documented default (90 days).
- [ ] The 48 existing waivers and the fleet's manual tests are dated, with the chosen baseline and its rationale recorded in this note.

## Steps

- [ ] Implement the staleness computation and wire it into `VERIFY`.
- [ ] Implement waiver expiry.
- [ ] Decide the backfill baseline (see Notes) and record the reasoning.
- [ ] Date the 48 waivers and the manual tests; run the fleet validator and record the resulting counts.

## Notes

**The backfill baseline is a real choice, not a default.** Dating existing manual tests from their creation date marks most of the fleet stale immediately — honest, and noisy enough that it may be ignored, which would waste the mechanism. Dating from migration starts everyone with a clean 90 days — kinder, and a claim that verification happened when it did not. Recommended: date from creation and accept the initial noise, because a stale marker that everyone knows is artificially clean is worth nothing. Whichever is chosen, record why here — that is an acceptance criterion of [[REQ-0023-Manual-Verification-Expires|REQ-0023]].

**48 waivers need expiry dates.** Assigning them individually is 48 judgements about work that is mostly closed. Consider expiring them all at one near date and letting renewal be the forcing function — a waiver nobody renews was not load-bearing.

**Why no `stale` status.** It would regrow the taxonomy [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]] is cutting, and — decisively — it would be a value an agent could type, reintroducing the assertion problem this whole feature removes. Staleness is computed from a date; it is not a claim anyone makes.
