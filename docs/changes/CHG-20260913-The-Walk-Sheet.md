---
type: "[[change]]"
id: CHG-20260913-The-Walk-Sheet
aliases: ["CHG-20260913-The-Walk-Sheet"]
title: "A release is walked from a generated sheet: the changed screens first, then every owed check in the project's own order"
status: merged
owner: user:edwin
created: 2026-09-13
updated: "2026-09-13"
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "Edwin, 2026-09-13, asking what to do in what order to satisfy the outstanding acceptance checks, and noting that nothing tells him to look at the changed screens"]
commit: ""
pr: ""
impacts: ["tools/scripts/walk-sheet.py", "tools/scripts/test-walk-sheet.sh", "tools/instructions/TESTING.md", "docs/__templates__/walk.md", "docs/__templates__/test.md", "docs/__templates__/task.md", "docs/__templates__/change.md", "docs/__templates__/release.md", "docs/__templates__/SCHEMAS.md", "docs/GLOSSARY.md", "docs/tests/README.md", "tools/skills/release-prep/SKILL.md", "tools/skills/release-verification/SKILL.md", "tools/skills/close-out/SKILL.md", "tools/skills/test-authoring/SKILL.md"]
issues: ["[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]", "[[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]]"]
features: ["[[FEAT-0029-The-Walk-Sheet]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""   # a change note owes no review (ADR-0019)
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[PHASE-0004-The-Walk]]", "[[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]"]
---

# A release is walked from a generated sheet

## Summary

The person walking a release now runs one command and reads one document. `python3 tools/scripts/walk-sheet.py --release REL-#### --platform <platform>` prints the screens the release changed, then every acceptance check the platform still owes, grouped into sittings in the order the project authored, with each check's setup, steps and expected result on the page. Before this, a release handed them a list of owed checks in id order, and the order, the bench list and the "look at this screen first" were written by hand each time and thrown away.

## Impact

**What changes for a person preparing a release.** `release-prep` step 2 generates the sheet instead of listing blockers, one per platform, and reports the owed and sitting counts. `release-verification` step 7 says to walk the sheet in its order, sitting by sitting, and to record every verdict as a ledger event; the instruction to write `status: passing` and `last_verified:` onto an acceptance note is gone, which is [[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand|ISS-0046]]. The release test matrix gains a **Sitting** column filled from the sheet, so the matrix and the sheet agree on order rather than offering two.

**What changes for a person closing out work.** One step, and it asks nothing when nothing was reopened: if the work changed a surface an acceptance check asserts against, record an invalidation event in the working ledger naming the change. That event is what the survey reads. `## Acceptance checks reopened` on the task or change note is optional prose beside it, now offered as a commented-out section in both templates.

**What changes for a person writing a check.** A new acceptance check is born with four headings — Setup, Steps, Expect, Not this check — because a sheet row prints the first three. A check missing Setup prints "Setup: not stated" on every sheet until somebody writes one, so the sheet is the worklist for bringing an old corpus to that shape. An optional `after:` names the check that should pass first; it orders the sheet and gates nothing.

**What a project authors once.** `docs/tests/acceptance/WALK.md`, from the new `docs/__templates__/walk.md`. One `###` heading per sitting with a fenced `yaml` block naming the surfaces it claims, the state it needs and what must be on the bench. A project with no WALK.md still gets a sheet — one sitting per `area:` — and is told on the sheet that its order is nobody's.

**Where the rules live.** `tools/instructions/TESTING.md`, "The walk", eight numbered rules. Everything else links to it: the template, the schema entry, the generator's docstring and `--help`, four skills, and the cockpit's page.

## What it deliberately is not

No second list of what a release owes: the rows are the ledger's owed set and nothing else contributes one. No schedule: a sheet counts rows and prints no minutes, because the previous attempt at ordering a walk read setup cost out of prose and got six false positives out of six. No new close-out obligation beyond the invalidation event the ledger already refused to take without a change id. No verdict on the sheet: it is generated, never edited, and nothing reads it back.

## Evidence

- `bash tools/scripts/test-walk-sheet.sh` — **80 assertions, 0 failures**, over four fixture repos: the walk, the ledger's resolution layer, the note and WALK.md shapes a real corpus has, and the four refusals. It is [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]], whose `adequacy:` lists twenty-eight mutations and the one known survivor.
- The owed predicate was checked against the other implementation rather than asserted: over your-trainer's live 649-note corpus, `ledger.owed()` from project-os-cockpit and this generator returned identical sets on both platforms, 61 on android and 545 on ios, with zero differences in the resolved verdicts.
- Generated in anger, and it paid: your-trainer's REL-0017 android sheet is **39 owed rows**, survey first. Reading it caught two defects the 32-assertion harness had passed — every row link was an absolute filesystem path, and most rows printed no procedure at all — 53 of 61 as it then stood — because the pre-ADR-0027 corpus keeps it in an unheaded paragraph the two named fallbacks do not cover. Both fixed, and both now asserted.
- Synced into the four repos that keep an acceptance suite. `validate-fleet.sh` is byte-identical before and after across all 13 repos.

## What the independent review changed

The gate ran two rounds (ADR-0028). Round one returned `changes-requested` with ten reproduced findings, and six were real defects in the generator:

- an invalidation naming a **change** note produced a survey entry with no id, no title and nothing quoted — the id pattern matched only three or four digits, and the validator's note index deliberately excludes `CHG-*`, so a second index over `docs/changes/` was needed;
- `resolve()` and the cockpit's `ledger.owed()` disagreed on a ledger whose `sealed:` and `release:` fields disagreed, because one keyed the sort and the other the expiry;
- a mistyped `--platform` printed a confident sheet of every check in the repo rather than refusing;
- a block-style YAML list in WALK.md vanished with no warning;
- the unheaded-prose fallback took the first prose in the file, so an HTML comment above a title became the row's steps;
- `--release` was a label nothing read, so a sheet could name an already-sealed release without saying so.

Two findings were documentation and became amendments rather than fixes: rule 5 now states all three heading fallbacks, and rule 8 now says the *generator* writes no duration while text quoted from a note prints verbatim — a real sheet carries three, all of them a check author's own words. REQ-0028's `## Amendments` records the matching criteria changes. Two were filed rather than fixed, [[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect|ISS-0064]] and [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]], which is the severity bar working rather than an oversight.

