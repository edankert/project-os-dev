---
type: "[[change]]"
id: CHG-20260927-Each-Section-Lists-What-Changed-On-Its-Own-Screens
title: "Each release test section lists what changed on its own screens, for the platform being tested, and flags a picture older than its change"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0191-Each-Section-Lists-What-Changed-On-This-Platform]]"]
commit: "project-os 61421da, 0a14cef"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/scripts/test-release-test.sh", "tools/scripts/test-release-test-preparation.py", "docs/__templates__/change.md", "docs/__templates__/what-changed.md", "docs/__templates__/SCHEMAS.md", "tools/instructions/TESTING.md"]
platforms: []
issues: []
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "[[TST-0044-Each-Section-Lists-What-Changed-On-Its-Own-Screens-For-One-Platform]]"]
---

# Each release test section lists what changed on its own screens

## Summary

A tester now sees the changes to a section's screens at the head of that section, for the platform being tested only, instead of one long list for both platforms at the top of the page. A screenshot committed before the change it should show is flagged with its date. Someone writing change notes should add `platforms:` to each one that names a screen, in a project with more than one platform.

## Impact

- No screen changed: project-os has no surface notes. In each consumer, the release test page moves what changed into the sections, as below.

What changed for someone reading the page or writing the notes:

- **Where a change is listed.** Each section starts with "What changed on the screens this section tests". A section tests the screens its `surfaces:` names and the screens of the checks its `checks:` names; the first section in order keeps a screen. A changed screen that no printed section tests is listed once, before the first section. A section none of whose screens changed says so in one line.
- **One platform.** A change note's `platforms:` says where it is listed, and an Impact line starting `[ios]` or `[android]` counts on that platform only. A note with no `platforms:` is listed on every platform, and the page names it.
- **`--check`.** In a project with ledgers for more than one platform, a change note created on or after 2026-09-28 that names a screen and has no `platforms:` is an error, and an older one is a warning. A platform with no ledger is an error.
- **Stale pictures.** A candidate picture whose last commit comes before the commit that added its change note is flagged: "this picture is older than the change". A picture with uncommitted edits counts as new.
- **Short lines.** `docs/tests/acceptance/release-test/what-changed-<platform>.md`, from the new template `what-changed.md`, holds one short line per change and screen. The page uses them while the file's `tag:` is the last release tag, and otherwise says "Short lines not used" and why. `--check` warns about a change since the tag with no line. The file is not read as a procedure.
- **Code names**, for project-os-cockpit's bundle: `Placed.what_changed`, `ReleaseTest.what_changed_overview`, `short_lines_problem` and `undeclared`; `Screen.short`; `Capture.stale` and `stale_against`; `Change.platforms`, `marks`, `created` and `on(platform)`; `screen_homes`, `stale_finder`, `load_short_lines`, `short_lines_for`. `ReleaseTest.what_changed` still holds every changed screen on the platform. `build_what_changed` and `build_release_test` gain keyword arguments only.

On a scratch copy of your-trainer, the Equipment section opens with the Equipment panel's 13 lines. Ten Android pictures are flagged, all from 2026-09-14 (your-trainer ISS-0516). 23 change notes are named as having no `platforms:`, and `--check --quiet` adds one warning line for them.

## Documentation Coverage (All Types Considered)

- features: not-applicable (FEAT-0040 continues)
- requirements: not-applicable (REQ-0035 is advanced at the feature's close-out)
- tasks: updated (TASK-0191)
- issues: not-applicable
- tests: new (TST-0044)
- workflows: not-applicable
- decisions: not-applicable (ADR-0050 D3 already records the short lines)
- risks: not-applicable. The cut-off date is a new contract: a consumer that syncs after 2026-09-28 with notes written since then and no `platforms:` gets errors, which is the rule working. It is recorded here and in TASK-0191.
- changes: new
- snapshot: updated

## Follow-ups

- [ ] TASK-0193's skill decides each old note's platform from its Impact lines and diff while it writes the short lines.
- [ ] TASK-0190 lays out each section in three parts, with what changed first.
- [ ] project-os-cockpit FEAT-0155 shows each section's list and the overview from the new fields.
