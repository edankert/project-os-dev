---
type: "[[adr]]"
id: ADR-0050
aliases: ["ADR-0050"]
title: "The walk is renamed the release test, each check's short expected result lives in the check itself, and an agent writes what cannot be generated"
status: accepted
decided_option: "1"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
decided: 2026-09-27
source: ["Edwin, 2026-09-27: 'We have a problem with the amount of text the walk procedure has. It is just a wall of text, there are no clear paragraphs or headings and all together it is just way too much. [...] Review and suggest how to make this more human friendly. More concise and better formatting to start with!!'", "Edwin, 2026-09-27: 'At first I want to see concise information about what has changed for the section we plan to test (including the before/after screen-shots), then I want to see the setup for the section (but this can be hidden away behind a open/close option) and then I would like to see the actual checks as concise and complete as possible.'", "Edwin, 2026-09-27: 'on the checks, I need to be able to record not just pass and fail, so please add back the other options as well'", "Edwin, 2026-09-27: 'I have said this before I don't like calling this a walk, can we think about what this is and how we present this / how to open this in the cockpit?'", "Edwin, 2026-09-27: '1. do as recommended. 2. rename all in one go. (to avoid confusion later on) ... if this cannot be fully automated, I have no problem if we would use an LLM agent / skill to hand edit some of this info when going to a release?' (1: the short expected text lives in the test notes; 2: internal names are renamed too)", "Measurement of your-trainer's REL-0017 Android sheet, 2026-09-27: 86 owed checks, 353 steps, 37,254 words", "Edwin, 2026-09-27, choosing the recommended answer to each open question: rename the old meaning of section; rename the ledger key mark to result; let the pilot set the section budget"]
decision: "Option 1, three decisions Edwin made on 2026-09-27. D1: the walk is called the release test everywhere, internal names included; a sitting is a section, the survey is 'what changed', a mark shown to a person is a result, and 'check' stays. Closed ADRs, change notes and archived notes are not rewritten. D2: each check's short expected result is written in the test note's own Expect lines, one line per platform where the platforms differ; procedures carry actions and tags only, never their own copy of an expectation. D3: text that cannot be generated mechanically (the per-section what-changed lines, shortened Expect lines, short action lines) may be written by an agent during release preparation, and the length guard checks the result."
context: "Your Trainer's v2.2.0 Android sheet turned 86 owed checks into 353 steps and 37,254 words. The procedures grew from 33,000 to 74,000 words after 2026-09-14. A person cannot read that at the bench."
alternatives: ["Keep the vocabulary and only shorten the output", "Let procedures carry their own short expected text beside the check's long text", "Generate every short line mechanically and accept whatever length results"]
consequences: ["Every script, field, path, skill, template and instruction that says walk, sitting or survey is renamed in one template release, and consumers take it with a migration script", "Test notes become the only place an expected result is written, so rewording one changes every page that shows it and no procedure drifts", "Test notes gain a per-platform form for Expect lines", "Release preparation gains an agent step, and the validator gains a length guard that starts as a warning", "ADR-0045's rule that an expectation line quotes the check word for word is replaced by tags only"]
supersedes: ""
superseded: ""
amends: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]", "[[ADR-0049-A-Walk-Step-May-Cite-A-Check-Without-Quoting-It]]"]
related: ["[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]", "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]", "[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"]
---

# The walk is renamed the release test, and each check's short expected result lives in the check itself

## Context

The page a person reads while testing a release by hand has become too long to use. Your Trainer's v2.2.0 Android sheet turned 86 owed checks into 353 steps and 37,254 words. Measured on 2026-09-27:

- The procedures grew from 33,000 words on 2026-09-14 to 74,000 words.
- 149 of the 353 "Required state" paragraphs repeat the previous step word for word.
- 273 expected-result lines start with "Step N:". That N is the step number inside the test note, not the step on the page.
- iOS wording appears in the Android sheet.
- The list of changed screens is 4,400 words long, comes before the first step, and quotes the title of every change note.

