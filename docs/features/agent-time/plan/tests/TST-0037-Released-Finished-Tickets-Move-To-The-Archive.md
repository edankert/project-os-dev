---
type: "[[test]]"
id: TST-0037
aliases: ["TST-0037"]
title: "Finished tickets whose release is out move to docs/archive/, leave the snapshot, keep resolving, and draw only structural findings"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0180]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-archive-notes.sh"
command: "bash ../project-os/tools/scripts/test-archive-notes.sh"
covers: ["[[ISS-0091-Finished-Notes-Have-No-Archive]]"]
tasks: ["[[TASK-0180]]"]
issues: ["[[ISS-0091-Finished-Notes-Have-No-Archive]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 11 assertions. Five mutations in a scratch copy: M1 a ticket finished after the release moves too, 2 failures; M2 archived notes judged in full, 2; M3 structural findings about archived notes hidden too, 1; M4 snapshot entries kept, 1; M5 a plain move instead of git mv, 1. Pristine 11 of 11."
related: []
---

# Finished tickets whose release is out move to docs/archive/, leave the snapshot, keep resolving, and draw only structural findings

## Purpose

ISS-0091: finished notes stayed beside live ones for good, so searches and validator runs paid for them on every use.

## Procedure

`bash tools/scripts/test-archive-notes.sh` in `~/Dev/repos/project-os`: a copy of the template in a git repo tagged `v1.0`, with a released REL note.

- The dry run names one task, one issue and one retired check (and the template's own change notes) and moves nothing.
- `--apply` moves them under `docs/archive/` at the same sub-path, as git renames; a task finished after the release, an open task and a live test stay; nothing is deleted.
- The archived task leaves SNAPSHOT.yaml; the repo validates, and an open task's link to the archived one resolves.
- A content finding about an archived note is hidden and counted; a frontmatter parse error on one is still reported.
- The template's `.ignore` names `docs/archive/`.

## Expected results

- Exit 0: 11 of 11, 2026-09-26.
