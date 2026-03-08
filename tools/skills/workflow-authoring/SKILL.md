---
type: skill
id: SKILL-WORKFLOW-AUTHORING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, workflows]
---

# Skill: Workflow authoring

## When to use
- A new “front door” command/script should be documented.
- A workflow changed and documentation must be updated.

## Inputs
- Entrypoint commands/scripts, required env vars, inputs, outputs, expected artifacts.

## Outputs
- Updated workflow note + snapshot entry.

## Checklist
1. Allocate `WF-####` if new (use `../../../SNAPSHOT.yaml -> counters.WF`).
2. Update `../../../SNAPSHOT.yaml` under `items.workflows`:
   - `file`, `title`, `status`, `owner`, `entrypoints`
3. Create/update `../../../docs/workflows/WF-####-*.md` from `../../../docs/__templates__/workflow.md`.
4. Link the workflow from impacted features/tasks in notes + snapshot.
