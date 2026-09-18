---
type: "[[feature]]"
id: FEAT-0037
title: "Every repo can take the template again"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["Edwin, 2026-09-18: 'Can you enumerate the changes needed for the template files in the different projects and suggest how to resolve?', then 'Implement as suggested.'", "[[TASK-0131-Roll-Out-And-Measure-Five-Reviews]] hand-merge list"]
goal: "The template sync fast-forwards every file that has no local edits. Files that belong to a project stop being reported. Work that was built in a project first reaches the template. So a sync reports only files that really need a person."
requirements: []
tasks: [TASK-0134, TASK-0135, TASK-0136, TASK-0137]
issues: [ISS-0068]
release: ""
acceptance_exception: "Tooling for the template's own sync; it is checked by the sync's fixture test and by the fleet's dry-run results, which the tasks record."
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]"]
---

# Every repo can take the template again

## Goal

Rolling PHASE-0007 out to the fleet on 2026-09-18 turned up about 100 template-owned files that the sync would not update. They fall into four groups:
- **51 are stale.** Each is exactly an older template version, left behind because an earlier sync skipped it and then recorded a later baseline.
- **14 hold content that belongs to the project**, such as a filled-in `LLM_BRIEF.md` or a CI workflow that differs on purpose.
- **About 12 are template work that was built in a project first.**
- **The rest are older local variants.**

This feature makes the sync handle the first two groups by itself, and clears the rest by hand.

## Scope

- [[TASK-0134-The-Sync-Fast-Forwards-Stale-Copies|TASK-0134]] (step 1): the sync fast-forwards any file that equals an older template version. `LLM_BRIEF.md`, `SECURITY.md`, `docs/INDEX.md` and `docs/README.md` become seed files. Workflows other than `validate-docs.yml` become project-owned. A repo can list files it keeps on purpose. Then the fleet is re-synced.
- [[TASK-0135-Older-Local-Variants-Take-The-Template|TASK-0135]] (step 2): the older local variants take the template, after a check each.
- [[TASK-0136-The-Cockpits-Validator-Checks-Reach-The-Template|TASK-0136]] (step 3): the cockpit's four validator checks move to the template, and the cockpit takes the template's validator.
- [[TASK-0137-Three-Repos-Reach-The-Current-Validator|TASK-0137]] (step 5): edankert.com, your-applications.com and yourtrainer-mcp clear the debt that stops the current validator, then take it.

## Out of Scope

- The walk-preparation files (`walk-sheet.py`, `test-walk-sheet.sh`, `procedure.md`, the walk-procedure skill, `walk_readiness_for:`). They reach the template when [[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup|TASK-0125]] closes, in its own session.
- project-os-cockpit's `tools/adapters/codex/ADAPTER.md`, which another session is editing.

## Acceptance

- A fleet dry-run lists no template-owned file that equals an older template version.
- Every file still reported is written up in a task note, with the reason it needs a person.

## Links
- Tests: [[TST-0016-The-Sync-Fast-Forwards-Only-What-Nobody-Edited|TST-0016]], [[TST-0017-Ledger-And-Frontmatter-Checks-Hold-Their-Rules|TST-0017]]
- Filed: [[ISS-0068-The-Cockpits-Validator-Carries-Rules-The-Template-Lacks|ISS-0068]]
