---
type: instruction
id: INSTR-HOOKS
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-07-21
tags: [instructions, hooks]
---

# Hook contracts (tool-agnostic)

These contracts define the checks every project-os workflow must perform at key lifecycle points, independent of which LLM tool drives the session. Each contract states the trigger, the project-os rule it enforces, the check logic, and the failure behavior; `../adapters/<tool>/ADAPTER.md` documents how a given tool implements it. The Claude Code adapter implements all eight as session hooks (`../adapters/claude-code/hooks/`); the Codex/generic path implements a subset with `AGENTS.md` instructions plus `tools/agents/*.sh` scripts, with the rest enforced at pre-commit/CI.

Contract IDs are `HC-001`..`HC-008`. (Earlier revisions of this file used `CHC-00x` codes; the mapping is at the end for downstream docs that still cite them.)

## HC-001: Document-first gate

- Trigger: before functional code changes.
- Rule: `LIFECYCLE.md` — "Preflight (must happen before code changes)" and "Mandatory Automated Documentation".
- Check logic:
  - `SNAPSHOT.yaml` has an active `focus.task` or `focus.issue` covering the work (docs/tools/config paths are exempt).
  - Code changes have a `docs/changes/CHG-*.md` note when required.
  - Change notes have no pending documentation-coverage entries.
- Implementations: Claude Code `hooks/document-first-gate.sh` (blocking PreToolUse); Codex/generic `bash tools/agents/start-change.sh "<short title>"` + `bash tools/agents/check-docs-first.sh`.
- On failure: block the code edit (or close-out) until the documentation state is explicit.

## HC-002: Startup preflight / snapshot freshness

- Trigger: session start or before selecting work.
- Rule: `LIFECYCLE.md` — "Preflight", step 2 (orchestration check); `SNAPSHOT.md` — "Update rules (agent behavior)".
- Check logic:
  - Required context files exist and `SNAPSHOT.yaml` can be read.
  - Current branch, head, focus, and working tree are visible.
- Implementations: Claude Code `hooks/snapshot-freshness.sh` (SessionStart reminder); Codex/generic `bash tools/agents/bootstrap.sh`.
- On failure: stop and fix missing required files before implementation.

## HC-003: Verification gate

- Trigger: before marking a task `done`, issue `closed`, requirement `verified`, or feature `done`.
- Rule: `QUALITY.md` — "Verification gating (tests)".
- Check logic:
  - Find linked `TST-*` IDs from the snapshot and note frontmatter.
  - Confirm every required test is `status: passing`.
- On failure: block the terminal status transition unless an explicit `verification_waiver: <reason>` is recorded in the note frontmatter (the waiver is a logged artifact, not a silent skip).
- Enforcement: this gate must be mechanical, not advisory. The Claude Code adapter implements it as a blocking PreToolUse hook (`../adapters/claude-code/hooks/verification-gate.py`); other adapters must run `tools/scripts/validate-docs.sh` before close-out and at pre-commit/CI, which enforces the same invariant repo-wide.

## HC-004: Phase alignment

- Trigger: before starting or transitioning a task to `doing`.
- Rule: `LIFECYCLE.md` — "Phase alignment (optional gating)".
- Check logic:
  - Read `focus.phase` from `SNAPSHOT.yaml` and the task or parent feature `phase`.
  - If both phases are set and the task belongs to a future phase, flag the mismatch.
- Implementations: Claude Code `hooks/phase-alignment.sh` (PostToolUse advisory).
- On failure: warn and require explicit user confirmation before proceeding.

## HC-005: Risk-scan trigger

- Trigger: after changes to dependency manifests, environment/configuration surfaces, CI definitions, or artifact paths.
- Rule: `LIFECYCLE.md` — "Risk scan triggers"; `../skills/risk-scan/SKILL.md`.
- Check logic: match the changed path against the risk-scan trigger list in `LIFECYCLE.md`; when it matches, a `RISK-*` note must be created or updated per `../skills/risk-scan/SKILL.md`.
- Implementations: Claude Code `hooks/risk-scan-trigger.sh` (PostToolUse advisory).
- On failure: warn; close-out (HC-006) verifies the `RISK-*` note exists when hazards changed.

## HC-006: Close-out check

- Trigger: before final response after implementation work.
- Rule: `LIFECYCLE.md` — "Close-out (must happen after work)"; `QUALITY.md` — "Minimum close-out for any implemented task".
- Check logic:
  - Snapshot and note statuses agree.
  - `focus` is cleared or moved to the next active item.
  - Metrics and relationships are updated.
  - Required `CHG-*` and `RISK-*` notes exist when behavior, paths, contracts, or hazards changed.
- Implementations: Claude Code `hooks/close-out-check.sh` (blocking Stop hook, also runs HC-007).
- On failure: complete the missing close-out work before stopping.

## HC-007: Mechanical docs validation

- Trigger: before final response after implementation work, at git pre-commit, and in CI.
- Rule: `QUALITY.md` — "Documentation Fidelity" (mechanical enforcement).
- Entrypoint: `bash tools/scripts/validate-docs.sh` (install the git hook once with `bash tools/scripts/install-git-hooks.sh`).
- Check logic (deterministic, exit non-zero on violation):
  - Every `items.*` entry's `file` exists and its frontmatter id/status/type agree with the snapshot.
  - Status values are within the allowed taxonomy (`STATUSES.md`).
  - No allocated ID exceeds its `counters` value.
  - Every ID referenced from snapshot relationship fields or active-note frontmatter resolves to a snapshot item or note.
  - No terminal status without passing linked tests (or a recorded `verification_waiver`).
  - `metrics.counts` values match the computed counts (`--fix-metrics` rewrites them).
- On failure: fix the drift before stopping/committing. Rationale: convention-only rules are demonstrably bypassed by agents under context pressure; the three layers (session hook, pre-commit, CI) exist because the first two can be skipped and CI cannot.

## HC-008: Model routing hint

- Trigger: prompt submission (before the agent begins work).
- Rule: `LIFECYCLE.md` — "Preflight (must happen before code changes)" and "Close-out"; `QUALITY.md` — independent review must not be performed by the authoring model.
- Check logic:
  - Read `focus.task`/`focus.issue`/`focus.feature` from `SNAPSHOT.yaml` and resolve the item's status.
  - Map the lifecycle phase to the agent that should do the work: planning statuses → the `planner` subagent, execution statuses → the main loop, review statuses → the `independent-reviewer` subagent.
  - Stay silent on a template placeholder snapshot (`template.replace_me: true`) or when no snapshot exists.
- Implementations: Claude Code `hooks/model-routing-hint.sh` (advisory UserPromptSubmit) plus the model-pinned subagents generated by `tools/scripts/generate-adapters.py`. Tools without subagents implement the routing as instructions only.
- On failure: none — the hint is advisory. Hooks cannot change a session's model, so enforcement lives in the subagent model pins, not here.

## Legacy CHC-* code mapping

Earlier revisions numbered these contracts `CHC-001`..`CHC-006` in a different order. For downstream docs that still cite them: CHC-001 → HC-002, CHC-002 → HC-001, CHC-003 → HC-004, CHC-004 → HC-003, CHC-005 → HC-006, CHC-006 → HC-007. (HC-005 risk-scan had no CHC code.)
