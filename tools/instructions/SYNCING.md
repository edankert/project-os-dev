---
type: instruction
id: INSTR-SYNCING
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
tags: [instructions, sync]
---

# Syncing project-os template updates

Use this when the project-os template lives outside the dev repo and you want to pull updates safely.

## Template-owned (safe to sync)
- `tools/instructions/`
- `tools/skills/`
- `docs/__templates__/`
- `docs/__bases__/`
- `docs/README.md`
- `docs/INDEX.md`
- `CONTEXT.md`
- Optional: `SECURITY.md`, `ROADMAP.md`

## Project-owned (do NOT overwrite)
- `SNAPSHOT.yaml`
- `docs/features/`
- `docs/issues/`
- `docs/requirements/`
- `docs/tests/`
- `docs/changes/`
- `docs/decisions/`
- `docs/workflows/` (except template updates you explicitly choose to merge)

## Recommended flow
1. Pull latest upstream project-os.
2. Run `tools/scripts/sync-project-os.sh <path-to-upstream>`.
3. Review changes (git diff).
4. Run `tools/skills/snapshot-sync/SKILL.md`.
