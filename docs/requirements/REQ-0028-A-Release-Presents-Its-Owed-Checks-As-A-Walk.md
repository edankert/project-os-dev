---
type: "[[requirement]]"
id: REQ-0028
aliases: ["REQ-0028"]
title: "A release presents its owed acceptance checks as a walk sheet: the changed surfaces first, then sittings in an authored order, each check walkable inline"
status: implemented
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "Edwin, 2026-09-13: the outstanding checks do not say what to do in what order, and never say to look at the changed screens first"]
priority: high
scope: "The project-os template: tools/instructions/TESTING.md, docs/__templates__/, tools/scripts/walk-sheet.py, and the release-prep, release-verification, close-out and test-authoring skills. The cockpit's page and the consumers' WALK.md files are downstream of this scope."
acceptance:
  - "For a release and a platform, the sheet's rows are exactly the ledger's owed manual checks (no surviving clearing verdict, feature and regression sections only). No other source contributes a row, and no row is removable except by a ledger event."
  - "The sheet opens with a survey: every surface (area:, SUR-* where present) that has an owed check whose latest ledger event is an invalidation, each surface naming the tasks and changes in invalidated_by: with their titles, and quoting a '## Acceptance checks reopened' section when the note has one."
  - "Sittings appear in the order docs/tests/acceptance/WALK.md lists them, sittings with nothing owed are omitted, and checks no sitting claims appear in a final sitting labelled 'Unplaced'."
  - "A row shows the check's id, title, Setup, Steps and Expect inline. Where a heading is missing the row says which one and prints what the note does have: no Setup shows 'Setup: not stated'; no Steps falls back to Procedure and then to the note's unheaded description under 'Steps: no heading'; no Expect falls back to Expected results and then says the note states none."
  - "The generator writes no time estimate of its own; counts of rows are the only number it produces. Text quoted verbatim from a note may contain one, and that is the note author's sentence."
  - "TESTING.md states the walk rules once, and the WALK.md template, the generator and the four skills link to that section without restating it. The cockpit's linkage is its own repo's acceptance (project-os-cockpit FEAT-0149), outside this requirement's scope."
  - "A consumer repo receives the template, the generator and the skill steps at its next sync with no migration of its checks; a repo without a ledger is refused by the generator with a message naming ISS-0059."
