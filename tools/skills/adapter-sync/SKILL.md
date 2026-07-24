---
type: skill
id: SKILL-ADAPTER-SYNC
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-05-05
tags: [skills, adapters, codex]
---

# Skill: Adapter sync

## When to use
- After updating instruction files in `../../../tools/instructions/`.
- After updating skill files in `../../../tools/skills/`.
- After syncing the project-os template upstream.
- When refreshing Codex-facing startup or enforcement guidance.

## Inputs
- Updated instruction/skill files.
- Codex adapter docs: `../../../tools/adapters/codex/ADAPTER.md`.
- Root Codex-facing files: `../../../AGENTS.md` and `../../../LLM_BRIEF.md`.

## Outputs
- `../../../AGENTS.md` aligned with current project-os lifecycle and docs-first rules.
- `../../../LLM_BRIEF.md` aligned with current command/path expectations.
- Adapter docs updated if enforcement contracts or helper scripts changed.

## Checklist
1. Read `../../../tools/adapters/codex/ADAPTER.md`.
2. Review changed files under `../../../tools/instructions/` and `../../../tools/skills/`.
3. Update `../../../AGENTS.md` if startup order, docs-first rules, snapshot rules, phase handling, verification gates, or close-out expectations changed.
4. Update `../../../LLM_BRIEF.md` if important paths, commands, or invariants changed.
5. Update `../../../tools/instructions/HOOKS.md` if Codex hook-equivalent contracts changed.
6. Preserve project-specific sections in downstream repositories when regenerating these files.
7. Do not add unsupported tool adapters as part of Codex adapter sync.
