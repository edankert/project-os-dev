---
type: instruction
id: INSTR-SNAPSHOT
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, snapshot]
---

# Snapshot rules (`../../SNAPSHOT.yaml`)

`../../SNAPSHOT.yaml` is the canonical, machine-readable active-context snapshot for agents/LLMs.

## Goals
- Enable another agent to resume work from **one file** (the snapshot) and jump to the right notes via `file`.
- Make state transitions explicit (status changes, focus changes, relationships).
- Avoid forcing humans to read the snapshot: human-facing views are the notes and Bases views.

## Required top-level keys
- `version` (int): Schema version (bump only when breaking changes are made).
- `updated` (timestamp string): Last update time.
- `project` (object): Project metadata (name/summary/repo root).
- `session` (object, optional): Active agent session metadata for recovery.
- `retention` (object): Retention policy for keeping the snapshot small (optional but recommended).
- `counters` (object): Highest allocated IDs per type (used for new ID allocation).
- `focus` (object): Current in-flight IDs and active phase (empty strings if none).
- `items` (object): Canonical state for each tracked item type.
- `metrics` (object): Derived counts (optional but recommended).

## Required `items.*` collections
The snapshot should contain (at least) these collections:
- `items.features`
- `items.phases`
- `items.tasks`
- `items.issues`
- `items.requirements`
- `items.risks`
- `items.tests`
- `items.workflows`
- `items.changes`
- `items.decisions` (ADRs)

Projects may add collections (e.g. `epics`, `milestones`) if rules are documented and applied consistently.

## Focus object
The `focus` object tracks the current work context:
- `focus.phase` (PHASE ID, integer, or empty string): Active development phase. `PHASE-*` IDs are preferred when using first-class phase notes; integer values are accepted for simple projects and migration.
- `focus.feature` (string): Currently active feature ID (or empty string).
- `focus.task` (string): Currently active task ID (or empty string).
- `focus.issue` (string): Currently active issue ID (or empty string).

When phase-gated development is used:
- Update `focus.phase` when transitioning to a new milestone.
- Agents should verify work aligns with the active phase before starting implementation.
- Keep `focus.phase` aligned with `items.phases.<PHASE-ID>` when phase notes are used.

## Required fields per item (minimum)
Each item entry must include:
- `file` (string): Repo-relative path to the canonical note (e.g. `docs/issues/ISS-0001-...md`).
- `title` (string): Short human title (no ID).
- `status` (string)
- `owner` (string)
Optional collaboration fields:
- `claimed_by` (string): Agent/user currently working this item (if any).
- `claim_started` (string): Timestamp when the claim began.

Then type-specific fields, for example:
- Phase: `order`, `goal`, `features` (FEAT IDs), `requirements` (REQ IDs), `tasks` (TASK IDs), `issues` (ISS IDs)
- Feature: `goal`, `phase` (optional), `requirements` (REQ IDs), `tasks` (TASK IDs), `issues` (ISS IDs), `tests` (TST IDs), `workflows` (WF IDs), `release`
- Task: `parent` (FEAT/ISS ID), `phase` (optional, inherit from parent), `effort`, `due`, `depends`, `blocks`, `related`
- Task: (verification) `tests` (TST IDs) when applicable
- Issue: `severity`, `component`, `phase` (optional), `features` (FEAT IDs), optional `tasks` (TASK IDs), optional `tests` (TST IDs)
- Requirement: `priority`, `scope`, `phase` (optional), `features` (FEAT IDs), `verifies` (paths/links), optional `tests` (TST IDs)
- Risk: `likelihood`, `impact`, `related` (IDs), optional `mitigation_tasks` (TASK IDs)
- Test: `scope`, `kind`, `level`, `entrypoint`, `requirements` (REQ IDs), optional `features`/`issues`/`tasks` (IDs), optional `artifacts`, optional `last_run`
- Workflow: `entrypoints` (paths), optional `inputs`/`outputs`
- Change: `commit`, `pr`, `issues` (ISS IDs), `features` (FEAT IDs)
- Decision (ADR): `decision`, `context`, `supersedes`, `superseded`, `related` (IDs)

## Invariants
- `file` must point to an existing note under `../../docs/`, and the note’s frontmatter `id` should match the snapshot key.
- Status values must be one of the allowed values (see `STATUSES.md`).
- Relationships must be **bi-directionally consistent** where applicable:
  - If an item has `phase: PHASE-0001`, `items.phases.PHASE-0001` should list that item under the appropriate collection when phase notes are used.
  - If a task `parent: FEAT-0001`, that feature’s `tasks` must include the task ID.
  - If an issue lists `features: [FEAT-0001]`, the feature should list the issue under `issues` (unless intentionally omitted).

## Session fields (optional)
Use these to support recovery and multi-agent collaboration:
- `session.agent_id`: identifier for the current agent/user.
- `session.started`: timestamp for when the session began.
- `session.last_heartbeat`: timestamp for the last update by the agent.
- `session.current_step`: short text describing the current work step.

## Update rules (agent behavior)
- Agents/LLMs must update the snapshot **before** starting implementation work (create/modify issues/features/tasks/risks as needed).
- After finishing work, agents/LLMs must update snapshot statuses and relationships and clear/move `focus`.
- Keep `counters` up to date when allocating new IDs.
- If using multi-agent collaboration, update `session` and `claimed_by` during work and clear claims on handoff.

## Retention policy (active + recent)
The snapshot is not a full historical database.

Recommended approach:
- Keep **active** items in `items.*`:
  - tasks: anything not `done`
  - issues: anything not `closed`
  - features: anything not `done`
  - risks: anything not `closed`
  - requirements: keep `approved` requirements that still matter for current work, retire when obsolete
- Keep **recent** changes only in `items.changes` (e.g. last 10–50), and rely on `../../docs/changes/` notes for history.
- Keep **all history in notes** (issues/tasks/features/changes/ADRs remain in `../../docs/**` even if removed from the snapshot).

If you remove an item from the snapshot, do not delete its note; the note is the archive.
