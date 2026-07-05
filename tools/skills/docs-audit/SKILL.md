---
type: skill
id: SKILL-DOCS-AUDIT
status: active
owner: group:maintainers
created: 2026-07-05
updated: 2026-07-05
tags: [skills, audit, consistency]
---

# Skill: Docs audit (cross-document consistency, to quiescence)

## Why this exists
Documentation-as-database systems accumulate cross-document defects — stale references, schema mismatches between notes, statuses that drifted apart — and single-file review cannot detect them *by construction*: each file looks fine on its own. Empirically, systems of this class needed multiple full-scope audit rounds before converging. This skill is the periodic full-graph sweep that catches what per-edit checks miss.

## When to use
- On a cadence: during backlog grooming, before a release (`../release-prep/SKILL.md`), and after any large import/merge/sync.
- After running `../../scripts/sync-project-os.sh` (template sync can orphan references).
- When `tools/scripts/validate-docs.sh` passes but behavior suggests the docs are lying (the validator checks structure, not meaning).

## Inputs
- `../../../SNAPSHOT.yaml` and the full note graph under `../../../docs/`.
- `tools/scripts/validate-docs.sh` output (run it first — never spend LLM effort on what the validator catches mechanically).

## Outputs
- Fixed notes/snapshot entries for every confirmed inconsistency.
- `ISS-*` notes (status `triage`) for inconsistencies that need human judgment to resolve.
- An audit record: a short `CHG-*` note when the audit changed anything, stating rounds run and defect counts per round.

## Audit dimensions (each pass covers all of these)
1. **Mechanical baseline**: `bash tools/scripts/validate-docs.sh` must pass before and after the audit.
2. **Stale references**: prose (not just frontmatter) mentioning files, paths, IDs, commands, or flags that no longer exist. This is empirically the largest defect class in systems like this.
3. **Cross-note contradiction**: two notes describing the same behavior differently (e.g. a `CHG-*` says a path moved, a `WF-*` still documents the old path; a feature note claims a capability its open `ISS-*` says is broken).
4. **Schema/contract mismatch**: notes that reference each other's fields or artifacts inconsistently (a `TST-*` entrypoint that doesn't match the workflow it verifies; a `REQ-*` acceptance criterion no linked test actually checks).
5. **Status semantics**: items whose status is technically allowed but semantically wrong (a `monitoring` risk whose trigger condition disappeared; a `passing` test whose entrypoint no longer exists).
6. **Instruction/template drift** (template repos): instruction files, templates, and `SCHEMAS.md` describing different shapes for the same note type.

## Checklist
1. Run the mechanical validator; fix anything it reports first.
2. Sweep the full graph across all six dimensions above. Audit **cross-file**, not file-by-file: for each item, follow its links outward and check that both ends agree.
3. Fix what is unambiguous; file `ISS-*` for what is not.
4. Repeat from step 1. **Quiescence rule: the audit is complete only after two consecutive full passes find zero new defects.** One clean pass is not convergence — fixes in round N routinely create or expose defects visible only in round N+1.
5. Record the audit in a `CHG-*` note if anything changed (rounds run, defects found/fixed per round).

## Independence recommendation
Run the audit with a different model than the one maintaining the docs (see `../independent-review/SKILL.md` for why). The maintainer model normalized its own drift into the graph; a fresh model family reads the notes as they are, not as they were intended.
