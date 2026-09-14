---
type: "[[change]]"
id: CHG-20260914-The-Walk-Reads-As-A-Script
title: "A walk sheet opens with the screens a release changed, and a sitting can be walked from one written script"
status: merged
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[PHASE-0005-The-Walk-Reads-As-A-Script]]", "[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
commit: "project-os c3cdb4c, a0c80e3, 0f1b673"
pr: ""
impacts: ["tools/instructions/TESTING.md", "tools/instructions/TAXONOMY.md", "tools/scripts/walk-sheet.py", "tools/scripts/validate-docs.sh", "docs/__templates__/", "tools/skills/"]
issues: []
features: ["[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]", "[[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]", "[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]"]
---

# A walk sheet reads as a script

## Summary

Two things change for whoever walks a release. The sheet's first section now lists the **app screens** the release changed, each with one sentence a person using the product would understand and a picture of the screen at the last release beside a picture of the build being walked. And a sitting may be walked from **one written procedure** instead of from each check in turn: the setup stated once, numbered steps that name the screen they happen on, and expectation lines that quote the check's own words and say which check step they satisfy.

The walk sheet from PHASE-0004 worked and a real release showed what it lacked. Its survey read the ledger's invalidation events, and an invalidation names a check, never a screen — so the first section named test categories such as "Hardware", which spans five screens, to a person who was about to open screens. A change that altered a screen without reopening a check was invisible. And inside a sitting the sheet printed each check separately: on your-trainer's REL-0017 sheet the same "fake a connected trainer" setup printed four times in one sitting, and the same comparison against a drivable trainer printed in four checks.

## Impact

- No screen changed: this repo tracks the project-os template's development. It ships instructions, templates, skills and scripts, and has no product surface of its own. The screens this work changes are in the repos that use the template, and each of them records its own.

## What changed, for a person using the template

**A surface is a screen by default.** `TAXONOMY.md` states four rules once: a state such as data-only mode is not a surface; a dialog, sheet or panel is a child with `parent:`; a check that walks several screens names their parent; a screen placed differently per platform is still one surface. A surface note carries `gallery:`, the screenshot keys that capture it. The 12 to 15 surface target applies to top-level screens only.

**A change note names the screens it changed.** `change.md`'s `## Impact` is one `[[SUR-####]]` line per screen with one sentence each, or `No screen changed` and why. The change-note and close-out skills ask an LLM to draft it from the diff and the repo's surface notes, then to check every id resolves. This is the one thing the walk adds at close-out, and ADR-0029 rule 8 had refused any such obligation — the measurement is why it was right to add this one: twelve change notes since your-trainer's v2.1.8 tag, four with an Impact section, **none of the four naming a screen**. The survey's only input was recorded nowhere.

`## Acceptance checks reopened` is removed from the template. Nothing reads it now, and why a check was reopened is the `reason:` on the ledger's invalidation event, which the ledger refuses without.

**The survey comes from change notes and pictures.** `walk-sheet.py` finds the last release from the newest released `REL-*` note for the platform, reads its `tag:`, and asks git which change notes were added since. Pictures live at `docs/tests/acceptance/gallery/<tag>/<key>.<ext>` and `.../candidate/<key>.<ext>`. A dialog prints under its parent screen. The survey prints no `TST-` id at all. Where there is no released note, no `tag:`, or no tag in this checkout, it says which and the rest of the sheet still prints.

**A sitting may carry a procedure.** `docs/tests/acceptance/walk/<name>.md`, from the new `procedure.md` template, whose `sitting:` repeats the `### ` heading in `WALK.md` word for word — and nothing in `WALK.md` points back, because a pointer in two files can disagree. `python3 tools/scripts/walk-sheet.py --check [--platform <p>]` refuses a procedure that leaves an owed part uncited, cites one from two steps, names a retired or unknown check, names a step the check does not have, names a check another sitting claims, or misquotes an `## Expect` line. The sheet prints the setup once and only the steps citing something still owed, marking a tag whose check has already passed.

**`validate-docs.sh` runs that check** for every platform with a ledger, quietly. A procedure goes stale when a ledger event lands, and a ledger event is a commit — so pre-commit and CI are where the staleness arrives. Quietly, because the check also reports things that are nobody's mistake, and seven or twelve of those on every commit is how validator output stops being read.

**A new skill, `walk-procedure`,** writes or rewrites a sitting's script and keeps it only when the check passes. `release-prep` and `release-verification` each run the check before a sheet is handed over.

## What a reader should watch for

- **Every change note now owes an `## Impact` list.** A repo's existing notes do not have one, and `walk-sheet.py --check` names each of them. That is a worklist, not a failure; nothing blocks on it.
- **A repo with no procedures behaves exactly as before.** A sitting without one prints per-check rows, and `--check` on a repo with none exits 0 in silence.
- **The generator now runs `git`.** A machine without it, or a checkout that is not a repository, loses the survey and keeps the sheet. A shallow clone is named as such.

## Documentation Coverage (All Types Considered)

- features: updated
- requirements: updated
- tasks: updated
- issues: not-applicable
- tests: updated
- workflows: not-applicable
- decisions: updated
- risks: not-applicable
- changes: new
- snapshot: updated

## Verification

`bash tools/scripts/test-walk-sheet.sh` — 157 assertions over ten fixture repos, two of them real git checkouts, 0 failures. **36 mutations applied to `walk-sheet.py` one at a time, none survived** ([[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]]).

Every other template harness re-run and green: decision-rule 26, retention 23, hooks 74, pause-rule 15, verdict-model 31, word-budgets 3.

Downstream after the sync: project-os-cockpit `pytest tests/test_walk_*.py` 57 passed and `node --test desktop/tests/*.mjs` 146 passed; `test-walk-sheet.sh` 157 assertions in all five synced repos; `validate-docs.sh` OK in all six. `validate-fleet.sh` over thirteen repos is unchanged before and after — the same four pre-existing failures with the same counts, no new error anywhere.

**Same exposure as the rest:** [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]] still stands, and this harness is the eighth. The template's own CI runs none of them, so these numbers come from a developer's machine.

## The independent review

Round one returned `changes-requested` on all three notes and refuted three of REQ-0029's eight criteria. **Eight blocking findings, every one reproduced, every one fixed here with the fixture that would have caught it** — the list is in the review response on FEAT-0031. The sharpest of them was not in the generator: `walk_payload` in project-os-cockpit and `walk-sheet.py` disagreed about the same procedure, which is the failure bundling the module exists to prevent, and neither repo's suite could see it because no cockpit test wrote a procedure file.

Five of the nine non-blocking findings are fixed too. Two are filed at `triage`: [[ISS-0066-An-Expectation-Line-May-Quote-Any-Expect-Line-Of-Its-Check|ISS-0066]] and [[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]].

## Follow-ups

- [ ] your-trainer PHASE-024: the surface mapping Edwin approves (TASK-0900), the `area:` rewrite, where captures live, and the v2.2.0 procedures.
- [ ] project-os-cockpit PHASE-044: the survey as screen cards, each sitting as its procedure, and a tick per step. Its TASK-0622 records what this sync already landed there.
- [ ] The sync manifest globs `tools/scripts/`, so it had been copying `__pycache__/*.pyc` between repos. One tracked `.pyc` was removed from your-trainer and the copies deleted; teaching the manifest to skip them is unowned. File an `ISS-*` if it comes back.
