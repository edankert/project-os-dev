# LLM Brief

## Project Identity
- Name: REPLACE ME
- Purpose: REPLACE ME
- Canonical runtime state: `SNAPSHOT.yaml`

## Read Order
1. `CONTEXT.md`
2. `docs/INDEX.md`
3. `SNAPSHOT.yaml`
4. `docs/ARCHITECTURE.md`
5. `docs/workflows/`

## High-Value Paths
- Core implementation entrypoints: REPLACE ME
- Operational tooling: `tools/`
- Optional non-lifecycle reference/source material: `docs/reference/`
- Codex adapter: `tools/adapters/codex/ADAPTER.md`
- Optional docs cockpit: `tools/cockpit/run.sh docs --bind 127.0.0.1 --port 8765`
- Documentation templates: `docs/__templates__/`

## Invariants
- `SNAPSHOT.yaml` is canonical for active work state.
- Keep traceability links coherent between features, tasks, issues, tests, workflows, and changes.
- Prefer repo-relative paths in docs and logs.
- Do not introduce secrets or proprietary binaries.

## Typical Commands
- Bootstrap context: `bash tools/agents/bootstrap.sh`
- Start docs-first intake: `bash tools/agents/start-change.sh "<short title>"`
- Validate docs-first gate: `bash tools/agents/check-docs-first.sh`
- Validate docs invariants (snapshot/notes/links/verification): `bash tools/scripts/validate-docs.sh`
- Browse docs cockpit: `bash tools/cockpit/run.sh docs --bind 127.0.0.1 --port 8765`
- Sync Codex adapter guidance: read `tools/skills/adapter-sync/SKILL.md`

## External Dependencies (Common)
- Define project-specific dependencies during project init.

## Fast Failure Checks
- Run `bash tools/agents/bootstrap.sh` and inspect alerts.
- Confirm required paths exist before running project workflows.
- Keep `SNAPSHOT.yaml` and notes aligned after every functional change.
