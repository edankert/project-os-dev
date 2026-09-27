---
type: "[[feature]]"
id: FEAT-0040
aliases: ["FEAT-0040"]
title: "The release test reads in short lines: the generator feeds one short page per section and platform"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["Edwin, 2026-09-27: 'We have a problem with the amount of text the walk procedure has. It is just a wall of text, there are no clear paragraphs or headings and all together it is just way too much. [...] Review and suggest how to make this more human friendly. More concise and better formatting to start with!!'", "Edwin, 2026-09-27: 'At first I want to see concise information about what has changed for the section we plan to test (including the before/after screen-shots), then I want to see the setup for the section (but this can be hidden away behind a open/close option) and then I would like to see the actual checks as concise and complete as possible.'", "Edwin, 2026-09-27: 'on the checks, I need to be able to record not just pass and fail, so please add back the other options as well'", "Edwin, 2026-09-27: 'I have said this before I don't like calling this a walk, can we think about what this is and how we present this / how to open this in the cockpit?'", "Edwin, 2026-09-27: '1. do as recommended. 2. rename all in one go. (to avoid confusion later on) ... if this cannot be fully automated, I have no problem if we would use an LLM agent / skill to hand edit some of this info when going to a release?' (1: the short expected text lives in the test notes; 2: internal names are renamed too)", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]"]
goal: "The template's generator, notes and skills produce, for each section and platform, a page a tester can read at the bench: what changed, setup folded away, and each check as a number, one action line, one expected line and its tag."
requirements: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[REQ-0034-A-Check-Writes-Its-Expected-Result-Once-Per-Platform]]", "[[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform]]", "[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]", "[[REQ-0037-The-Walk-Is-Called-The-Release-Test-Everywhere]]"]
tasks: ["[[TASK-0187]]", "[[TASK-0188]]", "[[TASK-0189]]", "[[TASK-0190]]", "[[TASK-0191]]", "[[TASK-0192]]", "[[TASK-0193]]", "[[TASK-0194]]", "[[TASK-0195]]", "[[TASK-0196]]"]
release: ""
acceptance_exception: ""
reviewed_by: "model:claude-opus-5-5 (two reviewers, fresh contexts)"
review_date: 2026-09-27
review_verdict: "approved"
review_round: 2
related: ["[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]", "[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]", "[[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey]]", "[[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths]]"]
---

# The release test reads in short lines

## Goal

A tester reads one short page per section and platform instead of a 37,000-word sheet. The template's generator produces what that page shows, and the page itself is drawn by project-os-cockpit. Each check becomes a number, one short action line, one short expected line and its TST tag.

The decisions are in [[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks|ADR-0050]]: rename the walk to the release test everywhere (D1), keep each short expected result in the check's own note (D2), and let an agent write what cannot be generated (D3).

## The shared finish line

Edwin set one goal for this feature, project-os-dev FEAT-0040, project-os-cockpit FEAT-0155 and your-trainer FEAT-0129 on 2026-09-27: **Edwin can test v2.2.0 on Android and iOS from the cockpit's Tests pane, every section opens in the approved layout, and one `release-test-prep` request prepared all of them.** your-trainer FEAT-0129, "The shared finish line for all three features", states the seven conditions and the nine stages. The three features finish together.

## Scope

In scope, all in the template (`~/Dev/repos/project-os`):

- **The generator's new output** ([[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line|REQ-0033]]). Per platform: sections, each with a check count and one "on the bench" line. Per section: what changed, setup in three parts, and checks in groups with a start state written once. Readiness problems become one line saying why and which result fits. The same content goes to the Markdown sheet and to the JSON the cockpit reads.
- **Per-platform Expect lines in test notes** ([[REQ-0034-A-Check-Writes-Its-Expected-Result-Once-Per-Platform|REQ-0034]]). A line marked `[android]` or `[ios]` prints only on that platform.
- **"What changed" per section and platform** ([[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform|REQ-0035]]). Change notes declare `platforms:`. Each section lists only its own screens' changes, one line per change, with before and after screenshots and a flag when a screenshot is older than the change.
- **The length check and the release-preparation skill** ([[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported|REQ-0036]]). The validator warns when an action line passes about 20 words, an expected line about 25, or a section its budget. A new skill, `release-test-prep`, writes the short text with an agent and runs the check.
- **The rename** ([[REQ-0037-The-Walk-Is-Called-The-Release-Test-Everywhere|REQ-0037]]). Every name in ADR-0050's rename map, including the `walk-procedure` skill, which becomes `release-test-procedure`.

Out of scope:

- The page in the cockpit: project-os-cockpit FEAT-0155, the release test page in the Tests pane.
- Your Trainer's own procedures and test notes: your-trainer FEAT-0129, the rewrite of the procedures and test notes with the Equipment section pilot.
- Rewriting closed ADRs, change notes and archived notes.
- Recording results other than pass and fail. The template's ledger already stores all seven (pass, fail, partial, question, blocked, N/A, excused); offering them on the page is the cockpit's work.