implements: "[[FEAT-0029-The-Walk-Sheet]]"
verifies: []
reviewed_by: "model:claude-opus-5"
review_date: 2026-09-13
review_verdict: approved
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]"]
tests: ["[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
---

# A release presents its owed checks as a walk

## Statement

When a release is being prepared, the person walking its acceptance checks shall be handed a walk sheet: one document per release and platform that lists every owed check in the order to walk them, opens with the surfaces the release changed, and carries each check's setup, steps and expected result inline. The sheet shall be generated from the release ledger and the project's authored walk order, and shall never be written or edited by hand.

Glossary for this note. To **walk** a check is to execute it by hand. A **walk sheet** is the generated document above. A **sitting** is a group of checks sharing one setup state, walked in one go. The **survey** is the sheet's first section, the changed surfaces. The **walk order** is `docs/tests/acceptance/WALK.md`, one authored file per project listing sittings in product-state order.

The rules that produce the sheet are decided in [[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once|ADR-0029]] and, once TASK-0111 lands, stated once in `tools/instructions/TESTING.md`, "The walk". This requirement states what a person can observe on the result.

## Acceptance Criteria

- [x] For a release and a platform, the sheet's rows are exactly the ledger's owed manual checks, with no other source contributing a row and no row removable except by a ledger event — evidence: `walk-sheet.py` `build_walk()` takes `[c for c in checks.values() if c.section != "automated" and ((v := verdicts.get(c.id)) is None or not v.clears)]` and reads nothing else. Cross-checked against the other implementation on a live corpus: over your-trainer's 431 acceptance notes, `ledger.owed()` from project-os-cockpit and this generator's `resolve()` returned identical sets on both platforms — 39 on android, 327 on ios — with zero differences in the resolved verdicts, and `section_of` agreed on every note. The same comparison on the cockpit's corpus returns 3 and 3. A check at `status: retired` is kept and no longer asked, matching `acceptance._is_retired` exactly. `test-walk-sheet.sh` asserts on a fixture that the automated, passed and excused checks are absent and the invalidated and never-walked ones present.
- [x] The sheet opens with a survey of every surface that has an owed check whose latest ledger event is an invalidation, each surface naming the invalidating tasks and changes with their titles and quoting a `## Acceptance checks reopened` section when one exists — evidence: `build_walk()` groups `latest.get(check.id).is_invalidation` by `area:`, resolves each `invalidated_by:` id to its note title, and quotes that note's reopened section. `test-walk-sheet.sh` asserts the surface, the invalidating task with its title, the quoted reopened section, the gallery command, and the absence of a surface nobody invalidated. On your-trainer's real sheet the survey names App shell & UX (SUR-0001), Hardware (SUR-0003), Hardware — cadence source and five more, each with its PHASE-021 and FEAT-0112 tasks and their reopened sections quoted.
- [x] Sittings appear in WALK.md order, sittings with nothing owed are omitted, and unclaimed checks appear in a final sitting labelled "Unplaced" — evidence: `test-walk-sheet.sh` asserts file order against a fixture whose first sitting sorts last alphabetically, asserts that a check named by id joins that sitting rather than its own area's later one, and asserts the unclaimed area's check under "Unplaced". A repo with no WALK.md gets one sitting per `area:` and is told on the sheet that its order is unauthored, which is asserted too.
- [x] A row shows the check's id, title, Setup, Steps and Expect inline, and names any heading the note is missing while printing what it does have — evidence: `render()`, asserted on the fixture for the Setup text, the "not stated" label, the steps and expected result verbatim, the tick box, the sitting's state and its bench. `Steps` and `Expect` fall back to the pre-ADR-0027 `Procedure` and `Expected results` headings, and where a note has neither — 31 of your-trainer's 39 owed rows, whose procedure sits in an unheaded paragraph under the title — the row prints that prose under "Steps: no heading". Every row on the real sheet carries its procedure text. `Setup` has no fallback, which is what makes its label a worklist.
- [x] The generator writes no time estimate of its own — evidence: `test-walk-sheet.sh` scans a rendered sheet for a duration and finds none, and the generator's own strings contain no minutes, estimate or burden field. **Amended 2026-09-13**, see Amendments: the original criterion said the sheet carries none anywhere, and a real sheet quotes note text that sometimes does. The header counts owed rows and sittings and nothing else.
- [x] TESTING.md states the walk rules once, and the template, the generator and the four skills link there without restating — evidence: `tools/instructions/TESTING.md` "The walk" is the only place the eight rules appear. `docs/__templates__/walk.md`, `SCHEMAS.md`, `docs/tests/README.md`, `walk-sheet.py`'s docstring and `--help`, and the release-prep, release-verification, close-out and test-authoring skills all link to it by section name and restate none of it; ADR-0029's Decision opening now defers to it. **Amended 2026-09-13**, see Amendments: the cockpit was dropped from this criterion, because `scope:` puts it downstream and nothing here can check it.
- [x] A consumer repo receives everything at its next sync with no migration, and a repo without a ledger is refused with a message naming ISS-0059 — evidence: synced into your-trainer, project-os-cockpit, project-os-deck and your-sudoku on 2026-09-13, with no check in any repo edited. `validate-fleet.sh` is byte-identical before and after across all 13 repos. your-sudoku keeps no ledger and the generator there exits 2 with the ISS-0059 message; `test-walk-sheet.sh` holds the same behaviour on a fixture.

## Independent review, 2026-09-13 (model:claude-opus-5, clean context)

Verdict `changes-requested`. Judged against `walk-sheet.py` sha1 `8f6be72f` and the 38-assertion harness. Four ticked criteria are refuted by a command the reviewer ran; the findings are transcribed in the reviewer's report and the reproduced ones belong in `ISS-*` notes at `triage`.

**Criterion 2 (the survey) is false when an invalidation names a change note.** `_ids()` matches `[A-Z]{2,6}-\d{3,4}\b`, and a change id is `CHG-YYYYMMDD-Short-Description`: the eight-digit date fails the `\d{3,4}\b` group, so `_ids("CHG-20260913-The-Banner-Moves")` returns `[]`. The survey then prints the surface heading, the line "Reopened by:", and nothing — no id, no title, and no `## Acceptance checks reopened` quote, which is the section the criterion promises. The criterion, ADR-0029 rule 2 and TESTING.md rule 2 all say "tasks **and changes**"; only tasks work. your-trainer's ledger happens to name only `TASK-*` and `REL-*` ids today, which is why the live run did not show it.

**Criterion 4 (a row shows Setup, Steps and Expect inline) holds for Steps and fails for Expect.** On your-trainer's REL-0017 android sheet, 57 of the 61 rows print `_The note states no expected result._` — the same corpus shape that motivated `lead_paragraph()` for Steps (53 of 61) is present for Expect, and worse, and was not measured. Those notes keep the material under the repo's own headings ("What a failure looks like" ×8, "What a rider still judges" ×4), which the generator reads as neither `Expect` nor `Expected results`. Whatever justifies the Steps fallback also applies here; whatever justifies leaving Expect to "rewrite on contact" also applied to Steps. The two are decided differently with no reason recorded anywhere.

**Criterion 5 (no time estimate anywhere) is false of a real sheet.** `grep -Eic '[0-9]+ *(min|minutes?|hours?)|\bminutes?\b|\bhours?\b'` over the generated your-trainer sheet returns 3: "in about four minutes" twice inside a quoted `## Acceptance checks reopened` block, and "a 40-minute ride" in a check title. TASK-0113's Notes state the real rule — the generator adds no duration of its own and a check author's text prints verbatim — but neither this criterion nor TESTING.md rule 8, which is the stated-once home and reads "A sheet carries counts of rows and nothing else numeric: no minutes", carries that carve-out. The rule as stated is not the rule as built.

**Criterion 6 (stated once) has a live counter-example and an unsatisfiable clause.** The "**Steps: no heading.**" label and the `lead_paragraph()` fallback are a behaviour a walker meets on 53 of 61 real rows, and they appear in no normative document: TESTING.md rule 5 describes only "Setup: not stated". Separately, the criterion requires the cockpit to link to the section, while this note's own `scope:` puts the cockpit downstream and out of scope; the ticked evidence does not mention the cockpit at all, so the clause cannot have been checked.

Three further reproduced defects do not map to a criterion but produce a wrong sheet. A mistyped `--platform` is not detected: `--platform andriod` against your-trainer prints "**545 owed rows in 23 sittings**" with no warning, because the refusal fires only when the repo has no ledger at all. `--release` is a free-text label read by nothing, so a sheet titled for the already-sealed REL-0016 shows today's owed set — a hazard for the committed-as-a-record use rule 1 permits. And the generator disagrees with `ledger.owed()` on a ledger whose `sealed:` and `release:` fields do not agree, because it sorts ledgers by `sealed` and decides excuse expiry by `release` while the cockpit uses `sealed` for both: on a ledger with `sealed` and no `release` the cockpit reports the check owed and the sheet reports "0 owed rows in 0 sittings". Silently omitting an owed row is what the Conformance clause and ADR-0029 rule 7 exist to prevent.


## Amendments

**Criterion 2, the survey, was replaced on 2026-09-14 by [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]] decision 1.** It said the sheet opens with every surface that has an owed check whose latest ledger event is an invalidation, naming the invalidating notes and quoting their `## Acceptance checks reopened` sections. That is now false of the sheet, and the criterion is superseded rather than failed: the survey lists the screens named in the `## Impact` section of every change note added since the last release tag, with each change's one rider-facing sentence and the screen's before and after captures, and it prints no check id at all.

