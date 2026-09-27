---
type: "[[requirement]]"
id: REQ-0035
aliases: ["REQ-0035"]
title: "Each section says what changed on this platform since the last release, grouped by screen, one line per change"
status: implemented
review_verdict: approved
review_round: 2
review_date: 2026-09-27
reviewed_by: "model:claude-opus-5-5 (FEAT-0040 review, two rounds)"
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["Edwin, 2026-09-27: approval of the release test page example", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]] (D3)", "Edwin, 2026-09-27, approving REQ-0033 to REQ-0037: 'approved, start stage 2'"]
priority: high
scope: "docs/__templates__/change.md, SCHEMAS.md, the generator, TESTING.md"
acceptance:
  - "A change note that names a screen in its Impact list declares platforms:, and the validator reports one that does not"
  - "A section lists only changes to its own screens on the platform being tested, grouped by screen, one line per change"
  - "Short what-changed lines written at release preparation are used when they match the last release tag, and the Impact sentences are used otherwise, with a line saying so"
  - "Each changed screen shows its before and after screenshots, and a screenshot older than the change is flagged"
  - "A changed screen that belongs to no section is listed once on the platform overview"
implements: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
verifies: []
related: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey]]"]
tests: []
---

# Each section says what changed on this platform since the last release

## Statement

Each section of the release test shall open with what changed since the previous release, on the platform being tested only. Changes shall be grouped by screen, one short line per change, with before and after screenshots. A screenshot taken before the change it should show shall be flagged.

Today the whole list comes first, runs to 4,400 words on Your Trainer's Android sheet, quotes every change note's title, and mixes in iOS changes.

What each part needs:

- **Platform.** A change note gains `platforms:` in its frontmatter, such as `[android]`, `[ios]` or `[android, ios]`. A note whose Impact list names a screen must declare it. An Impact line may be marked `[ios]` or `[android]` where one note changes both platforms differently.
- **Section.** A screen belongs to the first section whose `surfaces:` names it in the section order file (`RELEASE-TEST.md`, today `WALK.md`). A child screen goes with its top-level screen, as today.
- **Short lines.** The Impact sentences are long. At release preparation an agent writes one short line per change, per section and platform (ADR-0050, D3). The lines live in one file per platform, `docs/tests/acceptance/release-test/what-changed-<platform>.md`, whose frontmatter names the release tag they were written against. Each line carries the change note's ID, so the validator can tell whether every change in range has a line. When the file's tag is not the last release tag, the generator falls back to the Impact sentences and says so in one line.
- **Stale screenshots.** A candidate screenshot whose last commit is older than the change note that altered its screen is flagged, with its date.

## Acceptance Criteria

- [x] A change note that names a screen in its Impact list declares platforms:, and the validator reports one that does not — evidence: `platform_findings` and `PLATFORMS_REQUIRED_FROM` (TASK-0191, template 61421da and 0a14cef)
- [x] A section lists only changes to its own screens on the platform being tested, grouped by screen, one line per change — evidence: `screen_homes` and `build_what_changed` with `keep` (TASK-0191); TST-0040
- [x] Short what-changed lines written at release preparation are used when they match the last release tag, and the Impact sentences are used otherwise, with a line saying so — evidence: `load_short_lines` and `short_lines_for` (TASK-0191); your-trainer's `what-changed-android.md`
- [x] Each changed screen shows its before and after screenshots, and a screenshot older than the change is flagged — evidence: `capture_finder` and `stale_finder` (TASK-0191)
- [x] A changed screen that belongs to no section is listed once on the platform overview — evidence: `test-release-test.sh` "the screen no section tests is listed before the sections, and only there"

## Traceability

- Implements: [[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]
- Related open issue: [[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]]. The rename moves many files at once, which is when git's rename detection can hide a new change note.
- Verified by: the renamed `test-release-test.sh`, once TASK-0191 lands.