Open for Edwin, from ADR-0050: whether the ledger's stored key `mark` becomes `result`, and what to do about "section" already naming the three kinds of test (feature, regression, automated). REQ-0036 adds a third: the form of a section's word budget.

## Acceptance

- [x] For Your Trainer's Equipment section on Android, the generated page has the approved example's shape: what changed for Android only, grouped by screen; setup in "On the bench", "Before you start" and "Later"; checks numbered from 1 in groups, each a single action line, a single expected line and a tag. TST-0040, tested 2026-09-27.
- [x] No Android page prints an iOS-only Expect line, and no iOS page prints an Android-only one. TST-0040 on the Equipment section; your-trainer TASK-0976 and TASK-0978 moved the rest of its iOS wording into `action_for:` and iOS setup items.
- [x] No expected line on the page starts with "Step N:". TST-0040; the generator strips the prefix (`_STEP_PREFIX_RE`).
- [x] A group's start state prints once, and again only after checks that were skipped. TST-0040; `test-release-test.sh`.
- [x] The length check warns on an over-long line or section, and a switch turns the warning into an error. REQ-0036; since template aa5fd7e the default is an error.
- [x] `release-test-prep` shortens lines with an agent and keeps its edits only when the length check and the validator pass. REQ-0036; the skill prepared your-trainer's v2.2.0 on 2026-09-27, and a reviewer checked each batch before it was kept.
- [x] No file outside history in the template uses "walk", "sitting" or "survey" for this feature, and a consumer's old names are migrated by a script and then refused with the new name. REQ-0037.

## Verification

Full run in project-os, 2026-09-27, at 116d14e: every `tools/scripts/test-*.sh` passes (`test-release-test.sh`: 270 assertions, 0 failures), `test-release-test-preparation.py` OK, `test-retention.py` OK (26 assertions), and `validate-docs.sh` OK. On the consumers: your-trainer's release test has no error or warning on Android or iOS, and project-os-cockpit's 2,136 Python tests pass against the synced bundle.

Not yet run. The acceptance check is [[TST-0040-A-Release-Test-Section-Reads-As-Short-Lines|TST-0040]].

## Links

- Plan: [[features/release-test/plan/PLAN|PLAN]]
- Earlier work this changes: [[FEAT-0029-The-Walk-Sheet|FEAT-0029]] (the sheet), [[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens|FEAT-0030]] (changed screens), [[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure|FEAT-0031]] (procedures), [[FEAT-0033-A-Walk-Keeps-Required-Preparation|FEAT-0033]] (declared preparation)
- Risk: [[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths|RISK-0005]]

## Review

Round 1, 2026-09-27. Two independent reviewers (model:claude-opus-5-5, fresh contexts) reviewed project-os 681675d..116d14e. Every guard they removed was caught by a test, 14 in all. Combined verdict: **changes-requested**.

| Claim | Combined | What was done (project-os e292e4e, aee9c6a, 8088594) |
|---|---|---|
| Rename: no template file uses the old words, and readers accept `mark` (REQ-0037) | refuted | The template's shipped `tools/cockpit/` was from 2026-09-19. It read WALK.md through `walk_sheet_bundled.py` and refused a ledger migrated to `result`. It is now released from project-os-cockpit's latest, and it reads your-trainer's ledgers. |
| Tag `.N` pairs with the Nth line (REQ-0034) | refuted | When a check's Expect lines did not number one per step on a platform, every tag printed every line, silently. `--check` now refuses such a tag, naming the check, the platform and both counts. |
| TST-0040 tested | the packet said "not yet run" | TST-0040 is a manual check in a repo with no ledger. Its result is `last_verified: 2026-09-27` and its "Tested" section, which one reviewer reproduced. |
| Every other claim | holds | — |

Fixed from the observations as well:

- Identical Expect lines no longer shift the pairing.
- A "Step N:" prefix in single emphasis is stripped.
- With no release tag, the page says why the short lines are unused.
- A short line prints once per change and screen.
- The heading says "What changed on Android".
- The prep skill calls over-long lines errors.

Kept as they are, with the reason:

- `PLATFORMS_REQUIRED_FROM` is 2026-09-28 on purpose. Notes written before it get a warning.
- A sync deletes a renamed old path whether or not it was edited, as its docstring says.
- A group with no Start line after skipped checks prints no start when the state has not changed.
- Some project-os-dev test note file names keep the old words. They are identifiers.
- Two reviewers working in one tree at once was unsafe. Round 2 reviewers work in their own worktrees.

Round 2, 2026-09-27. Two reviewers, each working in its own worktree, answered **fixed** for both refuted claims. Removing the new pairing refusal failed two tests. The shipped cockpit loads your-trainer's three ledgers and has no reader of the old files. Both returned **approved**. A comment in the shipped `cockpit.py` still said "the walk survey", and it was corrected at its source (project-os 2c037dd).
