---
type: "[[issue]]"
id: ISS-0013
aliases: ["ISS-0013"]
title: "Completeness assertion sees only tuples, its prose says 'constant'; the 'covers every status collection in this file' docstring phrase survives ISS-0012's own post-mortem; a round-one finding (stale your-sudoku follow-up) left unaddressed"
status: fixed
severity: low
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
component: tooling
source: ["review:2026-07-26-independent-re-review-TST-0002"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [ISS-0011, ISS-0012, ADR-0012, TST-0002]
tests: [TST-0002]
---

# Round-two review findings: boundary prose of the completeness assertion, and one survivor from round one

## Problem

Independent re-review of [[TST-0002]] / [[CHG-20260726-Phase-Resolved-Declined]] (commit 12a7c70, reviewed by model:claude-fable-5) confirms every round-one finding from [[ISS-0012]] is fixed and verified — all six inversion branches reproduce verbatim, all 11 fleet validators are byte-identical, all ten repos validate clean. What remains is smaller, and it is the same *shape* of defect one level up: the completeness assertion's own coverage is described more broadly than it is.

1. **The completeness walker sees only `tuple`s.** `validate_status_tables` filters on `isinstance(value, tuple)`, so a module-level status collection written as a `set`, `frozenset`, `list`, or `dict` evades it silently — demonstrated: `NEW_SET_STATUSES = {"bogus", "done"}` at module scope leaves `--self-check` green (likewise frozenset, list, and dict shapes). TST-0002's coverage-boundary sentence "What the assertion covers is the next-most-likely mistake: a new module-level constant that nobody registered" is refuted by that counterexample, and "That is the remaining gap" (singular, referring to inline literals) undercounts. A set is not an exotic authoring shape here: the file's own dict tables hold sets, and the retired `risks_open` literal was a set. The fix is two-line — widen the isinstance to `(tuple, list, set, frozenset)` (both `_check_values` and the `id()`-based registration already handle any iterable of strings) — or, at minimum, correct the two sentences to say "tuple". Lower-severity siblings of the same boundary: lowercase/mixed-case names and empty tuples also evade (`name.isupper()` / `not value` filters); acceptable as convention, but the note should own the choice.
2. **The docstring phrase ISS-0012's post-mortem branded is still in the file.** [[ISS-0012]] records: "the docstring said 'covers every status collection in this file' and was wrong at the moment it was written." The fixed `validate_status_tables` docstring still opens its coverage list with exactly that phrase — and by ISS-0012's own adjudication (which counted the inline local `DESCOPED` as a status collection), it is still refutable: `("passing", "failing")` (TEST-FIELDS) and `("draft", "approved")` (REQ-STALE) are inline status collections inside `validate()`, and `compute_metric_counts` still holds nine inline single-status set literals — siblings, in the same dict, of the exact `risks_open` literal ISS-0012 hoisted. Demonstrated: mutating either inline tuple to retired/invented vocabulary leaves `--self-check` green while the check silently narrows. TST-0002's Procedure section repeats the phrase ("For every status collection in the file it asserts"), then its Coverage boundary walks it back; the docstring never walks it back. Either scope the phrase ("every module-level status collection") in both places, or hoist the two inline tuples.
3. **A round-one finding survived the rewrite it sits in.** The CHG's round-one review section states the your-sudoku follow-up "no longer holds … can be ticked or rewritten" — and three lines below it, the unticked checkbox still asserts, present-tense, that your-sudoku "is 146 lines behind and its plan notes fail the newer PLAN-ID check." Both claims are now false: your-sudoku's validator is byte-identical to upstream (its commit f4728a6) and the repo validates OK.

Noted, not defects: `TERMINAL`↔`TERMINAL_TYPES` sync is one-directional — a `TERMINAL` key missing from `TERMINAL_TYPES` errors (the direction that matters, since `TERMINAL` drives real validation and `TERMINAL_TYPES` is guard-only metadata), but an orphan `TERMINAL_TYPES` key is silent, and a wrong-type `TERMINAL_TYPES` value is caught only when the terminal status happens to be illegal for the wrong type (`"tasks": "feature"` drifts green because `done` is legal for both). Worth one sentence in TST-0002 if left as-is. `_NON_STATUS_TUPLES` is correctly scoped: `ID_PREFIXES` holds ID prefixes and `RELATIONSHIP_FIELDS` holds frontmatter field names (its `deferred`/`superseded` entries are field names, not statuses), and no other existing module-level container (`COLLECTION_TYPE`, `PROMOTIONS`, `METRIC_PREFIXES`) holds status values — verified by AST scan.

## Repro

```
# 1. set-shaped collection evades the completeness assertion
sed -i '' 's/^RISK_OPEN_STATUSES = ("open",)/RISK_OPEN_STATUSES = ("open",)\nNEW_SET_STATUSES = {"bogus", "done"}/' tools/scripts/validate-docs.py
python3 tools/scripts/validate-docs.py --self-check   # exits 0

# 2. inline collection drifts silently (docstring says "every status collection in this file")
sed -i '' 's/if status in ("draft", "approved") and all_resolved:/if status in ("draft", "pending") and all_resolved:/' tools/scripts/validate-docs.py
python3 tools/scripts/validate-docs.py --self-check   # exits 0; REQ-STALE silently narrowed
```

## Expected

The assertion's boundary is stated exactly (tuples, uppercase names, non-empty) wherever it is described, or the boundary is widened to match the prose; the docstring's "every status collection in this file" is scoped or made true; the CHG carries no present-tense claims that are false.

## Actual

Prose describes the walker as covering "a new module-level constant"; four container shapes evade it; the branded docstring phrase persists and remains refutable via two inline tuples and nine inline metric sets; the stale follow-up checkbox stands.

## Evidence

- Demonstrations run 2026-07-26 on scratch copies; recorded in the round-two review sections of [[TST-0002]] and [[CHG-20260726-Phase-Resolved-Declined]].
- Fleet identity and clean validation confirmed the same day (11 files byte-identical via `cmp`; `validate-docs.sh` OK in all ten repos).

## Next Actions

- [ ] Widen the completeness walker to `(tuple, list, set, frozenset)` of strings, or amend TST-0002's two boundary sentences to say "tuple" — pick one and make prose and code agree
- [ ] Scope or satisfy the docstring's "covers every status collection in this file" (and TST-0002's Procedure echo): either say "every module-level status collection" or hoist `("passing", "failing")` and `("draft", "approved")`
- [ ] Tick or rewrite the your-sudoku follow-up in the CHG; drop the now-false "146 lines behind" claim
- [ ] Optional: one sentence in TST-0002 on the `TERMINAL_TYPES` reverse direction being deliberately uncovered

