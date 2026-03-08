---
type: skill
id: SKILL-RISK-MITIGATION-PLANNING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, risk]
---

# Skill: Risk mitigation planning

## When to use
- A `RISK-*` exists but mitigations are not actionable tasks yet.

## Inputs
- Risk note + snapshot risk entry.

## Outputs
- One or more mitigation tasks linked from the risk and tracked in `../../../SNAPSHOT.yaml`.

## Checklist
1. Read the risk and list concrete mitigations.
2. For each mitigation:
   - create a `TASK-*` with a clear DoD
   - set `parent` to the relevant feature (or create a small “hygiene” feature)
3. Update `../../../SNAPSHOT.yaml`:
   - add tasks under `items.tasks`
   - link tasks from the risk (`related` and/or `mitigation_tasks` if you adopt it)
4. Update the risk note to link the tasks and set status to `mitigating` if active.
