---
type: "[[adr]]"
id: ADR-0025
aliases: ["ADR-0025"]
title: "An executable test records no verdict; CI is the verdict"
status: "accepted"
owner: user:edwin
created: 2026-09-03
updated: "2026-09-03"
source: ["[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]", "[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]] rows 1, 3 and 30", "project-os-cockpit ADR-0038"]
decision: "Option 2. A test note that carries a command: holds no status verdict, no last_run and no exit_code; the runner reports and CI gates. A manual test keeps its hand-written verdict with last_verified. Acceptance checks keep the per-release ledger."
decided_option: 2
context: "The template said two things about a test with a command:. STATUSES.md and TESTING.md said it records no verdict (cockpit ADR-0038); the test template, SCHEMAS.md, run-tests.py and this repo said the runner stamps passing or failing on the note (ADR-0010). Both were true in different files, and the drift sweep at the close of PHASE-0003 listed the contradiction three times."
alternatives: []
consequences: []
supersedes: ""
superseded: ""
related: ["[[ADR-0010-Test-Status-Stamped-By-Execution]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]"]
---

# An executable test records no verdict; CI is the verdict

**Accepted 2026-09-03 with option 2** (decision record below).

## Context

Two models for the verdict of a test that carries a `command:` lived in the template at once. ADR-0010 (2026-07) had the runner, `tools/scripts/run-tests.py`, write `status: passing` or `failing`, `last_run:` and `exit_code:` onto the note from the exit code, so that the party seeking a transition never certified it by hand. Cockpit ADR-0038 (2026-08), synced into STATUSES.md and TESTING.md, went one step further: an executable test records no verdict at all, because CI answers that question and answers it better, and a red automated test is a broken build rather than a state anybody writes down. The templates, the runner, the test-authoring and release-verification skills, and this repo's seven automated tests still followed ADR-0010. The drift sweep under ADR-0024 found the contradiction in three places (ISS-0048 rows 1, 3 and 30), and ISS-0046 had already asked which model the release-verification skill should describe.

## Options

1. **The runner stamps the note.** Keep ADR-0010: `run-tests.py --write` records the verdict on the note; STATUSES.md and TESTING.md are corrected to say so. Keeps this repo's seven passing tests as they are.
2. **No verdict on the note.** Follow ADR-0038: a test with a `command:` never carries `passing`, `failing`, `last_run:` or `exit_code:`; the runner reports and CI gates; the validator treats such a test as settled by CI. This repo's automated tests lose their status.

## Decision

Option 2.

## Consequences

- `run-tests.py` stops writing; it runs, reports and exits non-zero on a failure, which is what a CI step needs.
- The validator treats a test with a `command:` as settled by CI in the verification gate, and warns, with a dated promotion under ADR-0011, on a `command:` test that still carries a verdict field. Measured at landing across the fleet: 33 such notes (this repo 7, your-health 19, your-sudoku 4, your-trainer 2, project-os-cockpit 1) plus 5 at `ready`.
- The test template, SCHEMAS.md, the test-authoring and release-verification skills say the one model. ISS-0046 closes on the rewrite.
- A manual test is unchanged: a hand-written verdict, `last_verified:`, and staleness. An acceptance check is unchanged: the ledger holds its verdict per release and platform (ADR-0037).
- Which sessions gate on the tests is now a property of CI, not of the note. A repo whose CI does not run `run-tests.py` has no gate for its executable tests until it does; the template's CI seed runs it.

## Decision record

> [!note] Accept — 2026-09-03 (user:edwin)
> On ISS-0046: "If it is possible to automate this let's do so but otherwise we leave it at writing this by hand (either me or you)". Asked in plain language where the verdict of a test with a `command:` lives, with the runner-stamps option recommended: "No verdict on the note". Asked whether to scaffold it for the next pass or do it now: "Do it now under this goal".
