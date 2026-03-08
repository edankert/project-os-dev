---
type: skill
id: SKILL-ADAPTER-SYNC
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
tags: [skills, adapters]
---

# Skill: Adapter sync

## When to use
- After updating instruction files in `tools/instructions/`
- After updating skill files in `tools/skills/`
- After syncing the project-os template upstream
- When setting up a new adapter for a tool

## Inputs
- Target adapter (claude-code, codex, cursor, or all)
- Updated instruction/skill files

## Outputs
- Regenerated tool-specific instruction files (CLAUDE.md, AGENTS.md, .cursor/rules/)
- Updated hook configurations if applicable

## Checklist

### For Claude Code adapter
1. Read `tools/adapters/claude-code/ADAPTER.md` for the reference CLAUDE.md structure.
2. Update or regenerate the project root `CLAUDE.md`:
   - Ensure all `@` imports reference the correct instruction file paths
   - Ensure all skill playbook paths are listed
   - Preserve any project-specific sections (role description, custom rules)
3. Install hooks:
   - If `.claude/settings.json` does not exist: create it with the hooks configuration from `tools/adapters/claude-code/ADAPTER.md`
   - If `.claude/settings.json` exists: merge the `hooks` key from the adapter (preserve any existing non-hook settings)
   - Verify all hook scripts in `tools/adapters/claude-code/hooks/` are executable (`chmod +x`)
   - Verify hook scripts reference correct paths to SNAPSHOT.yaml and docs/

### For Codex adapter
1. Read `tools/adapters/codex/ADAPTER.md` for the AGENTS.md structure.
2. Regenerate `AGENTS.md` in the project root:
   - Inline core rules (LIFECYCLE, STATUSES, QUALITY) — Codex does not support imports
   - Condense reference instructions into summary sections
   - List skill playbook paths for on-demand reading
3. Preserve any project-specific sections.

### For Cursor adapter
1. Read `tools/adapters/cursor/ADAPTER.md` for the .mdc structure.
2. Regenerate `.cursor/rules/*.mdc` files:
   - Map each instruction file to a scoped rule file per the mapping table
   - Set appropriate glob scopes for each rule
   - Inline the instruction content
3. Remove any orphaned .mdc files no longer mapped to instructions.

### Post-sync
1. Verify the regenerated files are consistent with current instruction content.
2. If instruction content has changed materially, note the update in a `CHG-*` change note.
