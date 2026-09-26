---
type: "[[task]]"
id: TASK-0168
aliases: ["TASK-0168"]
title: "A harness measures the share of finished notes a session opens and edits, and the hook times"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0100-Nobody-Has-Measured-Time-Spent-On-Finished-Notes]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0100-Nobody-Has-Measured-Time-Spent-On-Finished-Notes]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0026]]"]
---

# A harness measures the share of finished notes a session opens and edits, and the hook times

## Definition of Done
- [x] `tools/scripts/session-cost.py` reads Claude Code transcripts for a repo and reports, per session and in total, notes read and notes edited, and how many of each were finished when the session started.
- [x] Hook times measured on your-trainer with the template's scripts: pre-commit and Stop hook, cold and warm.
- [x] The baseline is recorded on PHASE-0009 before any other PHASE-0009 change is measured.
- [x] A harness asserts the counts on a fixture transcript and fails when the finished-note classification is broken.

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches.

## Result

See PHASE-0009, "Baseline, 2026-09-26". The first version counted only Edit and Write as edits, which found 10 edited notes in 36 your-trainer sessions; agents there edit through the shell, and counting `sed -i`, redirects, `tee`, Python writes, `mv` and `cp` found 198. A writing command counts as an edit only, not also as an open.
