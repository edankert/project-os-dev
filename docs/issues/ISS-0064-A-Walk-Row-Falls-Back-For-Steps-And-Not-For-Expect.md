---
type: "[[issue]]"
id: ISS-0064
aliases: ["ISS-0064"]
title: "35 of 39 owed rows on a real walk sheet say the note states no expected result, and for some of them the note does state one under a heading nobody anticipated"
status: fixed
owner: user:edwin
created: 2026-09-13
updated: 2026-09-18
source: ["Independent review of FEAT-0029, 2026-09-13, finding F3"]
severity: medium
component: tooling
related: ["[[FEAT-0029-The-Walk-Sheet]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]"]
tests: []
---

# A row falls back for Steps and not for Expect

## Problem

A walk sheet row prints what a check expects, or says the note states none. On your-trainer's REL-0017 android sheet, **35 of 39 rows say none**. For most of those the note genuinely never said what should happen, which is ADR-0027's measured finding and a worklist entry working exactly as intended. For some of them it is not: the note does say what to expect, under a heading the generator does not look for. The reviewer counted "What a failure looks like" on eight notes and "What a rider still judges" on four, over the 61-row sheet that predates the retired-check fix; that count has not been re-taken on the 39 rows, and taking it is the first action below.

The asymmetry is the thing to decide. Steps gained two fallbacks, `## Procedure` and then the note's unheaded description, because 31 of the 39 rows would otherwise have printed nothing at all. Expect got one fallback, `## Expected results`, and no prose fallback. That was deliberate — a check that never said what should happen has nothing to fall back to — but it was decided without measuring, and the measurement says some of the empty rows are a naming mismatch rather than a missing assertion.

## Evidence

- `cd ~/Dev/repos/your-trainer && python3 tools/scripts/walk-sheet.py --release REL-0017 --platform android | grep -c '_The note states no expected result._'` → `35`, against 39 rows, measured 2026-09-13 after the retired-check fix. The figures the independent review reported, 57 of 61, were taken before it and counted 22 retired checks the sheet should never have printed.
- The two headings, counted by the reviewer over the pre-fix 61-row sheet: "What a failure looks like" ×8, "What a rider still judges" ×4.

## Expected

A row shows what the check expects whenever the note says it.

## Actual

It shows "the note states no expected result" whenever the note says it under a heading other than `## Expect` or `## Expected results`.

## Next Actions

- [ ] Re-count the two headings over the 39 owed rows; the reviewer's figure predates the retired-check fix.
- [ ] Decide whether the fix belongs in the template or in the corpus. A per-repo list of extra Expect headings puts product vocabulary into a template that should not know it; rewriting those twelve notes on contact is ADR-0027's own rule and costs nothing to the template.
- [ ] If neither, say so in `TESTING.md` rule 5 so the asymmetry is stated rather than discovered.

## Checked against the template, 2026-09-18: already fixed

Later work fixed this and the note was never updated. TESTING.md rule 5 now states the asymmetry this note asked for. `walk-sheet.py --release REL-0017 --platform android` in your-trainer prints 39 owed rows, none of them "states no expected result". Notes with older headings are rewritten when next walked (ADR-0027).

Checked as part of FEAT-0036 (TASK-0140).
