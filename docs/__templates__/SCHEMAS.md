---
type: reference
id: TEMPLATES-SCHEMAS
status: active
owner: team:docs
created: 2026-01-27
updated: 2026-05-08
tags: [templates, schema]
---

# Template schemas (frontmatter fields)

This document defines the intended meaning of the frontmatter fields used by the note templates in `docs/__templates__/`.

Conventions (naming, linking, property rules): `../../tools/instructions/OBSIDIAN.md`.

## Common fields (most templates)

- (required) `type` (link string): Obsidian link identifying the note type, e.g. `type: "[[task]]"`.
  - Used by tools/automation to classify notes; the snapshot references these types.
- (required) `id` (string): Stable identifier (should match the filename prefix).
  - Used for traceability and for `SNAPSHOT.yaml` keys.
- (recommended) `title` (string): Human-friendly title for views and summaries.
  - Keep short; no need to repeat the ID.
  - Keep it consistent with `SNAPSHOT.yaml` where possible.
- (required) `status` (string): Lifecycle state; each note type has its own allowed values.
- (optional) `phase` (link or integer): Development phase for milestone grouping. Prefer `[[PHASE-####]]` links when using first-class phase notes; legacy integer values may be used during migration. See `[[PHASES]]` for definitions.
  - Enables machine-filtering, automated progress tracking, and phase grouping.
  - Leave empty/omit for items not tied to a specific phase.
- (required) `owner` (string): Accountable person/team (can be `unassigned`).
  - Values must be defined in `[[OWNERSHIP]]` (or be `unassigned`).
- (required) `created` (date string): Creation date; keep stable.
- (required) `updated` (date string): Last material edit date; bump when meaningfully changed.
- (optional) `related` (list of links/strings): Cross-links to other notes and/or repo paths.
  - Prefer links (`[[...]]`) when pointing to other notes in this docs set.
- (optional) `source` (list of strings/links): Provenance for imported/derived items.
  - Use for links to external trackers, changelogs, or source documents.

## `adr.md` (`type: [[adr]]`)

Purpose: capture “why we chose X” with alternatives and consequences.

Fields:
- (required) `decision` (string): One-sentence decision statement.
- (required) `context` (string): One-sentence reason/background for the decision.
- (optional) `alternatives` (list): Options considered (strings or links).
- (optional) `consequences` (list): Key impacts/tradeoffs (strings or links).
- (optional) `supersedes` (string/link): Link to the ADR replaced by this one (prefer `[[ADR-....]]`).
- (optional) `superseded` (string/link): Link to the ADR that replaces this one (prefer `[[ADR-....]]`).

Where used:
- Referenced from `../decisions/README.md` for organization.

## `change.md` (`type: [[change]]`)

Purpose: durable “what shipped and why” note.

Naming:
- Filename should be `CHG-YYYYMMDD-Short-Description.md`.
- `id` should match the filename without `.md` (same `CHG-...-Short-Description` string).

Fields:
- (optional) `commit` (string): Commit hash.
- (optional) `pr` (string): PR/MR identifier or link.
- (recommended) `impacts` (list of strings): Affected areas/paths/flows (keep short).
- (optional) `issues` (list of links): Issues associated with the change.
- (optional) `features` (list of links): Features associated with the change.
- (optional) `reviewed_by` (string): Independent reviewer identity (`model:...` or `user:...`), per `tools/skills/independent-review/SKILL.md`.
- (optional) `review_date` (string/date): Date of the independent review.
- (optional) `review_verdict` (string): `approved | changes-requested`.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.changes`) for agent context and linked from change notes.

## `feature.md` (`type: [[feature]]`)

Purpose: a work package describing a capability, with traceability to requirements and tasks.

Fields:
- (required) `goal` (string): Short outcome statement.
- (optional) `requirements` (list of links): `[[REQ-...]]` links implemented by this feature.
- (optional) `tasks` (list of links): `[[TASK-...]]` links that deliver the feature.
- (optional) `tests` (list of links): `[[TST-...]]` links used to verify the feature.
- (optional) `release` (string): Milestone/release label.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.features`) for agent context and linked from feature notes.

## `phase.md` (`type: [[phase]]`)

Purpose: define a delivery milestone with explicit scope, linked work, and exit criteria.

Naming:
- Filename should be `PHASE-####-Short-Name.md`.
- `id` should match the filename prefix.

