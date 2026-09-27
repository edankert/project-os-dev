---
type: "[[task]]"
id: TASK-0190
aliases: ["TASK-0190"]
title: "The generator prints each section as what changed, setup in three parts, and numbered checks in groups, in both the sheet and the cockpit's JSON"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0188]]", "[[TASK-0189]]"]
blocks: []
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"]
tests: ["[[TST-0045-A-Release-Test-Section-Prints-Numbered-Checks-In-Groups-From-One-Model]]"]
---

# The generator prints each section as what changed, setup in three parts, and numbered checks in groups, in both the sheet and the cockpit's JSON

This is the new output. For each platform the generator lists the sections with their counts and bench lines. For each section it prints what changed, the setup split three ways, and the checks in groups, numbered from 1.

## Definition of Done
- [x] Per platform: the sections in order, each with its owed check count and one on-the-bench line built from the order file's `bench:` list. project-os b2dc17f: a "Sections" table before what changed, `bench_line` joining `bench:` with " · ", "Nothing extra" when empty, Unplaced last. TST-0045; mutation: table removed, 3 failures.
- [x] Per section: what changed, then setup, then checks. `render_section`; the order is asserted by line numbers in TST-0045.
- [x] Setup is split into "On the bench", "Before you start" (numbered) and "Later" (a setup item needed by one printed check, naming that check's number). `_setup_payload`: `bench:` from the order file; `setup_for: all` items and items first needed by check 1 go before; others go later, named by the first printed check that needs them, sorted. Legacy prose setup splits into one entry per list item or paragraph. Mutations: later always before, 1 unit failure; items not split, 1.
- [x] Each check prints as its section number, one action line, this platform's Expect line and its tag. No expected line starts with "Step N:". `_procedure_checks` numbers the kept steps from 1; `shown_expected` drops the list marker, the tags and a leading "Step N:" (putting back an emphasis marker it took) and capitalises what is left. Mutations: procedure numbers printed, 1 and 2 unit; "Step N" kept, 1 and 1; not capitalised, 1 and 1.
- [x] A group's start state prints once, and again before the next printed check when checks in between were skipped. "Start:" under the group heading, "Start again:" after a gap, "Start:" where `state_for` changes it. Mutations: no restate after a skip, 2; label, 1; group start not printed, 3.
- [x] A readiness problem prints as one line: the reason, the issue if any, and "Suggested: <result>". `readiness_line`; without `result:` a preparation suggests Blocked and a decision Question (`DEFAULT_RESULT`). Mutation: one default, 2 unit.
- [x] A section with no procedure prints one row per owed check, its title as the action line. Linked to the note, with its Setup and Steps indented under it so it can still be tested from the page (TESTING.md rule 5). Mutation: those parts dropped, 10 failures.
- [x] The Markdown sheet and the JSON payload carry the same sections, groups, numbers and lines, proven by one test that compares them. The Markdown is rendered from `payload(sheet)`, and TST-0045 renders the `--json` output with `render_page` and compares it with the sheet byte for byte. Mutation: Markdown built differently, 1.
- [x] The JSON payload's shape is documented in TESTING.md or SCHEMAS.md for the cockpit to read. TESTING.md, "The release test", rule 10 (project-os d4b4010).
- [x] ISS-0086: the only step numbers a tester sees are the printed ones, and generated text refers to them. Done in the generator: "Check 13 needs", "Compare with what you kept at check 1" and the start lines use printed numbers; mutation: comparison using the procedure's number, 1 unit. ISS-0086 itself stays open until the cockpit's section page draws these numbers (project-os-cockpit TASK-0643), which is the second half its own Expected names.

## Steps
- [x] Build the new section model in the generator.
- [x] Render it to Markdown and to JSON from the same model.
- [x] Update TESTING.md, "The release test", rules 5 and 9 (and a new rule 10 for the JSON).
- [x] Regenerate Your Trainer's Equipment section on Android from a copy and compare it with the approved example.

## Notes
- The cockpit draws the page from the JSON: project-os-cockpit FEAT-0155, the release test page in the Tests pane. The payload shape is written in TESTING.md rule 10 for TASK-0640 to read; the cockpit has not built against it yet.
- The approved example is the Equipment Hub section, Android, v2.2.0. It was a static HTML page Edwin approved on 2026-09-27.
- **Your Trainer's Equipment section on Android**, from a scratch copy with its current procedure (not yet rewritten; that is your-trainer TASK-0975): 3,052 words and 6 headings, against about 4,300 words and 28 headings on today's page and about 1,000 words on the approved example. What is still longer than the example: the action lines still start with a bold screen name and run to 40 words; the expected lines are the checks' full Expect sentences, some mixing both platforms; the "Later" items are the procedure's long setup sentences; and state_for lines repeat "the ride from step 10". All four are the pilot's rewrite and TASK-0977's shorter Expect lines, not the generator.
- **Checks already passed.** Beside each expected line only the tags still owed print. A passed tag stays in the JSON (`passed`, `passed_lines`), for a host that wants to show it.
- **Per-check rows keep Setup and Steps.** REQ-0033 says a row's action is the check's title. A title alone cannot be tested, so the row also carries the note's Setup and Steps, indented. The length check (TASK-0192) will count them.
- Your Trainer on the scratch copy: the Android page is 31,953 words (37,787 before this task), the iOS page 64,838 (78,567).