Edwin approved a redesign on 2026-09-27. The approved example is one section, the Equipment Hub on Android. Each check on it is a number, one short action line, one short expected line, and its TST tag. Its 28 checks take about 1,000 words, where today's sheet uses about 4,300. The page itself is built in project-os-cockpit. This decision covers what the template's generator, notes and skills must change to feed it.

Three questions came up while designing it, and Edwin answered all three the same day. They are D1, D2 and D3 below.

## Options

1. **Rename once, keep one source for each expected result, and let an agent write the short text at release time.** Costs one large rename across three repositories and a new release-preparation step. Buys a page that uses the same words as the tooling, expectations that cannot drift, and short lines that do not depend on a person rewriting 350 steps by hand.
2. **Keep the words "walk", "sitting" and "survey", and only shorten the output.** Cheaper now. The page would say "section" while every script, field and instruction says "sitting", which is the confusion Edwin wants to avoid.
3. **Let each procedure carry its own short expected line beside the check's long one.** Shorter procedures without touching test notes. Two texts for one expectation drift apart. A result would also no longer rest on the check's own words, which project-os-cockpit ADR-0041 requires.

## Decision

**Option 1.** It is three decisions. The rules they change are stated once, in `tools/instructions/TESTING.md`, "The release test" (today "The walk"), and TESTING.md governs where the two differ (ADR-0024).

### D1. The vocabulary is renamed everywhere, in one go

A person testing a release and the code that builds the page use the same words. Edwin, 2026-09-27: rename internal names too, "to avoid confusion later on".

| Old word | New word | What it means |
|---|---|---|
| walk | release test | testing a release by hand, check by check |
| walk sheet | release test sheet | the generated page for one release and platform |
| walker | tester | the person doing the release test |
| sitting | section | a group of checks tested with one setup |
| survey | what changed | the list of screens this release changed |
| walk order | section order | the authored file that lists the sections |
| mark or verdict, as shown to a person | result | pass, fail, partial, question, blocked, N/A or excused |
| check | check | unchanged |

The stored result values stay as they are: `pass`, `partial`, `na`, `excused`, `blocked`, `question`, `fail`.

"Section" already named the three kinds of test (feature, regression, automated) in `TESTING.md` and in project-os-cockpit ADR-0039. Edwin decided on 2026-09-27 that the old meaning is renamed: those three are now **kinds** of test ("test kinds"), in the same rename. After it, "section" means only a group of checks tested with one setup.

**What is not rewritten.** Closed ADRs, change notes and archived notes are history. They keep the old words. A new note that cites one of them may quote it.

**The rename map.** Every name below changes in the same template release. The left column is today's name.

