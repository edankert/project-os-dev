---
type: "[[task]]"
id: TASK-0177
aliases: ["TASK-0177"]
title: "A note links a rule by name instead of restating it"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0092-A-Note-Restates-A-Rule-It-Should-Link]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0092-A-Note-Restates-A-Rule-It-Should-Link]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0034-Notes-Hold-Current-State-And-Link-Rules]]"]
---

# A note links a rule by name instead of restating it

## Definition of Done
- [x] WRITING.md states it in one line: rule 12, "Link a rule by name; do not restate it".

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0034).