The sharpest finding was about the harness, not the code: its fixture had one open ledger and no sealed one, so the whole excuse-expiry layer was unexercised and the reviewer mutated all of it unnoticed. The suite is now 73 assertions over four fixture repos. Round two approved, and found one more gap in the harness rather than the code: the fixture pinned the order of two sealed ledgers but not the boundary between sealed and open, and reversing that boundary dropped 35 of your-trainer's 61 owed rows in silence. Closed the same day with one more fixture row; no generator code changed, so no third round was owed.

## Two more defects, found downstream after the review closed

The cockpit built its walk page against this generator the same day and filed two findings, both precise, both owned here, and both fixed before this landed.

**A retired check was still being asked** (project-os-cockpit ISS-0303). `load_checks` read `type:` and `level:` and never `status:`, so a check at `retired` — kept as the record that a behaviour was once walked, and no longer asked — appeared on the sheet. It is the single largest correction in this work: your-trainer keeps **217 retired acceptance checks**, and its owed count for REL-0017 android goes from 61 to **39**. The cockpit's page was already right, because it passes its own suite in; the two now load the same 431 notes and agree on 39 owed for android and 327 for ios, and on 3 for the cockpit's own corpus.

The fix had to be narrower than the issue suggested. Adding `superseded` beside `retired` looked harmless and introduced a *second* disagreement — one fewer owed row here than the page — because `acceptance._is_retired` matches `retired` alone and `superseded` is not a legal status for a `[[test]]`. One disagreement fixed by introducing another is not a fix, so the filter reproduces their predicate exactly.

**A comma inside a quoted walk-order entry split it in two** (project-os-cockpit ISS-0304). `_inline_list` split on every comma and stripped quotes afterwards, so the quotes protected nothing: `bench: ["A second device on the same Wi-Fi, for the tablet row"]` printed two items, the second of which is an instruction to fetch nothing. `bench:` is the field people write as sentences, which is where it showed. The split now respects quotes.

Both were found by pointing a second implementation at the same corpus, which is the thing bundling was decided for. Neither the independent review nor the harness caught either; both are now asserted, and ISS-0063's own measurement was corrected as a consequence — the 649-against-431 it reported was these 217 retired checks, not the directory scoping it blamed.

## Documentation Coverage (All Types Considered)

- features: updated ([[FEAT-0029-The-Walk-Sheet]] done)
- requirements: updated ([[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]] implemented, three criteria amended with rationale)
- tasks: updated (TASK-0110 to TASK-0115 done)
- issues: new ([[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]], [[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect]], [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]); [[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand|ISS-0046]] addressed by the step-7 rewrite
- tests: new ([[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]])
- workflows: not-applicable
- decisions: updated ([[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]] accepted, four acceptance boxes ticked)
- risks: not-applicable — no new dependency, environment variable, directory, long-running step or credential; the one hazard, a second implementation of the owed predicate, is removed by the cockpit bundling this module
- changes: new (this note)
- snapshot: updated

## Follow-ups

- [ ] [[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently|ISS-0063]]: decide whether an acceptance check may live outside `docs/tests/acceptance/`, and make both readers cite one rule.
- [ ] your-trainer FEAT-0119 authors its WALK.md and retires the 719-line run plan; the starting figure, 39 owed rows in 13 area groups, is recorded there.
- [ ] project-os-cockpit FEAT-0149 builds the page and bundles this module.
- [ ] `sync-project-os.py` copies gitignored files, so a stray `__pycache__` would ship `.pyc` files to every consumer. Deleted by hand in the template. project-os-dev additionally *tracks* one, `tools/scripts/__pycache__/validate-docs.cpython-313.pyc`, with no `__pycache__` line in its `.gitignore`; left alone here.
