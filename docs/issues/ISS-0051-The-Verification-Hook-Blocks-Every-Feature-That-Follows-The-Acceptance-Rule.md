---
type: "[[issue]]"
id: ISS-0051
aliases: ["ISS-0051"]
title: "The verification hook blocks every feature that follows the acceptance-check rule"
status: triage
phase: "[[PHASE-0003]]"
severity: high
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
component: adapters-hooks
source: ["The ISS-0048 drift sweep, pass 12, run 2026-09-04 in a clean context over template e2bee28"]
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
tasks: []
tests: []
---

# The verification hook blocks every feature that follows the acceptance-check rule

## Problem

`feature-scaffold/SKILL.md` tells you to give every feature an acceptance check. `STATUSES.md` says an acceptance check rests at `active` and never reaches `passing`. The blocking HC-003 hook demands `status: passing` of every linked `TST-*`. Follow the first two rules and the third denies your feature ever reaching `done`.

The same hook blocks on a test carrying `command:`, which ADR-0025 says records no verdict at all.

The repo-wide validator gets this right and the hook does not, so the two enforcement paths disagree about the ordinary case. `HOOKS.md` HC-003 claims they "enforce the same invariant".

## Repro

```bash
cd ~/Dev/repos/project-os
sed -n '158,163p' tools/adapters/claude-code/hooks/verification-gate.py   # status != "passing" -> blocked, no exemptions
sed -n '2109,2120p' tools/scripts/validate-docs.py                        # command: -> continue; acceptance -> settled-check, continue
```

## Expected

The hook exempts what the validator exempts: a test with `command:` (settled by CI) and a test at `level: acceptance` (settled in the release ledger).

## Actual

`Verification gate (HC-003): terminal status set while linked tests are not passing: FEAT-xxxx -> TST-yyyy is 'active'` — on a feature whose only fault is having the acceptance check the scaffold skill required.

## Evidence

- `tools/adapters/claude-code/hooks/verification-gate.py:150-163` — the loop, with no exemption for either kind.
- `tools/scripts/validate-docs.py:2109-2120` — the two exemptions, with the reasoning in comments.
- `tools/instructions/HOOKS.md:47` — the "same invariant" claim.

## Next Actions

- [ ] Give the hook the validator's two exemptions, and make HC-003 state the exemptions once so both implementations cite them rather than each carrying a copy.
- [ ] Decide whether the hook should also check acceptance settledness (the validator's VERIFY-ACCEPTANCE) or stay out of the ledger's way.
- [ ] Two further divergences pass 12 found in the same pair, worth folding in: the validator requires `waiver_expires:` and the hook accepts a bare waiver; the validator gates on the reverse `covers:` index and the hook on the subject's `tests:`.

## Sibling search

Sibling found: [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]] (the sweep this came from) and [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make]], which is the same shape one layer down: two implementations of one rule, disagreeing, with a document asserting they agree. Searched `docs/issues/` for: verification gate, HC-003, acceptance, passing.

## Risk scan

No new dependency, env var, path or credential. The hazard is that this is a **blocking** PreToolUse hook, so the fix ships as enforcement: too loose and the gate stops gating, too tight and it denies ordinary work. `TST-0007` is the harness that should carry the new cases.
