---
type: "[[phase]]"
id: PHASE-0004
aliases: ["PHASE-0004"]
title: "The walk: a procedure over the owed checks"
status: done
order: 4
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
goal: "Give a release walk the layer it has never had: a generated sheet that lists every owed acceptance check in an authored order, opens with the surfaces the release changed, and carries each check's setup, steps and expected result inline, so the person walking never opens another file and never writes a run plan by hand again"
features: [FEAT-0029]
requirements: [REQ-0028]
tasks: [TASK-0110, TASK-0111, TASK-0112, TASK-0113, TASK-0114, TASK-0115]
issues: []
related: [ADR-0029, ADR-0027, ADR-0025, ISS-0059, ISS-0060, ISS-0046]
tags: [phase, acceptance, walk]
---

# The walk: a procedure over the owed checks

## Goal

On 2026-09-13 Edwin said he finds it increasingly difficult to understand what steps to take to satisfy the outstanding acceptance checks, and that the checks never tell him to look at the changed screens first, which is the first thing he would do. The review that followed found that project-os has a good check layer, a good verdict layer and a good list layer, and no procedure layer at all. This phase builds that layer.

The vocabulary, used throughout the phase. To **walk** a check is to execute it by hand; the word is already the repo's. A **walk sheet** is a document generated per release and per platform that lists every owed check in the order a person should walk them, with each check's setup, steps and expected result inline. A **sitting** is a group of checks that share one setup state, such as one build, one tier or one piece of hardware on the bench, and are walked in one go. The **survey** is the sheet's first section: the surfaces a release changed, so the walker looks at those screens before running a scripted check. The **walk order** is one authored file per project, `docs/tests/acceptance/WALK.md`, listing sittings in product-state order with the state each needs and what must be on the bench.

The rules are decided in [[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once|ADR-0029]], required by [[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk|REQ-0028]] and built by [[FEAT-0029-The-Walk-Sheet|FEAT-0029]]. Edwin's rule from PHASE-0003 applies: a coherent body of work with an order and a plan is a phase, not parking.

## Scope

- **One decision**: [[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once|ADR-0029]]. The sheet is derived from the release ledger, the order is authored once in WALK.md, and the rules are stated once in TESTING.md.
- **One requirement**: [[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk|REQ-0028]], the observable contract of the sheet.
- **One feature, six tasks**: [[FEAT-0029-The-Walk-Sheet|FEAT-0029]]. In order: ADR-0027's four headings land in the test template (TASK-0110); TESTING.md gains "The walk" and the `after:` field (TASK-0111); the WALK.md template (TASK-0112); the generator script and its fixture test (TASK-0113); the skills and note templates (TASK-0114); downstream to the consumers and the cockpit (TASK-0115).
- **Two other repos do the rest**, and this phase names the work there without owning it: project-os-cockpit renders the sheet as a page in its publication view (documented there as FEAT-0149), and your-trainer is the first consumer (documented there as FEAT-0119).

## Out of Scope

- The validator rule ADR-0027 proposes for a check without a Setup heading. That stays on ADR-0027's own acceptance thread; this phase lands only the headings.
- Recording verdicts from the markdown sheet directly. A verdict goes to the ledger through the cockpit or the ledger write path; the sheet is never the store. The pre-ledger write path a new project starts on is [[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path|ISS-0059]] and stays there.
- Making the validator read the ledger instead of `mark:` on the note. That is [[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger|ISS-0060]], filed before this phase; the sheet makes the disagreement visible but does not fix it.
- Any per-release authored run plan. That is the thing this phase replaces.

## Exit Criteria

- [x] ADR-0029 is accepted or superseded, with its four acceptance boxes ticked or cut with a reason — accepted 2026-09-13; all four boxes ticked: the WALK.md syntax is fixed and is the only one the generator parses, `after:` is accepted, a generated sheet may be committed but `--out` has no default so nothing enters git unless a person asks, and project-os-cockpit FEAT-0149 records that it bundles the generator.
- [x] REQ-0028 is implemented, every criterion ticked with evidence — seven criteria, each with its evidence, and three of them amended with recorded rationale after the independent review rather than ticked to fit (`## Amendments` on the note).
- [x] FEAT-0029 is done, and `bash tools/scripts/test-walk-sheet.sh` passes in the template — 80 assertions, 0 failures, over four fixture repos; [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]] carries 28 mutations and its one known survivor.
- [x] TESTING.md states the walk rules once; the WALK.md template, the script, the skills and the cockpit link to that section and restate none of it — `tools/instructions/TESTING.md`, "The walk". Two restatements that crept into `docs/tests/README.md` and the release-prep skill were cut back to pointers before close-out.
- [~] your-trainer generates its 2.2.0 sheet from the ledger, and its hand-written `docs/tests/ACCEPTANCE_RUN_PLAN.md` is retired — **half delivered, and the other half is not this phase's.** The sheet generates: 39 owed rows, survey first, recorded on your-trainer FEAT-0119 as the starting figure. Retiring the run plan needs that repo's WALK.md, its Setup lines and its area alignment, which FEAT-0029's own Scope puts in your-trainer FEAT-0119 (TASK-0893 to TASK-0897). Cut here rather than held open, because this phase cannot close another repo's feature.

## Notes

- **Order matters inside FEAT-0029.** TASK-0110 lands the headings a sheet row prints; everything after it reads them. TASK-0113 needs TASK-0112's syntax to parse. TASK-0115 is last because it syncs what the others produced.
- **The template repo is where the files change.** Every task edits `~/Dev/repos/project-os`; this repo holds the record and its own vendored copies follow at sync, per the standing arrangement in `CLAUDE.md`.
- **What the phase must not become.** No time estimates anywhere on a sheet, only counts of rows. No burden inferred from prose. No second list of "the checks for this release". Each of those is a way an earlier attempt died, and ADR-0029 records which.
