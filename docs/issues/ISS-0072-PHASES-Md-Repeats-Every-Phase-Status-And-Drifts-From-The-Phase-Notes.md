---
type: "[[issue]]"
id: ISS-0072
aliases: ["ISS-0072"]
title: "docs/PHASES.md repeats every phase's status by hand, and in your-health it drifted from the phase notes"
status: open
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["your-health, 2026-09-19: Edwin asked whether PHASES.md is superseded by the phase notes"]
reported_by: user:edwin
question: ""
severity: low
component: "templates"
parent: ""
related: ["[[FEAT-0008-Phase-Notes]]", "[[ISS-0071-A-Merge-Owned-File-Nobody-Edited-Never-Receives-Template-Updates]]"]
tests: []
---

# PHASES.md repeats every phase's status by hand, and drifts from the phase notes

## Problem

In your-health, the table in `docs/PHASES.md` showed a finished phase as planned and an active phase as planned, and it left two phases out. Anyone reading the table got a wrong picture of the roadmap. The status of each phase is already written in its note under `docs/phases/`. The table was a second copy kept by hand, which ADR-0009 says a status must never be.

FEAT-0008 (done) had "Replace `docs/PHASES.md` registry with individual phase notes" in scope. The template still ships `PHASES.md` with an example table, though. It still says the file "can either list simple phase definitions directly or point to first-class `PHASE-*` notes". So nothing tells a repo with phase notes to stop keeping the table.

> [!quote] As reported — 2026-09-19 (user:edwin)
> is phases.md not superseded by the new phase type?

## Evidence

- your-health, before 2026-09-19: the table said PHASE-0019 `planned` (note: `done`) and PHASE-0020 `planned` (note: `active`), and it had no rows for PHASE-0021 or PHASE-0022. The table was removed that day. The rest of the file stays: how phases work, and the history of why each phase was planned.
- Repos that still keep a table beside phase notes: project-os-dev (8 rows, 8 notes), project-os-bench (4, 4), articles (2, 2).

## Next Actions
- [ ] Decide what `PHASES.md` is for once a repo has phase notes. The recommendation is the explanation of phases plus the project's planning history, with no status table.
- [ ] Update the template's `PHASES.md` to say so, and drop the example table or mark it for repos with no phase notes.
- [ ] Optionally, have the validator warn when `PHASES.md` has a status column and `docs/phases/` exists.
- [ ] Remove the tables in project-os-dev, project-os-bench and articles.
