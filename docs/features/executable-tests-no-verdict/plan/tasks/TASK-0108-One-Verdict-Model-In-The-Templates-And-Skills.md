---
type: "[[task]]"
id: TASK-0108
aliases: ["TASK-0108"]
title: "One verdict model in the templates and skills; release-verification rewritten"
status: done
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
- [x] `docs/__templates__/test.md` and `SCHEMAS.md` drop `last_run:` and `exit_code:`, and say a `command:` test records no verdict (STATUSES.md `[[test]]` is the home).
- [x] `test-authoring/SKILL.md` says the same for automated tests.
- [x] `release-verification/SKILL.md` steps 3, 4, 6 and 7 describe the one model: a manual test's staleness is `last_verified:`, a `command:` test is settled by CI, an acceptance check by the ledger. ISS-0046 closes on this.
- [x] `SNAPSHOT.md` drops `last_run` from the test fields.

## Notes

Landed as template commit `87b64cf` on 2026-09-03; ISS-0046 fixed by the release-verification rewrite (steps 3, 4, 6, 7, the matrix and the final gate).
