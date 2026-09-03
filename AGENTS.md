# Agent Startup Contract

This repository is project-os enabled. Follow this startup sequence before doing any work.

## Mandatory First Steps
1. Read `CONTEXT.md`.
2. Read `docs/INDEX.md`.
3. Read `SNAPSHOT.yaml`.
4. Run `bash tools/agents/bootstrap.sh`.
5. Follow `tools/instructions/MARKDOWN.md`: do not hard-wrap Markdown prose to a fixed column width.
6. Follow `tools/instructions/WRITING.md`: write so a reader can follow it — point first, one idea per sentence, no undefined jargon.

Do not skip or reorder these steps.

## Mandatory Docs-First Gate
The rule is stated once in `tools/instructions/LIFECYCLE.md`: preflight before code (a task or issue in `SNAPSHOT.yaml` focus), and a change note at close-out when behaviour, paths or contracts change. On the Codex and generic paths: `bash tools/agents/start-change.sh "<short title>"` scaffolds the change note when one is due, and `bash tools/agents/check-docs-first.sh` checks the documentation state after edits.

After edits, run `bash tools/agents/check-docs-first.sh` and `bash tools/scripts/validate-docs.sh`, and fix what they report; the validator also runs at pre-commit and in CI (`tools/instructions/QUALITY.md`, "Documentation Fidelity").

Every documentation type is considered on a behaviour or path change; the list is the "Documentation Coverage" checklist in `docs/__templates__/change.md`.

## Canonical State
- `SNAPSHOT.yaml` is the canonical current-work state; its statuses, counters and metrics are derived from the notes by `tools/scripts/sync-snapshot.py` (`tools/instructions/LIFECYCLE.md`, "Mandatory Automated Documentation").
- If note files and `SNAPSHOT.yaml` disagree, the notes are authored and the snapshot is derived: run the sync script and report what it changed.

## Primary Work Entrypoints
- Replace with project-specific commands after initialization.
- Optional docs cockpit: `bash tools/cockpit/run.sh docs --bind 127.0.0.1 --port 8765`.

## Edit Boundaries
- Which paths are live documentation, reference documentation and tool instructions is stated once in `CONTEXT.md`, "Edit policy".

## Output Expectations
- Prose written for a person follows `tools/instructions/WRITING.md`: one line before starting on what you are about to do, a recap at the end that stands on its own, and evidence for every claim of progress (`tools/instructions/QUALITY.md`, "Verification expectations").
- After edits, report changed files and validation commands run.
- If blocked by missing dependencies or external repos, state exact missing path/tool.
