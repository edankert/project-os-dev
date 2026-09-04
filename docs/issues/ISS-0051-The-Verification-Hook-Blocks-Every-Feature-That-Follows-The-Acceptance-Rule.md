---
type: "[[issue]]"
id: ISS-0051
aliases: ["ISS-0051"]
title: "The verification hook blocks every feature that follows the acceptance-check rule"
status: fixed
phase: "[[PHASE-0003]]"
severity: high
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
component: adapters-hooks
source: ["The ISS-0048 drift sweep, pass 12, run 2026-09-04 in a clean context over template e2bee28"]
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
tasks: []
tests: ["[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]"]
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

- [x] Give the hook the validator's two exemptions, and make HC-003 state them once — template commit `ad61433`. `tst_exemption()` skips a test carrying `command:` and a test at `level: acceptance`, in that order, and HC-003 now carries the list both programs read.
- [x] Decide whether the hook checks acceptance settledness: **no**. Settledness is a release-ledger event and this hook reads frontmatter, so it cannot see one. `VERIFY-ACCEPTANCE` in the validator keeps it, and HC-003 says which gate owns which half.
- [x] The waiver divergence, folded in: a `verification_waiver:` now needs `waiver_expires:` in both implementations. `QUALITY.md` also said "the validator reports the waiver as a warning", which was wrong for the case that actually fails; it now states that a missing, unparseable or past expiry is an error (ADR-0010).
- [ ] **Still open**: the validator gates on the reverse `covers:` index and the hook on the subject's `tests:`, so the validator sees links the hook does not. HC-003 records the difference rather than claiming parity. Closing it means teaching the hook the reverse index, which is a bigger change than this fix.

## Resolution

Six assertions were added to `TST-0007`'s harness: an acceptance test at `active` and a test carrying `command:` no longer block `done`, a failing manual test still does, and a waiver is accepted only with an expiry. Removing the exemption again fails two of them with the original denial text, so the harness catches a regression rather than describing one.

Verified: `test-hooks.sh` 37 assertions 0 failures, all four test scripts green, `generate-adapters --check` 35 artifacts current, `validate-docs.sh` OK on the template.

## Sibling search

Sibling found: [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]] (the sweep this came from) and [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make]], which is the same shape one layer down: two implementations of one rule, disagreeing, with a document asserting they agree. Searched `docs/issues/` for: verification gate, HC-003, acceptance, passing.

## Risk scan

No new dependency, env var, path or credential. The hazard is that this is a **blocking** PreToolUse hook, so the fix ships as enforcement: too loose and the gate stops gating, too tight and it denies ordinary work. `TST-0007` is the harness that should carry the new cases.
