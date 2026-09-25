---
type: "[[issue]]"
id: ISS-0086
aliases: ["ISS-0086"]
title: "A walk's printed step numbers do not match the step numbers the procedure's own text refers to"
status: open
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["FEAT-0033 independent review, round 1, reviewer A, 2026-09-24", "Edwin, 2026-09-25: 'do as suggested' (print the procedure's own step number)"]
reported_by: review
question: "Edwin agreed on 2026-09-25 that the sheet should print each step's number in the procedure. The cockpit's walk page shows position numbers on purpose, under project-os-cockpit FEAT-0151 criterion B3, and a test pins them. Options: (1) the sheet and the cockpit both show the procedure's number, with the cockpit's progress count (1 of 4) kept separate. That changes FEAT-0151 in a repo where another session is working on it. (2) The sheet only; the cockpit keeps position numbers, so the two show different numbers for the same step. (3) Neither; procedures stop referring to steps by number, which is Your Trainer's TASK-0960 to do. Recommendation: (1), done by the session that owns FEAT-0151, with the generator change landing in the same sync."
severity: medium
component: "tools/scripts/walk-sheet.py; project-os-cockpit walk page"
parent: ""
related: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]"]
tests: []
---

# A walk's printed step numbers do not match the step numbers the procedure's own text refers to

## Problem

A walker following the sheet reads "For step 21" in the setup, but step 21 is printed as step 3. The sheet numbers the steps it keeps 1, 2, 3 and adds "(source step N)", while a procedure's text refers to steps by their number in the procedure. Your Trainer's REL-0017 Android sheet, Sitting 13: the setup says "For step 21" (printed as step 3), and printed step 2 says "The connection-copy sweep in step 3 is done", a sweep printed as step 1. Sitting 5's setup says "ready for step 49".

## Why it is not simply changed

The sheet's numbering is one line in `render_procedure`. The cockpit's walk page numbers steps itself: `acceptance.py` builds `display_number` from the position, `renderer.ts` says "Source numbers are the procedure file's own and stay secondary (B3)", and `walk-page.test.mjs` asserts "a display position, not source step 13". B3 is a criterion of project-os-cockpit FEAT-0151 (clear context and progress, "Step 1 of 4"). Changing only the sheet would show the same step under two numbers. Changing the cockpit collides with the session working on FEAT-0151 now. The options and a recommendation are in `question:`.

## Expected

Whatever number a walker sees for a step matches what the procedure's text calls it, and the sheet and the cockpit show the same number.
