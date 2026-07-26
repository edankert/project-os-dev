---
type: "[[issue]]"
id: ISS-0014
aliases: ["ISS-0014"]
title: "validate-docs.py ships its own second half twice: lines 1560–2560 duplicate 556–1556 verbatim, fleet-wide; the 'no inline status literal remains' claim is false; the walker's boundary prose still overclaims on dict, underscore names and nesting"
status: fixed
severity: medium
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
component: tooling
source: ["review:2026-07-26-independent-review-round-three-TST-0002"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [ISS-0011, ISS-0012, ISS-0013, ADR-0012, TST-0002]
tests: [TST-0002]
---

# Round-three review findings: the ISS-0013 fix commit doubled the file, and two of its claims are refutable

## Problem

Independent round-three review of [[TST-0002]] / [[CHG-20260726-Phase-Resolved-Declined]] (commit 4943af3, reviewed by model:claude-fable-5) verified the substance of the ISS-0013 fix — the widened walker catches all nine claimed branches, the metrics rewrite is behaviour-preserving on all 18 metrics across all 11 repos, and the fleet is byte-identical and clean. Three findings remain, one of them a new shipped defect.

1. **The commit doubled the file's second half.** `validate-docs.py` was 1514 lines at 12a7c70 and is 2560 at 4943af3: lines 1560–2560 are a **verbatim byte-for-byte duplicate of lines 556–1556** (`fix_metrics` through the `if __name__ == "__main__"` block), appended *after* the real entry point. Run as a script, `sys.exit(main())` at line 1556 means the duplicate never executes; imported as a module, the duplicate re-executes identical definitions — so behaviour is unchanged, which is exactly why every mechanical check shipped green over it. But ~1000 lines of accidental duplication now sit in **all 12 fleet files** (11 repos plus the cockpit bundle, all byte-identical), unmentioned in the commit message, the CHG, ISS-0013's Resolution, or TST-0002. It is also a live maintenance trap: every function from `fix_metrics` to `main` is now defined twice (e.g. the METRICS error lines exist at 1443 *and* 2447), so a targeted future edit can silently patch one copy — and if the copies ever diverge, which copy wins depends on whether the file is run or imported.
2. **"No inline status literal remains in the file" is false.** The claim appears bolded in ISS-0013's Resolution, in the commit message, in the CHG's ISS-0013 follow-up, and (as "no inline status literal remains") in TST-0002's coverage boundary. Refuted inside `validate()` today: line 1446, `for coll_name, settled in (("tests", {"passing"}), ("changes", {"merged"})):` — two inline *collections* of status literals (the ADR-0011 REVIEW check), the exact shape ISS-0013 hoisted elsewhere. Beyond collections, at least eight single-status comparisons remain: `!= "passing"` (1169, VERIFY), `== "deferred"` (1189, 1193), `== "draft"` (1269, REQ-PREMATURE — sitting right next to the registered `REQ_UNADVANCED_STATUSES`), `== "implemented"` (1280), `!= "done"` (1316, 1375), `!= "deferred"` (1397). A rename of any of these values silently narrows the check it lives in — the precise drift class TST-0002 exists for. All are duplicated again in the dead tail.
3. **The boundary prose is still written slightly wider than the code — the fourth iteration of the pattern, now on three narrower axes.** Demonstrated on scratch copies, each leaving `--self-check` green at exit 0: a module-level **dict** of statuses (`NEW_DICT_STATUSES = {"issue": {"bogus", "fixed"}}`, and likewise `{"bogus": "done"}`) — and dict is the file's own most-used table shape, `PHASE_RESOLVED` itself; an **underscore-prefixed name** (`_HIDDEN_STATUSES = ("bogus", "done")`) — the walker must skip `_` names so `_NON_STATUS_COLLECTIONS` does not flag itself, but nothing says so; a **nested container** (`NESTED_STATUSES = (("bogus", "done"),)`); and an empty collection. Against that: the docstring's "Covers every status collection at MODULE SCOPE" and "every module-level string collection is either registered above or named in _NON_STATUS_COLLECTIONS" are both refuted by the dict and underscore cases, and TST-0002's "the assertion is type-agnostic and case-agnostic … whatever the name looks like" is refuted twice in one sentence ("type-agnostic" — dict evades; "whatever the name looks like" — `_` names are skipped).

Noted, not a defect: ISS-0013's Resolution row "a metric prefix loses its type map — caught" holds only for prefixes with non-`None` filters (deleting `"ISS"` from `METRIC_PREFIX_TYPE` errors; deleting `"REL"`, whose only metric is `("REL", None)`, is silent — defensible, since there are no statuses to check, but the table row overstates).

## Repro

```
# 1. the duplicate
wc -l tools/scripts/validate-docs.py                      # 2560; was 1514 at 12a7c70
sed -n '556,1556p'  tools/scripts/validate-docs.py > /tmp/a
sed -n '1560,2560p' tools/scripts/validate-docs.py > /tmp/b
diff /tmp/a /tmp/b && echo IDENTICAL                      # IDENTICAL

# 2. inline status collections inside validate()
grep -n '("tests", {"passing"}), ("changes", {"merged"})' tools/scripts/validate-docs.py

# 3. boundary evasions (each leaves --self-check green)
#   NEW_DICT_STATUSES = {"issue": {"bogus", "fixed"}}
#   _HIDDEN_STATUSES = ("bogus", "done")
#   NESTED_STATUSES = (("bogus", "done"),)
```

## Expected

The file contains one copy of itself; claims about the file ("no inline status literal remains") are true of the file; the walker's boundary is stated exactly (four container types, non-underscore names, non-empty, flat) wherever it is described, or widened to match the prose.

## Actual

Lines 1560–2560 duplicate 556–1556 in all 12 fleet files; inline status collections and eight single-status comparisons remain inside `validate()`; dict-shaped, underscore-named, nested and empty status collections all evade the completeness assertion while the prose says "every status collection at MODULE SCOPE", "type-agnostic", "whatever the name looks like".

## Evidence

- Demonstrations run 2026-07-26 on scratch copies; recorded in the round-three review sections of [[TST-0002]] and [[CHG-20260726-Phase-Resolved-Declined]].
- What held up is recorded there too: all nine ISS-0013 inversion branches re-induced and caught; metrics parity independently recomputed (old `compute_metric_counts` at 12a7c70 vs new, all 18 metrics identical in all 11 repos; key order differs but both consumers are order-insensitive); METRICS + `--fix-metrics` verified end-to-end on a scratch repo; all 12 fleet files byte-identical; all 11 repos validate 0 / `--self-check` 0 / `sync-snapshot --check` 0; cockpit vocabulary suite 24 passed.

## Next Actions

- [ ] Delete lines 1557–2560 of `validate-docs.py` (everything after the first `if __name__ == "__main__":` block), confirm the file returns to ~1514 lines and `diff` against 12a7c70 shows only the intended ISS-0013 changes, then re-propagate to all 11 repos and the cockpit bundle
- [ ] Retract or scope the "no inline status literal remains" sentence everywhere it appears (ISS-0013 Resolution, CHG follow-up, TST-0002 coverage boundary), or hoist the line-1446 sets and decide explicitly whether single-status comparisons are in or out of the claim
- [ ] State the walker's boundary exactly in the docstring and TST-0002: tuple/list/set/frozenset only (dict excluded — say why, or walk dict keys/values), names not starting with `_` (say why), non-empty, flat
- [ ] Optional: qualify ISS-0013's prefix-map Resolution row (caught only when the prefix has non-None filters)

## Resolution

Fixed 2026-07-26, same session.

**The duplicated tail.** Deleted; the file is back to one copy of every definition (`ast` confirms zero duplicated top-level defs), and re-propagated to all 12 fleet files. The cause was mine and it was crude: the ISS-0013 metrics rewrite used ad-hoc string surgery on the source, and a botched `join` re-appended the second half of the file after `sys.exit(main())`. Run as a script the tail never executed, so nothing anywhere went red — the validator, the self-check, the cockpit suite and eleven repos all passed over a file that had silently doubled.

That is a lesson about method, not about this bug. Editing a source file by string replacement gives no structural feedback; the `ast.parse` I ran confirmed the result was *valid Python*, which a doubled file is. Later edits in this issue used anchored single-target replacements and an AST check for duplicate definitions.

**"No inline status literal remains" — retracted and replaced.** The claim was false: `(("tests", {"passing"}), ("changes", {"merged"}))` sat inside `validate()`. Hoisted as `REVIEW_SETTLED_STATUSES` and registered, checked through `COLLECTION_TYPE`. An AST scan now confirms no multi-value inline status collection remains. The single-status comparisons the review also listed (`status == "done"`) are ordinary code, are not collections, and are explicitly declared out of scope rather than quietly ignored.

**The walker's remaining evasions.** It took tuple/list/set/frozenset but not `dict` — and `PHASE_RESOLVED`, the file's most-used table, is a dict. It also skipped underscore-prefixed names. Both closed: the walk recurses into any container to depth 4 and exempts only `_NON_STATUS_COLLECTIONS` itself, by identity rather than by name shape.

**The type tables.** `COLLECTION_TYPE`, `TERMINAL_TYPES` and `METRIC_PREFIX_TYPE` hold note *types*, so `_check_values` does not apply, but a type renamed in one and not `ALLOWED_STATUS` fails just as quietly. Now asserted.

That assertion found a live bug on its first run: **`decision` is an accepted note type — `COLLECTION_TYPE` has mapped decisions to `{"adr", "decision"}` all along — but `ALLOWED_STATUS` never carried it, so a `decision`-typed note's status was validated against nothing.** One such note exists fleet-wide (`your-health` ADR-0006, `accepted`, legal under either spelling). The alias now carries `adr`'s vocabulary.

**The prefix-map row.** ISS-0013's table said "a metric prefix loses its type map — caught". True only for prefixes with a non-`None` filter; deleting `REL`, whose only metric counts everything, is silent. Row qualified.

Verified by inversion, twelve branches, all caught:

| Induced | |
|---|---|
| module-level `dict` of statuses — **this issue's evasion #1** | caught |
| underscore-prefixed name — **#2** | caught |
| nested tuple-of-tuples — **#3** | caught |
| module-level `set` (ISS-0013 repro) | caught |
| `frozenset`; lowercase-named tuple | caught, both |
| `CLOSED_PHASE_STATUSES` renamed (ISS-0012 repro) | caught |
| `PHASE_RESOLVED["issue"]` reverted to `wont-fix` (ISS-0011 repro) | caught |
| `REVIEW_SETTLED_STATUSES` drifts | caught |
| a note type renamed in `COLLECTION_TYPE` / `METRIC_PREFIX_TYPE` / `TERMINAL_TYPES` only | caught, all three |

Metrics parity re-confirmed after every edit: all 18 keys, identical values, all 11 repos, old code against new. Fleet: 12 files byte-identical at 1619 lines, 0 errors, self-check ok, snapshots clean, cockpit suite 314 passed / 1 skipped.

## Four rounds

| | The miss | Shipped green? |
|---|---|---|
| [[ISS-0011]] | a rename missed three status tables | yes |
| [[ISS-0012]] | the fix for ISS-0011 missed a table it had just created | yes |
| [[ISS-0013]] | the guard against ISS-0012 missed a table *type* | yes |
| ISS-0014 | the widened guard missed `dict`, the most common shape — and the commit doubled the file | yes |

The through-line is not carelessness in any one round; each fix was tested by inversion and each passed. It is that **a guard cannot establish its own coverage, and the artifact that keeps being wrong is the sentence claiming it can.** Four times the prose was written wider than the code, and four times every mechanical check agreed with the prose.

The only thing that has actually caught this, every time, is a reviewer attacking the guard rather than reading it.