The reason is a measurement, not a preference. **An invalidation names a check and never a screen.** Grouping by the invalidated check's `area:` printed "Hardware" on your-trainer, which spans five screens, and "Riding — structured", which is a mode of the ride cockpit — so the first section of the sheet named test categories to a person who was about to open screens. Worse, a change that altered a screen and reopened no check was invisible, and half the `## Acceptance checks reopened` sections in the fleet say "None". Twelve change notes since your-trainer's v2.1.8 tag: four have an Impact section, none of the four names a screen. So the input the new rule needs was recorded nowhere, which is why ADR-0045 decision 2 adds the one close-out obligation ADR-0029 rule 8 had refused.

What carries the criterion now is [[REQ-0029-A-Release-Walk-Reads-As-A-Script|REQ-0029]] criterion 3. The tick above stays as the record that the old rule was built and worked; it is not a claim about today's sheet. TESTING.md, "The walk", rule 2 is the normative text either way.

---

Three criteria were amended on 2026-09-13, after the independent review of FEAT-0029 reproduced findings against them. Each is recorded here rather than reworded silently.

**"The sheet carries no time estimate anywhere"** was false of a real sheet and is now a claim about the generator. Measured on your-trainer's REL-0017 android sheet: three duration strings, all of them text the sheet quoted verbatim — "in about four minutes" twice inside a quoted `## Acceptance checks reopened` section, and "a 40-minute ride" inside a check's own title. The guard rail the cancelled ordering attempt left behind is that the walk must not *invent* a schedule, and that is what the criterion now says. TESTING.md rule 8 carries the same boundary.

