---
type: reference
id: LEDGERS-README
status: active
owner: group:maintainers
created: 2026-09-18
updated: 2026-09-18
tags: [releases, acceptance]
---

# Acceptance ledgers

This folder records the result of each acceptance walk. A result is not written on the test note. It is a dated line in a JSON file here, saying who walked which check, on which platform, with what outcome (ADR-0037). The outcomes and what each one means are in `tools/instructions/TAXONOMY.md`, "Acceptance outcomes (the ledger's vocabulary)".

## The files

| file | what it is |
| --- | --- |
| `WORKING-<platform>.json` | The open ledger, one per platform. Every new result is added here. |
| `REL-####-<platform>.json` | A sealed ledger: the results a release was checked against. It is never edited. |

The platform is the surface a result was earned on. A project that is one application everywhere can use a single `WORKING-app.json`. Add a ledger per operating system only for checks that really differ between them: a check with no result on a platform counts as owed there.

## One file, by example

```json
{
  "platform": "app",
  "entries": [
    {"check": "TST-0001", "mark": "pass", "date": "2026-09-18", "method": "manual", "by": "user:you"},
    {"check": "TST-0002", "mark": "fail", "date": "2026-09-18", "method": "manual", "by": "user:you", "reason": "The save button stays grey after typing a name."}
  ]
}
```

Every outcome except `pass` needs a `reason`. To withdraw a result after the code changes, add an entry with `invalidated_by:` naming the change note, rather than deleting the line.

## What the validator does with them

Once this folder holds a `.json` file:
- each entry is checked for its fields, its date and its outcome word (the `LEDGER-*` codes);
- a test note may no longer carry `mark:` or the other verdict fields that moved here (`LEDGER-FIELD`);
- a finished feature's acceptance checks count as walked when a ledger clears them on at least one platform (`VERIFY-ACCEPTANCE`).

`tools/scripts/walk-sheet.py` reads the same files to list what is still owed for a release.
