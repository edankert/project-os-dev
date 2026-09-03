---
type: instruction
id: INSTR-HANDOFF
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-09-03
tags: [instructions, handoff]
---

# Handoff and recovery

Use this when work may stop unexpectedly or another agent/session picks it up.

The durable handoff surface is the snapshot plus the notes; anything a successor needs must be written there. The snapshot holds no coordination state (`SNAPSHOT.md`, "Team model").

## Before stopping work (handoff checklist)
1. Update `SNAPSHOT.yaml`'s curated fields (membership, relationships); statuses and metrics are derived (`LIFECYCLE.md`, "Mandatory Automated Documentation").
2. Set/clear `focus` appropriately — an empty `focus` means "no work in flight", so leave it set only if work genuinely continues.
3. Record what is in flight in the active task/issue note: what was done, what is next, and any blocker (a brief "Next Actions" section).
4. Ensure uncommitted work is described somewhere durable (task note or `CHG-*`), since the working tree is not part of the handoff surface.
5. Record the approaches you tried and set aside, each with the reason it was closed, in the task note's `## Notes` section. Reason: a successor who inherits only the position re-explores every closed path.
6. Record constraints and user decisions in the user's exact words, in the same section or in the decision callout `DECISIONS.md` describes. Reason: a paraphrase is where a constraint quietly loosens.

## Recovery checklist
1. Read `SNAPSHOT.yaml`: `focus`, item statuses, and `updated`.
2. Run `tools/skills/snapshot-sync/SKILL.md` to reconcile notes vs snapshot, then `bash tools/scripts/validate-docs.sh` to find drift mechanically.
3. Inspect the working tree (`git status`, `git log`) and recent `docs/changes/` notes to see what actually landed.
4. Resume from the focused item's "Next Actions", or pick the next item by status if `focus` is empty.
