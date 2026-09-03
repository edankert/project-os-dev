---
type: "[[task]]"
id: TASK-0099
aliases: ["TASK-0099"]
title: "The same pass over STATUSES, TESTING, QUALITY and DECISIONS"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 4.1"]
parent: "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"
effort: L
depends: ["[[TASK-0098]]"]
related: ["[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]"]
tests: []
---

# The same pass over STATUSES, TESTING, QUALITY and DECISIONS

## Definition of Done
- [ ] Each of the four files states each rule as a normative sentence, one line of reason, and a link.
- [ ] The retired `[[check]]` section and the ISS-0006 preamble story leave STATUSES.md; the ISS-0196 italic paragraph leaves QUALITY.md; the census dates and the DECISION-RULE landing narrative leave DECISIONS.md; the "54 rows carried a hand-written RE-RUN annotation" passage leaves TESTING.md.
- [ ] Each moved passage lands in an ADR Context section or a change note, and appears in the moved-text table.
- [ ] One commit per file.
- [ ] The mannered phrasing named in [[TASK-0096]] is gone from these four files.

## Steps
- [ ] STATUSES.md first: it is the largest and holds the clearest removals.
- [ ] Re-run the generator after the last one and commit the regenerated Cursor rules.

## Notes

Two coordination points. [[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]] deletes a QUALITY.md paragraph, and [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]] moves the `kind` heading in TAXONOMY.md; fix both issues before this pass, so this task is not re-deleting text or preserving text that should have gone.

No budget is set for these four. The requirement counts only the always-loaded file, and whether the others get numbers is the open question in the plan.
