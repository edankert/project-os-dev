---
type: "[[task]]"
id: TASK-0065
aliases: ["TASK-0065"]
title: "Rewrite the snapshot-sync skill against the generator; move semantic reconciliation to docs-audit"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: S
due: ""
depends: [TASK-0060, TASK-0061]
related: [REQ-0019, ADR-0009]
tests: []
---

# Rewrite snapshot-sync

## Definition of Done

- [ ] `tools/skills/snapshot-sync/SKILL.md` rewritten: reconciling hand-written drift is replaced by running the generator.
- [ ] Anything remaining that is genuinely semantic — notes that contradict each other rather than contradicting the snapshot — is moved to `docs-audit/SKILL.md` or deleted as duplicate.
- [ ] `CLAUDE.md` and the generated adapters no longer advertise a skill for work the tooling now does.
- [ ] Cross-references from `close-out`, `LIFECYCLE.md` and `QUALITY.md` updated.
- [ ] If nothing substantive survives, the skill is **deleted** rather than kept as a stub.

## Steps

- [ ] Audit the 51-line skill: classify each step as *now generated*, *semantic (belongs in docs-audit)*, or *obsolete*.
- [ ] Rewrite or delete accordingly.
- [ ] Update every inbound reference.
- [ ] Regenerate adapters.

## Notes

The skill exists to reconcile the snapshot against the notes. Once the snapshot is generated from the notes, most of it describes a problem that cannot occur.

Resist keeping a stub. A skill that says "run the generator" is a line in `QUALITY.md`, not a playbook, and a thin skill in the listing costs attention from every agent that scans it looking for the right one.

What may genuinely survive: reconciling notes that contradict *each other* — a task claiming a parent that does not list it, two notes claiming one ID. That is `docs-audit` territory ("the semantic consistency the validator cannot check mechanically"), and moving it there is better than keeping a skill alive around it.
