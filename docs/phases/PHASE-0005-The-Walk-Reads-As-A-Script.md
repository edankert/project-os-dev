---
type: "[[phase]]"
id: PHASE-0005
aliases: ["PHASE-0005"]
title: "The walk reads as a script: changed screens first, then one written procedure per sitting"
status: planned
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
- **expectation tag**: a label on a line of a procedure step, such as `TST-0648·4`, saying that line satisfies step 4 of check TST-0648.
- **owed part**: one numbered step of a check the release still owes. A check with no numbered steps is one part.
- **gallery key**: the name a screenshot tool gives one captured screen, such as `equipment-hub-dataonly`.

## Scope

- **Two decisions, both proposed.** [[ADR-0044-A-Surface-Is-A-Screen-By-Default|ADR-0044]]: a surface is a screen by default, with four rules for states, dialogs, checks that cross screens, and screens placed differently per platform. [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]]: it amends ADR-0029 so the survey comes from change notes and screenshots, and a sitting may be walked from an LLM-written procedure that a script holds to the owed set.
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

- [ ] ADR-0044 and ADR-0045 are accepted, amended or declined by Edwin, and ADR-0029 carries a pointer to whichever amendment was accepted.
- [ ] REQ-0029 is implemented, each criterion ticked with evidence or amended with a recorded reason.
- [ ] REQ-0028's survey criterion is amended in its `## Amendments` section, not reworded silently.
- [ ] In the template, the fixture test proves the validator fails on an owed part no step cites, on a part two steps cite, on a tag naming a retired check, and on a tag naming a step the check does not have.
- [ ] On your-trainer's REL-0017 Android sheet, the survey lists screens with no test id, and every sitting that has a procedure prints only steps that cite an owed part. That repo's own phase proves it; this criterion records the evidence.
- [ ] TESTING.md "The walk" still states the rules once. The skills, templates, generator and cockpit link there.

## Notes

- **Order.** ADR-0044 and ADR-0045 come first, because every task writes one of their rules. TASK-0116 and TASK-0119 land the text. TASK-0117 and TASK-0118 need TASK-0116. TASK-0120 and TASK-0121 need TASK-0119. TASK-0122 needs TASK-0120. TASK-0123 is last.
- **Files change in the template repo** (`~/Dev/repos/project-os`). This repo holds the record, as in PHASE-0004. The template's own `SNAPSHOT.yaml` is a blank template and gets no planning items.
- **Parallel work downstream.** your-trainer's screen mapping (its TASK-0900, which pauses for Edwin's approval) and the cockpit's step ticks (its TASK-0624, built against a fixture) can start before this phase finishes.
- **Risk scan.** No new external dependency or environment variable. The generator gains one input (change notes since a git tag), which means it now runs `git` to find the last release tag. That is a new runtime dependency on git history being present, which a shallow CI clone does not have. Recorded on TASK-0118 as a design constraint rather than a `RISK-*`, because the fallback is stated there.
