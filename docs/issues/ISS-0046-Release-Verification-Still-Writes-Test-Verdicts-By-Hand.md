---
type: "[[issue]]"
id: ISS-0046
aliases: ["ISS-0046"]
title: "Release verification still writes test verdicts by hand"
status: triage
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: docs
source: ["Found while fixing [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]] in the template, 2026-09-03", "project-os CHG-20260903-Prompting-Guide-Contradictions, follow-up 1"]
related: ["[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]", "[[ADR-0010-Test-Status-Stamped-By-Execution]]"]
tasks: []
tests: []
---

# Release verification still writes test verdicts by hand

## Problem

ISS-0043 fixed the vocabulary in `tools/skills/release-verification/SKILL.md`. Underneath the vocabulary the skill's verdict model predates two decisions, and the vocabulary fix deliberately left it alone because it is a model change, not a word change.

- Step 6 says: "Reset STALE and UNTESTED tests to `status: ready` to signal they need re-running." ADR-0010 says a test carrying a `command:` has its status written only by the runner; a hand edit is a validator error.
- Step 3 judges staleness by comparing the note's `last_run` with the latest task `updated` date. TESTING.md says a feature test is invalidated by the change that overlaps it, recorded as `invalidated_by:` with the change id, and ADR-0037 says an acceptance verdict is a ledger event per release and platform, not a field on the note.
- Step 4 writes `status: passing` or `failing` and `last_run` onto the note after a run. For a manual test that is right; for a test with a `command:` it is the runner's job.

Filed at triage because it needs a decision about which model the skill should describe, not because the defect is unclear.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -n "status: ready" tools/skills/release-verification/SKILL.md
grep -n "last_run" tools/skills/release-verification/SKILL.md
```

## Expected

The skill describes the verdict model the instructions state: manual tests carry an author-written verdict with `last_verified:`; tests with a `command:` are stamped by `tools/scripts/run-tests.py`; acceptance checks are settled per release and platform in the ledger, and invalidated by a named change.

## Actual

The skill describes a `last_run`-versus-task-date model with hand-written status resets. An agent following it step by step commits a validator error at step 6.

## Evidence

- `tools/skills/release-verification/SKILL.md` steps 3, 4, 6 and 7 in the template, read 2026-09-03.
- `tools/instructions/STATUSES.md` `[[test]]`, `tools/instructions/TESTING.md` "When to invalidate", ADR-0010, ADR-0037.

## Next Actions

- [ ] Decide the model the skill describes: the current TESTING.md and ledger model, or a reduced one for repos without ledgers.
- [ ] Rewrite steps 3, 4, 6 and 7 against that model; the vocabulary pass in ISS-0043 already fixed steps 5 and 9.

## Sibling search

No sibling found (searched `docs/issues/` for: release-verification, last_run, staleness, status: ready). ISS-0043 is the parent this was split from.

## Risk scan

No new risks: prose only.
