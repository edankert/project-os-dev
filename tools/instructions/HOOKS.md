---
type: instruction
id: INSTR-HOOKS
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-05-05
tags: [instructions, hooks, codex]
---

# Codex hook-equivalent contracts

These contracts define the checks that a Codex workflow should perform at key points. The current template implements them with `AGENTS.md` instructions and `tools/agents/*.sh` scripts rather than a tool-specific hook runtime.

## CHC-001: Startup preflight

- Trigger: session start or before selecting work.
- Entrypoint: `bash tools/agents/bootstrap.sh`.
- Check logic:
  - Required context files exist.
  - `SNAPSHOT.yaml` can be read.
  - Current branch, head, focus, and working tree are visible.
- On failure: stop and fix missing required files before implementation.

## CHC-002: Docs-first gate

- Trigger: before functional code changes in downstream projects that enforce docs-first tracking.
- Entrypoints:
  - `bash tools/agents/start-change.sh "<short title>"`
  - `bash tools/agents/check-docs-first.sh`
- Check logic:
  - Code changes have a `docs/changes/CHG-*.md` note when required.
  - `SNAPSHOT.yaml` is updated when code changes are present.
  - Change notes have no pending documentation coverage entries.
- On failure: block close-out until documentation state is explicit.

## CHC-003: Phase alignment

- Trigger: before starting or transitioning a task to `doing`.
- Check logic:
  - Read `focus.phase` from `SNAPSHOT.yaml`.
  - Read the task or parent feature `phase`.
  - If both phases are set and the task belongs to a future phase, flag the mismatch.
- On failure: warn and require explicit user confirmation before proceeding.

## CHC-004: Verification gate

- Trigger: before marking a task `done`, issue `closed`, requirement `verified`, or feature `done`.
- Check logic:
  - Find linked `TST-*` IDs from the snapshot and note frontmatter.
  - Confirm every required test is `status: passing`.
- On failure: block the terminal status transition unless an explicit `verification_waiver: <reason>` is recorded in the note frontmatter (the waiver is a logged artifact, not a silent skip).
- Enforcement: this gate must be mechanical, not advisory. The Claude Code adapter implements it as a blocking PreToolUse hook (`../adapters/claude-code/hooks/verification-gate.py`); other adapters must run `tools/scripts/validate-docs.sh` before close-out and at pre-commit/CI, which enforces the same invariant repo-wide.

## CHC-005: Close-out check

- Trigger: before final response after implementation work.
- Check logic:
  - Snapshot and note statuses agree.
  - `focus` is cleared or moved to the next active item.
  - Metrics and relationships are updated.
  - Required `CHG-*` and `RISK-*` notes exist when behavior, paths, contracts, or hazards changed.
- On failure: complete the missing close-out work before stopping.

## CHC-006: Mechanical docs validation

- Trigger: before final response after implementation work, at git pre-commit, and in CI.
- Entrypoint: `bash tools/scripts/validate-docs.sh` (install the git hook once with `bash tools/scripts/install-git-hooks.sh`).
- Check logic (deterministic, exit non-zero on violation):
  - Every `items.*` entry's `file` exists and its frontmatter id/status/type agree with the snapshot.
  - Status values are within the allowed taxonomy (`STATUSES.md`).
  - No allocated ID exceeds its `counters` value.
  - Every ID referenced from snapshot relationship fields or active-note frontmatter resolves to a snapshot item or note.
  - No terminal status without passing linked tests (or a recorded `verification_waiver`).
- On failure: fix the drift before stopping/committing. Rationale: convention-only rules are demonstrably bypassed by agents under context pressure; the three layers (session hook, pre-commit, CI) exist because the first two can be skipped and CI cannot.
