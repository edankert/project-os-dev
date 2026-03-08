---
type: skill
id: SKILL-PROJECT-INIT
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, init]
---

# Skill: Project init (template → project)

## When to use
- You copied the contents of the template into your repo root and want to initialize it.
- You want `../../../SNAPSHOT.yaml` to stop being a template and reflect your project.
 - If you are initializing an existing project, use `../project-derive/SKILL.md` instead.

## Inputs
- Project name and a short summary.
- Repo-relative entrypoints you want to document as workflows.

## Outputs
- `../../../SNAPSHOT.yaml` initialized for the new project (template marker cleared; clean counters/focus/items).
- Project-specific “REPLACE ME” sections replaced.

## Rules
- Do not create a separate snapshot file: `../../../SNAPSHOT.yaml` is the snapshot file.
- Do not commit or depend on Obsidian user state (`.obsidian/`, `.trash/`) if present (user-specific).
- Prefer updating rules in `../../instructions/*` instead of duplicating them here.

## Checklist
1. Ensure user-specific Obsidian state is not versioned (if you use Obsidian):
   - keep `../../../docs/.obsidian/` and `../../../docs/.trash/` local-only (do not commit)
   - if they appear in version control, remove them from tracking and ignore them going forward
2. Replace template placeholders:
   - search for `REPLACE ME` and replace with your project specifics
   - at minimum update:
     - `../../../docs/ARCHITECTURE.md`
     - `../../../docs/GLOSSARY.md`
     - `../../../docs/workflows/*`
3. Initialize `../../../SNAPSHOT.yaml`:
   - set `template.replace_me: false`
   - set `updated` to “now”
   - set `project.name`, `project.summary`, and `project.repo_root`
   - reset `counters` to the starting allocation:
     - if you have no items yet: set all counters to `0` (and set `CHG.last_date` to `0`)
     - if you imported existing notes: set each counter to the highest existing `TYPE-NNNN`
   - clear `focus`
   - clear `items.*` collections (and any `recent_changes`, if present)
   - set `metrics.counts.*` to zeros (or remove `metrics` entirely until you have data)
   - keep `retention` policy intact (snapshot keeps only active + recent; notes are the archive)
4. Decide what to do with the example notes under `../../../docs/`:
   - recommended: delete/replace them and create your own using:
     - `../feature-scaffold/SKILL.md`
     - `../issue-intake/SKILL.md`
     - `../task-breakdown/SKILL.md`
     - `../workflow-authoring/SKILL.md`
     - `../test-authoring/SKILL.md`
5. Validate the new baseline:
   - run `../snapshot-sync/SKILL.md`
   - ensure `grep -R "REPLACE ME" .` returns nothing (or only intentional examples)
