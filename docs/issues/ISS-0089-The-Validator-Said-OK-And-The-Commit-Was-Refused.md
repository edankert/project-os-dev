---
type: "[[issue]]"
id: ISS-0089
aliases: ["ISS-0089"]
title: "validate-docs.sh prints OK before its last check runs, and a walk failure after it does not look like an error"
status: triage
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["your-trainer session your-trainer-b8, on Edwin's instruction (2026-09-26: 'review where most of the time went', then 'Make it so')"]
reported_by: review
question: ""
severity: medium
component: "tools/scripts/validate-docs.sh; tools/scripts/walk-sheet.py"
parent: ""
related: []
tests: []
---

# validate-docs.sh prints OK before its last check runs, and a walk failure after it does not look like an error

## Problem

`validate-docs.sh` can print `validate-docs: OK` and still fail. It runs the Python validator first, which prints its own summary line, and only then runs the walk check. A walk failure prints after the OK line, without an `ERROR` prefix, and sets the exit status to 1. An agent that reads the output for `ERROR` lines and the summary, instead of checking the exit status, reads OK while the script has failed.

## Evidence

- `tools/scripts/validate-docs.sh`, checked 2026-09-26: line 83 runs `validate-docs.py`, which prints `validate-docs: OK (<repo>)` (`validate-docs.py:4300`); line 98 then runs `walk-sheet.py --check --quiet`; line 101 exits with the combined status.
- `walk-sheet.py` prints each problem as `walk-sheet --check (<platform>): ...` (`walk-sheet.py:2639`), with no `ERROR` prefix.
- In your-trainer, a session ran `bash tools/scripts/validate-docs.sh`, filtered its output with `grep -E "^ERROR|validate-docs:"`, did not check `$?`, and read OK. The pre-commit hook, which runs the same script and checks its status, then refused the commit for walk-quote drift (ISS-0088's case). Cause confirmed by that session on 2026-09-26.

## Proposal (from the your-trainer session)

- Print one final verdict line after every step has run, so the last line of output is the whole script's answer.
- Prefix walk-sheet disagreements with `ERROR [WALK]`, so filtering for errors finds them.

## Correction

This issue first reported that the walk checks run only in the pre-commit hook. They do not: `validate-docs.sh` runs them, and the pre-commit hook runs `validate-docs.sh`. The report's mechanism was corrected on 2026-09-26 by the session that raised it.
