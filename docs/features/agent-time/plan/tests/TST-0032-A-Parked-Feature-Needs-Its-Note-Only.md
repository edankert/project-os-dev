---
type: "[[test]]"
id: TST-0032
aliases: ["TST-0032"]
title: "A feature filed for later validates with its feature note only, and is asked for its acceptance check once it is done"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0174]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-parked-feature.sh"
command: "bash ../project-os/tools/scripts/test-parked-feature.sh"
covers: ["[[ISS-0087-A-Parked-Feature-Gets-A-Full-Scaffold]]"]
tasks: ["[[TASK-0174]]"]
issues: ["[[ISS-0087-A-Parked-Feature-Gets-A-Full-Scaffold]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 4 assertions. Mutation in a scratch copy: M1 FEATURE-UNCOVERED fires for every status, 1 failure. Pristine 4 of 4."
related: []
---

# A feature filed for later validates with its feature note only, and is asked for its acceptance check once it is done

## Purpose

ISS-0087: the feature scaffold wrote a full set of notes for a feature nobody would build yet. The skill now gives such a feature its note only. This test pins down that the validator agrees, in a repo that holds an acceptance suite (where FEATURE-UNCOVERED is live).

## Procedure

`bash tools/scripts/test-parked-feature.sh` in `~/Dev/repos/project-os`, on a copy of the template.

- A `backlog` feature in a `planned` phase, with Findings and Open questions and nothing else, validates, and no finding names it.
- The same feature at `done` gets FEATURE-UNCOVERED.
- `feature-scaffold/SKILL.md` has the short path and says no requirements, plan, tasks, risk notes or acceptance check are written yet.

## Expected results

- Exit 0: 4 of 4, 2026-09-26.
