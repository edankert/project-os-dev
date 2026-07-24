---
type: "[[requirement]]"
id: REQ-0005
aliases: ["REQ-0005"]
title: "project-os must delegate agent coordination to native tool orchestration"
status: implemented
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-07-21
source: []
priority: high
scope: "orchestration"
acceptance:
  - "SNAPSHOT.yaml does not contain session, claimed_by, or heartbeat fields"
  - "SNAPSHOT.yaml documents an optional team model identifying members and their tool adapters (descriptive only; ships commented out in the template)"
  - "Preflight rules do not include claim-checking steps"
  - "Recovery/handoff instructions work without agent-specific session metadata"
implements: ["[[FEAT-0003-Team-Model]]", "[[FEAT-0004-Snapshot-Simplification]]"]
verifies: []
related: []
tests: []
---

# project-os must delegate agent coordination to native tool orchestration

## Statement
project-os MUST NOT implement agent coordination (claiming, heartbeats, session tracking). It MUST delegate this to native tool orchestration (Claude Code Agent Teams, Codex parallel tasks, etc.) and focus on project-level context.

## Acceptance Criteria

- [x] `SNAPSHOT.yaml` contains no `session`, `claimed_by`, or `heartbeat` fields — evidence: no such keys, active or commented; the legacy commented `session:` example block was removed from the template snapshot and `SNAPSHOT.md` no longer defines `session`/`claimed_by`/`claim_started`.
- [x] `SNAPSHOT.yaml` documents an optional `team` model of members and their tool adapters — evidence: commented `team.members` block in the template `SNAPSHOT.yaml` (id / tool / adapter per member), documented under `SNAPSHOT.md` "Team model (optional)" and listed in the required-top-level-keys table as descriptive-only.
- [x] Preflight rules include no claim-checking steps — evidence: `tools/instructions/LIFECYCLE.md` "Preflight" step 2 is an orchestration check against the snapshot; no claim/heartbeat/session step; `tools/agents/*.sh` contain no claim logic.
- [x] Recovery/handoff works without agent session metadata — evidence: `tools/instructions/HANDOFF.md` rewritten to run off snapshot `focus`, note "Next Actions", `validate-docs.sh` and git state; `tools/skills/snapshot-sync/SKILL.md:50` now checks stale `focus` instead of stale `claimed_by`.

## Amendments (2026-07-21)

Three of the four criteria were **not** satisfied at verification time: the orchestration-delegation cleanup (ADR-0003) landed in `SNAPSHOT.yaml`'s active keys and the LIFECYCLE preflight, but `SNAPSHOT.md`, `HANDOFF.md`, and `snapshot-sync/SKILL.md` were never updated and still mandated `session.last_heartbeat`, `claimed_by`, and claim release on handoff — a live contradiction with an accepted ADR.

Resolution: the work was completed rather than the criteria narrowed. `HANDOFF.md` was rewritten around the snapshot/notes/git handoff surface, `SNAPSHOT.md` lost its session/claim field definitions and gained a "Team model (optional)" section, `snapshot-sync` step 7 now checks stale `focus`, and the commented `session:` example was removed from the template snapshot.

**Criterion 2** was narrowed: the `team` model ships as a *documented, commented-out optional* block rather than an active field, since a template cannot ship real member identities. Its descriptive-only role (no coordination state) is now documented in `SNAPSHOT.md`.

## Traceability
- Implements: [[FEAT-0003-Team-Model]], [[FEAT-0004-Snapshot-Simplification]]
- Decided by: [[ADR-0003-Delegate-Orchestration]]
