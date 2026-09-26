---
type: "[[issue]]"
id: ISS-0099
aliases: ["ISS-0099"]
title: "654 warnings about fields an earlier change moved into the ledger will be printed on every run for months"
status: open
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: medium
component: "tools/scripts (a one-off migration); validate-docs.py LEDGER-FIELD"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: []
---

# 654 warnings about fields an earlier change moved into the ledger will be printed on every run for months

## Problem

your-trainer prints 654 LEDGER-FIELD warnings on every validator run: fields the ledger change (ADR-0037) moved off acceptance-check notes. The rule warns until 2026-12-17. The fix is mechanical and the same for every note, but it is left to happen note by note.

## Expected

A one-off migration script moves or drops the fields across a repo, with a dry run and a report, and the warnings go in one commit.

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.
