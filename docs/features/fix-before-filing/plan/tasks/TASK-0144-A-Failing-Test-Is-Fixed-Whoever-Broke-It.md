---
type: "[[task]]"
id: TASK-0144
aliases: ["TASK-0144"]
title: "A failing test is fixed, whoever broke it and whenever"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["Edwin, 2026-09-19: 'You should not care if those failures were for today, they need to be fixed. Make sure to update the rules around this!'"]
parent: "[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
verification_waiver: "A rule change; its evidence is the fleet's test runs recorded below, which went from red to green"
waiver_expires: 2026-12-19
tests: []
---

# A failing test is fixed, whoever broke it and whenever

## Definition of Done
- [x] `QUALITY.md` states the rule once: a test that fails in any run is fixed before the work closes, even when the work did not cause it. A machine-caused failure skips with its reason; only a fix needing the owner's decision waits, asked in the same turn (project-os `aa278b5`).
- [x] The filing bar says a failing test is never "code the feature did not change". `LIFECYCLE.md` "Scope of a change" and the close-out skill point at the rule.
- [x] Synced to all twelve fleet repos (project-os `60f87f7`).
- [x] The red runs found on 2026-09-19 are green.

## What was red, and what fixed it

**project-os-cockpit Python suite: 6 failed, now 2,170 passed, 0 failed** (cockpit `bc2d2e2`). Three had failed since before this work; none was a product defect:
- Two surface tests asserted the repo had exactly one screen. It has four. They now read `docs/surfaces/`.
- The phase-banding test ranked each group with no records, so "Unphased" read as finished. It now passes each group's features, and leaves out the unattached-requirements group.
- The live walk-survey test predated the rule that a changed dialog brings its containing screen onto the survey.
- The desktop app had no labels for REVIEW-ROUND, ACCEPT-LOCATION, ISSUE-REPORTER and ISSUE-QUESTION.
- The runtime-freshness case failed only because a file changed mid-run.

**Template test scripts, run in all twelve repos.** project-os-cockpit failed five runner checks in `test-verdict-model.sh`, because it keeps its own `run-tests.py` on purpose (its ADR-0038). Those checks now skip there with that reason (project-os `60f87f7`). articles failed three scripts only because another session's uncommitted edit leaves its working `SNAPSHOT.yaml` unparseable; at its committed state all pass. That edit is the other session's to fix, and Edwin was told.
