---
type: "[[test]]"
id: TST-0038
aliases: ["TST-0038"]
title: "snapshot-query --search and --links-to list live notes first and fold finished ones, with or without rg, and no instruction teaches grep -r"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0181]]", "[[TASK-0182]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-snapshot-query.sh"
command: "bash ../project-os/tools/scripts/test-snapshot-query.sh && bash ../project-os/tools/scripts/test-writing-rules.sh"
covers: ["[[ISS-0101-A-Search-Returns-Finished-Notes-Mixed-In]]", "[[ISS-0102-Shell-Searches-Read-Files-The-Repo-Ignores]]"]
tasks: ["[[TASK-0181]]", "[[TASK-0182]]"]
issues: ["[[ISS-0101-A-Search-Returns-Finished-Notes-Mixed-In]]", "[[ISS-0102-Shell-Searches-Read-Files-The-Repo-Ignores]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 8 new assertions in test-snapshot-query.sh (31 in all) and 2 in test-writing-rules.sh (7). Four mutations in a scratch copy: M1 nothing folded, 4 failures; M2 the fallback reads the archive, 4; M3 rg always reads ignored files, 1; M4 a skill teaches grep -R again, 1. Pristine 31 of 31 and 7 of 7."
related: []
---

# snapshot-query --search and --links-to list live notes first and fold finished ones, with or without rg, and no instruction teaches grep -r

## Purpose

ISS-0101: a search put finished notes in front of the agent mixed in with live ones. ISS-0102: `grep -r` reads what the repo ignores, including the archive.

## Procedure

`bash tools/scripts/test-snapshot-query.sh` and `bash tools/scripts/test-writing-rules.sh` in `~/Dev/repos/project-os`.

- `--search` lists the live note with its id and status, folds the finished one into a count, and leaves the archive out; `--all` lists both, marked.
- The same answer comes back without rg installed; with a stand-in rg on PATH it is used, and `--no-ignore` is passed only with `--all`.
- `--links-to` lists the live note linking to an item and folds the finished one; `--json` carries the live list and the finished count.
- The session-start orientation names both.
- LIFECYCLE says to search with the Grep tool or `rg`, and no instruction or skill tells an agent to run `grep -r`.

## Expected results

- Exit 0: 31 of 31 and 7 of 7, 2026-09-26.
