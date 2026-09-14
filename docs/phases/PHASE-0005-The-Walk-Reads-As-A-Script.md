---
type: "[[phase]]"
id: PHASE-0005
aliases: ["PHASE-0005"]
title: "The walk reads as a script: changed screens first, then one written procedure per sitting"
status: done
order: 5
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
goal: "A person walking a release reads one script: first the app screens the release changed, each with a sentence a rider would understand and before and after pictures, then one procedure per sitting that states the setup once, names the screen for every step and tags each expectation with the check it satisfies. No check note has to be opened."
features: [FEAT-0030, FEAT-0031]
requirements: [REQ-0029]
tasks: [TASK-0116, TASK-0117, TASK-0118, TASK-0119, TASK-0120, TASK-0121, TASK-0122, TASK-0123]
issues: []
related: [ADR-0044, ADR-0045, ADR-0029, REQ-0028, FEAT-0029, ADR-0027, ISS-0063, ISS-0064, ISS-0050]
tags: [phase, acceptance, walk, surfaces]
---

# The walk reads as a script

## Goal

The walk sheet from [[PHASE-0004-The-Walk|PHASE-0004]] groups checks into sittings, but it still prints each check's Setup, Steps and Expect one after another. On your-trainer's v2.2.0 sheet that means the same "fake a connected trainer" setup is printed four times in one sitting, and the comparison against a drivable trainer recurs in four checks. The survey also lists test categories such as "Hardware", not the screens Edwin opens. This phase makes the sheet read like a script.

Edwin approved this wording on 2026-09-14: *"Before v2.2.0 ships, Edwin walks the release from a sheet that works like a script. It opens with the app screens this release changed: what each one now shows, with before and after screenshots. Then it gives one procedure per sitting (checks sharing one setup): the setup stated once, each step naming the screen it happens on, and each expectation tagged with the check it satisfies. A tick in the cockpit records the verdict for every check that step satisfies."*

Words used in this phase:

- **procedure**: a written script for one sitting. It states the setup once, then numbered steps.
- **expectation tag**: an ASCII label on a line of a procedure step, such as `TST-0648.4`, saying that line satisfies step 4 of check TST-0648. The line quotes that check's Expect text word for word.
- **owed part**: one numbered step of a check the release still owes. A check with no numbered steps is one part.
- **gallery key**: the name a screenshot tool gives one captured screen, such as `equipment-hub-dataonly`.

## Scope

- **Two decisions, both accepted by Edwin on 2026-09-14.** [[ADR-0044-A-Surface-Is-A-Screen-By-Default|ADR-0044]]: a surface is a screen by default, with four rules for states, dialogs, checks that cross screens, and screens placed differently per platform. [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]]: it amends ADR-0029 so the survey comes from change notes and screenshots, and a sitting may be walked from an LLM-written procedure that a script holds to the owed set.
- **One requirement**: [[REQ-0029-A-Release-Walk-Reads-As-A-Script|REQ-0029]], what a person can observe on the result.
- **[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens|FEAT-0030]]**: the surface rules (TASK-0116), a change note's Impact section naming screens (TASK-0117), and the survey built from change notes and before and after captures (TASK-0118).
- **[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure|FEAT-0031]]**: the procedure format (TASK-0119), the validator (TASK-0120), the sheet printing only owed parts (TASK-0121), the skill that regenerates a procedure (TASK-0122), and the sync to the consumers and the cockpit (TASK-0123).
- **Two other repos do the rest**, named here and owned there. your-trainer PHASE-024 (FEAT-0120, FEAT-0121) turns its surfaces into screens, names screens on its change notes, captures the gallery at v2.1.8 and at the release candidate, and writes the v2.2.0 procedures. project-os-cockpit PHASE-044 (FEAT-0150) renders the survey as screen cards and each sitting as its procedure, with a tick per step.

## Out of Scope

- `area:` as a list. A check names one surface.
- Merging steps automatically without a written procedure.
- Any change to the ledger format. A verdict is still one event per check.
- Walking v2.2.0. That stays your-trainer REL-0017's gate.
- Validator rules that read the ledger instead of `mark:` ([[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger|ISS-0060]]).

## Exit Criteria

