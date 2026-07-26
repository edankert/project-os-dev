---
type: "[[task]]"
id: TASK-0067
aliases: ["TASK-0067"]
title: "Build run-tests.py: stamp TST-* status from execution; make hand-edited status an error"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0016-Executable-Verification]]"
effort: L
due: ""
depends: [TASK-0066]
blocks: []
related: [REQ-0022, REQ-0006, ADR-0010]
tests: []
---

# Test runner

## Definition of Done

- [ ] `tools/scripts/run-tests.py` executes each `TST-*` note's `command:` and writes `status`, `last_run:` and `exit_code:`.
- [ ] Three outcomes are distinguished: `passing` (exit 0), `failing` (non-zero), and **unrunnable** (missing binary, missing env) — which reports as a finding and does **not** stamp `failing`.
- [ ] Changing `status` on a note with a `command:` without a corresponding `last_run:` change is a validator error.
- [ ] Fixture: a deliberately broken command produces a `failing` note and blocks a terminal transition through `VERIFY`.
- [ ] `--dry-run` reports what would be stamped without writing — used for the first fleet pass.
- [ ] Timeout per command, so one hanging test cannot stall the run.
- [ ] Working directory, environment, and timeout are documented, since they determine whether a result is trustworthy.

## Steps

- [ ] Implement the runner with the three-outcome model as the core design, not as later refinement.
- [ ] Add the validator check for hand-edited status.
- [ ] Build the fixture; confirm `failing` actually blocks a terminal transition end to end.
- [ ] Run `--dry-run` across the fleet's 80 `TST-*` notes and **record the result** — it is the first honest measurement of verification health the project has ever had.

## Notes

**The unrunnable outcome is the one that decides whether this is trusted.** A test that cannot run because a binary is missing is not a failing test, and stamping it `failing` would produce exactly the noise that makes people stop believing the status — the failure mode this feature exists to end. Conflating the two would also repeat the `blocked`-versus-`failing` confusion ADR-0007's amendment called out.

**Expect the first honest run to be red.** `failing` has never been written once in 5,890 status writes; 78% of test notes are born `passing`. Some of those are wrong today and have been for a long time. Surfacing it is the deliverable — say so in the change note before anyone sees the number, so the first red build is not misread as caused by this change.

**Scope guard:** this stamps note status from a command. It is not a test framework and does not own the suite.
