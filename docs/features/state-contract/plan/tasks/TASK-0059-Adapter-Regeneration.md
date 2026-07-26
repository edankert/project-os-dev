---
type: "[[task]]"
id: TASK-0059
aliases: ["TASK-0059"]
title: "Regenerate adapters and verify no tool-facing surface embeds a copy of the state rules"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0014-Single-State-Contract]]"
effort: S
due: ""
depends: [TASK-0058]
blocks: []
related: [REQ-0018, REQ-0002]
tests: []
---

# Adapter regeneration

## Definition of Done

- [ ] `generate-adapters.py` run; CLAUDE.md, AGENTS.md and generated skills reference the contract rather than embedding it.
- [ ] `generate-adapters.py --check` clean.
- [ ] Audit confirms no adapter or generated skill restates a status value, gate, or transition rule.
- [ ] The corrected rules are synced to all 10 fleet repos via `sync-project-os.sh`.
- [ ] [[REQ-0002-Native-Instruction-Format|REQ-0002]] is respected: adapters still deliver rules in each tool's native format — the change is that they point at the contract instead of duplicating it.

## Steps

- [ ] Run `adapter-sync` (`tools/skills/adapter-sync/SKILL.md`) after TASK-0058 lands.
- [ ] Audit generated output for embedded state rules.
- [ ] Sync to the fleet; confirm each repo validates clean afterwards.

## Notes

Adapters are the highest-risk place for a copy to survive, because they are *generated* — a template that embeds the rules will faithfully reproduce them into 10 repos on every sync, and the copies will look authoritative to every agent that reads them. If the generator embeds rather than references, the fix belongs in the generator template, not in its output.

**Watch the `updated:` blast radius.** A fleet sync touches many notes at once, which per [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] re-arms the ADR-0007 gate on each one. Confirm ISS-0007 is resolved before syncing, or this routine step converts warnings into build failures across the fleet.
