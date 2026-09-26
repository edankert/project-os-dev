---
type: "[[issue]]"
id: ISS-0101
aliases: ["ISS-0101"]
title: "A search for a rule returns finished notes mixed in with live ones, and each has to be opened to tell which is which"
status: open
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["Edwin, 2026-09-26: 'why don't we build a database of the links before the session starts ... (review and suggest)', 'should we use rg instead of grep?', then 'Do as suggested'"]
reported_by: agent
question: ""
severity: medium
component: "tools/scripts/snapshot-query.py"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]", "[[ISS-0093-The-Checks-Parse-Every-Note-Several-Times]]", "[[ISS-0091-Finished-Notes-Have-No-Archive]]"]
tests: []
---

# A search for a rule returns finished notes mixed in with live ones, and each has to be opened to tell which is which

## Problem

In the your-trainer session, a search for one rule returned 57 notes, and 27 of them were finished tasks, issues and change notes. Each had to be opened and judged as history before the live ones could be read. Nothing in a search hit says whether the note is live, finished, frozen or superseded, and nothing answers "what links to this note" except another text search.

## Expected

`snapshot-query.py` gains two views, both read from ISS-0093's note index:

- `--search <text>` runs rg over `docs/` and labels each hit with its note's id and status. Live notes come first; frozen and superseded notes are collapsed into a count unless `--all` is given.
- `--links-to <ID>` lists the notes that link to an item, with the same labels.

The session-start orientation names both, as it names the lookup today, because agents reach for grep by habit (PHASE-0008: 255 of 260 lookups). ISS-0100's measurement should show the share of finished notes opened fall.
