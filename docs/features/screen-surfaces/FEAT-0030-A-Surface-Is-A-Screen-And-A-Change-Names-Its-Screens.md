---
type: "[[feature]]"
id: FEAT-0030
aliases: ["FEAT-0030"]
title: "A surface is a screen, a change note names the screens it changed, and the survey shows those screens before and after"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["Edwin, 2026-09-14, approved goal: 'It opens with the app screens this release changed: what each one now shows, with before and after screenshots.'", "Edwin, 2026-09-14: no new screens concept; update the surfaces to be the real screens"]
goal: "The walk sheet's survey lists the app screens a release changed, each with a sentence a rider would understand and a before and after capture, because surfaces are screens and every change note says which screens it changed."
requirements: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tasks: ["[[TASK-0116-TAXONOMY-States-What-A-Surface-Is]]", "[[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed]]", "[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
release: ""
acceptance_exception: ""
related: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them]]"]
---

# A surface is a screen, and a change names its screens

## Goal

The survey at the top of a walk sheet lists the app screens a release changed. Each screen carries the sentence every change wrote about it, in words a rider would understand, and a capture of the screen at the last release beside a capture of the release candidate. No test id appears.

Today the survey groups invalidated checks by `area:` and quotes "Acceptance checks reopened" sections. On your-trainer that prints "Hardware" and "Riding — structured", which are test categories, above text that justifies reopening a check rather than describing a screen.

## Scope

In, all in the template repo:

- **What a surface is** ([[TASK-0116-TAXONOMY-States-What-A-Surface-Is|TASK-0116]]). TAXONOMY.md and `surface.md` say a surface is a screen by default and state ADR-0044's four rules: states, dialogs as children, checks that cross screens, and per-platform placement. Plus where a gallery capture key maps to a surface and an optional state.
- **What a change note records** ([[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed|TASK-0117]]). `change.md`'s Impact section lists `SUR-*` ids, each with one rider-facing sentence. The change-note and close-out skills ask an LLM to draft it from the diff.
- **How the survey is built** ([[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures|TASK-0118]]). TESTING.md rule 2 and `walk-sheet.py`: change notes merged since the last release tag, grouped by the surfaces they name, with before and after captures.

Out:

- Rewriting any consumer's surfaces or `area:` values. your-trainer does that in its PHASE-024.
- Taking screenshots. The template names where captures are found; each consumer's gallery tool produces them.
- The cockpit's screen cards (project-os-cockpit FEAT-0150).

## Acceptance

- TAXONOMY.md carries the four rules once, and `surface.md` points there.
- A change note written from the template has an Impact section that lists `SUR-*` ids with one sentence each, and the close-out skill tells the agent to draft it with an LLM from the diff.
- On a fixture repo with a release tag, two change notes after it and a capture map, the sheet's survey lists exactly the surfaces those notes name, with their sentences and both captures, and contains no `TST-` string. [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After|TST-0011]] holds this.

## Risk scan

The survey gains one runtime input: the most recent release tag in git. A shallow clone has none, so the survey says it cannot find the tag rather than printing an empty list. No new external dependency, environment variable or credential. Captures are image files in each consumer repo; their size in git is that repo's risk (your-trainer RISK-0010), not the template's. No `RISK-*` here.

## Links

- Decision: [[ADR-0044-A-Surface-Is-A-Screen-By-Default]], and ADR-0045 decisions 1 and 2.
- Requirement: [[REQ-0029-A-Release-Walk-Reads-As-A-Script]] criteria 1 to 3.
- Downstream: your-trainer FEAT-0120 (its surfaces become screens, its change notes name them), project-os-cockpit FEAT-0150 (screen cards).
