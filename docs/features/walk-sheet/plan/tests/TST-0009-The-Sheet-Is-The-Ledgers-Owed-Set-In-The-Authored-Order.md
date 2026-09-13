---
type: "[[test]]"
id: TST-0009
aliases: ["TST-0009"]
title: "The walk sheet is the ledger's owed set, in WALK.md's order, with every row walkable on the page"
status: active
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[TASK-0113-The-Generator-And-Its-Fixture-Test]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-walk-sheet.sh"
command: "bash ../project-os/tools/scripts/test-walk-sheet.sh"
covers: ["[[FEAT-0029-The-Walk-Sheet]]"]
requirements: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]"]
features: ["[[FEAT-0029-The-Walk-Sheet]]"]
tasks: ["[[TASK-0113-The-Generator-And-Its-Fixture-Test]]"]
artifacts: []
adequacy: "Twenty-eight mutations against the 80-assertion harness, 2026-09-13, over two rounds of independent review and two defects found downstream. The suite runs four fixture repos: the walk, the ledger's resolution layer (three sealed ledgers and one open one), the note and WALK.md shapes a real corpus has, and four refusals. Caught, with failure counts: an invalidation stopped from reopening a check (20); an invalidation clearing only the transient layer (20); excused added to PERSISTS so an excuse never expires (2); a non-persisting mark in a sealed ledger made transient (4); the open ledger resolved before the sealed ones (2); the whole ledger sort reversed (2); the seal-date ordering dropped so filename order decides (2); expiry keyed on `release` instead of `sealed` (2); the automated-section exclusion removed (3); sittings sorted by name (2); after: edges dropped (1); the after: cycle fallback made to drop its rows (2); the Procedure fallback deleted (1); the Expected-results fallback deleted (1); the unheaded-prose fallback removed (2); that fallback allowed to run past the next heading (1); the row link reverted to an absolute path (2); the id pattern narrowed back to four digits (2); the change-note index removed (2); SUR-* resolution disabled (3); sitting-claiming by SUR-* id removed (2); section() made to stop skipping fenced blocks (2); the WALK.md comment stripper removed (4); the malformed-ledger-filename refusal turned into a skip (1); date validation removed (1); has_ledger relaxed to a directory test (1); the no-WALK.md area fallback collapsed to one sitting (1); the retired-check filter removed (2); `superseded` added beside `retired`, which is a disagreement with acceptance._is_retired rather than a fix (1); the quote-aware list split reverted to a naive comma split (2). ONE survivor, and it is unobservable rather than untested: misrouting the regression branch changes no sheet, because feature and regression are both manual sections and a row does not say which it is. Said in the code at Check.section. One near-equivalent mutant is worth naming so nobody re-derives it: replacing the invalidation branch's condition with False, rather than deleting its body, lets the event fall through into the transient layer where its empty mark still fails to clear, so most checks stay owed and the harness rightly reports nothing. The strongest evidence is not in the harness: ledger.owed() from project-os-cockpit and this generator's resolve() were run over your-trainer's live 649-check corpus on both platforms and agreed on every check, with zero differences in the resolved verdicts."
reviewed_by: "model:claude-opus-5"
review_date: 2026-09-13
review_verdict: approved
related: ["[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]"]
---

# The sheet is the ledger's owed set, in the authored order

## Purpose

[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once|ADR-0029]] makes claims a harness can settle: a row appears if and only if the ledger still owes that check, the sittings follow WALK.md's file order, a check joins the first sitting that claims it, `after:` beats id inside a sitting, a check with no Setup heading says so, and no sheet carries a duration. This note executes all of them.

## Procedure

`bash ../project-os/tools/scripts/test-walk-sheet.sh`, four fixture repos under a tempdir. The first has ten acceptance checks across three areas, one working ledger and a WALK.md with two sittings; the others are described below. 80 assertions:

