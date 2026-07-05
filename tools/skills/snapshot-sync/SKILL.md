---
type: skill
id: SKILL-SNAPSHOT-SYNC
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, snapshot]
---

# Skill: Snapshot sync

## When to use
- After any work that changes statuses/relationships.
- When you suspect drift between `../../../SNAPSHOT.yaml` and the notes.

## Inputs
- `../../../SNAPSHOT.yaml`
- The affected notes under `../../../docs/`

## Outputs
- A consistent snapshot and notes (IDs, statuses, relationships aligned).

## Checklist
1. Run `bash tools/scripts/validate-docs.sh` first — it mechanically checks file existence, id/status/type agreement, counters, link resolution, and the verification invariant, so you only spend judgment on what it cannot decide. Then validate the remaining `../../../SNAPSHOT.yaml` invariants (see `../../instructions/SNAPSHOT.md`).
2. For each item in the snapshot:
   - ensure `items.<type>.<ID>.file` exists on disk
   - ensure note frontmatter `id` matches `<ID>`
   - ensure note frontmatter `status` matches snapshot `status`
   - ensure note frontmatter `type` matches the expected type for its collection
3. Check relationship consistency:
   - phase `features`/`requirements`/`tasks`/`issues` ↔ item `phase`
   - task `parent` ↔ feature/issue `tasks`
   - issue ↔ feature links
   - feature ↔ requirement links
   - test ↔ requirement/feature/issue/task links
   - risk ↔ mitigation task links
4. Check verification status consistency:
   - task `done` requires linked tests to be `passing`
   - issue `closed` requires linked tests to be `passing`
   - requirement `verified` requires linked tests to be `passing`
   - feature `done` requires required tasks and tests to be complete
5. Detect orphaned notes:
   - scan `../../../docs/phases/`, `../../../docs/features/`, `../../../docs/issues/`, `../../../docs/requirements/`, `../../../docs/risks/`, and `../../../docs/tests/`
   - flag notes with valid `id` frontmatter that are not represented in the snapshot and are not intentionally archived
6. Apply retention policy:
   - remove snapshot entries that policy excludes from active state
   - preserve note files as the archive
   - keep recent changes within `recent_changes_max`
7. If `claimed_by` exists, ensure it is intentional and not stale (update or clear).
8. Update `metrics` counts in the snapshot after reconciliation and pruning.
