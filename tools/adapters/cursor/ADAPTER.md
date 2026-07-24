---
type: adapter
tool: cursor
status: draft
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
---

# Cursor Adapter (Stub)

## Overview

Cursor reads project instructions from `.cursor/rules/*.mdc` files. Each rule file can be scoped to specific file globs, making it possible to deliver context-sensitive instructions.

## Native instruction format

- **Directory**: `.cursor/rules/`
- **Extension**: `.mdc` (Markdown with YAML frontmatter)
- **Scoping**: Each rule file has a `globs` field that controls when it's loaded
- **Loading**: Rules are loaded automatically when matching files are edited

## Import strategy

Map project-os instructions to scoped rule files:

| project-os instruction | Cursor rule file | Glob scope |
|---|---|---|
| LIFECYCLE.md | `.cursor/rules/lifecycle.mdc` | `**/*` (always active) |
| STATUSES.md | `.cursor/rules/statuses.mdc` | `**/*` |
| QUALITY.md | `.cursor/rules/quality.mdc` | `**/*` |
| SNAPSHOT.md | `.cursor/rules/snapshot.mdc` | `SNAPSHOT.yaml` |
| TRACEABILITY.md | `.cursor/rules/traceability.mdc` | `docs/**/*.md` |
| OBSIDIAN.md | `.cursor/rules/obsidian.mdc` | `docs/**/*.md` |

### Generating .cursor/rules/

Use the `adapter-sync` skill (`tools/skills/adapter-sync/SKILL.md`) to regenerate rule files from project-os instructions:

```
"Run tools/skills/adapter-sync/SKILL.md for the cursor adapter"
```

### .mdc format

Each rule file follows this structure:

```markdown
---
description: Brief description of when this rule applies
globs: ["**/*"]
---

# Rule content here (copied/adapted from project-os instruction)
```

## Hook support

Cursor does not currently support shell hooks. Enforcement relies on instruction-based rules only.

## Limitations

- No shell hook support — enforcement is prescriptive only
- Rules must be regenerated when project-os instructions change
- No `@file` import mechanism — content must be inlined per rule file
