---
type: "[[feature]]"
id: FEAT-0028
aliases: ["FEAT-0028"]
title: "Executable tests carry no verdict"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]", "[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]"]
goal: "Make the template and this repo follow one verdict model: a test with a command: is run and reported, never stamped; CI gates it; the validator treats it as settled."
requirements: []
tasks: ["[[TASK-0106]]", "[[TASK-0107]]", "[[TASK-0108]]", "[[TASK-0109]]"]
release: ""
related: ["[[ADR-0010-Test-Status-Stamped-By-Execution]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"]
tests: ["[[TST-0008]]"]
---

# Executable tests carry no verdict

## Goal

A test note with a `command:` stops carrying a verdict. The runner runs it and reports; CI gates on the exit code; the validator treats the test as settled by CI. Every file that said otherwise (the runner, the test template, SCHEMAS.md, the test-authoring and release-verification skills, and this repo's seven automated tests) follows STATUSES.md and TESTING.md, which already said this. Decided by Edwin on 2026-09-03 ([[ADR-0025-An-Executable-Test-Records-No-Verdict|ADR-0025]]).

## Scope

| Task | What | Files |
|---|---|---|
| [[TASK-0106]] | The runner reports and exits; it no longer writes | `tools/scripts/run-tests.py`, the CI seed |
| [[TASK-0107]] | The validator treats a `command:` test as settled and warns on a verdict field | `tools/scripts/validate-docs.py` |
| [[TASK-0108]] | One model in the templates and skills; ISS-0046's rewrite | `docs/__templates__/test.md`, `SCHEMAS.md`, `test-authoring`, `release-verification`, `SNAPSHOT.md` |
| [[TASK-0109]] | This repo follows: sync its tools, clear its validation debt, strip the seven verdicts | `tools/`, `docs/tests/`, `docs/features/*/plan/tests/`, feature notes |

## Out of scope

- Acceptance checks and their ledger (ADR-0037): unchanged.
- Manual tests: unchanged, a hand-written verdict with `last_verified:`.
- Downstream repos' own notes: the validator warns until the ADR-0011 cutover; each repo strips its own verdict fields.

## Acceptance

- [x] `run-tests.py` has no `--write` and leaves every note byte-identical after a run — evidence: [[TST-0008]] assertions 12 to 16 at the 18-assertion harness, 2026-09-03; template commits `3d67f11` and `293e5a2`
- [x] A task or feature whose linked test carries a `command:` and sits at `active` passes the verification gate; the same test with `status: passing` draws the dated warning — evidence: [[TST-0008]] assertions 1 to 6; template commits `a8694f0` and `b5e8f9f` (the acceptance-level case the first version missed)
- [x] The test template, SCHEMAS.md, test-authoring and release-verification describe the one model, and ISS-0046 is fixed — evidence: template commit `87b64cf`; release-verification steps 3, 4, 6 and 7 settle each test by its kind and reset nothing by hand
- [x] This repo's seven automated tests carry `status: active` and no `last_run:` or `exit_code:`, and its validator is the template's — evidence: `git grep -l "^last_run" docs/` returns nothing, `validate-docs.sh` OK after the sync from `09ae4dc`, `run-tests.py` 8 of 8 (TST-0008 included)

## Risk scan

Run against the LIFECYCLE.md triggers. Two fire. The validator gains a check with a dated promotion, which is the ADR-0011 shape and not a new hazard. This repo's tools sync carries 47 pre-existing validation errors that must be cleared before its pre-commit passes again; that is [[TASK-0109]]'s first step, recorded there rather than as a `RISK-*`.
