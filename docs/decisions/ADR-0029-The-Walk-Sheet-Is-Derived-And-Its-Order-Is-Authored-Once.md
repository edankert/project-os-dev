---
type: "[[adr]]"
id: ADR-0029
aliases: ["ADR-0029"]
title: "A release walk is presented as a sheet derived from the ledger, in an order authored once per project"
status: accepted
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["Edwin, 2026-09-13: 'I find it increasingly difficult to understand what steps need to be done to satisfy the outstanding acceptance tests, so I am wondering is there another thing we need to create on-top of the actual tests, which goes through the things that I should be doing to satisfy these tests in a logical order (one thing I notice the tests do not suggest me doing is to look at the changed screens at all, which is strange because that is normally the first step I would do)'", "Review of your-trainer's acceptance artefacts, the cockpit's checks page and the template's release skills, 2026-09-13", "Industry survey of test procedure specifications, test runs and session-based testing, 2026-09-13"]
decision: "Option 3, accepted 2026-09-13 when the owner directed PHASE-0004 be implemented and the four acceptance boxes closed. A walk sheet is generated per release and platform from the ledger's owed set; it opens with a survey of the surfaces the release changed, derived from the ledger's invalidation events; its sittings follow one authored file per project, docs/tests/acceptance/WALK.md, and nothing about the order is inferred; each row prints the check's Setup, Steps and Expect inline. The rules are stated once in TESTING.md. The template ships the generator and the cockpit bundles it."
context: "project-os has a check layer, a verdict layer and a list layer, and no procedure layer. Every consumer with a large suite writes the procedure by hand per release and throws it away."
alternatives: ["Prose guidance in the release-verification skill only", "A per-release authored run plan note type"]
consequences: ["Work lands in three repos: the template, the cockpit and the first consumer", "ADR-0027's four headings become a hard dependency, because a sheet row prints them", "The cockpit's cancelled TASK-0449 is answered: the order is authored, not inferred", "No new close-out obligation: the survey reads invalidation events the ledger already refuses to take without a change id"]
supersedes: ""
superseded: ""
related: ["[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]"]
---

# The walk sheet is derived, and its order is authored once

> [!note] Amended 2026-09-14 by [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]], accepted by Edwin the same day. Rules 2, 5 and 8 changed: the survey comes from change notes and before and after captures, a sitting may be walked from a written procedure that a validator holds to the owed set, and change notes now list the screens they changed at close-out. Rules 1, 3, 4, 6 and 7 stand. The text below is left as it was decided.

## Rule

Every release walk in a project-os repo is presented as a walk sheet whose rows are exactly the ledger's owed manual checks for that release and platform, whose sittings follow the project's `docs/tests/acceptance/WALK.md` in file order, and whose first section is the survey of the surfaces the release changed.

## Domain

Every repo on the project-os template that keeps an acceptance suite (`[[test]]` notes at `level: acceptance`) and a release ledger under `docs/releases/ledgers/`. A repo with a suite and no ledger is the pre-ledger case of ISS-0059 and is outside this rule until its ledger exists.

## Conformance

The discharge is [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]], whose `command:` is `tools/scripts/test-walk-sheet.sh` in the template: a fixture test that generates a sheet from a known ledger and a known WALK.md and asserts the rows, the order, the survey and the labels. On disagreement between a sheet and a person's memory of what is owed, the ledger is authoritative, and a sheet that differs from `ledger.owed()` is a defect in the generator, never a reason to edit the sheet.

## Context

**A walker has three layers today and needs a fourth.** A check is a `[[test]]` note with a procedure. A verdict is an event in the release ledger, per check, platform and release (project-os-cockpit ADR-0037). The list is the cockpit's checks page, which groups by section and by `area:` and floats owed rows to the top of their area, in id order. Nothing says in what order to walk the owed rows, what has to be on the bench for a group of them, or which screens to open first. The template's own answer to "how do I run the manual checks for this release" is the release-prep skill's step 2, "list every check it calls a blocker", and the release-verification skill's step 7, "present the procedure to the user for execution", one check at a time.

