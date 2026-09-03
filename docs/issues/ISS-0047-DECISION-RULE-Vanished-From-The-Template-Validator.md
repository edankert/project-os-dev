---
type: "[[issue]]"
id: ISS-0047
aliases: ["ISS-0047"]
title: "DECISION-RULE vanished from the template validator; TST-0004 still says passing"
status: fixed
phase: "[[PHASE-0003]]"
severity: high
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: tooling
source: ["Found running the template's own test suite on 2026-09-03 while landing ISS-0041 to ISS-0044"]
related: ["[[FEAT-0023-Rule-ADRs-Carry-Their-Conformance]]", "[[REQ-0025-Rule-ADRs-Carry-Conformance]]", "[[TST-0004-Decision-Rule-Check]]", "[[ADR-0023-A-Quantified-Rule-Is-A-Decision]]", "[[ADR-0010-Test-Status-Stamped-By-Execution]]"]
tasks: []
tests: ["[[TST-0004-Decision-Rule-Check]]"]
---

# DECISION-RULE vanished from the template validator; TST-0004 still says passing

## Problem

The template's `tools/scripts/validate-docs.py` no longer contains the DECISION-RULE check or the `validate_decision_rule` function that FEAT-0023 landed on 2026-08-12 (template commit `6ca15f4`). Template commit `57739c9` on 2026-08-18, "ADR-0031: close the command: exemption, and stop counting acceptance rows", removed it, six days after it landed. Only `validate_decision_options` remains.

Three things are now false on the record:

- `tools/instructions/DECISIONS.md` line 117 still says "**This is checked.** `DECISION-RULE` is an error when a decision note carries a `## Rule` heading and its `## Domain` or `## Conformance` section is missing or empty."
- The template's own harness, `tools/scripts/test-decision-rule.py`, fails on a clean tree with `AttributeError: module 'vd' has no attribute 'validate_decision_rule'`.
- This repo's [[TST-0004-Decision-Rule-Check|TST-0004]] carries `status: passing` with `last_run: 2026-08-12T18:17Z`. Its command is that harness. A dry run of `tools/scripts/run-tests.py --filter TST-0004` today reports the failure; the status has not been stamped because stamping it makes FEAT-0023, which is `done`, fail the verification invariant and blocks every commit in this repo until the template is fixed. That is Edwin's call, recorded here rather than taken silently.

A rule-ADR whose conformance is gone binds nothing (ADR-0023). ADR-0024, accepted today, is a rule-ADR that relies on the same convention.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -c validate_decision_rule tools/scripts/validate-docs.py      # 0
python3 tools/scripts/test-decision-rule.py; echo $?                # AttributeError, exit 1
git log -S'validate_decision_rule' --format='%h %ad %s' --date=short -- tools/scripts/validate-docs.py
cd ~/Dev/repos/project-os-dev && python3 tools/scripts/run-tests.py --filter TST-0004   # dry run, fails
```

## Expected

The template validator errors on a decision note with `## Rule` and a missing or empty `## Domain` or `## Conformance`, as DECISIONS.md says; the harness passes; TST-0004's recorded status matches the last run.

## Actual

The check is absent, the harness cannot import it, and the test note records a pass from before the removal.

## Evidence

- Template `git log -S'validate_decision_rule'`: present in `6ca15f4` (2026-08-12), removed in `57739c9` (2026-08-18).
- `tools/scripts/test-decision-rule.py` tail: `AttributeError: module 'vd' has no attribute 'validate_decision_rule'`.
- This repo, 2026-09-03: `run-tests.py --filter TST-0004` dry run fails.

## Next Actions

- [x] Restore `validate_decision_rule` and its DECISION-RULE wiring in the template validator from `6ca15f4` and `4aa2238`, and make the harness pass.
- [x] Check the bundled cockpit validator and the twelve vendored copies for the same loss; the removing commit was an acceptance-model change and may have been hand-merged elsewhere.
- [x] Stamp TST-0004 with `run-tests.py --write` once the template is fixed, or now if Edwin prefers the honest red over the blocked commits.
- [x] Ask why the harness did not catch this: it is a `TST-*` with a `command:` and nothing ran it between 2026-08-12 and today. The per-commit runner exists; it is not wired to pre-commit or CI here.

## Resolution

Fixed in the template by commit `66cd2a4` on 2026-09-03 (CHG-20260903-Decision-Rule-Restored there). The two regexes, `_decision_sections`, `validate_decision_rule` and the call in `validate()` are restored verbatim from `6ca15f4`; `4aa2238` turned out to touch the harness only, and the harness was never lost. The harness passes 26 of 26, the count the 2026-08-12 review recorded. The restored check reports zero findings across every repo under `~/Dev/repos`, so no downstream repo breaks at its next sync.

The bundled cockpit validator lacks the check and was not patched: it is a separately maintained fork owned by project-os-cockpit, about 1,200 diff lines away from the template file, so the fix belongs there and is a follow-up in the template's change note. The other fleet copies are plain syncs and get the check at their next sync.

[[TST-0004-Decision-Rule-Check|TST-0004]] was stamped by `run-tests.py --write` after the fix, at 2026-09-03T15:31Z, passing. Edwin chose the order: fix first, then stamp, so this repo never carried a red test that blocked commits.

Why nothing caught it: the harness is run only by `run-tests.py`, and nothing runs that at pre-commit or in CI here. Wiring it is the second follow-up in the template's change note.

## Sibling search

No sibling found (searched `docs/issues/` for: test-decision-rule, DECISION-RULE, validate_decision_rule). ISS-0035 and ISS-0036 concern the bundled validators for a different check and are linked through FEAT-0023's history, not as siblings of this loss.

## Risk scan

The template's validator is a synced, template-owned file; a regression in it reaches every downstream repo at the next sync. No new dependency or path; the hazard is the existing one RISK-0002 describes for generated state, applied to a check.
