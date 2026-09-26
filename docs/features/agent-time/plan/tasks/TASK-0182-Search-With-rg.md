---
type: "[[task]]"
id: TASK-0182
aliases: ["TASK-0182"]
title: "Searches use rg, which honours what the repo ignores"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0102-Shell-Searches-Read-Files-The-Repo-Ignores]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0102-Shell-Searches-Read-Files-The-Repo-Ignores]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0038-Search-Puts-Live-Notes-First]]"]
---

# Searches use rg, which honours what the repo ignores

## Definition of Done
- [x] An always-loaded instruction says to search with the Grep tool or `rg`, not `grep -r`: LIFECYCLE, "Source of truth". LIFECYCLE stays at 999 of its 1,000 words; four phrases were trimmed to make room. The project-init skill's `grep -R` became `rg`.
- [x] Template scripts that search use rg when installed and fall back to grep. The one script that searches notes, `snapshot-query.py --search`, falls back to a Python scan instead, because grep would not skip `docs/archive/` as `.ignore` does. On this machine `rg` exists only as a Claude Code shell function, so scripts cannot assume it.

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0038: four mutations, all caught).
