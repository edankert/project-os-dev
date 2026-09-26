---
type: "[[issue]]"
id: ISS-0097
aliases: ["ISS-0097"]
title: "Nothing stops a released ticket from being rewritten to match later work"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: medium
component: "tools/scripts/validate-docs.py; tools/instructions/LIFECYCLE.md"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tasks: ["[[TASK-0178]]"]
tests: ["[[TST-0035-An-Edit-To-A-Released-Ticket-Warns]]"]
---

# Nothing stops a released ticket from being rewritten to match later work

## Problem

LIFECYCLE says never to delete a completed note, but nothing says a finished ticket should not be rewritten. So agents keep old tasks and issues consistent with later work, which is the upkeep the your-trainer session measured.

## Expected

A ticket (task, issue, change note) whose release is out is frozen. An edit to it, other than the tool-written supersession pointer, is reported as a warning at pre-commit, so an unforeseen correction stays possible and visible (ADR-0048).

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

## Fixed, 2026-09-26

TASK-0178. The validator warns FROZEN-EDIT when a task or issue that was finished at the last release, or any change note, is edited in the working tree or the index. It names the ticket and the release. The tools' own writes (a supersession pointer, a derived list) and renames are not reported. It is a warning, as Edwin decided. TST-0035 tests it.
