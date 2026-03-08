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
- Avoid forcing humans to read the snapshot: human-facing views are the notes and Bases dashboards.

## Required top-level keys
- `version` (int): Schema version (bump only when breaking changes are made).
- `updated` (timestamp string): Last update time.
- `project` (object): Project metadata (name/summary/repo root).
- `team` (object, optional): Team members and their tool adapters (see Team Model below).
- `retention` (object): Retention policy for keeping the snapshot small (optional but recommended).
- `counters` (object): Highest allocated IDs per type (used for new ID allocation).
- `focus` (object): Current in-flight IDs and active phase (empty strings if none).
- `items` (object): Canonical state for each tracked item type.
- `metrics` (object): Derived counts (optional but recommended).

## Required `items.*` collections
The snapshot should contain (at least) these collections:
- `items.features`
- `items.tasks`
- `items.issues`
- `items.requirements`
- `items.risks`
- `items.tests`
- `items.workflows`
- `items.changes`
- `items.releases`
- `items.decisions` (ADRs)

Projects may add collections (e.g. `epics`, `milestones`) if rules are documented and applied consistently.

## Focus object
The `focus` object tracks the current work context:
- `focus.phase` (integer or empty string): Active development phase (see `../../docs/PHASES.md` for definitions).
- `focus.feature` (string): Currently active feature ID (or empty string).
- `focus.task` (string): Currently active task ID (or empty string).
- `focus.issue` (string): Currently active issue ID (or empty string).

When phase-gated development is used:
- Update `focus.phase` when transitioning to a new milestone.
- Agents should verify work aligns with the active phase before starting implementation.

## Required fields per item (minimum)
Each item entry must include:
- `file` (string): Repo-relative path to the canonical note (e.g. `docs/issues/ISS-0001-...md`).
- `title` (string): Short human title (no ID).
- `status` (string)
- `owner` (string)

Optional cross-cutting fields:
- `platform` (string, optional): Target platform (`ios`, `android`, `shared`, or empty). For multi-platform projects only.

Then type-specific fields, for example:
- Feature: `goal`, `phase` (optional), `requirements` (REQ IDs), `tasks` (TASK IDs), `issues` (ISS IDs), `tests` (TST IDs), `workflows` (WF IDs), `release`
- Task: `parent` (FEAT/ISS ID), `phase` (optional, inherit from parent), `effort`, `due`, `depends`, `blocks`, `related`
- Task: (verification) `tests` (TST IDs) when applicable
- Issue: `severity`, `component`, `phase` (optional), `features` (FEAT IDs), optional `tasks` (TASK IDs), optional `tests` (TST IDs)
- Requirement: `priority`, `scope`, `phase` (optional), `features` (FEAT IDs), `verifies` (paths/links), optional `tests` (TST IDs)
- Risk: `likelihood`, `impact`, `related` (IDs), optional `mitigation_tasks` (TASK IDs)
- Test: `scope`, `kind`, `level`, `entrypoint`, `requirements` (REQ IDs), optional `features`/`issues`/`tasks` (IDs), optional `artifacts`, optional `last_run`
- Workflow: `entrypoints` (paths), optional `inputs`/`outputs`
- Change: `commit`, `pr`, `issues` (ISS IDs), `features` (FEAT IDs)
- Release: `version`, `tag`, `date`, `features` (FEAT IDs), `changes` (CHG IDs), `tests_verified` (TST IDs), `previous_release` (REL ID)
- Decision (ADR): `decision`, `context`, `supersedes`, `superseded`, `related` (IDs)

## Optional metrics: `by_platform`
For multi-platform projects, the `metrics` section may include a `by_platform` block with per-platform counts:
```yaml
metrics:
  by_platform:
    ios: { tasks_total: N, tasks_done: N }
    android: { tasks_total: N, tasks_done: N }
    shared: { tasks_total: N, tasks_done: N }
```

## Invariants
- `file` must point to an existing note under `../../docs/`, and the note’s frontmatter `id` should match the snapshot key.
- Status values must be one of the allowed values (see `STATUSES.md`).
- Relationships must be **bi-directionally consistent** where applicable:
  - If a task `parent: FEAT-0001`, that feature’s `tasks` must include the task ID.
  - If an issue lists `features: [FEAT-0001]`, the feature should list the issue under `issues` (unless intentionally omitted).

## Team model (optional)
Use the `team` object to identify team members and their tool adapters in multi-user or multi-agent projects.

```yaml
team:
  members:
    - id: user:edwin
      tool: claude-code
      adapter: tools/adapters/claude-code
    - id: user:alice
      tool: codex
      adapter: tools/adapters/codex
```

Fields per member:
- `id` (string): Owner identifier (same format as `owner` — `user:*`, `team:*`, etc.)
- `tool` (string): LLM tool used by this member (claude-code, codex, cursor, etc.)
- `adapter` (string): Path to the adapter directory for this member's tool

The team model is informational — it identifies who uses what tool and which adapter applies. Agent coordination (task assignment, parallel execution, conflict avoidance) is delegated to each tool's native orchestration mechanism (e.g., Claude Code Agent Teams, Codex parallel agents).

## Releases section (optional)
Use the `releases` top-level key for lightweight release tracking that agents can read without scanning notes.

```yaml
releases:
  latest:
    id: REL-0003
    version: "1.2.0"
    tag: v1.2.0
    date: "2026-03-08"
    status: released
  history:
    - { id: REL-0003, version: "1.2.0", date: "2026-03-08", status: released }
    - { id: REL-0002, version: "1.1.0", date: "2026-02-15", status: released }
    - { id: REL-0001, version: "1.0.0", date: "2026-01-30", status: released }
```

Fields:
- `releases.latest` (object): The most recent release (quick lookup for agents).
- `releases.history` (list): Recent releases in reverse chronological order. Apply the same retention policy as changes (keep last N).
- Each entry: `id`, `version`, `tag`, `date`, `status`.

The full release record (features included, tests verified, notes) lives in the `REL-*` note under `items.releases`.

## Update rules (agent behavior)
- Agents/LLMs must update the snapshot **before** starting implementation work (create/modify issues/features/tasks/risks as needed).
- After finishing work, agents/LLMs must update snapshot statuses and relationships and clear/move `focus`.
- Keep `counters` up to date when allocating new IDs.

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