1. **Rows.** The `command:` check, the passed check and the excused check are absent; the invalidated and never-walked checks are present; the header counts rows and sittings and names ISS-0060 (1 to 7).
2. **Survey.** It names the invalidated check's surface, the task that reopened it with that task's title, the quoted `## Acceptance checks reopened` section and WALK.md's gallery command, and it leaves out a surface nobody invalidated (8 to 12).
3. **Order.** Sittings render in file order against an alphabetical ordering that would reverse them; a check with `after:` renders after its prerequisite against id order; a check named by id joins that sitting rather than its own area's later one (13 to 15).
4. **Labels.** An unclaimed area's check lands under "Unplaced"; a check with no Setup heading prints "Setup: not stated"; a check with one prints it; steps, expected results, the tick box, the sitting's state and its bench all render (16 to 24).
5. **No schedule.** The whole sheet is scanned for a duration and carries none (25).
5b. **The shapes a real corpus has.** A check whose procedure is an unheaded paragraph under its title prints that prose under "Steps: no heading", stopping at the next heading; a check with nothing under its title says the note states no steps; a check still on `Procedure`/`Expected results` prints both; an HTML comment above a title is not read as the steps; a fenced block inside a section does not end it; every row link is repo-relative and none is absolute.
5c. **The ledger's resolution layer**, on a second fixture with three sealed ledgers and one open one: an excuse in the open ledger does not destroy the pass beneath it; an excuse expires when its ledger seals; a non-persisting mark in a sealed ledger expires and leaves the pass under it; a pass in a later-sealed ledger overtakes an invalidation in an earlier-sealed one, with the two ledgers named so that filename order contradicts seal order; an invalidation in the open ledger reopens a pass from a sealed one, which is the boundary between sealed and open; sealing is read from `sealed:` and not from `release:`.
5d. **The survey's harder joins**, on a third fixture: an invalidation naming a change note resolves by full id and by canonical id, with the note's title and its quoted reopened section; a `SUR-*` note labels its surface; a sitting claims by `SUR-*` id; a trailing comment is stripped from both a `state:` and a `surfaces:`; a block-style list and a sitting claiming nothing are both reported; a cycle in `after:` is reported and drops no row.
5d2. **Statuses and quoted text**: a check at `retired` is kept and no longer asked; a check at a status the sheet does not filter is still asked, so the filter matches `acceptance._is_retired` rather than widening past it; a comma inside a quoted `bench:` entry does not split it.
5e. **The four refusals**, on a fourth fixture: an empty `ledgers/` directory, an unknown platform, a ledger filename naming no platform, and a date-shaped string that is not a date.
6. **Fallbacks.** A repo with no WALK.md still gets every owed row, grouped by area and labelled as unauthored; `--out` writes the file.

## Expected results

- Exit 0, `test-walk-sheet: 80 assertions, 0 failure(s)`.

## Evidence (fill after running)

- 2026-09-13, template repo at the FEAT-0029 landing: 80 assertions, 0 failures, after both rounds of the independent review and the two defects the cockpit found.

## Adequacy (who verifies this test?)

See `adequacy:` above: twenty-eight mutations, one known survivor, and it is unobservable on a sheet rather than untested. Plus the cross-implementation agreement with the cockpit's `ledger.owed()` over a live 649-check corpus.

The suite's history is the honest part. At 32 assertions it passed while two real defects were live, both found by reading a generated sheet. At 38 it passed while an independent review mutated the entire ledger-expiry layer unnoticed, because the fixture had no sealed ledger at all. At 72 it passed while the reviewer reversed the boundary between sealed and open ledgers, dropping 35 of your-trainer's 61 owed rows in silence, because every invalidation in the fixture sat in the earliest sealed ledger and nothing pinned that edge. At 73 it passed while the cockpit, pointing its own implementation at the same corpus, found that the sheet was still asking 217 retired checks on your-trainer and splitting a quoted bench sentence in two. All four gaps are closed and the lesson is not: a fixture asserts what its author thought to put in it, and the corpus and the adversary are where the rest lives.

