---
type: reference
id: TOOLS-ADAPTERS-README
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-09-16
tags: [tools, adapters]
---

# Tool adapters

Adapters map project-os rules to a target LLM tool's native instruction format and, where the tool supports it, to native enforcement (session hooks). The rules themselves stay tool-agnostic in `../instructions/` and `../skills/`; adapters only deliver them.

## Directory structure

```text
tools/adapters/
├── README.md
├── claude-code/   # CLAUDE.md @imports + blocking session hooks
├── codex/         # AGENTS.md + generated skills, agents, and native lifecycle hooks
├── cursor/        # .cursor/rules/*.mdc generated from the skill playbooks
└── generic/       # CONTEXT.md single-file fallback for any other tool
```

## Enforcement coverage

All tools share the same mechanical backstop, the outer two of the three enforcement layers in `../instructions/QUALITY.md` "Documentation Fidelity". What differs is in-session, real-time enforcement of the hook contracts (`../instructions/HOOKS.md`):

| Adapter | In-session enforcement | Install |
|---|---|---|
| claude-code | All eight HC-* contracts as session hooks; HC-001/HC-003 blocking | `claude-code/ADAPTER.md` (hooks into `.claude/settings.json`) |
| codex | Native HC-001..HC-008 hooks where trusted; HC-009 shared git/CI runner; limits in `codex/ADAPTER.md` | `python3 tools/scripts/generate-adapters.py --install-hooks`, then review `/hooks` |
| cursor | None (rules prose only) | Generate `.cursor/rules/` per `cursor/ADAPTER.md` |
| generic | None (prose only) | Point the tool at `CONTEXT.md` |

## Keeping adapters aligned

Run `tools/skills/adapter-sync/SKILL.md` after changing project-os instructions or skills so every adapter's generated/native artifacts stay aligned with the canonical rules.