**The missing layer has a name in the standards.** ISO/IEC/IEEE 29119-3 calls it a test procedure specification: the test cases of a selected set "in execution order, along with any associated actions to set up the initial preconditions and any post execution wrap up" (https://wildart.github.io/MISG5020/standards/ISO-IEC-IEEE-29119-3.pdf, 7.4.5). ISTQB's test execution schedule adds the ordering rule that a dependency wins over a priority (https://istqb-glossary.page/test-execution-schedule/). The test-management tools call the per-release instance a test run, a test execution or a test cycle: a selection of cases with an order, an assignee, an environment and a result per row. Session-based test management puts a survey session first, "devoted to learning a product and characterizing the general risks", before any deep-coverage session (https://www.satisfice.com/blog/archives/598, https://en.wikipedia.org/wiki/Session-based_testing). Whittaker's tours give that survey a shape for changed user interface: the Landmark tour visits chosen screens in a set order, the Prior-Version tour reruns what used to work (https://www.getxray.app/blog/test-tours-exploratory-testing-strategy-qa-teams). Hand-made release checklists for desktop and mobile apps group by environment and setup cost first and by feature second (Nextcloud desktop, https://github.com/nextcloud/desktop/issues/6562; Element Android, https://github.com/element-hq/element-android/issues/7505). Nobody found selects manual tests by changed screen; the nearest practice is test-impact analysis, which selects from a diff.

**The consumer with the largest suite has written this layer by hand three times.** your-trainer's `docs/tests/ACCEPTANCE_RUN_PLAN.md` is 719 lines, headed "TEMPORARY", with twelve phases in product-state order, a pre-flight section listing what goes on the bench, and every action and expected result inline "so you don't flip back". Its 315 row addresses point into a document that was deleted, and only five rows carry a check id, so no row can be resolved to the check it discharges. Its two predecessors for v2.1.1 are retired. Each was written for one release and thrown away, so the ordering knowledge and the bench list never became reusable. The same repo reports three different counts of what 2.2.0 owes: 88 from `mark:` on the notes, 51 from the ledger, 67 in the release note's prose. The only inter-check ordering anywhere is a sentence in TST-0659, "run it when the sweep is already known to work".

**Two earlier attempts at ordering died, and this decision has to say why it is different.** project-os-cockpit TASK-0449, cancelled 2026-08-16, wanted to order the walk by setup cost using burden tags read from prose, and was killed because the tags existed in one hand-written document and a scanner produced only false positives. It left two guard rails: no time estimates, and no new tag vocabulary. project-os-cockpit ADR-0036 withdrew the close-out acceptance sweep because its common case was "nothing to do, say so", an obligation whose cost was the asking.

## Options

1. **Prose guidance in the release-verification skill only.** Tell the agent to group the blockers by area and walk them in a sensible order. Costs nothing and changes nothing: the skill already lists the blockers, and prose guidance is what your-trainer's three hand-written plans were produced under.

2. **A per-release authored run plan note type.** Make what your-trainer does by hand a first-class note, `RUN-*` or similar, written for each release. Buys a place for the artefact and a status for it. Costs a second maintained list of "the checks for this release" beside the ledger, which project-os-cockpit ADR-0040 and ADR-0041 reject on sight, and which rots the way a maintained matrix rots. ADR-0030 decision 5 in the cockpit froze the existing per-release plans as history and said new releases freeze a structured check set instead; this option reverses that.

3. **A derived sheet, an authored order, and setup on the check.** The sheet is generated from the ledger; the order is one file per project that changes rarely; each check carries its own Setup line under ADR-0027's headings. Nothing per release is written by hand. Costs a generator, a template, a section in TESTING.md, a page in the cockpit, and one optional field. Buys a sheet that cannot disagree with the gate, an order that survives releases, and a survey section nobody has to write.

## Decision

**Option 3, as eight rules.** The normative text is `tools/instructions/TESTING.md`, "The walk", landed by TASK-0111 on 2026-09-13; every other document links there and restates none of it. The eight rules below are the decision record and the reasoning behind each. Where the two ever differ, TESTING.md governs (ADR-0024).

1. **The sheet is derived, never stored.** Rows are exactly `ledger.owed(platform, checks)` restricted to the manual sections, feature and regression (project-os-cockpit ADR-0039). No second list of the checks for a release exists anywhere. A generated sheet may be committed as a record of what was walked, but it is never edited by hand and never read back by tooling.

2. **The survey is derived from the ledger's invalidation events.** For every owed check whose latest event is an invalidation, take the check's `area:` (its surface, a `SUR-*` note where the repo has them) and the change ids in `invalidated_by:`. Group by surface. Under each surface list the invalidating tasks and changes with their titles, and quote a `## Acceptance checks reopened` section from those notes when one exists. Where the repo declares a screen gallery, the survey names the command that regenerates it. The survey renders before the first sitting. No new close-out obligation is created: the invalidation event is already mandatory and is refused without a change id (project-os-cockpit ADR-0037), and the reopened section stays optional prose. This is the answer to ADR-0036: the survey asks nothing at close-out that the ledger did not already ask.

3. **The order is authored once, in WALK.md, never inferred.** Sittings appear in file order. A check falls into the first sitting whose `surfaces:` names its `area:`; a sitting may also name check ids to pull them in regardless of area. Checks no sitting claims land in a final sitting labelled "Unplaced", which is the author's worklist. Sittings with nothing owed are omitted. This is the answer to TASK-0449: nothing is inferred, and its two guard rails stand. A sheet carries counts of rows and never a time estimate, and no tag vocabulary is added.

4. **Inside a sitting, `after:` first, then id.** One optional frontmatter field on an acceptance check, `after: []`, lists check ids that should have passed before this one is walked. The sheet orders by it topologically. Nothing gates on it.

5. **Each row is walkable without leaving the sheet.** A row prints the check id, its title, and its Setup, Steps and Expect sections from ADR-0027's four headings. A check without a Setup heading prints "Setup: not stated", so the sheet doubles as the ADR-0027 worklist. This is the fully paid version of project-os-cockpit ADR-0041 decision 4, "the settle surface must render each check's procedure text".

6. **A verdict goes to the ledger, from the sheet.** In the cockpit a row's tick is the existing mark dialog writing a ledger event with `method: manual`. From a markdown sheet the walker records verdicts through the cockpit or the ledger write path. The sheet is never the store.

7. **One implementation.** The template ships `tools/scripts/walk-sheet.py`, which reads the notes, the ledgers and WALK.md and writes markdown. The cockpit bundles that module the way it bundles the validator and renders its page from the same data, so a badge and a sheet cannot disagree about one corpus.

8. **Stated once.** The rules live in TESTING.md. The WALK.md template, the script, the skills and the cockpit link to it and restate none of it.

## Alternatives

- Option 1, prose guidance only. Rejected because it is the condition under which the hand-written plans were produced.
- Option 2, a per-release run plan note type. Rejected because it is a second store beside the ledger, and the cockpit's ADR-0030, ADR-0040 and ADR-0041 already refused that shape.
- Ordering by inferred burden, the cancelled TASK-0449. Rejected again for the reason it was cancelled; the authored WALK.md is what replaces the inference.

## Consequences

- Work lands in three repos. The template carries the rules, the generator, the templates and the skills (FEAT-0029 here). The cockpit renders the sheet as a page in its publication view and bundles the generator (documented in project-os-cockpit as FEAT-0149). your-trainer is the first consumer and authors the first WALK.md from its hand-written plan (documented there as FEAT-0119).
- ADR-0027's four headings become a hard dependency, because rule 5 prints them. TASK-0110 lands the headings in the test template; ADR-0027's validator rule stays on its own acceptance thread.
- "Setup: not stated" on a sheet row is a worklist entry, not a defect in the sheet. Existing corpora are rewritten on contact, which is ADR-0027's rule, and the sheet is where contact happens.
- The three disagreeing counts in your-trainer become one, the ledger's, on every sheet. The validator still reads `mark:` (ISS-0060); the sheet makes that visible and does not fix it.
- No close-out obligation is added. The survey is read from events the ledger already refuses to take without a change id.

## Acceptance

- [x] **The WALK.md syntax is fixed.** One `### ` heading per sitting, one fenced `yaml` block under it, four keys: `surfaces`, `checks`, `state`, `bench`. Landed 2026-09-13 as `docs/__templates__/walk.md`, documented in `SCHEMAS.md` under "`walk.md` — the walk order (`WALK.md`)", and it is the only syntax `tools/scripts/walk-sheet.py` parses.
- [x] **The `after:` field is accepted.** Optional, on an acceptance check only, a list of check ids. It orders rows inside a sitting and gates nothing. Landed 2026-09-13 in `docs/__templates__/test.md` and `SCHEMAS.md`, "Acceptance fields".
- [x] **A generated sheet may be committed, and nothing writes one unless a person asks.** `--out` has no default: `walk-sheet.py` prints to stdout, so generating a sheet never puts a file in the repo. Naming `--out` writes one, and rule 1 permits keeping it as a record of what was walked. No `.gitignore` entry is added, because there is no path to ignore. Decided 2026-09-13 with TASK-0113.
- [x] **The cockpit bundles the generator.** Recorded on project-os-cockpit FEAT-0149: *"implemented once in `tools/scripts/walk-sheet.py` upstream (project-os-dev FEAT-0029), and the cockpit bundles that module the way it bundles the validator"*, with the drift hazard covered by the same sync and fleet check that cover `validate_docs_bundled.py`.