| Kind | Old name | New name |
|---|---|---|
| Generator and validator | `tools/scripts/walk-sheet.py` | `tools/scripts/release-test.py` |
| Tag rewriter | `tools/scripts/walk-tags.py` | `tools/scripts/release-test-tags.py` |
| Test harness | `tools/scripts/test-walk-sheet.sh` | `tools/scripts/test-release-test.sh` |
| Test harness | `tools/scripts/test-walk-preparation.py` | `tools/scripts/test-release-test-preparation.py` |
| Consumer script (your-trainer) | `tools/scripts/make-walk-route-fixtures.py` | `tools/scripts/make-release-test-route-fixtures.py` |
| Consumer script (your-trainer) | `tools/scripts/test-walk-corpus.py` | `tools/scripts/test-release-test-corpus.py` |
| Section order file (consumer) | `docs/tests/acceptance/WALK.md` | `docs/tests/acceptance/RELEASE-TEST.md` |
| Procedure folder (consumer) | `docs/tests/acceptance/walk/` | `docs/tests/acceptance/release-test/` |
| Template for the order file | `docs/__templates__/walk.md` | `docs/__templates__/release-test.md` |
| Template for a procedure | `docs/__templates__/procedure.md` | unchanged |
| Procedure frontmatter | `sitting:` | `section:` |
| Procedure frontmatter | `state_for:` | replaced by a group's start line (REQ-0033) |
| Check frontmatter | `walk_readiness_for:` | `readiness_for:`, the same name a procedure uses |
| Procedure and check frontmatter | `readiness_for:` values | gain an optional `result:`, the suggested result (REQ-0033) |
| Change note frontmatter | none | `platforms:` (REQ-0035) |
| Skill | `tools/skills/walk-procedure/` and its copies under `.claude/skills/` and `.agents/skills/` | `tools/skills/release-test-procedure/` |
| New skill | none | `tools/skills/release-test-prep/` (REQ-0036, D3) |
| Instruction section | `TESTING.md`, "The walk" | `TESTING.md`, "The release test" |
| Instruction section | `SCHEMAS.md`, "`walk.md` — the walk order (`WALK.md`)" | `SCHEMAS.md`, "`release-test.md` — the section order (`RELEASE-TEST.md`)" |
| Instruction table | `TAXONOMY.md`, "Acceptance outcomes", column "mark" | column "result" |
| Other instructions and skills | "walk", "sitting", "survey" in `LIFECYCLE.md`, `QUALITY.md`, `STATUSES.md`, `HOOKS.md`, `WRITING.md`, `GLOSSARY.md`, `INDEX.md`, `docs/tests/README.md`, `docs/releases/ledgers/README.md`, the release-prep, release-verification, test-authoring, change-note, close-out and feature-scaffold skills, `ADAPTER.md`, the verification-gate and document-first-gate hooks, `CLAUDE.md`'s skill list, and the generated Cursor and Codex adapters | the new words |
| Code identifiers | `survey`, `survey_tag`, `survey_release`, `survey_problem`, `sitting`, `sitting_name`, `walk_payload`, `walk_path` and the like | `what_changed`, `what_changed_tag`, `section`, `section_name`, `release_test_payload`, `release_test_path` and the like |
| Cockpit bundle (project-os-cockpit) | `walk_sheet_bundled.py` | `release_test_bundled.py` |
| Cockpit route (project-os-cockpit) | `/api/cockpit/walk` | `/api/cockpit/release-test` |
| Cockpit tests (project-os-cockpit) | `test_walk_payload.py`, `test_walk_bundle.py`, `test_walk_survey.py`, `walk-page.test.mjs` | `test_release_test_payload.py`, `test_release_test_bundle.py`, `test_what_changed.py`, `release-test-page.test.mjs` |

**No shims.** The old script names are not kept as aliases. A consumer that calls one gets "file not found" and the migration message in the sync log. Edwin asked for one rename, not a period with two names.

**Old names in consumer files are migrated, then refused.** A migration script rewrites a consumer's `WALK.md`, `walk/` folder, `sitting:` and `walk_readiness_for:` fields. After that, the validator reports an old name as an error that names the new one. Nothing is silently ignored.

**The ledger field name is a separate question.** A ledger entry stores its result under the key `mark`, as in `{"check": "TST-0001", "mark": "pass", ...}`. Sealed ledgers are records and are never rewritten. Two readings fit D1:

- (a) Keep `mark` as the stored key. Only what a person sees says "result".
- (b) New entries write `result`. Every reader accepts `mark` forever, so sealed ledgers stay valid. The migration script rewrites unsealed `WORKING-*.json` ledgers once.

Edwin chose (b) on 2026-09-27. New entries write `result`, every reader accepts `mark` forever, and the migration script rewrites unsealed `WORKING-*.json` ledgers once.

### D2. The short expected result lives in the test note

Each check's `## Expect` lines are shortened in the test note itself. They become one short line per thing to see, for one platform. Procedures do not carry their own copy of any expectation. A procedure line is its tags only, such as `` - `TST-0657.1` ``. The generator prints the check's current Expect line in its place.

Reasons:

- A result counts only if the tester read the check's own words (project-os-cockpit ADR-0041). With one source, the page always shows those words.
- One source cannot drift. Today the procedures quote the checks and must be re-quoted whenever a check is reworded (ADR-0049).

