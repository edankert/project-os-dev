---
type: reference
id: TOOLS-AGENTS-README
status: active
owner: team:docs
created: 2026-01-27
updated: 2026-01-27
tags: [tools, agents]
---

# `tools/agents/`

Reserved for agent-facing collateral (e.g., contributor/LLM operational notes, automation adapters, or future agent configuration).

## What goes here
- Agent-specific guidance that is not part of the documentation system structure itself.
- Lightweight helper files used by automation/agents (if introduced).

Current helpers:
- `bootstrap.sh`: quick repository/context/status preflight.
- `start-change.sh`: scaffold a `docs/changes/CHG-*.md` note with all required documentation-type coverage fields.
- `check-docs-first.sh`: enforce docs-first gating for code changes.

## What does not go here
- Project documentation content (belongs under `../../docs/`).
- Normative documentation conventions (belong under `../instructions/`).
