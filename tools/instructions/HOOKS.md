---
type: instruction
id: INSTR-HOOKS
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-09-04
tags: [instructions, hooks]
---

# Hook contracts (tool-agnostic)

These contracts define the checks every project-os workflow must perform at key lifecycle points, independent of which LLM tool drives the session. Each contract states the trigger, the project-os rule it enforces, the check logic, and the failure behavior; `../adapters/<tool>/ADAPTER.md` documents how a given tool implements it. The Claude Code adapter implements all eight as session hooks (`../adapters/claude-code/hooks/`); the Codex/generic path implements a subset with `AGENTS.md` instructions plus `tools/agents/*.sh` scripts, with the rest enforced at pre-commit/CI.

Contract IDs are `HC-001`..`HC-008`. (Earlier revisions of this file used `CHC-00x` codes; the mapping is at the end for downstream docs that still cite them.)

## HC-001: Document-first gate

- Trigger: before functional code changes.
- Rule: `LIFECYCLE.md` — "Preflight (must happen before code changes)" and "Mandatory Automated Documentation".
- Check logic:
  - `SNAPSHOT.yaml` has an active `focus.task` or `focus.issue` covering the work. Exempt paths, stated once here and cited by both implementations: `docs/`, `tools/`, `.claude/`, `.cursor/`, `.github/`, `SNAPSHOT.yaml`, `CLAUDE.md`, `CONTEXT.md`, `README.md`, `AGENTS.md`, `LLM_BRIEF.md`, and the lint and sync configs (`.prettierrc`, `.markdownlint*`, `.yamllint*`, `.gitignore`, `.project-os-sync`).
  - Code changes have a `docs/changes/CHG-*.md` note when required.
  - Change notes have no pending documentation-coverage entries.
- Implementations: Claude Code `hooks/document-first-gate.sh` (blocking PreToolUse); Codex/generic `bash tools/agents/start-change.sh "<short title>"` + `bash tools/agents/check-docs-first.sh`.
- The target file's repo governs the edit. A file outside every project-os repo is not gated: when the walk up from the target finds no `SNAPSHOT.yaml`, only a relative path or a path under the session repo falls back to the session repo's focus; any other path is allowed (project-os-dev ISS-0003).
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

- Trigger: before marking a task `done`, issue `fixed`, or feature `done`. A requirement is never test-gated (`STATUSES.md` `[[requirement]]`), so `implemented` is not a trigger.
- Rule: `QUALITY.md` — "Verification gating (tests)".
- Check logic:
  - Find linked `TST-*` IDs from the snapshot and note frontmatter.
  - Confirm every required test is `status: passing`.
- **Two tests are not required tests.** Stated here because two programs enforce this gate and both must read the same list:
  - a test carrying `command:` — it records no verdict and CI is the verdict (`STATUSES.md` `[[test]]`, ADR-0025). Checked first: an acceptance check that gains a `command:` is automated (`TESTING.md`, "When to create", rule 3).
  - a test at `level: acceptance` — it rests at `active` and its verdict is a release-ledger event (`STATUSES.md` `[[test]]`, ADR-0037). Whether it is *settled* is the validator's `VERIFY-ACCEPTANCE`; the hook reads frontmatter and cannot see the ledger, so it does not check settledness.
- A `verification_waiver:` requires `waiver_expires: YYYY-MM-DD` in both implementations; an open-ended waiver is a rule deletion written in the passive voice (ADR-0010).
- On failure: block the terminal status transition unless a `verification_waiver` is recorded (`QUALITY.md`, "Verification gating").
- Enforcement: this gate must be mechanical, not advisory. The Claude Code adapter implements it as a blocking PreToolUse hook (`../adapters/claude-code/hooks/verification-gate.py`); other adapters must run `tools/scripts/validate-docs.sh` before close-out and at pre-commit/CI. The two agree on the exemptions and the waiver rule above. They still differ in reach: the validator gates on the reverse `covers:` index and the hook on the subject's `tests:`, so the validator sees links the hook does not (project-os-dev ISS-0051, follow-up).

## HC-004: Phase alignment

- Trigger: before starting or transitioning a task to `doing`.
- Rule: `LIFECYCLE.md` — "Phase alignment (optional gating)".
- Check logic:
  - Read `focus.phase` from `SNAPSHOT.yaml` and the task or parent feature `phase`.
  - If both phases are set and the task belongs to a future phase, flag the mismatch.
- Implementations: Claude Code `hooks/phase-alignment.sh` (PostToolUse advisory).
- On failure: warn. Whether the task runs ahead of its phase is the user's decision (`LIFECYCLE.md`, "When to pause for the user").

## HC-005: Risk-scan trigger

- Trigger: a changed path matching the risk-scan trigger list.
- Rule: `LIFECYCLE.md` — "Risk scan triggers" (the list); `../skills/risk-scan/SKILL.md`.
- Check logic: match the changed path against the risk-scan trigger list in `LIFECYCLE.md`; when it matches, a `RISK-*` note must be created or updated per `../skills/risk-scan/SKILL.md`.
- Implementations: Claude Code `hooks/risk-scan-trigger.sh` (PostToolUse advisory).
- On failure: warn; close-out (HC-006) verifies the `RISK-*` note exists when hazards changed.

## HC-006: Close-out check

- Trigger: before final response after implementation work.
- Rule: `LIFECYCLE.md` — "Close-out (must happen after work)"; `QUALITY.md` — "Minimum close-out for any implemented task".
- The block names two actions: if the work is complete, set the status and clear focus now; if stopping mid-flight for the user, write the handoff into the task note (`HANDOFF.md`, "Before stopping work") and stop. The loop guard lets that second stop through.
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
- On failure: fix the drift before stopping/committing. Rationale and the three enforcement layers: `QUALITY.md`, "Documentation Fidelity".

## HC-008: Delegation hint

- Trigger: prompt submission (before the agent begins work).
- Rule: `LIFECYCLE.md` — "Preflight (must happen before code changes)" and "Close-out"; `QUALITY.md` — "Independent review (clean-context)", which states once what makes a review independent.
- Check logic:
  - Read `focus.task`/`focus.issue`/`focus.feature` and `focus.phase` from `SNAPSHOT.yaml`, resolve the item's status, and state all three.
  - Say who writes the note: a single issue or task gets its note in the main loop; a multi-item scaffold or an ambiguous ask goes to the `planner` subagent, with the user's prompt verbatim and one sentence on what the result enables. The documentation requirement itself does not change.
  - Name the `independent-reviewer` subagent only in review states.
  - Stay within 3 lines and 600 characters (asserted by `tools/scripts/test-hooks.sh`), so the hint never grows into the SessionStart slice. Stay silent on a template placeholder snapshot (`template.replace_me: true`) or when no snapshot exists.
- Implementations: Claude Code `hooks/model-routing-hint.sh` (advisory UserPromptSubmit) plus the model-pinned subagents generated by `tools/scripts/generate-adapters.py`. The script keeps its filename so existing `.claude/settings.json` files keep resolving. Tools without subagents implement this as instructions only.
- On failure: none. The hint informs; the harness routes (project-os-dev ADR-0003). It does not and cannot change a session's model.

## Legacy CHC-* code mapping

Earlier revisions numbered these contracts `CHC-001`..`CHC-006` in a different order. For downstream docs that still cite them: CHC-001 → HC-002, CHC-002 → HC-001, CHC-003 → HC-004, CHC-004 → HC-003, CHC-005 → HC-006, CHC-006 → HC-007. (HC-005 risk-scan had no CHC code.)
