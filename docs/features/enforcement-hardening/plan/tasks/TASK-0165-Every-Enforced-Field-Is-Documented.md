---
type: "[[task]]"
id: TASK-0165
aliases: ["TASK-0165"]
title: "Every frontmatter field the validator reads is documented in SCHEMAS.md"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["Edwin, 2026-09-25: 'Complete and test PHASE-0003 fully'"]
parent: "[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]"
effort: M
due: ""
depends: []
blocks: []
related: []
tests: ["[[TST-0025]]"]
---

# Every frontmatter field the validator reads is documented in SCHEMAS.md

## Definition of Done
- [x] The set of frontmatter keys the validator reads is derived from its source, not maintained by hand — `frontmatter_fields_read()` walks the validator's syntax tree: 55 fields.
- [x] Each one missing from `docs/__templates__/SCHEMAS.md` is reported; the known gaps are documented so the template passes — FIELD-UNDOCUMENTED. Nine were missing: `asset`, `fixes`, `ledgers`, `mitigation_tasks`, `phases`, `preparing`, `verification_waiver`, `waiver_expires`, `workflows`; all nine are now in SCHEMAS.md. Warns until 2026-12-24, because every other repo keeps an older SCHEMAS.md.
- [x] A harness asserts an undocumented key is reported, and a mutation removing the check fails it — TST-0025, D4.
