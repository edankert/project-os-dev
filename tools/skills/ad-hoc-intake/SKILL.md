---
type: skill
id: SKILL-ADHOC-INTAKE
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
tags: [skills, intake, adhoc]
---

# Skill: Ad-hoc prompt intake

## When to use
- A prompt arrives that is unstructured, unexpected, or not clearly tied to existing work.

## Inputs
- The raw user prompt.
- Any immediate context or constraints provided.

## Outputs
- Either a direct answer (no artifacts created), or new/updated items in `SNAPSHOT.yaml` and docs notes.

## Critical rule (no-op path)
- If the prompt is a **simple question** that does **not** require updates to any sources or documentation, **answer directly** and **do not create** any tracking item.

## Triage guide
- Bug/gap/mismatch → use `../issue-intake/SKILL.md`.
- New capability or enhancement → use `../feature-scaffold/SKILL.md`.
- Small, actionable change → create a `TASK-*` (or use `../task-breakdown/SKILL.md` if scope is unclear).
- Clarification needed → create an `ISS-*` with `status: triage` and request specifics.

## Checklist
1. Decide if the prompt requires documentation or project state changes.
2. If **no**: answer directly and stop.
3. If **yes**: choose the correct intake path (issue/feature/task).
4. Capture the prompt verbatim in the note (Problem/Evidence) and link related items.
5. Update `SNAPSHOT.yaml` and run `../snapshot-sync/SKILL.md` if multiple items changed.
