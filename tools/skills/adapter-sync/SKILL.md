---
type: skill
id: SKILL-ADAPTER-SYNC
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-07-17
tags: [skills, adapters]
---

# Skill: Adapter sync

## When to use
- After updating instruction files in `../../../tools/instructions/`.
- After updating skill files in `../../../tools/skills/`.
- After syncing the project-os template upstream.
- When refreshing any tool-facing startup or enforcement guidance (Claude Code, Codex, Cursor, generic).

## Inputs
- Updated instruction/skill files.
- Adapter docs under `../../../tools/adapters/` (claude-code, codex, cursor, generic).
- Root tool-facing files: `../../../CLAUDE.md`, `../../../AGENTS.md`, `../../../LLM_BRIEF.md`, `../../../CONTEXT.md`.

## Outputs
- Regenerated native artifacts: `.claude/skills/`, `.claude/agents/`, `.cursor/rules/` (via the generator; never hand-edited).
- `AGENTS.md` / `LLM_BRIEF.md` aligned with current lifecycle, docs-first, and close-out rules.
- Adapter docs updated if enforcement contracts (`../../instructions/HOOKS.md`, HC-*) or helper scripts changed.

## Checklist
1. **Regenerate derived artifacts:** run `python3 tools/scripts/generate-adapters.py --install-hooks` from the repo root. This rewrites `.claude/skills/<name>/SKILL.md`, `.claude/agents/independent-reviewer.md`, and `.cursor/rules/*.mdc` from the canonical sources and installs/merges the Claude Code hook set. Verify with `--check`.
2. Review changed files under `../../../tools/instructions/` and `../../../tools/skills/` for contract changes the generator cannot derive (startup order, docs-first rules, verification gates, close-out expectations).
3. Update `../../../AGENTS.md` if any of those changed (it is the generic/Codex startup contract).
4. Update `../../../LLM_BRIEF.md` if important paths, commands, or invariants changed.
5. Update `../../../tools/instructions/HOOKS.md` if hook contracts (HC-*) changed, and keep `../../adapters/claude-code/ADAPTER.md`'s hook table consistent with it.
6. Preserve project-specific sections in downstream repositories when regenerating root files; generated `.claude/`/`.cursor/` artifacts carry a do-not-edit header and may be overwritten freely.
7. Confirm `CLAUDE.md`'s instruction imports and skill index still match `tools/instructions/` and `tools/skills/` contents.
