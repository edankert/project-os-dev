---
type: "[[issue]]"
id: ISS-0096
aliases: ["ISS-0096"]
title: "Superseding a decision means editing the old note, and an agent that reaches the old note by a link is not told"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: medium
component: "tools/instructions/DECISIONS.md; sync-snapshot.py; snapshot-query.py; validate-docs.py"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tasks: ["[[TASK-0173]]"]
tests: ["[[TST-0031-Supersession-Is-Stamped-On-The-Old-Note]]"]
---

# Superseding a decision means editing the old note, and an agent that reaches the old note by a link is not told

## Problem

DECISIONS.md, "Superseding", has the author write `supersedes:` on the new ADR and `superseded:` plus a status change on the old one. So superseding means opening and editing the old note. The ADR-0045/ADR-0046 pair shows the other failure: ADR-0046 amended ADR-0045 on 2026-09-16, and ADR-0045 carried no pointer until 2026-09-25, so a reader who reached it by a link read a rule that no longer held.

## Expected

The author writes `supersedes:` (or `amends:`) once, on the new note. `sync-snapshot.py` stamps the old note's back-pointer and status; `snapshot-query.py` shows it; the validator warns when a live note cites a superseded one. Edwin proposed dropping the back-pointer, on the grounds that reading goes newest-first. ADR-0048, option 2, records why reading does not go newest-first, so the pointer stays but is generated rather than written by hand.

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

## Fixed, 2026-09-26

TASK-0173. The author writes `supersedes:` or `amends:` on the new note. `sync-snapshot.py` stamps the old note's pointer and, for supersession, its status, before every commit and stop. `snapshot-query.py` prints `superseded-by=`, and CITES-SUPERSEDED warns when work in flight links a replaced note. TST-0031 tests it.
