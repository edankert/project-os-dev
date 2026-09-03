---
type: "[[task]]"
id: TASK-0100
aliases: ["TASK-0100"]
title: "Template frontmatter comments: one line per field, plus a pointer"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 4.3"]
parent: "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"
effort: S
depends: []
related: ["[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]"]
tests: []
---

# Template frontmatter comments: one line per field, plus a pointer

## Definition of Done
- [ ] `docs/__templates__/feature.md:15-22` is one line on `acceptance_exception` plus a pointer to `SCHEMAS.md`, which already carries the full explanation.
- [ ] `docs/__templates__/test.md:26-33` is one line per acceptance field plus the same pointer.
- [ ] A note scaffolded from either template carries no paragraph of rule text that the author has to decide whether to delete.

## Steps
- [ ] Check that `SCHEMAS.md` really does explain each field before shortening the comment; if it does not, move the text there rather than deleting it.

## Notes

Every scaffolded feature and test inherits these comments unless the agent deletes them, and mostly they are not deleted — so the explanation is copied into the repo once per note, forever.

Overlaps [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]], which removes `tier:` from the same acceptance block in `test.md`. Do the issue first.