## Independent review, 2026-09-13 (model:claude-opus-5, clean context)

Verdict `changes-requested`, on the guarding judgment. The eight recorded mutations were re-run and every count reproduced exactly (A 3, B 2, C 1, D 10, E 1 in a clean form rather than the recorded 27, F 2, G 2, H 1); the tree was restored byte-identical each time and the pristine suite returned 38 of 38 (`walk-sheet.py` sha1 `8f6be72f`). The record is honest.

**The suite's blind spot is a region, not a list.** A further 22 mutations were run against the 38-assertion harness and **12 survived it untouched**. The largest block of survivors is the sealed-ledger layer, which the fixture never builds: the fixture has one `WORKING-testbed.json` and no sealed ledger, so `PERSISTS`, the `elif not event.release` branch and the ledger sort order are all unexercised. Mutations that pass 38 of 38: `PERSISTS` widened to include `excused` (so an excuse never expires at the seal — the property project-os-cockpit's `ledger.py` calls "the sharpest single property" of its ADR-0037 decision 7, and which an earlier independent review had to find by hand); a sealed ledger's non-persisting marks treated as transient; and the two-ledger sort reversed so the working ledger resolves first.

Other surviving mutations, each a behaviour some note claims: the `Procedure` / `Expected results` fallbacks deleted (claimed in TASK-0113's Notes and in REQ-0028 criterion 4's evidence); `SUR-*` surface resolution disabled, and sitting-claiming by `SUR-*` id removed (REQ-0028 criterion 2 says "`area:`, `SUR-*` where present" — no fixture note is a surface note); `section()` no longer skipping fenced blocks; the malformed-ledger-filename refusal turned into a skip; `_usable_date` made to accept anything; `has_ledger` relaxed to a directory test; the `after:` cycle path made to drop the cycling rows; the `regression` branch of the section predicate misrouted to `automated`; the WALK.md comment stripper removed. The three defensive refusals in that list are each a defect a previous independent review found in the cockpit and whose fix this generator copied — it copied the fix and not the test.

Two of the fixture's own shapes also go unasserted: `--out` is only checked for a non-empty file, so a renderer that wrote garbage to it would pass, and the "claims nothing" warning for a sitting naming neither `surfaces` nor `checks` is never triggered.

The note's own text is now behind the harness in two places: the Procedure section says "eight acceptance checks" where the fixture builds nine, and `adequacy:` opens "Eight mutations ... against the pristine 32-assertion harness" while three of the eight were run against 38.

**Round two, 2026-09-13 — `approved`, with one residual named below.** The whole round-one battery was re-run against the 72-assertion harness at `walk-sheet.py` sha1 `80370fcb`.

First, a correction to round one: the survivor count was **15, not 12**. The list in the paragraphs above is right; the number was not. Of those fifteen, **thirteen are now caught**, at 1 to 5 failures each — including the entire sealed-ledger layer that was the largest single gap (`PERSISTS` widened to include `excused`, 2 failures; sealed non-persisting marks made transient, 4), the `Procedure`/`Expected results` fallbacks (2), `SUR-*` resolution and `SUR-*` sitting-claiming (5 and 4), `section()` fence-skipping (2), all three defensive refusals (1 each), the `after:` cycle path (2) and the WALK.md comment stripper (4). The four-repo fixture is what made that possible.

