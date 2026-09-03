---
type: skill
id: SKILL-TEST-AUTHORING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-03
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
- A new/updated test note, stored per `../../instructions/LIFECYCLE.md` "Test storage".

## What is being authored
A `TST-*` note is the record of verification: the procedure, the verdict, and the adequacy evidence a reader can re-run. The scratch checks written on the way to that verdict, a one-off script, a grep, a mutated copy of the code, are not kept; record what they showed in `adequacy:` and delete them. Committed code tests follow the repo's existing convention for that kind of change, sit beside the tests they resemble, and are sized to the behaviours the task states, roughly one focused test per behaviour. Reason: the verification gate rewards linking more `TST-*` notes, and nothing else says where the limit is.

## Checklist
1. Allocate the next `TST-####` (use `../../../SNAPSHOT.yaml -> counters.TST`).
2. Update `../../../SNAPSHOT.yaml`:
   - choose `scope: feature|system`
   - add `items.tests.<TST-####>` with `file`, `title`, `status`, `owner`, `scope`, `level`, `entrypoint`
   - link the test from impacted items (requirement/feature/task/issue) and link those IDs back from the test
3. Create/update the test note from `../../../docs/__templates__/test.md`:
   - Store the note per `../../instructions/LIFECYCLE.md` "Test storage".
   - For **manual** tests:
     - write an unambiguous procedure and expected results
     - leave `status: ready` (defined, not yet run; `../../instructions/STATUSES.md` `[[test]]`) and `evidence: []`
     - request human feedback (pass/fail + evidence)
   - For a test with a **`command:`**:
     - set `command:` and `entrypoint` (repo path) and the expected artifacts
     - leave `status: active` and record no verdict; CI is the verdict (`../../instructions/STATUSES.md` `[[test]]`, ADR-0025), and `python3 tools/scripts/run-tests.py --filter TST-####` reproduces the run without writing
4. Apply the gates in `../../instructions/STATUSES.md`, "The contract at a glance": a task, issue or feature does not reach its terminal status until the tests it links are `passing`, and a requirement is never test-gated.
