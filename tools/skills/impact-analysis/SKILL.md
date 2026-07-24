---
type: skill
id: SKILL-IMPACT-ANALYSIS
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-05-05
tags: [skills, impact-analysis, requirements, conflict-detection]
---

# Skill: Impact analysis

## When to use
- A new requirement (`REQ-*`) is being created or significantly modified.
- A new feature (`FEAT-*`) is being scaffolded that touches an existing area of the codebase.
- An issue (`ISS-*`) is filed that may affect features constrained by existing requirements.
- Any time a change may interact with or contradict existing documented requirements.

## Inputs
- The new or modified item (requirement, feature, or issue).
- `../../../SNAPSHOT.yaml` for the link graph.
- Relevant notes under `../../../docs/` (requirements, features, issues, decisions).

## Outputs
- A list of potentially affected features and their existing requirements.
- Any identified tensions or contradictions between the new item and existing requirements.
- If conflicts are found: a summary with resolution options.
- If no conflicts are found: explicit confirmation.

## Checklist
1. Identify the impact surface:
   - New requirement: identify intended implementing features.
   - New feature: identify existing features sharing the same component, workflow, or user-facing area.
   - New issue: identify affected features from the issue and snapshot links.
2. Gather existing constraints:
   - Read each affected feature note.
   - Read linked requirement notes, especially acceptance criteria and scope.
   - Read related ADRs when present.
3. Detect tensions:
   - Direct contradiction between requirements.
   - Overlapping scope with different behavior or acceptance rules.
   - Resource conflict such as UI space, performance budget, or operational cost.
   - Phase conflict between the new work and affected feature/task phases.
4. Report findings:
   - If no tensions are found, state which features and requirements were checked.
   - If tensions are found, list each conflict with the involved IDs, conflict type, and relevant requirement language.
5. Resolve before implementation:
   - Supersede or retire an older requirement.
   - Narrow the new requirement scope.
   - Document a deliberate trade-off with an ADR.
   - Stop for user decision when the resolution is not obvious.