- [x] ADR-0044 and ADR-0045 are accepted, amended or declined by Edwin, and ADR-0029 carries a pointer to whichever amendment was accepted. *(Both accepted 2026-09-14; ADR-0029 carries the pointer to ADR-0045.)*
- [x] REQ-0029 is implemented, each criterion ticked with evidence or amended with a recorded reason. *(All eight ticked 2026-09-14, each naming the code and the assertion behind it.)*
- [x] REQ-0028's survey criterion is amended in its `## Amendments` section, not reworded silently. *(Written 2026-09-14: criterion 2 is superseded by ADR-0045 decision 1, with the measurement that decided it and a pointer to REQ-0029 criterion 3.)*
- [x] In the template, the fixture test proves the validator fails on an owed part no step cites, on a part two steps cite, on a tag naming a retired check, on a tag naming a step the check does not have, and on a quoted expectation that does not match the check's Expect text. *(Five defects, one fixture each, plus six more the ADR did not name. 28 mutations, none survived — [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].)*
- [~] On your-trainer's REL-0017 Android sheet, the survey lists screens with no test id, and every sitting that has a procedure prints only steps that cite an owed part. **Cut from this phase, because it is another repo's work and Edwin decided on 2026-09-14 that v2.2.0 waits.** your-trainer's PHASE-024 has to run first: TASK-0900 (the surface mapping Edwin approves), TASK-0902 (the `area:` rewrite), TASK-0904 (captures) and TASK-0906 (the procedures). The machinery is there and synced — `walk-sheet.py --check` runs clean on that repo today, reporting thirteen sittings with no procedure and seven change notes with no Impact list, which is the worklist. Measured there 2026-09-14: 39 owed Android checks, 180 owed parts, 16 surfaces, no `gallery:` key yet.
- [x] TESTING.md "The walk" still states the rules once. The skills, templates, generator and cockpit link there. *(Rule 2 replaced, rules 5 and 8 narrowed, rule 9 added; "Nine rules" now. Everything downstream links by section name and restates none of it.)*

## Edwin's decisions, 2026-09-14

> "v2.2.0 should wait. go with your recommendations for the others, will I start the project-os-dev and cockpit phase first?"

"The recommendations" he accepted, recorded as his decisions:

1. **The close-out step is accepted.** Change notes list the screens they changed, and an LLM drafts the sentence. ADR-0045 decision 2 stands and TASK-0117 goes ahead.
2. **A procedure is written once per sitting for the whole product, not per release.** The validator decides what prints.
3. **Each expectation line quotes the check's own Expect text word for word**, and the validator checks the quote. This keeps a pass from a procedure step within project-os-cockpit ADR-0041 (TASK-0119, TASK-0120).
4. **The 12 to 15 surface target from project-os-cockpit FEAT-0130 applies to top-level screens only.** Children sit below them.
5. **REL-0017 waits for PHASE-024** (your-trainer).

Smaller points: procedures live in one file per sitting under `docs/tests/acceptance/walk/`, linked from WALK.md, and aim to cover every live check while the validator requires only the owed ones; the gallery-key map lives on the surface note as a `gallery:` list of `key` or `key:state`; captures are committed only for changed screens, as before and after pairs per release; cockpit step ticks live in per-workspace browser storage and the worst step mark decides the verdict; tags are ASCII, `TST-0648.4`; a check with unheaded prose steps is one part until the LLM writing its procedure numbers them.

## Start order

Edwin asked whether project-os-dev and the cockpit start first. The answer:

1. **This phase goes first**: FEAT-0030's surface rules and FEAT-0031's procedure format and validator, TASK-0116 to TASK-0120.
2. **In parallel**: your-trainer TASK-0900 (the mapping table), because it depends only on the accepted ADR-0044.
3. **project-os-cockpit PHASE-044 starts once TASK-0119 has fixed the procedure format**, working against a fixture.
4. **Then**: the template sync into your-trainer (TASK-0123 here, TASK-0905 there), then your-trainer's procedures (TASK-0906), then the end-to-end check (your-trainer TASK-0907, cockpit TASK-0626). TASK-0121 and TASK-0122 land before the sync.

## Notes

- **Order inside this phase.** TASK-0116 and TASK-0119 land the text. TASK-0117 and TASK-0118 need TASK-0116. TASK-0120 and TASK-0121 need TASK-0119. TASK-0122 needs TASK-0120. TASK-0123 is last.
- **Files change in the template repo** (`~/Dev/repos/project-os`). This repo holds the record, as in PHASE-0004. The template's own `SNAPSHOT.yaml` is a blank template and gets no planning items.
- **Parallel work downstream.** your-trainer's screen mapping (its TASK-0900, which pauses for Edwin's approval) and the cockpit's step ticks (its TASK-0624, built against a fixture) can start before this phase finishes.
- **Risk scan.** No new external dependency or environment variable. The generator gains one input (change notes since a git tag), which means it now runs `git` to find the last release tag. That is a new runtime dependency on git history being present, which a shallow CI clone does not have. Recorded on TASK-0118 as a design constraint rather than a `RISK-*`, because the fallback is stated there.

