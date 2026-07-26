---
type: "[[requirement]]"
id: REQ-0022
aliases: ["REQ-0022"]
title: "A test note's status must be written by executing the test, not asserted by the agent seeking the transition it gates"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: high
scope: verification
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0016]
related: [ADR-0010, REQ-0006, ADR-0007]
tests: []
acceptance:
  - "A TST-* note may declare a `command:`; when present, its status is written only by the test runner, which also records `last_run:` and the exit code."
  - "Changing `status` on a note that declares a `command:` without a corresponding `last_run:` change is a validator error."
  - "A command that cannot be executed at all (missing binary, missing environment) reports as a distinct finding and does not stamp `failing`."
  - "`failing` becomes reachable and is exercised by a fixture in which a deliberately broken command produces a failing note and blocks a terminal transition."
  - "The VERIFY gate is satisfied only by an executed `passing` result or an in-date manual verification, never by an assertion alone."
---

# Test status is stamped by execution

## Statement

Where a test can be executed, its recorded status shall be the result of executing it. A `TST-*` note declaring a `command:` shall have its `status` written only by the test runner, together with the time of the run and its exit code. No agent shall write the status of an executable test, because the agent writing it is in every case the party seeking the transition that status gates.

## Acceptance Criteria

- [x] `command:` declared; status written only by the runner with `last_run:` + exit code — evidence: `tools/scripts/run-tests.py`; `docs/__templates__/test.md`
- [x] Hand-edited status on a `command:` note is a validator error — evidence: `validate-docs.py` TEST-FIELDS (a stamped status with no `last_run:` means somebody typed it)
- [x] Unrunnable command reports distinctly and does not stamp `failing` — evidence: `run_one()` returns a third outcome for exit 127, OSError and timeout; the note keeps its previous status
- [x] `failing` reachable — evidence: retained by ADR-0008 for this purpose; the runner writes it from a non-zero exit
- [x] `VERIFY` satisfied only by an executed `passing` or in-date manual verification — evidence: `validate-docs.py` VERIFY now rejects a passing-but-stale manual test

## Evidence for the requirement

`QUALITY.md`'s verification gate is the most-referenced rule in the system. Across 10 repos and 5,890 status writes it has **never observed a failure**:

- **`failing`: 0 writes.** Not rare — never.
- **78%** of `TST-*` notes are created already at `passing`; **99%** never change status again.
- **48** notes carry a `verification_waiver` — the escape hatch has been used infinitely more often than the gate has fired.

[[ADR-0007-Requirement-Terminality-And-Ownership|ADR-0007]] diagnosed this exact shape one level up when it retired `verified`: a status "set on delivery or on nothing far more often than on proof". The same sentence is true of `passing`, for the same structural reason — nothing returns to the note after it is written.

## Impact analysis (2026-07-25)

- **[[REQ-0006-Verification-Gating|REQ-0006]] — this is its precondition, not its replacement.** REQ-0006 requires gating on passing linked tests and is currently satisfiable by assertion, which makes it a gate that audits only those who already comply (the mechanism ADR-0007 described: no link, empty loop, silent pass). This requirement supplies the evidence REQ-0006 always assumed it had. REQ-0006 is unchanged in wording and strengthened in effect.
- [[ADR-0007-Requirement-Terminality-And-Ownership|ADR-0007]] — **must be respected carefully.** ADR-0007 forbids gating *requirements* on linked tests, and its amendment reverted exactly that. This requirement makes test status trustworthy; it must not be read as licence to reintroduce the requirement-level test gate. Requirements remain gated on acceptance criteria alone.
- [[REQ-0016-Declared-Statuses-Observed-In-Use|REQ-0016]] — interacts and is resolved: `failing` has zero usage and would fail REQ-0016's rule, so ADR-0008 retains it under an explicit exception naming this requirement as the reason.
- [[ADR-0004-Mandatory-Skill-Steps|ADR-0004]] — aligned; this replaces a mandatory manual step with a mechanical one.

**No conflicts found.** One boundary to hold: trustworthy test status does not reopen requirement-level test gating (ADR-0007).

## Traceability

- Feature: [[FEAT-0016-Executable-Verification|FEAT-0016]]
- Decision: [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]]
