---
type: reference
id: TOOLS-SKILLS-README
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [tools, skills]
---

# `tools/skills/`

Reusable playbooks for an LLM (or other agents) to keep this documentation system consistent while doing work. These skills assume `SNAPSHOT.yaml` is the canonical agent state and must be kept in sync with notes.

## What goes here
- One subdirectory per skill, each containing a `SKILL.md` describing:
  - when to use the skill
  - inputs/outputs
  - required snapshot/notes updates
  - step-by-step checklist

## What does not go here
- Project documentation content (belongs under `../../docs/`).
- Obsidian templates (belong under `../../docs/__templates__/`).

## Skills index
- Issue intake: `issue-intake/SKILL.md`
- Feature scaffold: `feature-scaffold/SKILL.md`
- Task breakdown: `task-breakdown/SKILL.md`
- Test authoring: `test-authoring/SKILL.md`
- Impact analysis: `impact-analysis/SKILL.md`
- Risk scan: `risk-scan/SKILL.md`
- Change note: `change-note/SKILL.md`
- Snapshot sync: `snapshot-sync/SKILL.md`
- Status transition: `status-transition/SKILL.md`
- Close-out: `close-out/SKILL.md`
- Workflow authoring: `workflow-authoring/SKILL.md`
- ADR authoring: `adr-authoring/SKILL.md`
- Backlog grooming: `backlog-grooming/SKILL.md`
- Risk mitigation planning: `risk-mitigation-planning/SKILL.md`
- Project init: `project-init/SKILL.md`
- Project derive (existing project import): `project-derive/SKILL.md`
- Ad-hoc prompt intake: `ad-hoc-intake/SKILL.md`
- Release verification: `release-verification/SKILL.md`
- Adapter sync: `adapter-sync/SKILL.md`
