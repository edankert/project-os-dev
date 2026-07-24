# Plan: Phases as First-Class Note Type

## Approach
Define the phase note type (template + schema), create dashboards, then update all existing templates and instructions to use link-based phase references.

## Dependency
FEAT-0007 (relationship model) should land first — the `phase` field becomes a link that uses the same `contains`-based Bases filtering pattern.

## Sequence
1. **TASK-0030**: Create phase template and add to SCHEMAS.md
2. **TASK-0031**: Create Phases.base top-level dashboard
3. **TASK-0032**: Create phase-overview.base contextual dashboard template
4. **TASK-0033**: Migrate phase field from integer to link across all templates
5. **TASK-0034**: Update LIFECYCLE.md, SNAPSHOT.md, and phase alignment rules
6. **TASK-0035**: Update skills to create/reference phase notes

## Notes
- Tasks 1-3 are additive (new files, no breaking changes)
- Tasks 4-5 are schema changes (breaking — requires downstream migration)
- Task 6 updates agent behavior
- The old `docs/PHASES.md` registry is replaced by `docs/phases/PHASE-###-*.md` notes
