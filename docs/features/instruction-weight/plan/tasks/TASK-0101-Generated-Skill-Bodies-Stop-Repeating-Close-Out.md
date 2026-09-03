---
type: "[[task]]"
id: TASK-0101
aliases: ["TASK-0101"]
title: "Generated skill bodies stop repeating the close-out steps"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 4.4"]
parent: "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"
effort: S
depends: []
related: ["[[ADR-0004-Mandatory-Skill-Steps]]"]
tests: []
---

# Generated skill bodies stop repeating the close-out steps

## Definition of Done
- [ ] `generate-adapters.py:140-148` emits a body of the pointer to the canonical playbook plus its "when to use" bullets.
- [ ] The three close-out lines — run the validator, run `--as-committed` before pushing, confirm the run went green — appear in the generated close-out skill and nowhere else.
- [ ] "Execute its checklist exactly" becomes: follow its checklist; where the checklist and the repo disagree, say so and file an `ISS-*` rather than improvising.
- [ ] The generator is re-run and all 25 regenerated `.claude/skills/*/SKILL.md` are committed together.

## Steps
- [ ] Change the template string, re-run, read two or three of the regenerated files to confirm the shape.

## Notes

**Tension with [[ADR-0004-Mandatory-Skill-Steps]], stated rather than resolved silently.** Dropping "exactly" could read as licence to skip a step. It is not meant to: every step still runs, and a step that cannot be followed is reported and filed rather than skipped in silence — which is strictly more auditable than the current wording, under which a blocked agent improvises with no record. If the owner reads it the other way, keep "exactly" and add the file-an-issue clause after it.

Today `inbox-triage` and `ad-hoc-intake` both carry three close-out steps about pushing, and neither pushes anything.
