---
type: "[[test]]"
id: TST-0044
aliases: ["TST-0044"]
title: "Each section lists what changed on its own screens for one platform, flags a picture older than its change, and uses the short lines only while they match the last release tag"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0191-Each-Section-Lists-What-Changed-On-This-Platform]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-release-test.sh"
command: "bash ../project-os/tools/scripts/test-release-test.sh && python3 -B ../project-os/tools/scripts/test-release-test-preparation.py"
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
tasks: ["[[TASK-0191]]"]
requirements: ["[[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform]]"]
issues: []
artifacts: []
evidence: []
adequacy: "2026-09-27, the block headed 'REQ-0035 (TASK-0191)' in test-release-test.sh and the rewritten TST-0011 assertions (the harness has 245), and four unit tests in test-release-test-preparation.py (25 in all). Fifteen mutations of release-test.py, each failing the harness or the unit tests: platforms: ignored, 1 failure; an [other] line kept, 1; a section's share not filtered, 2 and 1 unit; the overview not filtered, 2 and 1 unit; a section's checks not giving it screens, 1 unit; the stale flag off, 2; an uncommitted picture flagged, 1; a short-lines tag not compared, 2; short lines not used, 2; a new note without platforms: not refused, 1; an unknown platform not refused, 1; a missing short line not warned, 1; the short-lines file read as a procedure, 1; undeclared notes named in a one-platform project, 1 unit; the 'nothing changed' line off, 1 unit. Pristine 245 of 245 and 25 of 25."
related: ["[[TST-0011]]", "[[TST-0042]]"]
---

# Each section lists what changed on its own screens for one platform

## Purpose

REQ-0035 moves "what changed" from one long list at the top of the page to the head of each section, for the platform being tested only. This test shows that a section lists the changes to its own screens, that a change note's `platforms:` and an Impact line's `[platform]` mark decide where it is listed, that a candidate picture committed before its change is flagged, and that the short lines from `what-changed-<platform>.md` replace the Impact sentences only while they name the last release tag.

## Procedure

`bash ../project-os/tools/scripts/test-release-test.sh`, then `python3 -B ../project-os/tools/scripts/test-release-test-preparation.py`. The shell fixture is a git repository tagged `v1.0`, with change notes added after the tag. A copy of it gains a second platform, change notes that declare `platforms:` or mark lines, and a short-lines file.

## Expected results

- A changed screen is listed in the section that tests it, and a changed screen no printed section tests is listed once, before the first section.
- A section that claims its checks by id alone still lists the changes to its checks' screens. A child screen goes with its top-level screen.
- A change declared for another platform is not listed. A line marked `[testbed]` is listed on testbed and a line marked `[other]` is not. Notes that declare no `platforms:` are named once, in a project with two platforms.
- `--check` refuses a note created on or after 2026-09-28 that names a screen and declares no `platforms:`, warns about an older one, and refuses a platform with no ledger.
- A candidate picture committed before the change note is flagged with its date. A recaptured picture, committed or not, is not.
- Short lines that name the last release tag replace the Impact sentence of each change they cover, and a change with no line keeps its sentence. `--check` warns about the missing line and about a line that names no change. Short lines written against another tag are not used, the page says why, and `--check` does not hold them to this release.
- The short-lines file is not read as a procedure.
