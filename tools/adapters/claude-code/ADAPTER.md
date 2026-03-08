---
type: adapter
tool: claude-code
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
---

# Claude Code Adapter

## Overview

Claude Code reads project instructions from `CLAUDE.md` in the repo root. It supports `@file` imports to include content from other files, making it well-suited for the project-os instruction model.

## Native instruction format

- **File**: `CLAUDE.md` (repo root)
- **Syntax**: Markdown with `@path/to/file.md` import directives
- **Overflow**: Additional rules in `.claude/rules/*.md` (auto-loaded, no import needed)
- **Limit**: Keep `CLAUDE.md` concise; Claude Code reads it at every session start

## Import strategy

The `CLAUDE.md` file should import project-os instruction files using `@` imports. This keeps rules maintained in one place (`tools/instructions/`) while delivered natively to Claude Code.

### Reference CLAUDE.md

```markdown
# Project: <project-name>

Read SNAPSHOT.yaml at session start to understand current project state and focus.
Read CONTEXT.md for the full project-os contract, edit policy, and invariants.

## project-os documentation system (core rules -- always active)

@tools/instructions/LIFECYCLE.md
@tools/instructions/STATUSES.md
@tools/instructions/QUALITY.md

## Reference instructions (read when relevant)

These files contain detailed rules. Read them when performing the related operation:
- Snapshot structure and update rules: tools/instructions/SNAPSHOT.md
- Allowed taxonomy values: tools/instructions/TAXONOMY.md
- Required link graphs: tools/instructions/TRACEABILITY.md
- ADR conventions: tools/instructions/DECISIONS.md
- Ownership rules: tools/instructions/OWNERSHIP.md
- Obsidian conventions: tools/instructions/OBSIDIAN.md
- Handoff/recovery: tools/instructions/HANDOFF.md
- Importing from existing projects: tools/instructions/IMPORTING.md
- Syncing template updates: tools/instructions/SYNCING.md
- Hook contracts: tools/instructions/HOOKS.md

## Skill playbooks (read before performing these operations)

- Issue intake: tools/skills/issue-intake/SKILL.md
- Feature scaffold: tools/skills/feature-scaffold/SKILL.md
- Task breakdown: tools/skills/task-breakdown/SKILL.md
- Close-out: tools/skills/close-out/SKILL.md
- Change note: tools/skills/change-note/SKILL.md
- Status transition: tools/skills/status-transition/SKILL.md
- Snapshot sync: tools/skills/snapshot-sync/SKILL.md
- Test authoring: tools/skills/test-authoring/SKILL.md
- ADR authoring: tools/skills/adr-authoring/SKILL.md
- Risk scan: tools/skills/risk-scan/SKILL.md
- Ad-hoc intake: tools/skills/ad-hoc-intake/SKILL.md
- Workflow authoring: tools/skills/workflow-authoring/SKILL.md
- Backlog grooming: tools/skills/backlog-grooming/SKILL.md
- Risk mitigation: tools/skills/risk-mitigation-planning/SKILL.md
- Impact analysis: tools/skills/impact-analysis/SKILL.md
- Adapter sync: tools/skills/adapter-sync/SKILL.md
- Project init: tools/skills/project-init/SKILL.md
- Project derive: tools/skills/project-derive/SKILL.md
```

### Notes

- The `@` imports inline the content of each file into Claude Code's context when the CLAUDE.md is loaded
- Core rules (LIFECYCLE, STATUSES, QUALITY) are always imported because they govern every interaction
- Reference instructions are listed as paths (not imported) to keep context window lean — Claude Code reads them on demand
- Skill playbooks are listed as paths for the same reason

## Hook support

Claude Code supports shell hooks via project-level settings files. project-os hooks should be installed in the **project repo** (not `~/.claude/`) because they reference project-specific files (SNAPSHOT.yaml, note frontmatter).

### Where to install

| File | Committed | Scope | Use when |
|---|---|---|---|
| `.claude/settings.json` | Yes (shared) | Everyone who clones | **Default** — hooks enforce shared project rules |
| `.claude/settings.local.json` | No (gitignored) | Just you | Personal testing before committing |

**Use `.claude/settings.json`** (committed) as the default. project-os hooks enforce project rules (document-first, verification gating), so all team members should get them automatically.

### Installation

Create `.claude/settings.json` in the project root with the hooks configuration from `hooks.json` in this adapter directory:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "bash tools/adapters/claude-code/hooks/document-first-gate.sh"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "bash tools/adapters/claude-code/hooks/verification-gate.sh"
      },
      {
        "matcher": "Write|Edit",
        "command": "bash tools/adapters/claude-code/hooks/phase-alignment.sh"
      },
      {
        "matcher": "Write|Edit",
        "command": "bash tools/adapters/claude-code/hooks/risk-scan-trigger.sh"
      }
    ],
    "SessionStart": [
      {
        "command": "bash tools/adapters/claude-code/hooks/snapshot-freshness.sh"
      }
    ]
  }
}
```

Ensure hook scripts are executable: `chmod +x tools/adapters/claude-code/hooks/*.sh`

### Hook events

- `PreToolUse`: runs before a tool is executed (can block with exit code 2)
- `PostToolUse`: runs after a tool completes (advisory only)
- `SessionStart`: runs when a session begins (advisory only)

See `tools/instructions/HOOKS.md` for the full hook contract specifications and `hooks/` in this directory for the implementations.

## Project-specific customization

After copying the reference CLAUDE.md, projects should add:
1. A "Role of this repo" section describing the project
2. Any project-specific rules not covered by project-os instructions
3. References to project-specific skills or workflows
