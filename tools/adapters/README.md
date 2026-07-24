---
type: reference
id: TOOLS-ADAPTERS-README
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-05-05
tags: [tools, adapters]
---

# Tool adapters

Adapters map project-os rules to a target LLM tool's native instruction format.

This template currently ships only the Codex adapter. Add other tool adapters only when they are intentionally supported by the template.

## Directory structure

```text
tools/adapters/
├── README.md
└── codex/
    └── ADAPTER.md
```

## Codex support

Codex reads repository instructions from `AGENTS.md`. The Codex adapter documents how `AGENTS.md`, `LLM_BRIEF.md`, and `tools/agents/*.sh` map onto the shared project-os lifecycle rules.

Use `tools/skills/adapter-sync/SKILL.md` after changing project-os instructions or skills so Codex-facing guidance stays aligned.