## Resolution

Fixed 2026-07-26, same session.

**The walker.** It checked `isinstance(value, tuple)` and `name.isupper()`. Neither type nor case is what makes something a status table, and a module-level `set` proved it by walking past the guard whose entire purpose is catching unregistered status collections. Now takes tuple/list/set/frozenset and ignores case; `_NON_STATUS_TUPLES` renamed `_NON_STATUS_COLLECTIONS` to match, with `METRIC_PREFIXES` added (ID prefixes, not statuses).

**The inline literals.** `TEST_RUNNER_STATUSES` and `REQ_UNADVANCED_STATUSES` hoisted and registered. The eight metric filters still written inline beside the one ISS-0012 hoisted are now one registered table, `METRIC_STATUS_FILTERS`, checked through a `METRIC_PREFIX_TYPE` map — so a drifted metric names which metric drifted. `RISK_OPEN_STATUSES` is subsumed by that table and gone. **No inline status literal remains in the file.**

**The docstring.** Now says "every status collection at MODULE SCOPE", with the qualifier flagged as load-bearing, and the coverage boundary in TST-0002 states the function-local gap exactly rather than as a class.

**The stale checkbox.** Ticked with evidence. It had survived round two's rewrite while sitting three lines below the review section flagging it — recorded in the CHG, because editing around a finding is its own failure mode.

Verified by inversion, nine branches including this issue's repro verbatim and the four collection types that previously evaded:

| Induced | Caught |
|---|---|
| `NEW_SET_STATUSES = {"bogus", "done"}` — **this issue, verbatim** | yes |
| module-level `frozenset` / `list` | yes, both |
| lowercase-named tuple | yes |
| tuple built by comprehension | yes |
| `TEST_RUNNER_STATUSES` / `REQ_UNADVANCED_STATUSES` drift | yes, both |
| a metric filter drifts; a metric prefix loses its type map | yes, both |

The metrics rewrite was separately shown behaviour-preserving: all 18 metrics identical across all 11 fleet repos, old code versus new.

## The pattern this issue completes

ISS-0011: a rename missed a table. ISS-0012: the fix for it missed a table it had just created. ISS-0013: the guard against that missed a table *type*.

Three rounds, each shipping green, each found by a reviewer attacking the guard rather than reading it. The recurring artifact is not the code — it is the sentence describing the code's reach, written slightly wider than the code every single time. The mitigation is not another assertion; it is that the boundary statement is now specific enough to be falsifiable, and that a reviewer tried to falsify it.
