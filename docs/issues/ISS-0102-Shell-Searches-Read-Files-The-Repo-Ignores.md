---
type: "[[issue]]"
id: ISS-0102
aliases: ["ISS-0102"]
title: "A shell search with grep -r reads files the repo ignores, and will read the archive too"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["Edwin, 2026-09-26: 'why don't we build a database of the links before the session starts ... (review and suggest)', 'should we use rg instead of grep?', then 'Do as suggested'"]
reported_by: agent
question: ""
severity: low
component: "tools/instructions (a search rule); tools/scripts that search"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]", "[[ISS-0093-The-Checks-Parse-Every-Note-Several-Times]]", "[[ISS-0091-Finished-Notes-Have-No-Archive]]"]
tasks: ["[[TASK-0182]]"]
tests: ["[[TST-0038-Search-Puts-Live-Notes-First]]"]
---

# A shell search with grep -r reads files the repo ignores, and will read the archive too

## Problem

`grep -r` ignores `.gitignore`. On your-trainer, searching the repo root for TASK-0922 found 348 files with grep and 174 with rg, which skips build output and agent worktree copies. Once ISS-0091 adds a `.ignore` for the archive, rg will skip that too and grep will not. Claude Code's own Grep tool is ripgrep already, so the gap is agents running `grep -r` in the shell, and scripts that shell out to grep.

## Expected

One instruction line: search with the Grep tool or `rg`, not `grep -r`. Scripts that search the repo use rg when it is installed and fall back to grep where it is not, so CI and machines without rg keep working. Speed is not the reason (0.07 s against 0.2 s); relevance is.

## Fixed, 2026-09-26

TASK-0182. LIFECYCLE says to search with the Grep tool or `rg`, not `grep -r`, and the searching script uses rg when installed and a scan that skips the archive when not. TST-0038 tests it.
