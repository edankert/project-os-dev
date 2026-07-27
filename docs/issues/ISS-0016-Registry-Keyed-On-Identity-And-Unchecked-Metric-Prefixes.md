---
type: "[[issue]]"
id: ISS-0016
aliases: ["ISS-0016"]
title: "The completeness registry was keyed on id(), which CPython constant-dedup defeats; and every total metric skipped its prefix check, so a mistyped prefix silently read zero"
status: fixed
severity: medium
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
component: tooling
source: ["experiment:TASK-0077 independence-premise", "review:model:gpt-5-codex", "review:model:claude-opus-5"]
phase: "[[PHASE-999]]"
related: [ISS-0011, ISS-0012, ISS-0013, ISS-0014, ISS-0015, TST-0002]
tests: [TST-0002]
fixed_by: "[[TASK-0077]]"
---

# Four more silent-drift channels, found by two reviewers on one prompt

## How these were found

[[TASK-0077]] ran two reviewers against the identical prompt: clean-context Opus (same family as the author) and gpt-5-codex (different family). Both returned `changes-requested`. Four findings between them, all with working reproductions, all confirmed independently before acceptance.

## 1. The completeness registry was keyed on `id()` — Opus

The load-bearing one, and it defeats the guard added for [[ISS-0012]] on its own terms.

`validate_status_tables` collected registered tables into `registered = {id(values) …}` and skipped any module-level collection whose `id()` was in that set. **CPython deduplicates equal tuple constants within a code object**, so two module-level tables with the same literal are the *same object*:

```
CLOSED_PHASE_STATUSES   = ("done", "superseded")
ISSUE_ARCHIVED_STATUSES = ("done", "superseded")   # ← same id(), registered by accident
```

Verified: both names bind one object, `id` identical. So an unregistered status table whose literal happens to match a registered one is invisible to the assertion whose entire purpose is catching unregistered status tables.

This is not exotic. Status tables share values constantly — `("done", "superseded")` already appears in several, `("draft", "approved")` in two. A second collision was demonstrated in the same run (`RISK_STALE_STATUSES` colliding with `REQ_UNADVANCED_STATUSES`). Both new tables carried values illegal for the types they named, and `--self-check` stayed green.

**Fix:** key on **name**, not identity. `registered = set(FLAT_STATUS_TABLES) | _CHECKED_TABLE_NAMES`. A name cannot be interned into another name. The bookkeeping frozensets are now named in `_NON_STATUS_COLLECTIONS` rather than exempted by identity — the identity exemption was the same mechanism in miniature.

## 2. `METRIC_PREFIXES` gated every metric and was checked against nothing — Opus

`METRIC_PREFIXES` decides which IDs get counted at all. It was exempted **by name** in `_NON_STATUS_COLLECTIONS` and asserted nowhere. Rename a prefix there — `RISK` → `RSK` — and every metric using it reads 0 permanently.

The nasty part: the `METRICS` validator check does not catch it, because it compares the snapshot's recorded counts against *the same broken computation*. Both agree on zero. Demonstrated with a genuinely open risk in the repo and `risks_open` returning 0, full validator silent, exit 0.

**Fix:** `METRIC_PREFIXES` and the prefixes in `METRIC_STATUS_FILTERS` must be the same set, asserted in both directions.

## 3. Total metrics skipped the prefix check entirely — Codex

`METRIC_STATUS_FILTERS` maps metric → `(prefix, statuses)`, and totals carry `statuses = None`. The loop began `if allowed is None: continue` — *before* validating the prefix. Seven of eighteen metrics are totals, and all seven were unguarded.

`ADR` was in fact **already missing** from `METRIC_PREFIX_TYPE` and nothing had noticed, because `decisions_total` is a total. Codex mutated `("ADR", None)` → `("BOGUS", None)`: `--self-check` green, `decisions_total` 12 → 0.

A metric reading 0 is worse than a crash — "no decisions recorded" is a plausible number.

**Fix:** the prefix is checked for every metric; `continue` moved after it. `ADR` added to `METRIC_PREFIX_TYPE`.

Note: Fable saw this territory in the [[ISS-0015]] round and called it *"defensible, but the row overstates"*. Same observation, opposite judgement, and Codex was right.

## 4. The `adr`/`decision` alias rows could drift apart — Opus

[[ISS-0015]] replaced STATUS-VALUE's hash-ordered type pick with a union over the collection's types, which is correct. It also means a value legal for **one** of an alias pair becomes legal for **both**, and nothing asserted the pair stays equal. Widening `decision` silently widened `adr`: an ADR at status `rejected` — legal for no note type — validated completely clean, full validator silent.

ISS-0015's own Resolution flagged the risk in prose ("nothing enforces that") and did not enforce it.

**Fix:** the alias rows are asserted equal.

## Verification

Eight inversion branches, all caught: both `id()`-collision cases, the alias drift, the `METRIC_PREFIXES` rename, Codex's total-metric mutation, and the [[ISS-0011]] / [[ISS-0012]] / [[ISS-0015]] repros still firing. Repo validates 0 errors.

## What this round says about the reviewers

Recorded here because it is the actual finding of [[TASK-0077]]:

| Reviewer | Family vs author | Findings | Tokens |
|---|---|---|---|
| clean-context Opus | **same** | 3 | one run |
| gpt-5-codex | different | 1 | one run |
| Fable (baseline) | same | 4, over four rounds | 440k |

The same-family arm, with clean context, out-found the different-family arm 3:1 in a single run — including the deepest defect in the whole ISS-0011..0016 sequence. `QUALITY.md` justifies its rule with "a second session of the same model reproduces the same blind spots"; that is now evidence against, not for.

Caveats hold: n=1 per arm, and both arms were told what earlier rounds found, which is an easier task than Fable faced in rounds 1–3.
