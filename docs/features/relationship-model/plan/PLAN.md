# Plan: Named Relationship Fields

## Approach
Schema-first: update the definitions (SCHEMAS.md, TRACEABILITY.md), then the templates, then the dashboards and skills. This ensures all artifacts stay consistent.

## Sequence
1. **TASK-0023**: Update SCHEMAS.md — define the new fields, deprecate old ones
2. **TASK-0024**: Update note templates (task, issue, requirement, test, feature)
3. **TASK-0025**: Update TRACEABILITY.md link rules
4. ~~**TASK-0026**: Update feature-overview.base template~~ — cancelled, superseded by FEAT-0009 (Cockpit Layout)
5. **TASK-0027**: Update top-level .base dashboards
6. **TASK-0028**: Update skills (feature-scaffold, issue-intake, task-breakdown, test-authoring)
7. **TASK-0029**: Update SNAPSHOT.md schema and migrate existing snapshot entries

## Notes
- Tasks 1-3 are schema/docs changes (no code)
- Task 5 is a dashboard change
- Task 6 updates agent behavior
- Task 7 updates the snapshot contract
- All changes are in the project-os template repo, then synced to downstream repos
- Per-feature Overview.base files are no longer needed — replaced by CONTEXT.base (FEAT-0009)