**Two survive, not one, and `adequacy:` above should be corrected to say so.** That field lists "the two-ledger sort reversed (2)" among the caught mutations and then claims ONE known survivor. Both halves of the sort key were tested separately here, and they do not behave alike. `ledgers.sort(key=(not sealed, sealed))` has two components: reversing the second — sealed ledgers by descending seal date — **is** caught, at exactly the 2 failures recorded, so that is the mutation the field describes. Reversing the first, so the open ledger resolves *before* the sealed ones, returns **72 of 72, 0 failures**. On your-trainer's live corpus that same edit takes the sheet from **61 owed rows to 26**: the open ledger's 44 invalidations are applied before the sealed ledger's 599 passes, so those passes survive on top and thirty-five owed rows disappear silently. That is what the Conformance clause exists to catch, so the survivor count is two and the second one is the consequential one.

The gap is narrow and nameable. The `LAYERS` fixture holds three sealed ledgers and one open one, but its only invalidation sits in the *earliest sealed* ledger (REL-0040, 2026-07-03), so nothing pins the sealed-before-open boundary — which is exactly your-trainer's real shape, 44 invalidations in `WORKING-android` against 599 passes in `REL-0016-android`. One open-ledger invalidation over a sealed pass would close it. Worth an `ISS-*` at `triage` rather than a third round: the shipped code is correct and no sheet is wrong today.

The second survivor is benign. Making the no-WALK.md fallback drop all but the first `area:` passes 72 of 72, but on your-trainer it leaves the owed count at **61 rows** and only collapses 16 sittings into 2 — it regroups and loses nothing, which puts it in the same class as the regression/feature label swap the author documented at `Check.section` rather than asserted. That swap was confirmed here to change no sheet (0 failures, as claimed); the sharper version that misroutes a regression check to `automated` and drops it from the sheet *is* caught (1 failure).

**Round two, 2026-09-13 — `approved`**, transcribed from the reviewer's report. Verification only, against `walk-sheet.py` sha1 `80370fcb` and the 72-assertion harness. On the guarding judgment it corrected its own round-one figure — **fifteen survivors, not twelve** — and found **thirteen of the fifteen now caught**, at one to five failures each, "including the whole sealed-ledger layer, both heading fallbacks, `SUR-*` resolution and claiming, fence-skipping, all three defensive refusals, the cycle path and the comment stripper. The four-repo fixture did that."

It named two survivors where `adequacy:` claimed one, and it was right. The ledger sort key has two components: reversing the second, the seal-date ordering of sealed ledgers, was caught at two failures and is the mutation the field described. Reversing the first, so the open ledger resolves before the sealed ones, passed 72 of 72 while your-trainer's real sheet went from 61 owed rows to 26 — thirty-five rows vanishing in silence, because the open ledger's 44 invalidations were applied before the sealed ledgers' 599 passes. The fixture's only invalidation sat in the earliest *sealed* ledger, so nothing pinned the boundary that matters on the corpus. The second survivor is benign: collapsing the no-WALK.md area fallback keeps all 61 rows and regroups 16 sittings into two.

**Closed rather than filed, the same day.** TST-0108 is passed in a sealed ledger and invalidated in the open one, which holds that boundary, and the two sealed ledgers are now named so that filename order contradicts seal order. Three sort mutations that had survived now fail: the open ledger resolving first (2), the whole sort reversed (2), and the seal-date key dropped so filename order decides (2). The area fallback is pinned too (1). No generator code changed, so no third round is owed (`QUALITY.md`, "Independent review (clean-context)"). `adequacy:` above is rewritten to the corrected figures: 26 mutations, one survivor, and it is unobservable on a sheet rather than untested.

**After the review, two defects from downstream.** The cockpit built its walk page against this generator on the same day and filed project-os-cockpit ISS-0303 (a retired check was still being asked) and ISS-0304 (a comma inside a quoted walk-order entry split it in two). Both are fixed upstream, both are asserted here, and both are mutated and caught. The first is the largest correction in this feature: your-trainer's owed count for REL-0017 android moves from 61 to 39, because 217 of its acceptance checks are retired. Neither the harness nor either review round found them, and the way they were found is worth keeping: a second implementation reading the same corpus. That is the thing ADR-0029 rule 7 decided bundling for, and it paid on the first day.
