---
type: "[[issue]]"
id: ISS-0015
aliases: ["ISS-0015"]
title: "The walker stops at depth 4 while the docstring and TST-0002 say 'any nesting depth'; and the decision-alias hole was a hash-seed coin flip, not 'validated against nothing' — STATUS-VALUE still picks its type nondeterministically"
status: fixed
severity: low
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
component: tooling
source: ["review:2026-07-26-independent-review-round-four-TST-0002"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [ISS-0011, ISS-0012, ISS-0013, ISS-0014, TST-0002]
tests: [TST-0002]
---

# Round-four review findings: the boundary sentence is still one notch wider than the code, and the decision-alias fix hides a nondeterministic gate

## Problem

Independent round-four review of [[TST-0002]] / [[CHG-20260726-Phase-Resolved-Declined]] (commit 5c4319d, reviewed by model:claude-fable-5) verified everything ISS-0014's Resolution claims: the file is structurally clean (1619 lines, one entry guard, zero duplicated top-level definitions by AST; the 12a7c70→5c4319d diff contains only the intended changes), all 12 fleet files are byte-identical, all mutation branches fire, the metrics rewrite is behaviour-preserving by an independent method, and the AST-verified "no multi-value inline status collection remains" claim is exact. Two findings remain, both demonstrated.

1. **"Any nesting depth" is refuted at depth 5.** `_holds_strings` returns `False` past `depth > 4`, so `DEEP_STATUSES = ((((("bogus",),),),),)` — a module-level status collection with a string at nesting depth 5 — leaves `--self-check` green (demonstrated; the same string at depth 4 is caught). The docstring says "every module-level container holding a string, at any nesting depth and of any shape"; TST-0002's coverage boundary says "to any nesting depth". Both are wider than the code. ISS-0014's own Resolution and the 5c4319d commit message say "to depth 4", correctly — so the file's descriptions of the same boundary now disagree with each other. This is the fifth iteration of the pattern the whole saga documents, though the narrowest yet: no real table nests past depth 3, so the code is adequate and only the sentence is wrong. ("Of any shape" is also refutable by a `types.MappingProxyType` of statuses, which is not a `dict` instance — contrived, since it requires importing `types` into the validator to hide a table, but the phrase invites it.)
2. **"A decision-typed note's status was validated against nothing" is imprecise, and the imprecision hides a live residual.** STATUS-VALUE resolves the type to check against with `type_key = next(iter(expected_types), None)` — and for the `decisions` collection `expected_types` is the two-element set `{"adr", "decision"}`, whose iteration order varies per process under hash randomization. Demonstrated on a scratch copy of `your-health` with ADR-0006's status set to `bogus`, using the 12a7c70 validator: the error fires on 5 of 10 `PYTHONHASHSEED` values and is silent on the other 5. So the pre-fix gate was not dead — it was a per-run coin flip, which is arguably worse (a bad status could pass CI on one run and fail on the next). The ISS-0014 alias fix makes the outcome deterministic (10/10 seeds caught) **only because the two vocabularies currently coincide**: `load_allowed_status()` overlays `[[adr]]` from the repo's STATUSES.md but no repo defines a `[[decision]]` section, so a downstream repo customising its adr `Allowed:` line silently re-splits `allowed_status["adr"]` from `allowed_status["decision"]` and the seed-dependence returns. Nothing asserts the two stay equal.

Noted, not defects: the CHG's "Files changed (11 across 10 repos)" table predates `project-os-bench` (the fleet is now 12 files across 11 repos, as ISS-0014 and the commit message correctly say); and the cockpit suite reports 315 passed where the Resolution says "314 passed / 1 skipped" (nothing fails either way; an environment-dependent skip appears to run here).

## Repro

```
# 1. depth-5 evasion (depth-4 is caught; insert before the __main__ guard, not after)
#    DEEP_STATUSES = ((((("bogus",),),),),)   -> --self-check exit 0
#    NEST4_STATUSES = (((("bogus",),),),)     -> --self-check exit 1

# 2. the coin flip, against the 12a7c70 validator with ADR-0006 status: bogus
for seed in 1 2 3 4 5 6 7 8 9 10; do PYTHONHASHSEED=$seed python3 old.py --repo-root . --quiet | grep -c STATUS-VALUE; done
# -> 1 1 0 1 0 0 0 0 1 1  (5c4319d: 1 1 1 1 1 1 1 1 1 1)
```

## Expected

The boundary sentence is exactly as wide as the code, everywhere it appears — including "depth 4" where the cap is 4; the record of the decision-alias bug describes a nondeterministic gate, not a dead one; STATUS-VALUE does not depend on set iteration order.

## Actual

Docstring and TST-0002 say "any nesting depth" over a depth-4 cap; ISS-0014, TST-0002, the CHG and the `ALLOWED_STATUS` comment say "validated against nothing" where the truth is "validated on the seeds where `next(iter(...))` happened to pick `adr`"; `type_key = next(iter(expected_types), None)` remains in STATUS-VALUE, deterministic today only by the accident that both vocabularies match.

## Next Actions

- [x] Make the depth sentence exact in the docstring and TST-0002 ("to nesting depth 4"), or remove the cap in favour of a `seen`-set cycle guard so "any nesting depth" becomes true; drop or qualify "of any shape"
- [x] Correct "validated against nothing" to the nondeterministic mechanism wherever it appears (ISS-0014 Resolution, TST-0002 coverage boundary, CHG follow-up, the `ALLOWED_STATUS` comment)
- [x] Replace `next(iter(expected_types), None)` in STATUS-VALUE with a check against the union of the expected types' allowed sets (or check against each), so the decisions collection is validated identically on every run regardless of overlay customisation
- [x] Optional: refresh the CHG's file table to name `project-os-bench` (12 files, 11 repos)

## Resolution

Fixed 2026-07-26, same session. Both findings held; neither needed argument.

**The depth cap.** `_holds_strings` stopped at depth 4 while the docstring one paragraph above promised "any nesting depth" — a sentence wider than the code, sitting below a warning about sentences wider than the code. Given the choice between trimming the sentence and making it true, the sentence is now true: the cap is gone and cycle-safety is by identity (`seen`), which is what the cap was standing in for. A number is arbitrary and a future table can exceed it; `seen` cannot be exceeded.

Verified: depth 5 (this issue's repro, verbatim), depth 9, and a self-referential container all caught, the last terminating rather than recursing forever.

**The `decision` coin flip, and the wrong words for it.** `STATUS-VALUE` picked its type with `next(iter(expected_types), None)` over an unordered set, so an item in the `decisions` collection was checked against `adr` or `decision` depending on the hash seed. Reproduced against the pre-fix validator with a bogus status: **fires on 6 of 12 `PYTHONHASHSEED` values, silent on the other 6.** After the fix — the union of every accepted type's vocabulary — 12 of 12.

That is worse than what ISS-0014 said. "Decision-typed notes were validated against nothing" describes a dead gate, which is at least consistently dead; a per-run coin flip passes CI and fails locally, or the reverse, and looks like flakiness rather than a missing check. Corrected wherever it appears — this note, ISS-0014, TST-0002 and the CHG.

The alias reads correct today only because `adr` and `decision` carry identical vocabularies. Nothing enforces that, and a downstream `STATUSES.md` customising `[[adr]]` re-splits them. The union check is what makes that safe rather than lucky.

## Five rounds

| | The miss | Shipped green? |
|---|---|---|
| [[ISS-0011]] | a rename missed three status tables | yes |
| [[ISS-0012]] | the fix for ISS-0011 missed a table it had just created | yes |
| [[ISS-0013]] | the guard against ISS-0012 missed a table *type* | yes |
| [[ISS-0014]] | the widened guard missed `dict`; the commit silently doubled the file | yes |
| ISS-0015 | the walk capped at depth 4 while promising any depth; a type pick was hash-ordered | yes |

The rounds are converging — round five is two small defects against round two's four, and nothing structural. But the shape has not changed once: **every round, a claim about coverage was written slightly wider than the code, and every mechanical check agreed with the claim.** Five for five.

The only thing that has caught it, five times out of five, is a reviewer attacking the guard instead of reading it. That is the finding this sequence is actually evidence for, and it is worth more than the guard.
