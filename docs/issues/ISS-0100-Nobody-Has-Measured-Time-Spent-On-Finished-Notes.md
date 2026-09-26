---
type: "[[issue]]"
id: ISS-0100
aliases: ["ISS-0100"]
title: "Nobody has measured how much of a session goes to finished notes, so no fix can show it helped"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: medium
component: "tools/scripts/rank-bench-sessions.py (PHASE-0008's transcript harness)"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tasks: ["[[TASK-0168]]"]
tests: ["[[TST-0026-Session-Cost-Counts-Finished-Notes]]"]
---

# Nobody has measured how much of a session goes to finished notes, so no fix can show it helped

## Problem

ADR-0048 and ISS-0087 to ISS-0099 all aim to cut the time agents spend on older notes, and none has a baseline. PHASE-0008 already built a harness that reads real session transcripts and the notes a session opened.

## Expected

The harness reports, per session, the share of notes read and notes edited that were already finished or released, and the wall time spent in the pre-commit and Stop hooks. A baseline is recorded before ADR-0048's changes land and measured again after.

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

## Fixed, 2026-09-26

TASK-0168. `tools/scripts/session-cost.py` counts the notes each session opened, edited and was shown by a search, and how many were already finished when the session began. The baseline is in PHASE-0009. The after-measurement of opened notes needs sessions run with the new tools, and is the one PHASE-0009 exit criterion that waits on them.
