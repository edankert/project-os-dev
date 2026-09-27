---
type: "[[test]]"
id: TST-0045
aliases: ["TST-0045"]
title: "A release test section prints what changed, setup in three parts and numbered checks in groups, and the Markdown is rendered from the JSON"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0190-The-Generator-Prints-Sections-Groups-And-Numbered-Checks]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-release-test.sh"
command: "bash ../project-os/tools/scripts/test-release-test.sh && python3 -B ../project-os/tools/scripts/test-release-test-preparation.py"
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
tasks: ["[[TASK-0190]]"]
requirements: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]"]
issues: ["[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"]
artifacts: []
evidence: []
adequacy: "2026-09-27. The harness has 254 assertions, about 60 of them rewritten from the old layout, and the unit tests 28. Fourteen mutations of release-test.py, each failing the harness or the unit tests: procedure numbers printed instead of section numbers, 1 and 2 unit; Later items always put before, 1 unit; no start restated after a skip, 2; the Start again label, 1; passed tags printed as owed, 2; one default result for both kinds, 2 unit; a leading Step N kept, 1 and 1 unit; per-check Setup and Steps dropped, 10; the sections table removed, 3; not capitalised, 1 and 1 unit; Markdown not rendered from the payload, 1; group start not printed, 3; setup items not split, 1 unit; a comparison naming the procedure's step number, 1 unit. Pristine 254 of 254 and 28 of 28."
related: ["[[TST-0043]]", "[[TST-0044]]"]
---

# A release test section prints numbered checks in groups from one model

## Purpose

REQ-0033 has each section print what changed, setup in three parts, and its checks numbered from 1, each one action line and one expected line with its tag. This test shows the page has that shape, and that the Markdown sheet is rendered from the same data `--json` prints.

## Procedure

`bash ../project-os/tools/scripts/test-release-test.sh`, then `python3 -B ../project-os/tools/scripts/test-release-test-preparation.py`.

## Expected results

- A table before the sections lists each section in order with its owed count and its bench line, and Unplaced last.
- A section prints what changed, then Setup, then Checks.
- Setup splits into On the bench, a numbered Before you start, and Later lines that name the printed check needing them.
- Printed checks are numbered from 1 in the section; lines about a check, such as a comparison, use those numbers.
- Each expected line carries only the tags still owed, loses a leading "Step N:", and starts with a capital.
- A group's Start line prints once, and "Start again" prints after skipped steps.
- A readiness problem is one line ending "Suggested: Blocked." for preparation or "Suggested: Question." for a decision, unless `result:` names another.
- A section with no procedure prints one numbered check per owed check, linked to its note, with its Setup and Steps under it.
- Rendering the `--json` output with `render_page` gives back the Markdown sheet byte for byte.
