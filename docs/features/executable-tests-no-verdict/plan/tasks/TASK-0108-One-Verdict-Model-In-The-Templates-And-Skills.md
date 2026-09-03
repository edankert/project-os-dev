---
type: "[[task]]"
id: TASK-0108
aliases: ["TASK-0108"]
title: "One verdict model in the templates and skills; release-verification rewritten"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
parent: "[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"
effort: M
depends: ["[[TASK-0107]]"]
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]"]
tests: []
---

# One verdict model in the templates and skills; release-verification rewritten

## Definition of Done
- [ ] `docs/__templates__/test.md` and `SCHEMAS.md` drop `last_run:` and `exit_code:`, and say a `command:` test records no verdict (STATUSES.md `[[test]]` is the home).
- [ ] `test-authoring/SKILL.md` says the same for automated tests.
- [ ] `release-verification/SKILL.md` steps 3, 4, 6 and 7 describe the one model: a manual test's staleness is `last_verified:`, a `command:` test is settled by CI, an acceptance check by the ledger. ISS-0046 closes on this.
- [ ] `SNAPSHOT.md` drops `last_run` from the test fields.
