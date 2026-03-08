---
type: instruction
id: INSTR-HANDOFF
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-03-08
tags: [instructions, handoff]
---

# Handoff and recovery

Use this when work may stop unexpectedly or when resuming after an interruption.

Agent coordination (task assignment, parallel execution) is handled by your tool's native orchestration (e.g., Claude Code Agent Teams, Codex parallel agents). This checklist focuses on **project state**, not agent state.

## Before stopping work (handoff checklist)
1. Update `SNAPSHOT.yaml` (items, statuses, relationships).
2. Set/clear `focus` appropriately.
3. Update note frontmatter to match snapshot statuses.
4. Add a brief "Next Actions" note in the most relevant task/issue.

## Recovery checklist
1. Read `SNAPSHOT.yaml` to understand current project state and focus.
2. Run `tools/skills/snapshot-sync/SKILL.md` to reconcile notes vs snapshot.
3. Check `git status` and recent commits for uncommitted or partial work.
4. Review recent changes in `docs/changes/` (if available).
5. Resume the task indicated by `focus.task`, or select the highest-priority `next` or `backlog` item.
