# Plan: Obsidian Cockpit Layout

## Approach
Create the two global bases (NAV.base, CONTEXT.base), clean up the now-unnecessary per-feature overview artifacts, then document the workspace setup.

## Dependencies
- FEAT-0007 (relationship model) must land first — CONTEXT.base filters on the new named fields
- FEAT-0008 (phase notes) for phases to appear in NAV.base

## Sequence
1. **TASK-0036**: Create NAV.base
2. **TASK-0037**: Create CONTEXT.base
3. **TASK-0038**: Remove feature-overview.base template and per-feature Overview.base generation from skills
4. **TASK-0039**: Update DASHBOARD.md hub note
5. **TASK-0040**: Document workspace setup in OBSIDIAN.md

## Notes
- Tasks 1-2 can be done in parallel
- Task 3 cleans up artifacts made obsolete by the cockpit design
- Task 5 should include screenshots or step-by-step instructions for pinning bases to sidebars
