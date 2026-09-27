---
type: "[[issue]]"
id: ISS-0086
aliases: ["ISS-0086"]
title: "A walk's printed step numbers do not match the step numbers the procedure's own text refers to"
status: fixed
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-27
source: ["FEAT-0033 independent review, round 1, reviewer A, 2026-09-24", "Edwin, 2026-09-25: 'do as suggested' (print the procedure's own step number)"]
reported_by: review
question: ""
severity: medium
component: "tools/scripts/walk-sheet.py; project-os-cockpit walk page"
parent: ""
related: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]", "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]"]
tests: []
tasks: ["[[TASK-0162]]", "[[TASK-0190]]"]
---

# A walk's printed step numbers do not match the step numbers the procedure's own text refers to

## Problem

A walker following the sheet reads "For step 21" in the setup, but step 21 is printed as step 3. The sheet numbers the steps it keeps 1, 2, 3 and adds "(source step N)", while a procedure's text refers to steps by their number in the procedure. Your Trainer's REL-0017 Android sheet, Sitting 13: the setup says "For step 21" (printed as step 3), and printed step 2 says "The connection-copy sweep in step 3 is done", a sweep printed as step 1. Sitting 5's setup says "ready for step 49".

## Why it is not simply changed

The sheet's numbering is one line in `render_procedure`. The cockpit's walk page numbers steps itself: `acceptance.py` builds `display_number` from the position, `renderer.ts` says "Source numbers are the procedure file's own and stay secondary (B3)", and `walk-page.test.mjs` asserts "a display position, not source step 13". B3 is a criterion of project-os-cockpit FEAT-0151 (clear context and progress, "Step 1 of 4"). Changing only the sheet would show the same step under two numbers. Changing the cockpit collides with the session working on FEAT-0151 now. The options and a recommendation are in `question:`.

## Expected

Whatever number a walker sees for a step matches what the procedure's text calls it, and the sheet and the cockpit show the same number.

## Where this stands

The redesigned release test answers this issue, and [[TASK-0190]] closes it. On the new page, checks are numbered from 1 in each section, those printed numbers are the only step numbers a tester sees, and text the generator writes refers to them ("check 13 needs Pro"). Procedure prose no longer cites step numbers ([[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks|ADR-0050]]).

- **Generator half, first fix: done.** [[TASK-0162]], template `cd50653`, prints each kept step under its number in the procedure, as Edwin chose on 2026-09-25 (option 1). TASK-0190 replaces that numbering with the section's own.
- **Cockpit half: no longer a separate change.** The handoff below asked the cockpit's walk page to show the procedure's number. The page is being rebuilt as project-os-cockpit FEAT-0155, the release test page in the Tests pane, which reads TASK-0190's numbers directly. The handoff is kept for the record and should not be applied on its own.

- **Generator: done, 2026-09-27.** [[TASK-0190]], template `b2dc17f`, numbers the printed checks from 1 in each section, and every line the page writes about a check uses that number. The JSON the cockpit reads carries the same numbers.

This issue is `fixed` when the cockpit's release test page (project-os-cockpit TASK-0643) draws those numbers.

## Decision and progress, 2026-09-25 (superseded by the section above)

Edwin chose option 1: the sheet and the cockpit both show the procedure's step number, and the cockpit keeps its progress count separate.

- **Generator half: done.** [[TASK-0162]], template `cd50653`. It is deliberately not synced to a repo with a walk (project-os-cockpit, your-trainer) yet; project-os-dev, which has none, took it on 2026-09-25.
- **Cockpit half: open.** It belongs to the session that owns project-os-cockpit FEAT-0151. This issue is fixed when both halves land in one sync.

### Handoff for the cockpit session

> The template's `walk-sheet.py` at `cd50653` prints each kept procedure step under its number in the procedure (project-os-dev ISS-0086, option 1, Edwin 2026-09-25), because procedure text refers to steps by those numbers ("for step 21"). The walk page should show the same number. In `acceptance.py`, the walk payload's `display_number` is the kept-step position; `renderer.ts` `walkStepPosition` and the card headings use it, and `walk-page.test.mjs` asserts "a display position, not source step 13". Change the headings and "waits on step N" text to the step's own number (`number`), keep "Step 1 of 4" progress as a separate count (FEAT-0151 B3), then sync the template (walk-sheet.py and both bundled copies, test-walk-preparation.py, TESTING.md) in the same commit, so the sheet and the page change together. your-trainer takes the same template sync afterwards.

## Fixed 2026-09-27

project-os-cockpit TASK-0643 draws the release test page from the generator's JSON, so the cockpit shows the same check numbers as the sheet. Checked on your-trainer's Fresh install section in the cockpit, TST-0092 step 4: checks 1 to 7, as the sheet numbers them.