## What this phase landed, 2026-09-14

Template commits `c3cdb4c`, `a0c80e3` and `0f1b673`; synced and committed into your-trainer, project-os-cockpit, project-os-deck, your-sudoku and this repo's vendored `tools/`.

A walk sheet now opens with the screens the release changed — each with the sentence a change note wrote for it and the screen at the last release beside the screen now — and a sitting that carries a written procedure prints as that procedure: the setup once, the steps that cite something still owed, each expectation line quoting the check's own words and saying which check step it satisfies.

Five things are worth carrying forward:

1. **The survey's input did not exist.** Twelve change notes since your-trainer's v2.1.8 tag, four with an `## Impact` section, none of the four naming a screen. That is what made the new close-out obligation the right call rather than an imposition — ADR-0029 rule 8 had refused one, and this is the exception it was refusing in ignorance of.
2. **Half the corpus has no numbered steps.** Of 39 owed Android checks there, 18 number their steps and 21 do not, giving 180 owed parts. So the "unheaded prose is one part" rule is the common case, and the skill's step 2 — number them in the check note first — is where most of the work will be.
3. **A measurement found a defect in the rule being written.** An Impact line reading "intervals.icu got its own, SUR-0016" in the middle of a sentence about `area:` values was read as a screen the release changed. The parser now requires the id to start the list item, and the fixture carries that exact sentence.
4. **Two mutations survived the first pass and both taught something.** One showed a rule written so it could not be got wrong and therefore could not be tested; the other showed a guarantee that was invisible on the sheet but load-bearing for the cockpit's payload. Both are closed, and the second is why the harness now imports the module rather than only grepping its output.
5. **The sync cost more than a file copy in one repo.** project-os-cockpit's `walk_payload` called the old API, so 37 of its tests went red the moment the module landed. Adapting the payload, rewriting its survey tests to the new rule and drawing the new shape plainly went with the sync, because a sync that leaves a downstream suite red is not a sync. The card layout and the per-step ticks stay that repo's PHASE-044.

## What the review cost, and what it was worth

**The gate ran both its rounds on 2026-09-14 and round two returned `approved` on all three notes.** Round one, from a clean context, returned `changes-requested`. **Eight blocking findings, every one reproduced, every one fixed with a fixture**, plus nine non-blocking of which five are fixed and two are filed ([[ISS-0066-An-Expectation-Line-May-Quote-Any-Expect-Line-Of-Its-Check|ISS-0066]], [[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]]). The harness went from 139 assertions and 28 mutations to 157 and 38.

Two things about those eight are worth carrying into the next phase.

**Five of them were about a shape the corpus writes and the fixtures did not.** Markdown's "every item is `1.`" — which defeated the doubly-cited rule outright — a worked example inside a fence, two screens on one Impact line, an `## Impact` list shown inside a fence, and a repo whose acceptance checks have all been retired. The fixtures had been written from the rule, and the rule is what the author already believed. A fixture drawn from a real note would have caught four of the five on the first run.

**The sharpest finding was not in the generator at all.** `walk_payload` in project-os-cockpit and `walk-sheet.py` disagreed about the same procedure, because the cockpit passed only the owed checks and a procedure legitimately cites checks that have already passed. That is exactly the failure rule 7 says bundling one implementation prevents — and bundling did not prevent it, because the bundled module took its inputs from a caller. Neither repo's suite could see it: no cockpit test wrote a procedure file. Two now do.

**Round two found one more thing, and it was mine.** The eighth fix made `--check` carry on past any `WalkError`, which also carried a broken ledger — a filename naming no platform, an entry dated `2026-13-45` — out of everything that reads one on a commit. Fixed with a narrow `NothingToWalk` and two assertions, not filed. Twice in this phase, making something quieter made it blind; the first time was deliberate and recorded, the second took a second reviewer.

**Not done and deliberately so:** the exit criterion above about your-trainer's real sheet. That is its PHASE-024, and Edwin's decision on 2026-09-14 was that v2.2.0 waits.