**Per-platform lines.** Where an expectation differs by platform, the test note writes one line per platform, marked with the platform name in square brackets: `- [android] The Hub opens from the equipment icons.` and `- [ios] The Hub opens from Settings.` An unmarked line holds on every platform. The generator prints only the current platform's lines and the unmarked ones. The pairing rule of ADR-0049, line N for step N, counts the lines that apply on the current platform.

**Shortening keeps the meaning.** A shortened Expect line must assert the same thing as the long one. A change of meaning is a change to the check, and it reopens the check in the ledger as any other change does.

### D3. An agent may write what cannot be generated

Some of the new page's text cannot come from the notes mechanically. Edwin, 2026-09-27: "if this cannot be fully automated, I have no problem if we would use an LLM agent / skill to hand edit some of this info when going to a release". An agent may write:

- the per-section, per-platform "what changed" lines;
- shortened Expect lines in test notes;
- procedure actions rewritten as short lines.

A new skill, `tools/skills/release-test-prep/`, does these edits during release preparation. It then runs the length guard and the validator, and keeps its edits only if both pass. The owner reviews the edits in the commit, as with any other change to a note.

### Amendments to earlier decisions

- **ADR-0029, rule 5** ("each row prints Setup, Steps and Expect"): a row now prints a number, one action line, the check's Expect line for this platform, and its tag.
- **ADR-0045, decisions 3 and 4**: a procedure step no longer names its screen, and an expectation line is its tags only. Quoted lines are refused once consumers have migrated. The procedure groups its steps under headings, each with a start state written once.
- **ADR-0046, clarification on `state_for:`**: the start state belongs to a group and is printed again only after skipped checks. `requires:`, `setup_for:`, `step_platforms:`, `action_for:`, `capture_for:`, `use_capture:` and `timer_for:` stand.
- **ADR-0049**: tag-only lines become the only form. `release-test-tags.py` converts any remaining quoted line to tags.

## Consequences

- Every name in the rename map changes in one template release. Consumers take it at their next sync and run the migration script ([[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths|RISK-0005]]).
- Five executable test notes in this repo run `test-walk-sheet.sh` or `test-walk-preparation.py`: TST-0009, TST-0010, TST-0011, TST-0023 and TST-0033. Their `command:` lines change with the rename.
- Test notes become the only home of an expected result. Rewording one changes every page that shows it, and no procedure needs a matching edit.
- Release preparation gains an agent step. The length guard starts as a warning and becomes an error once your-trainer's Android and iOS sections pass it.
- The printed check numbers restart at 1 in each section. Text the generator writes, such as "Later: check 13 needs Pro", uses those numbers. Procedure prose no longer refers to step numbers, which answers [[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose|ISS-0086]].

## Questions Edwin answered on 2026-09-27

Edwin answered the open questions on the same day, choosing the recommended option each time.

1. **The ledger's stored key becomes `result`.** New entries write `result`. Readers accept `mark` forever, so sealed ledgers stay valid. Unsealed `WORKING-*.json` ledgers are migrated once.
2. **The three kinds of test stop being called sections.** Feature tests, regression tests and automated tests are "test kinds" in `TESTING.md`, in code and in project-os-cockpit, in the same rename. "Section" then has one meaning: a group of checks tested with one setup.
3. **A section's word budget is set by the pilot.** The rewritten Equipment section is measured, and the budget is set from it, for example as words per check. It starts as a warning, like the line limits.

## Decision record

> [!note] Accept — 2026-09-27 (user:edwin)
> "1. do as recommended. 2. rename all in one go. (to avoid confusion later on) ... if this cannot be fully automated, I have no problem if we would use an LLM agent / skill to hand edit some of this info when going to a release?"
> Recorded as Option 1. Point 1 is D2: the short expected text lives in the test notes. Point 2 is D1: internal names are renamed too. The last sentence is D3. Edwin then answered the remaining questions: the ledger key becomes `result`, the three kinds of test are renamed "test kinds", and the pilot sets the section budget.
