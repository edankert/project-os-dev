---
type: "[[task]]"
id: TASK-0183
aliases: ["TASK-0183"]
title: "One migration clears the ledger-field warnings"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0099-Ledger-Field-Warnings-Wait-Ninety-Days]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0099-Ledger-Field-Warnings-Wait-Ninety-Days]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0039-Ledger-Fields-Go-Where-The-Ledger-Holds-Them]]"]
---

# One migration clears the ledger-field warnings

## Definition of Done
- [x] `tools/scripts/migrate-ledger-fields.py` drops the fields ADR-0037 moved into the ledger from acceptance-check notes, only where the ledger holds the same verdict; dry run by default, with a report.
- [x] Tested on a fixture (TST-0039); a dry run on your-trainer reports how many of its 654 findings it would clear (below).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0039: four mutations, all caught).

## Dry run on your-trainer, 2026-09-26

It would clear 236 of the 654 notes completely, and remove some fields from the other 418. What stays, and why:

| Kept | Reason |
|---|---|
| 272 | `automation: partial` (180) or `full` (92), and no automated verdict in a ledger yet |
| 146 | `covered_by` names a test class; ADR-0037 stage 2 moves it to the test's `@Covers` first |
| 60 | `invalidated_by` names an invalidation that predates the ledger and no ledger records |
| 13 | a reason, a date, evidence or a mark the ledger does not hold |

These need a person, or ADR-0037's stage 2, so the tool leaves them. Nothing was written to your-trainer; its session runs `--apply` when it chooses.
