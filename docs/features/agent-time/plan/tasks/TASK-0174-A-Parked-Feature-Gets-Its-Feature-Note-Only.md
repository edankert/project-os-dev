---
type: "[[task]]"
id: TASK-0174
aliases: ["TASK-0174"]
title: "A feature filed for later gets its feature note only"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0087-A-Parked-Feature-Gets-A-Full-Scaffold]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0087-A-Parked-Feature-Gets-A-Full-Scaffold]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0032-A-Parked-Feature-Needs-Its-Note-Only]]"]
---

# A feature filed for later gets its feature note only

## Definition of Done
- [x] `feature-scaffold/SKILL.md`: a feature filed at `backlog` or into a planned future phase gets the feature note, with findings and open questions; requirements, tasks and the acceptance check are written when its phase starts. The skill's new section "A feature filed for later gets its feature note only" says so and why.
- [x] The validator does not demand an acceptance check of such a feature. It already did not: FEATURE-UNCOVERED fires only at `done`. TST-0032 pins that down.
- [x] Checked by running the planner on a scratch copy with a request to file a feature for later. On 2026-09-26 the planner subagent, given a scratch template with an active PHASE-0001 and a planned PHASE-0002, filed "export a workout as CSV" as FEAT-0001: one note with Findings and Open questions, a snapshot entry and the phase's `features:` list, and nothing else. It took 10 tool calls and 78 seconds, against 184 tool calls and 55 minutes for your-trainer's FEAT-0128.

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0032).
