---
type: "[[task]]"
id: TASK-0191
aliases: ["TASK-0191"]
title: "Change notes declare their platforms, and each section lists what changed on its own screens for this platform"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0187]]"]
blocks: []
related: ["[[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform]]", "[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey]]"]
tests: []
---

# Change notes declare their platforms, and each section lists what changed on its own screens for this platform

"What changed" moves from one 4,400-word list at the top to a short list at the head of each section, for one platform.

## Definition of Done
- [ ] `docs/__templates__/change.md` and SCHEMAS.md gain `platforms:`, and an Impact line may be marked `[android]` or `[ios]`.
- [ ] The validator reports a change note with a screen in its Impact list and no `platforms:`. It is a warning for notes created before this lands.
- [ ] Each section lists only changes to its own screens on this platform, grouped by screen, one line per change.
- [ ] The generator reads `docs/tests/acceptance/release-test/what-changed-<platform>.md` when its frontmatter tag is the last release tag. Otherwise it uses the Impact sentences and prints one line saying the short lines are missing or out of date.
- [ ] The validator reports a change in range with no short line in that file.
- [ ] A candidate screenshot whose last commit is older than the change note that altered its screen is flagged with its date.
- [ ] A changed screen that belongs to no section is listed once on the platform overview.
- [ ] Tests cover each of the above, and each fails when its guard is removed.

## Steps
- [ ] Add `platforms:` to the change template and schema.
- [ ] Split the current survey builder by section and platform.
- [ ] Define the what-changed file's shape and read it.
- [ ] Add the stale-screenshot comparison.
- [ ] Update TESTING.md, "The release test", rule 2.

## Notes
- Existing change notes have no `platforms:`. For those, the agent step in TASK-0193 decides the platform from the note's Impact lines and diff while writing the short lines; the generator treats an undeclared note as all platforms and says so.