Fields:
- (required) `order` (integer): Sort order for roadmap sequencing.
- (required) `goal` (string): Short outcome statement for the milestone.
- (optional) `features` (list of links): Features planned for this phase.
- (optional) `requirements` (list of links): Requirements introduced or verified in this phase.
- (optional) `tasks` (list of links): Active or key tasks in this phase.
- (optional) `issues` (list of links): Issues tied to this phase.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.phases`) for agent context and linked from phase-aware items.

## `issue.md` (`type: [[issue]]`)

Purpose: canonical problem report / gap / bug.

Fields:
- (required) `severity` (string): e.g. `low|medium|high|critical` (project-defined).
- (recommended) `component` (string): Subsystem/area label (project-defined).
- (optional) `parent` (string/link): Link to a parent feature/epic note.
- (optional) `tests` (list of links): `[[TST-...]]` links used to reproduce/verify the issue.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.issues`) for agent context and linked from issue notes.

## `requirement.md` (`type: [[requirement]]`)

Purpose: acceptance criteria that features/tasks must satisfy.

Fields:
- (required) `priority` (string): e.g. `low|medium|high` (project-defined).
- (optional) `scope` (string): Short scoping label (area/domain).
- (required) `acceptance` (list): Acceptance criteria statements (strings).
- (optional) `implements` (list of links): Notes implementing the requirement (usually features).
- (optional) `verifies` (list of links/paths): Proof/verification pointers (workflows/tests/repo paths).
- (optional) `tests` (list of links): `[[TST-...]]` links that verify this requirement.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.requirements`) for agent context and linked from requirement notes.

## `reference.md` (`type: [[reference]]`)

Purpose: durable explanatory, registry, or background material that supports project understanding but is not itself a task, feature, workflow, decision, test, issue, requirement, phase, risk, or change.

Fields:
- (recommended) `scope` (string): Short scope label such as `project`, `docs`, `tooling`, or a domain-specific area.
- (optional) `related` (list of links/strings): Related notes or repo paths.
- (optional) `source` (list of strings/links): Provenance or upstream/source documents.

Where used:
- Surfaced by the cockpit project mode under References and by `/index/references`.
- Not normally tracked in `SNAPSHOT.yaml` unless a downstream project deliberately promotes a reference collection into active state.

## `risk.md` (`type: [[risk]]`)

Purpose: track hazards + mitigations.

Fields:
- (required) `likelihood` (string): e.g. `low|medium|high` (project-defined).
- (required) `impact` (string): e.g. `low|medium|high` (project-defined).
- (recommended) `mitigation` (list): Mitigation actions (strings or links to tasks).

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.risks`) for agent context and linked from risk notes.

## `task.md` (`type: [[task]]`)

Purpose: actionable unit of work with a Definition of Done.

Fields:
- (required) `parent` (link): Link to a feature or issue note this task belongs to.
- (optional) `effort` (string): Size label (e.g. `XS|S|M|L`).
- (optional) `due` (string/date): Due date.
- (optional) `depends` (list of links): Tasks/issues that must complete first.
- (optional) `blocks` (list of links): Tasks/issues blocked by this task.
- (optional) `tests` (list of links): `[[TST-...]]` links used to verify completion.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.tasks`) for agent context and linked from task notes.

## `test.md` (`type: [[test]]`)

Purpose: describe how to verify behavior (manual or automated) and provide durable coverage mapping.

Fields:
- (required) `scope` (string): `feature|system` (controls where the test note is stored).
- (required) `kind` (string): `manual|automated`.
- (recommended) `level` (string): `unit|integration|system|e2e`.
- (optional) `entrypoint` (string): Repo-relative command/script to run (or blank for purely manual tests).
- (recommended) `requirements` (list of links): Requirements verified by this test (`[[REQ-...]]`).
- (optional) `features` (list of links): Related features (`[[FEAT-...]]`).
- (optional) `issues` (list of links): Related issues (`[[ISS-...]]`).
- (optional) `tasks` (list of links): Related tasks (`[[TASK-...]]`).
- (optional) `artifacts` (list): Expected artifacts/logs.
- (optional) `evidence` (list): Evidence from the last run (paths/log excerpts).
- (optional) `last_run` (string): Timestamp/label for the last execution.
- (optional) `adequacy` (string): Evidence the test actually guards (see `tools/instructions/TESTING.md`, "Test adequacy").
- (optional) `mutation_score` (string): Mutation-testing score for the code this test guards, when measured.
- (optional) `reviewed_by` (string): Independent reviewer identity (`model:...` or `user:...`), per `tools/skills/independent-review/SKILL.md`.
- (optional) `review_date` (string/date): Date of the independent review.
- (optional) `review_verdict` (string): `approved | changes-requested`.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.tests`) for agent context and linked from test notes.

## `workflow.md` (`type: [[workflow]]`)

Purpose: canonical “front door” for a repo activity (what to run, inputs/outputs).

Fields:
- (recommended) `entrypoints` (list): Main scripts/commands (repo-relative).
- (optional) `prereqs` (list): Prerequisite tools/env/licenses (strings or links).
- (optional) `inputs` (list): Required inputs (paths/links).
- (optional) `outputs` (list): Expected outputs/artifacts/log locations.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.workflows`) for agent context and linked from workflow notes.
