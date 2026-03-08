---
type: instruction
id: INSTR-HOOKS
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
tags: [instructions, hooks, enforcement]
---

# Hook Contracts

Hook contracts define **what** project-os enforces at key workflow points. They are tool-agnostic — each contract specifies the check logic and failure behaviour without assuming a specific tool's hook mechanism.

Tool-specific implementations live under `../adapters/<tool>/hooks/`. See each adapter's `ADAPTER.md` for implementation details.

## Contract format

Each contract has:
- **ID**: `HC-###`
- **Name**: Short descriptive name
- **Trigger**: When this check should run
- **Check logic**: What to verify
- **On failure**: What happens when the check fails (block, warn, or flag)
- **Enforces**: Which project-os rule this contract implements

---

## HC-001: Document-First Gate

**Trigger**: Before any code file is written or edited (e.g., `src/**`, `lib/**`, `app/**` — excludes `docs/**`, `tools/**`, `SNAPSHOT.yaml`, `CLAUDE.md`).

**Check logic**:
1. Read `SNAPSHOT.yaml`
2. Check that `focus.task` or `focus.issue` is set (non-empty)
3. If empty: the agent is editing code without a documented task — violates the document-first rule

**On failure**: **Block.** The agent must create or update the relevant task/issue in SNAPSHOT.yaml before editing code.

**Enforces**: CONTEXT.md operating rule step 1 ("Document first"), LIFECYCLE.md preflight.

---

## HC-002: Snapshot Freshness

**Trigger**: At session start or periodically during long sessions.

**Check logic**:
1. Read `SNAPSHOT.yaml` `updated` timestamp
2. Compare to current time
3. If the snapshot hasn't been updated in the current session: the agent may be working from stale state

**On failure**: **Warn.** Remind the agent to read and verify SNAPSHOT.yaml before proceeding.

**Enforces**: LIFECYCLE.md preflight ("Read SNAPSHOT.yaml at session start").

---

## HC-003: Verification Gate

**Trigger**: Before a status transition to `done`, `closed`, or `verified` (detected by writes to note frontmatter or SNAPSHOT.yaml that set these statuses).

**Check logic**:
1. Identify the item being transitioned
2. Find all linked `TST-*` IDs in the snapshot
3. For each linked test, check its `status` field
4. If any linked test is not `status: passing`: block the transition

**On failure**: **Block.** The agent must not transition the item. Report which tests are failing.

**Enforces**: QUALITY.md verification gating, close-out skill step 1, status-transition skill verification gate.

---

## HC-004: Phase Alignment

**Trigger**: Before a task status transition to `doing`.

**Check logic**:
1. Read the task's `phase` property (from note or snapshot)
2. Read `focus.phase` from `SNAPSHOT.yaml`
3. If the task's phase is numerically greater than the active phase: the task belongs to a future phase

**On failure**: **Warn.** Flag to the user that this task is ahead of the active phase. The user may explicitly override.

**Enforces**: LIFECYCLE.md phase alignment, status-transition skill phase alignment gate.

---

## HC-005: Risk Scan Trigger

**Trigger**: After code changes are committed or during close-out.

**Check logic**:
1. Check if any of the following changed:
   - Package manifests (e.g., `package.json`, `Cargo.toml`, `requirements.txt`, `go.mod`)
   - Environment configuration files (e.g., `.env`, `.env.example`)
   - Directory structure (new top-level directories)
   - CI/CD configuration
2. If any of these changed: a risk scan should have been performed

**On failure**: **Warn.** Remind the agent to run the risk-scan skill and create/update `RISK-*` notes if applicable.

**Enforces**: LIFECYCLE.md risk scan triggers, close-out skill step 5.

---

## HC-006: Close-out Check

**Trigger**: When the agent finishes responding (Stop event).

**Check logic**:
1. Review whether code changes were made in the turn
2. If yes, check that:
   - SNAPSHOT.yaml was updated with current statuses
   - Task/feature/issue statuses were progressed appropriately
   - A CHG-* change note was created if behavior changed
3. If any close-out step was missed: flag it

**On failure**: **Continue with feedback.** The Stop hook returns `decision: "block"` with a reason, which prevents Claude from stopping and instructs it to complete the missing close-out steps. Uses `stop_hook_active` to prevent infinite loops — if the hook already forced one continuation, it allows stopping on the second attempt.

**Enforces**: LIFECYCLE.md close-out, QUALITY.md minimum close-out, close-out skill.

---

## Implementation matrix

| Contract | Claude Code | Codex | Cursor | Generic |
|---|---|---|---|---|
| HC-001 Document-First | PreToolUse agent hook | — | — | Instruction only |
| HC-002 Snapshot Freshness | SessionStart command hook | — | — | Instruction only |
| HC-003 Verification Gate | PostToolUse prompt hook | — | — | Instruction only |
| HC-004 Phase Alignment | PostToolUse prompt hook | — | — | Instruction only |
| HC-005 Risk Scan Trigger | PostToolUse command hook | — | — | Instruction only |
| HC-006 Close-out Check | Stop command hook | — | — | Instruction only |

Tools without hook support rely on instruction-based enforcement (skill checklists). When those tools add hook support, implement the contracts above.

## Hook types

| Type | Use when | Supported events | Trade-off |
|---|---|---|---|
| `command` | Simple checks (file path matching, existence checks) | All events | Fast, no LLM cost, but brittle parsing |
| `prompt` | Semantic checks (understanding status transitions, evaluating completeness) | PreToolUse, PostToolUse, Stop, and others | Slower (~10s), small LLM cost, understands context |
| `agent` | Checks that need file access (reading SNAPSHOT.yaml, scanning notes) | Same as prompt | Slowest (~15-60s), higher cost, can read and reason about files |

**Note:** `SessionStart`, `PreCompact`, `SessionEnd`, `Notification`, and worktree events only support `command` hooks.

## Response schema (prompt and agent hooks)

Prompt and agent hooks must return:
- `{"ok": true}` — allow the action to proceed
- `{"ok": false, "reason": "explanation"}` — block/flag the action

The effect of `ok: false` depends on the event:
- **PreToolUse**: blocks the tool call (agent must fix the issue first)
- **PostToolUse**: shows the reason to the agent as feedback (tool already ran)
- **Stop**: prevents Claude from stopping, forces continuation with the reason as instruction
