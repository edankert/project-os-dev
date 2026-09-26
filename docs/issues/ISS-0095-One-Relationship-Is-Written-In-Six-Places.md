---
type: "[[issue]]"
id: ISS-0095
aliases: ["ISS-0095"]
title: "Adding a task writes the same membership in six places by hand, and the copies drift"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: high
component: "tools/scripts/sync-snapshot.py; validate-docs.py (PARENT-BACKLINK, SNAPSHOT-MEMBERSHIP); feature, phase and snapshot lists"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tasks: ["[[TASK-0172]]"]
tests: ["[[TST-0030-A-Relationship-Written-On-The-Child-Reaches-Every-List]]"]
---

# Adding a task writes the same membership in six places by hand, and the copies drift

## Problem

Adding a task to a feature in a phase writes one fact six times: the task's `parent:` and `phase:`, the feature's `tasks:`, the phase note's `tasks:`, and the snapshot's task entry, feature `tasks:` and phase `tasks:`. Two checks (PARENT-BACKLINK, SNAPSHOT-MEMBERSHIP) exist only to catch the copies drifting, and ISS-0084 was a copy that drifted silently. The your-trainer session applied later decisions about one feature across up to eleven notes.

## Expected

A relationship is written once, on the child (`parent:`, `phase:`, `implements:`). The parent's lists, the phase's lists and the snapshot's membership are generated, as statuses already are (ADR-0009). PARENT-BACKLINK and the membership parts of SNAPSHOT-MEMBERSHIP retire.

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

## Fixed, 2026-09-26

TASK-0172. A task is written once, with its `parent:` and `phase:`. In a repo that sets `retention.derive_lists: true`, the sync writes the parent's `tasks:`, the phase note's lists, the snapshot's copies of both, and the snapshot entry for a live task. The pre-commit hook stages each note it wrote. PARENT-BACKLINK, SNAPSHOT-MEMBERSHIP and TASK-MEMBERSHIP stay silent in such a repo, because a disagreeing list is the sync's to fix and `sync-snapshot.py --check` reports it. TST-0030 tests the whole path through the hook. The fleet dry run is in TASK-0172.
