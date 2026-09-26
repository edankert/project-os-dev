---
type: "[[task]]"
id: TASK-0163
aliases: ["TASK-0163"]
title: "A misspelt frontmatter key is reported, and the cockpit's validator is checked for the parse hole"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["Edwin, 2026-09-25: 'Complete and test PHASE-0003 fully'"]
parent: "[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"
effort: M
due: ""
depends: []
blocks: []
related: []
tests: ["[[TST-0025]]"]
---

# A misspelt frontmatter key is reported, and the cockpit's validator is checked for the parse hole

## Definition of Done
- [x] A top-level frontmatter key that is not a known key but is one or two letters from one (`elated:` for `related:`) is reported, naming the key it was probably meant to be — FRONTMATTER-TYPO, limited to fields that carry links (`RELATIONSHIP_FIELDS` and `related`), with singular and plural forms excused.
- [x] Measured over every fleet repo before it ships — 8,668 notes on 2026-09-25. Flagging unknown keys near any known key gave about 50 findings, nearly all legitimate project fields (`feature`, `review_note`, `decisions`); near any link field, `created` matched `related` in every note. With known template keys excluded, 0 findings, and `elated:` still caught. So it ships as an error.
- [x] The cockpit's own validator is checked for the unparseable-frontmatter hole — all three copies carry NOTE-FRONTMATTER (the check was ported from there), and ISS-0053's repro on a copy of this repo is reported by both the cockpit's validator and the template's. Recorded on ISS-0053.
- [x] A harness asserts the typo is caught, an unrelated project-specific key is not, and a mutation removing the check fails it — TST-0025, D1 and D2.

## Notes
ISS-0053's first Next Action is already met: `NOTE-FRONTMATTER` (template, 2026-09-18) parses every note's frontmatter with PyYAML and names the file. This task is the other two.
