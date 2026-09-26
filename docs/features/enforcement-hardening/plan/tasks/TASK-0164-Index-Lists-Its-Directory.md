---
type: "[[task]]"
id: TASK-0164
aliases: ["TASK-0164"]
title: "An index that lists fewer entries than its directory holds is reported"
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

# An index that lists fewer entries than its directory holds is reported

## Definition of Done
- [x] The validator compares the indexes that list a directory (docs/INDEX.md against tools/instructions/, tools/skills/README.md against tools/skills/) and names each entry missing from the index — INDEX-COVERAGE, with the table in `INDEX_COVERAGE`; a `CLAUDE.md` counts only once it already lists that directory.
- [x] Measured over the fleet first — 38 findings in 13 repos, most seeded by the template's own `docs/INDEX.md` and the CLAUDE.md template in `ADAPTER.md`, both fixed. Warns until 2026-12-24.
- [x] A harness asserts a missing entry is reported and a complete index is not, and a mutation removing the check fails it — TST-0025, D3 (3 failures).
