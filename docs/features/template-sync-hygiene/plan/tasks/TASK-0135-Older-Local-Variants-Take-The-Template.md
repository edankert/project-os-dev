---
type: "[[task]]"
id: TASK-0135
aliases: ["TASK-0135"]
title: "Older local variants take the template"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
effort: "Medium"
due: ""
depends: [TASK-0134]
blocks: []
related: []
tests: [TST-0016]
---

# Older local variants take the template

## Definition of Done
- [x] `docs/__templates__/test.md` in articles, edankert.com, project-os-bench, your-applications.com and yourtrainer-mcp, and `migrate-status-vocabulary.py` in edankert.com, your-applications.com and yourtrainer-mcp, take the template.
- [x] your-trainer's one DECISION-RULE error is fixed, and its `validate-docs.py` takes the template.
- [x] project-os-cockpit's `TESTING.md`, `STATUSES.md`, `TAXONOMY.md` and `run-tests.py` take the template, after the cockpit's own tests pass with them. `feature.md` takes the template and keeps the cockpit's `acceptance:` and `design:` fields. The local paragraph in `CONTEXT.md` moves to the cockpit's `CLAUDE.md`.

## Outcome, 2026-09-18
- **The template's version was taken** for the test template in five repos, `migrate-status-vocabulary.py` in three, project-os-deck's MANIFEST, and your-trainer's HOOKS.md, generator and validator. your-trainer's ADR-0016 gained the Conformance section the template's validator requires, quoting its own Acceptance section and deciding nothing new.
- **In project-os-cockpit**, `CONTEXT.md`, `TESTING.md`, `STATUSES.md`, `TAXONOMY.md`, `HOOKS.md` and the test template took the template's. The feature template took the template's and kept the cockpit's `acceptance:` and `design:` fields. The cockpit's upstream-ADR paragraph went into the template's `CONTEXT.md` (project-os `0ef121d`), because every repo needs it.
- **One cockpit test was repaired, and I had broken it.** `test_the_gate_states_the_contracts_own_rule` quoted the retired acceptance-tests template; it now checks the gate sentence against `TESTING.md`.
- **Kept, not taken:** the cockpit's `run-tests.py`, the ADR-0038 runner with its own tests, differs in design from the template's ADR-0025 runner, so it is listed under `keep_local:`. The cockpit's generator was also left alone, because Codex adapter work is in progress there.
- **Four failing cockpit tests predate this work** and are unchanged: the three `test_fleet_validate` tests and the live walk survey. They read HEAD, whose SNAPSHOT.yaml counters lag the FEAT-0151 notes another session committed.
