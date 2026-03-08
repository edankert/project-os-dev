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
1. Validate `../../../SNAPSHOT.yaml` invariants (see `../../instructions/SNAPSHOT.md`).
2. For each item in the snapshot:
   - ensure `items.<type>.<ID>.file` exists on disk (flag missing files)
   - ensure note frontmatter `id` matches `<ID>` (flag mismatches)
   - ensure note frontmatter `status` matches snapshot `status` (flag mismatches)
   - ensure note frontmatter `type` matches the expected type for its collection (flag mismatches)
3. **Bi-directional link consistency (check each pair explicitly):**
   - For each task: does `parent` point to a feature or issue? Does that parent's `tasks` list include this task ID? Flag any missing back-links.
   - For each feature: does each ID in `tasks` have `parent` pointing back to this feature? Flag any orphaned task references.
   - For each feature: does each ID in `requirements` have this feature in its `implements`/`features` list? Flag mismatches.
   - For each issue: does each ID in `features` have this issue in its `issues` list? Flag mismatches.
   - For each test: does each ID in `requirements` have this test in its `tests` list? Flag mismatches.
   - For each risk: do referenced `mitigation_tasks` exist and link back? Flag broken links.
4. **Verification status consistency:**
   - For each task with `status: done`: check all linked `TST-*` IDs. If any test is not `status: passing`, flag the inconsistency.
   - For each issue with `status: closed`: same check against linked tests.
   - For each requirement with `status: verified`: same check against linked tests.
5. **Test staleness detection:**
   - For each `TST-*` with `status: passing` and a non-empty `last_run`:
     - Find all features linked to this test (via `features` field or via `requirements` → feature back-links).
     - For each linked feature, find the latest `updated` date among its tasks.
     - If the latest task update is after `last_run`: flag the test as **stale** — it passed for a previous version but the linked feature has changed since.
   - Report stale tests: "TST-XXXX is stale — FEAT-YYYY changed on DATE, test last run on DATE."
   - Do not automatically change test statuses; staleness is advisory. Use the `release-verification` skill to formally gate a release.
6. **Orphan detection:**
   - Scan `../../../docs/features/`, `../../../docs/issues/`, `../../../docs/requirements/`, `../../../docs/risks/`, `../../../docs/tests/` for notes with valid frontmatter `id` that are NOT present in the snapshot.
   - Flag orphaned notes: these may need to be added to the snapshot or archived.
7. **Retention enforcement:**
   - Read `retention` settings from the snapshot.
   - If `keep_done_tasks_in_snapshot: false`: remove all tasks with `status: done` from `items.tasks`. (The task notes under `docs/` are preserved as the archive.)
   - If `keep_done_features_in_snapshot: false`: remove all features with `status: done` from `items.features` — but only if ALL their tasks are also `done` or already pruned.
   - If `keep_closed_issues_in_snapshot: false`: remove all issues with `status: closed` from `items.issues`.
   - Keep risks with `status: closed` for one cycle (remove on next sync after they were closed).
   - Keep recent changes per `recent_changes_max` — remove oldest entries beyond the limit from `items.changes`.
   - Report: "Pruned N items from snapshot (retention policy). Notes preserved."
8. Update `metrics` counts in the snapshot (after pruning).