**"…and the cockpit link to that section"** named a repo this requirement's `scope:` puts downstream, so nothing here could check it and the tick would have been unearned. The cockpit's linkage is its own acceptance, on project-os-cockpit FEAT-0149.

**"or 'Setup: not stated' where the heading is missing"** described one of three fallbacks as though it were the only one. The generator also falls back from Steps to Procedure and then to the note's unheaded description, and from Expect to Expected results. The criterion now states all three, and TESTING.md rule 5 is the normative text.

**Round two, 2026-09-13 — `approved`.** Verification only, against `walk-sheet.py` sha1 `80370fcb` and the 72-assertion harness. All four criterion-level findings are fixed and re-tested. Criterion 2: a fixture carrying one full-slug change id, one canonical `CHG-<date>` and two change notes sharing a date now prints a title and a quoted reopened section for the first two, and the bare id with no guessed title for the ambiguous one — the right refusal. Criterion 4 and criterion 5 now read as claims the generator can meet, and TESTING.md rules 5 and 8 carry the same boundaries; criterion 6 no longer names a repo this note's `scope:` puts downstream. The `## Amendments` section records all three rewordings with the measurement behind each, which is the correct handling: the criteria were amended in the open rather than quietly satisfied.

The three non-criterion defects are fixed too. A mistyped platform is refused (`--platform andriod` exits 2 with "This repo keeps one for: android, ios"), a sheet named for a sealed release carries a `**Note:**` saying it shows what is owed now, and the generator and `ledger.owed()` now agree on both directions of the `sealed:`/`release:` mismatch (1/1 owed and 0/0 owed where they previously disagreed), with the live agreement over your-trainer unchanged at 583 resolved keys on android and 1 on ios, zero differences.

## Traceability

- Implements: [[FEAT-0029-The-Walk-Sheet]]
- Verified by: `tools/scripts/test-walk-sheet.sh` in the template (TASK-0113), and the docs-audit drift dimension for the stated-once criterion (REQ-0027)

**After round two, same day.** The approval came with one measured gap in the harness rather than the code, and it was closed rather than filed: the fixture pinned the order of two *sealed* ledgers but not the boundary between sealed and open, so resolving the open ledger first dropped 35 of your-trainer's 61 owed rows in silence. A check passed in a sealed ledger and invalidated in the open one now holds that edge, and the two sealed ledgers were renamed so filename order contradicts seal order. Three sort mutations that survived now fail. The harness is 73 assertions; no generator code changed, so no third round is owed (`QUALITY.md`, "Independent review (clean-context)").
