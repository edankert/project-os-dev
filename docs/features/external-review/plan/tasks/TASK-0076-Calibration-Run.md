---
type: "[[task]]"
id: TASK-0076
title: "Calibration run: point a non-Claude reviewer at ISS-0011..ISS-0015"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["session:2026-07-27"]
parent: "[[FEAT-0018]]"
effort: "S"
due: ""
depends: ["[[TASK-0075]]"]
blocks: []
related: []
tests: []
---

# Calibration run: ISS-0011..ISS-0015

## Why this case

It is the only case in the fleet with a known answer. Five same-family review rounds hardened `validate_status_tables`, each finding real defects, each recorded with a reproduction. So the question "is a cross-family reviewer worth institutionalising?" has a measurable form here that it has nowhere else:

- **Finds something all five missed** → the different-family gate is buying real coverage, and the runner is worth promoting.
- **Only re-finds what is already fixed** → also a result. It says the five rounds converged, and that the gate's value is lower than assumed. Worth recording rather than re-running until it says something flattering.
- **Reports findings that do not reproduce** → a result about the reviewer, not the code, and the schema filter should catch them before they cost review time.

## Definition of Done

- [ ] A run completes against a non-Claude model with the five issue notes, TST-0002, the CHG note and the `12a7c70..HEAD` diff as context
- [ ] The outcome is recorded verbatim — including a null result
- [ ] Any finding that reproduces is filed as an `ISS-*` like any other review finding
- [ ] The verdict is transcribed into note frontmatter by hand, not by the script
- [ ] The result is written up as the evidence for whether to promote the runner upstream

## Steps

- [ ] User installs and authenticates the CLI (OAuth device flow — cannot be done by an agent)
- [ ] Dry-run first, inspect the assembled prompt
- [ ] Run, capture raw output alongside the parsed verdict
- [ ] Triage findings against the five issues already closed

## Notes

Bias to guard against: I know what the five rounds found, so I will be tempted to read a vague finding as a hit. A finding counts only if its `repro` runs and shows what it claims — the same bar every finding in those five rounds met.
