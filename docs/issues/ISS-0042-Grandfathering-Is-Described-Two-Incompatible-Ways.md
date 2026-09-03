---
type: "[[issue]]"
id: ISS-0042
aliases: ["ISS-0042"]
title: "Grandfathering is described two incompatible ways"
status: fixed
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: docs
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 1.2", "https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc"]
related: ["[[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt]]", "[[ISS-0006-Status-Transition-Test-Gates-Requirements]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]"]
tasks: []
tests: []
---

# Grandfathering is described two incompatible ways

## Problem

QUALITY.md says the feature-requirement gate is grandfathered by the note's `updated:` date against a cutover constant, and that editing a grandfathered note for any reason re-arms the gate on it. STATUSES.md says there is no date-based exemption at all: grandfathered items are listed by ID in `tools/GRANDFATHERED.yaml`, and the date heuristic was removed because of that very re-arming (ISS-0007).

STATUSES.md is right and QUALITY.md is the leftover. An agent that reads QUALITY.md first will edit a note, expect the gate to arm, and act on a rule the validator no longer implements.

## Repro

```bash
cd ~/Dev/repos/project-os
sed -n '43p' tools/instructions/QUALITY.md      # FEATURE_REQ_GATE_FROM, updated: date, re-arming
sed -n '42p' tools/instructions/STATUSES.md     # listed by ID; there is no date-based exemption
```

## Expected

One statement of the grandfathering rule, in STATUSES.md, with QUALITY.md linking to it.

## Actual

Two statements, describing two different mechanisms, in the two files an agent is most likely to read before a close-out.

## Evidence

- Verified in the template on 2026-09-03. STATUSES.md "Grandfathering" reads: "There is no date-based exemption — the previous `updated:`-date heuristic re-armed a gate whenever a note was edited for any reason (ISS-0007)."
- QUALITY.md's paragraph is the sub-bullet under the FEATURE-REQ rule beginning "Mechanically, 'forward-only' is keyed on the note's `updated:` date".

## Next Actions

- [x] Delete the QUALITY.md paragraph and link to STATUSES.md "Grandfathering".
- [x] Confirm the validator still implements the ID-list mechanism only, so the deletion removes a false statement rather than an unimplemented one.

## Resolution

Fixed in the template by commit `685eef7` on 2026-09-03 (CHG-20260903-Prompting-Guide-Contradictions there). The QUALITY.md paragraph is replaced by one sentence linking STATUSES.md "Grandfathering", and the generated Cursor rule follows. Confirmed before deleting: the template validator reads `tools/GRANDFATHERED.yaml` and has no date cutover, so the paragraph described a mechanism that no longer existed.

## Sibling search

Siblings found: [[ISS-0006-Status-Transition-Test-Gates-Requirements]], and ISS-0041 and ISS-0043 filed the same day. Searched `docs/issues/` for: grandfather, cutover, restate, drift. Family rule proposed as [[ADR-0024-A-Normative-Rule-Is-Stated-Once]].

## Risk scan

Run against the LIFECYCLE.md triggers. No new risks: prose only, no behaviour change to the validator.
