---
type: instruction
id: INSTR-HANDOFF
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
tags: [instructions, handoff]
---

# Handoff and recovery

Use this when multiple agents are collaborating or when work may stop unexpectedly.

## Before stopping work (handoff checklist)
1. Update `SNAPSHOT.yaml` (items, statuses, relationships).
2. Set/clear `focus` appropriately.
3. Update `session.last_heartbeat` and `session.current_step`.
4. If you claimed any items, release or transfer them (`claimed_by`).
5. Add a brief “Next Actions” note in the most relevant task/issue.

## Recovery checklist
1. Run `tools/skills/snapshot-sync/SKILL.md` to reconcile notes vs snapshot.
2. Inspect `session` and `claimed_by` fields in `SNAPSHOT.yaml`.
3. Review recent changes in `docs/changes/` (if available).
4. Resume the most recent task or reassign claimed items.
