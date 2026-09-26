---
type: "[[test]]"
id: TST-0033
aliases: ["TST-0033"]
title: "A tag-only walk line prints the check's current words, so rewording the check breaks nothing; the converter changes only what it can without loss"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0175]]"]
scope: system
level: integration
entrypoint: "../project-os/tools/scripts/test-walk-sheet.sh"
command: "bash ../project-os/tools/scripts/test-walk-sheet.sh"
covers: ["[[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It]]"]
tasks: ["[[TASK-0175]]"]
issues: ["[[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 15 new assertions in test-walk-sheet.sh (176 in all). Five mutations in a scratch copy: M1 no expansion of tag-only lines, 9 failures; M2 no pairing of step N with Expect line N, 2; M3 the converter rewrites lossy lines, 3; M4 --refresh takes the wrong line, 1; M5 --refresh never re-quotes, 2. Pristine 176 of 176."
related: ["[[ADR-0049-A-Walk-Step-May-Cite-A-Check-Without-Quoting-It]]"]
---

# A tag-only walk line prints the check's current words, so rewording the check breaks nothing; the converter changes only what it can without loss

## Purpose

ISS-0088: rewording a check broke every walk that quoted it. ADR-0049 lets a line be its tags alone. This test pins down what the sheet, the payload, `--check` and `walk-tags.py` do with that.

## Procedure

The last section of `bash tools/scripts/test-walk-sheet.sh` in `~/Dev/repos/project-os`, on the procedure fixture the rest of that script uses.

- `--check` accepts a tag-only line. The sheet prints the check's words for it with the tag, only the Expect line paired with that step, and not the bare tag line. The payload carries the words, the tag and the owed part.
- Rewording the check breaks a procedure that quotes it (the ISS-0088 case) and does not break the tag-only one, whose sheet prints the new words.
- A check whose steps and Expect lines do not pair prints all its Expect lines for a tag.
- `walk-tags.py --apply` rewrites a line whose tag prints exactly its quote, keeps a line quoting one of several unpaired Expect lines, and the result passes `--check`.
- In a git repo, rewording that unpaired line breaks the quoting line; `walk-tags.py --refresh --apply` re-quotes it from the check's current Expect, and `--check` passes again.

## Expected results

- Exit 0: 176 of 176, 2026-09-26.
