---
type: skill
id: SKILL-TEST-AUTHORING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, tests]
---

# Skill: Test authoring (manual + automated)

## When to use
- A task/issue/feature changes behavior and needs verification.
- A requirement should be gated on verification.

## Inputs
- What changed and what should be true (links to issue/task/feature/requirement).
- Whether verification is manual or automated.

## Outputs
- `../../../SNAPSHOT.yaml` updated (`items.tests` + links from the affected items).
- A new/updated test note stored according to scope:
  - feature-scoped: `../../../docs/features/<feature-slug>/plan/tests/TST-####-Short-Description.md`
  - system-wide: `../../../docs/tests/TST-####-Short-Description.md`

## Checklist
1. Allocate the next `TST-####` (use `../../../SNAPSHOT.yaml -> counters.TST`).
2. Update `../../../SNAPSHOT.yaml`:
   - choose `scope: feature|system`
   - add `items.tests.<TST-####>` with `file`, `title`, `status`, `owner`, `scope`, `kind`, `level`, `entrypoint`
   - link the test from impacted items (requirement/feature/task/issue) and link those IDs back from the test
3. Create/update the test note from `../../../docs/__templates__/test.md`:
   - Store the note based on scope:
     - `scope: feature`: under `../../../docs/features/<feature-slug>/plan/tests/`
     - `scope: system`: under `../../../docs/tests/`
   - For **manual** tests:
     - write an unambiguous procedure and expected results
     - leave `status: ready` and `evidence: []`
     - request human feedback (pass/fail + evidence)
   - For **automated** tests:
     - set `entrypoint` to the command/script (repo path) and expected artifacts
     - once run, set `status: passing|failing` and record evidence paths/log excerpts
4. Apply gating:
   - Do not mark the implementing task `done` until required tests are `passing`.
   - Do not mark an issue `fixed` until verifying tests are `passing`. `fixed` is the single terminal issue status (ADR-0008); there is no separate `closed` step.
   - Do not mark a requirement `implemented` (its terminal status) until every acceptance criterion is ticked-with-evidence or reconciled. Requirements have no `verified` status — a test note's own `passing` status is the verification record.
