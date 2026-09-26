---
type: "[[test]]"
id: TST-0039
aliases: ["TST-0039"]
title: "migrate-ledger-fields.py drops a moved field only where the ledger holds the same fact, and says why the rest stay"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0183]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-migrate-ledger-fields.sh"
command: "bash ../project-os/tools/scripts/test-migrate-ledger-fields.sh"
covers: ["[[ISS-0099-Ledger-Field-Warnings-Wait-Ninety-Days]]"]
tasks: ["[[TASK-0183]]"]
issues: ["[[ISS-0099-Ledger-Field-Warnings-Wait-Ninety-Days]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 8 assertions. Four mutations in a scratch copy: M1 marks dropped without the ledger, 2 failures; M2 recorded invalidations kept, 2; M3 a dropped field swallows the comment after it, 1 (survived until the fixture had a comment); M4 nothing removed, 4. Pristine 8 of 8."
related: []
---

# migrate-ledger-fields.py drops a moved field only where the ledger holds the same fact, and says why the rest stay

## Purpose

ISS-0099: 654 LEDGER-FIELD warnings in your-trainer, each the same mechanical fix. The migration must never drop a fact the ledger does not hold.

## Procedure

`bash tools/scripts/test-migrate-ledger-fields.sh` in `~/Dev/repos/project-os`, on three acceptance notes and one ledger.

- The dry run counts one note cleared and two partly cleared, says why each kept field stays, and writes nothing.
- A note whose ledger holds everything loses every moved field and keeps the rest of its frontmatter and body.
- An invalidation the ledger records is dropped with its nested lines; a verdict the ledger lacks and a `partial` automation stay.
- A `todo` mark and dead provenance go; a comment and a `covered_by` list stay.
- A second run clears nothing more.

## Expected results

- Exit 0: 8 of 8, 2026-09-26.
