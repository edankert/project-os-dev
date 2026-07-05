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
- Independent review: tools/skills/independent-review/SKILL.md
- Docs audit: tools/skills/docs-audit/SKILL.md
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
- Core rules (LIFECYCLE) are always imported because it governs every interaction
- STATUSES and QUALITY are listed as reference instructions — Claude Code reads them on demand when relevant
- Reference instructions are listed as paths (not imported) to keep context window lean
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

Copy the hooks configuration from `hooks.json` in this adapter directory into `.claude/settings.json` in the project root. Or copy the file directly:

```bash
mkdir -p .claude
cp tools/adapters/claude-code/hooks.json .claude/settings.json
```

If `.claude/settings.json` already exists with other settings, merge the `hooks` key manually.

Ensure hook scripts are executable: `chmod +x tools/adapters/claude-code/hooks/*.sh`

> **Note:** Hook commands use `$CLAUDE_PROJECT_DIR` for reliable path resolution. Claude Code does not guarantee hooks run from the project root, so relative paths are unreliable.

### Hook events and types

| Event | Hooks | Type | Purpose |
|---|---|---|---|
| `PreToolUse` | HC-001 Document-First | `command` | Reads SNAPSHOT.yaml, blocks code edits without focus |
| `PreToolUse` | HC-003 Verification Gate | `command` | **Blocking**: denies status→done/closed/verified while linked TST-* notes are not `passing` (recorded `verification_waiver` escapes; no linked test → `ask`) |
| `PostToolUse` | HC-004 Phase Alignment | `command` | Detects status→doing, reminds about phase check |
| `PostToolUse` | HC-005 Risk Scan Trigger | `command` | Detects package/env/CI file changes |
| `Stop` | HC-006 Close-out Check + HC-007 Docs Validation | `command` | Runs `tools/scripts/validate-docs.sh` and blocks stop on violations; checks focus is cleared, forces close-out if not |
| `SessionStart` | HC-002 Snapshot Freshness | `command` | Reminds agent to read SNAPSHOT.yaml |

**All hooks are `command` type** (fast shell scripts, no API calls). This avoids LLM cost/latency and 529 overload errors. Stop hooks use `{decision: "block", reason: "..."}` to force continuation. All scripts use `$CLAUDE_PROJECT_DIR` for path resolution. HC-003 and HC-007 need `python3` on PATH (stdlib only); they fail open with a note if it is missing, so a broken runtime never bricks edits — but treat that note as a setup error.

Session hooks are the innermost of three enforcement layers: the same validator also runs at git pre-commit (`bash tools/scripts/install-git-hooks.sh` to install) and in CI (`.github/workflows/validate-docs.yml`). Session hooks and pre-commit can be bypassed; CI cannot — that layering is deliberate.

See `tools/instructions/HOOKS.md` for the full hook contract specifications and `hooks/` in this directory for the implementations.

## Project-specific customization

After copying the reference CLAUDE.md, projects should add:
1. A "Role of this repo" section describing the project
2. Any project-specific rules not covered by project-os instructions
3. References to project-specific skills or workflows
