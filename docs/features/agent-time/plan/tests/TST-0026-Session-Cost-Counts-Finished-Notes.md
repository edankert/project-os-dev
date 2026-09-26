---
type: "[[test]]"
id: TST-0026
aliases: ["TST-0026"]
title: "session-cost.py counts the notes a session opened, edited and was shown, and how many were already finished"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0168]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-session-cost.sh"
command: "bash ../project-os/tools/scripts/test-session-cost.sh"
covers: ["[[ISS-0100-Nobody-Has-Measured-Time-Spent-On-Finished-Notes]]"]
tasks: ["[[TASK-0168]]"]
issues: ["[[ISS-0100-Nobody-Has-Measured-Time-Spent-On-Finished-Notes]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 7 assertions. Four mutations in a scratch copy: M1 nothing counted as finished, 3 failures; M2 status read at HEAD instead of the session's start commit, 1; M3 every tool result counted as surfaced, 1; M4 shell edits not counted, 4. Pristine 7 of 7."
related: []
---

# session-cost.py counts the notes a session opened, edited and was shown, and how many were already finished

## Purpose

PHASE-0009's baseline and its second measurement come from `tools/scripts/session-cost.py`. The harness builds a two-commit git repo and a hand-written transcript with known contacts, and asserts each count.

## Procedure

`bash tools/scripts/test-session-cost.sh` in `~/Dev/repos/project-os`: a Read and a `cat` are opens; an Edit and a `sed -i` are edits (and `sed -i` is not also an open); only a search's result surfaces notes, not `ls`; a note closed after the session began counts as live; no transcript text reaches the output.

## Expected results

- Exit 0: 7 of 7, 2026-09-26.
