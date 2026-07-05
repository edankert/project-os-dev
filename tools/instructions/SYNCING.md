---
type: instruction
id: INSTR-SYNCING
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-05-08
tags: [instructions, sync]
---

# Syncing project-os template updates

Use this when the project-os template lives outside the dev repo and you want to pull updates safely.

## Template-owned (safe to sync)
- `tools/instructions/`
- `tools/skills/`
- `tools/agents/`
- `tools/adapters/`
- `tools/cockpit/`
- `tools/scripts/`
- `docs/__templates__/`
- `docs/__bases__/`
- `docs/phases/`
- `docs/README.md`
- `docs/INDEX.md`
- `docs/PHASES.md`
- `CONTEXT.md`
- `AGENTS.md`
- `LLM_BRIEF.md`
- Optional: `SECURITY.md`, `ROADMAP.md`
- Optional seed only: `docs/reference/README.md` when the downstream file does not already exist
- Optional seed only: `.github/workflows/validate-docs.yml` when the downstream file does not already exist (downstream repos own their CI config; the seed just wires up the docs validator)

## Project-owned (do NOT overwrite)
- `SNAPSHOT.yaml`
- `docs/features/`
- `docs/issues/`
- `docs/requirements/`
- `docs/tests/`
- `docs/changes/`
- `docs/decisions/`
- `docs/workflows/` (except template updates you explicitly choose to merge)
- `docs/reference/`
- `docs/research/`
- Other project-specific docs subdirectories
- Runtime artifacts produced by `tools/cockpit/run.sh`, such as `tools/cockpit/.venv/`

`docs/changes/` is intentionally project-owned: upstream template change notes describe the evolution of project-os itself, while downstream change notes describe the downstream project after init. Keep those histories separate unless a downstream project deliberately imports upstream template history for audit purposes.

`docs/reference/` and other non-lifecycle docs areas are intentionally project-owned: upstream may provide a starter README, but downstream projects use these areas for source, evidence, registry, background, research, and publication material. Template sync must not overwrite them.

## Recommended flow
1. Pull latest upstream project-os.
2. Run `tools/scripts/sync-project-os.sh <path-to-upstream>`.
3. Review changes (git diff).
4. Run `bash tools/scripts/validate-docs.sh`, then `tools/skills/snapshot-sync/SKILL.md` for anything it reports.
5. Re-run `bash tools/scripts/install-git-hooks.sh` (hook scripts may have changed) and, for Claude Code, re-copy `tools/adapters/claude-code/hooks.json` into `.claude/settings.json` if it changed.
6. After large syncs, run `tools/skills/docs-audit/SKILL.md` — template sync is a known source of stale cross-document references.
