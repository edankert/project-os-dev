---
type: instruction
id: INSTR-SYNCING
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-07-17
tags: [instructions, sync]
---

# Syncing project-os template updates

Use this when the project-os template lives outside the dev repo and you want to pull updates safely.

## Who owns which path

`../sync/MANIFEST.yaml` says, per path, whether the template owns a file or the project does. It is the only place that list lives, and the sync script reads it; a list repeated here is one the next path change forgets to update, which is how `.github/workflows/validate-docs.yml` stayed `seed` and stopped carrying validator changes downstream (TASK-0072).

Two ownership choices need the reason kept with them, because the path alone does not explain them:

`docs/changes/` is project-owned on purpose. Upstream change notes describe the evolution of project-os itself; downstream ones describe the downstream project after init. Keeping the histories separate is the point, unless a downstream project deliberately imports upstream history for audit.

`docs/reference/` and the other non-lifecycle docs areas are project-owned on purpose. Upstream seeds a starter README, and after that the downstream project uses the area for source, evidence, registry, background, research and publication material. A sync must not overwrite any of it.

## How sync decides what to touch (manifest + baseline)

Ownership is declared per path in `../sync/MANIFEST.yaml` (`template` / `merge` / `seed` / `project` / `generated`; the upstream template's copy is authoritative, most specific path wins). `tools/scripts/sync-project-os.sh` wraps `sync-project-os.py`, which compares each template-owned file against the **baseline** — the upstream commit recorded in `.project-os-sync` at the previous sync:

- target equals the new template version → up to date.
- target equals the baseline version → clean fast-forward, overwritten.
- target differs from both → **locally modified**: skipped and reported for hand-merge (`--force` overrides; `merge`-owned paths like `docs/PHASES.md`, `docs/phases/`, `docs/__templates__/SCHEMAS.md` are expected to diverge in repos that keep real content there and are only ever reported).

On the first manifest-based sync no baseline exists, so every locally different file reports as diverged; pass `--baseline <sha>` (the template commit the repo last synced from) to resolve fast-forwards mechanically. After a non-dry run the upstream HEAD is recorded as the new baseline and derived adapter artifacts are regenerated automatically.

## Fleet check

`bash tools/scripts/validate-fleet.sh [fleet-root]` runs the docs validator across every SNAPSHOT-bearing repo under a root (default: this repo's parent) and prints a per-repo errors/warnings/waivers summary — use it before and after template rollouts.

## Recommended flow
1. Pull latest upstream project-os.
2. Run `tools/scripts/sync-project-os.sh <path-to-upstream>` (add `--dry-run` first; `--baseline <sha>` on the first manifest-based sync).
3. Review changes (git diff) and hand-merge anything reported as DIVERGED/MERGE.
4. Run `bash tools/scripts/validate-docs.sh`, then `tools/skills/snapshot-sync/SKILL.md` for anything it reports.
5. Re-run `bash tools/scripts/install-git-hooks.sh` (hook scripts may have changed) and `python3 tools/scripts/generate-adapters.py --install-hooks` (regenerates `.claude/skills/`, `.claude/agents/`, `.cursor/rules/` and installs/merges the Claude Code hook set — replaces the old manual `hooks.json` copy step).
6. After large syncs, run `tools/skills/docs-audit/SKILL.md` — template sync is a known source of stale cross-document references.
