---
type: "[[issue]]"
aliases: ["ISS-0039"]
id: ISS-0039
title: "Round-seven review: the engineering is clean for a fourth consecutive round and the 203 = 200 + 3 skip set is exactly right on three surfaces — but the fourth, `test-retention.py`, kept the stale \"17\" and now attaches it to \"all zero-byte\", asserting a fleet population of 17 zero-byte notes where 3 exist"
status: open
severity: low
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-round-seven-FEAT-0022", "22 self-authored mutations + 7 extra formulations + full fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0026, ISS-0032, ISS-0033, ISS-0034, ISS-0035, ISS-0036, ISS-0037, ISS-0038, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Round-seven review findings on the FEAT-0022 record

Seventh clean-context independent review (fresh session; the notes and the diff only, never the authoring session's reasoning). `ISS-0033` through `ISS-0038` were read as records of claims to refute, not as findings to trust. Verdict: **changes-requested**, on one item, which is a one-line edit.

## The restated skip set is correct, and I confirmed it by measurement rather than by reading

Round six's finding was that the "seventeen" was false, and it proposed a replacement that was also false. The author then measured directly and restated the claim as **203 = 200 `CHG-*` + 3 zero-byte**. I re-derived that population from scratch, loading each repo's *own* `sync-snapshot.py`, collecting every id registered under `items.*`, and asking `note_fields` what it supplies:

| repo | registered | skipped | composition |
|---|---|---|---|
| your-trainer | 412 | 2 | 2 CHG |
| project-os-cockpit | 346 | 80 | 77 CHG + 3 TASK |
| your-health | 354 | 39 | 39 CHG |
| your-applications.com | 151 | 56 | 56 CHG |
| your-sudoku | 191 | 11 | 11 CHG |
| yourtrainer-mcp | 61 | 0 | — |
| edankert.com | 50 | 1 | 1 CHG |
| project-os-dev | 136 | 6 | 6 CHG |
| obsidian-supernote-sync | 34 | 5 | 5 CHG |
| project-os-bench | 29 | 0 | — |
| project-os | 0 | 0 | — |
| articles | 55 | 3 | 3 CHG |
| **fleet** | **1,819** | **203** | **200 CHG + 3 TASK** |

The 3 non-`CHG` skips are exactly `project-os-cockpit`'s `TASK-0182`, `TASK-0183` and `TASK-0187`, and those are exactly the 3 zero-byte `.md` files under `docs/` in the entire fleet — I searched all twelve for `-size 0` and found no others. **203 = 200 + 3 is confirmed.**

Both of the earlier readings are also confirmed refuted, independently:

- **The 14 PyYAML-rejecting files do supply titles.** I found the population at exactly 8 `your-trainer` / 5 `your-health` / 1 `your-applications.com`, and for every one of the 14 the code's own `load_yaml` returns a dict with a non-empty `title`. 14 of 14. `your-health`'s `SNAPSHOT.yaml:1506` carries the derived `"AI Coach: chat-based training recommendations"` for `REQ-0024` today, as the note says.
- **The 14 `your-health` `REF-*` entries are supplied.** They are registered in that repo's snapshot and none of them appears in its 39-entry skip set, which is all `CHG-*`. Round six's proposed composition is refuted by the same measurement that refutes the original.

## Blocking — `test-retention.py` kept the number and dropped the decomposition

Round six named four surfaces that had to move together. Three moved and are now correct:

- `CHG-20260804:78` — 203 / 200 / 3. Correct.
- `TST-0003:51` — identical text. Correct.
- `sync-snapshot.py:270-275` (`note_fields` docstring) — 203 / 200 / 3, and states explicitly that PyYAML-rejecting files are *not* among them. Correct.

The fourth, `tools/scripts/test-retention.py:133-136`, was edited but the number was left behind:

```python
    # Fail-safe on derivation: a note with no usable title must leave the
    # snapshot value ALONE rather than blanking it. 17 real notes are in this
    # state fleet-wide, all zero-byte; files whose frontmatter PyYAML rejects
    # are NOT among them, because load_yaml falls back to parse_yaml_subset.
```

The second clause is right and is the fix round six asked for. The number is not. As restated the sentence asserts that **17 notes fleet-wide are zero-byte**, and there are **3**. This is strictly worse than the text it replaced: the old `(3 zero-byte, 14 unparseable)` at least decomposed 17 into two populations it named, so a reader could check each; the new sentence puts the whole 17 behind "all zero-byte", where no measurement supports it.

I looked for a reading that would make 17 true here and there is none. Across the fleet: 3 zero-byte notes; 203 skipped registered entries; 5,087 `.md` files under `docs/`, of which 567 carry no usable title and 370 of those carry an `id:`. Nothing counts 17. The only 17 in the system is the arithmetic of the retracted claim.

**Fix:** replace `17 real notes` with `3 real notes` (or drop the count and say "the fleet's three zero-byte notes"). One line, one file. No code changes, no assertion changes — the fixture and the two assertions beside this comment are correct and catch the mutation they exist for.

## What I could not refute

Everything else, under direct attack:

- **Losslessness, re-derived from git.** 3,146 pre-migration items across the twelve; 1,352 entries removed; **0** whose note fails to supply exactly the collection's terminal status. Checked per collection against `PRUNABLE_TERMINAL`, not by trusting the prune's own conditions.
- **Migration records reconcile.** 709 rows fleet-wide across ten records, every `was:` value string-compared against that repo's own pre-migration `SNAPSHOT.yaml` at the migration commit's parent: **709 faithful, 0 mismatches**, and every record's `N value(s) replaced.` header equals its own section count (413/140/33/26/44/3/8/30/1/0/0/11).
- **Twelve repos.** `validate-docs.sh` exit 0 in eleven and exit 1 only here on the standing `REVIEW` error; **0** `^ERROR` elsewhere, **0** `internal error` anywhere; `sync-snapshot.py --check` exit 0 in all twelve; `test-retention.py` **23 assertions** green in all twelve.
- **Idempotence, on real syncs.** For each repo I hashed `SNAPSHOT.yaml`, ran two consecutive real (non-`--check`) syncs, and compared: byte-identical after the first and second in all twelve, *and* identical to the pre-run file — the fleet is at a fixed point. Every snapshot restored from backup and re-hashed afterwards.
- **Byte figures.** `1,151,665` before is exact, summed from each repo's snapshot at its own pre-migration parent. Every per-repo row in the impact table matches. After is 718,897 (−37.6%) against the note's `~714,800, about −38%`, which the note already discloses as drifting upward each round.
- **The bundled validators.** Twelve copies of `validate_docs_bundled.py` across the fleet, all twelve carrying the `claimants` fix.
- **No paste artifacts.** Round six's unbalanced backtick at `CHG:78` is gone; backticks are even and bold markers balanced on `CHG:78`/`:80` and `TST-0003:51`/`:53`.

## Mutation adequacy: "10 of 22" confirmed

I wrote 22 mutations from the code before reading any prior round's table, then 7 further formulations. My own 22 score **8 caught / 14 survived**; the difference from 10 is entirely which formulations I chose, not a weaker suite. Two of the breaks the notes name as caught I had initially written in weaker forms that the suite cannot see, and when written the way the notes describe them both are caught:

- `prune_entries` stubbed to `return []` — **caught**.
- A missing title written through as an empty string — **caught**, 2 assertions, exactly as `TST-0003`'s review note says.
- The scanner replaced with a comma search — **caught** under both natural formulations (`_value_end` reduced to `body.find(",")`, and `_scalar_span`'s inline scan replaced by a regex plus comma). My first attempt mutated only the depth guard, which the quoted fixture never reaches; that is my formulation being weak, not the suite.

Substituting those for two survivors gives exactly **10 caught / 12 survived**. All twelve survivors the notes name were individually confirmed to survive: condition 1, condition 4, blank-but-present title, non-string title, fail-open `_owes_verification`, the focus scan, the `in_items` guard, doubled-quote handling, a widened `PRUNABLE_TERMINAL`, a 4-column over-delete, the banner de-duplication, and the ambiguous-claim guard (in both `note_fields` and `note_statuses`). Caught, confirmed: condition 2, condition 5 reverted to index membership (4 assertions), condition 5 weakened to `not in statuses` (via `cond3 deferred survives`), condition 6, condition 7, `_scalar_span` reverted to `find("{")` (2 assertions), `_yaml_quote` emitting a bare scalar (2 assertions), and both destructive writers stubbed.

A method note for whoever runs this next: `importlib.spec_from_file_location` reuses `__pycache__` bytecode keyed on mtime and size, so two mutations whose replacement text is the same length can silently run each other's code. My first pass scored condition 4 as caught for that reason. Run the suite with `-B`.

## Non-blocking, recorded rather than held against the verdict

- `CHG:54`'s "item counts are the stable measure: **3,146 → 1,817**" measures **1,819** today, with the `project-os-dev` table row at 136 rather than 134. The drift is real, disclosed, and caused by this review adding notes to this repo — but it is disclosed for *bytes*, and the sentence then offers item counts as the figure that does *not* drift, which is the one claim in the paragraph that its own mechanism undermines.
- `CHG:85`'s "1,350 removals" measures 1,352 now; it is attributed to round three and was true when measured.
- The three recorded debts — the ADR-0018 six-vs-seven reconciliation, the 15-line bundled drift, and the latent `index`-vs-`claimants` issue — are all **true as stated** and are not held against this verdict.
- Condition (4) still has no fixture, condition (1) deleted still survives, and `compute_metric_counts` still has no test. All three are named in the notes as gaps.

## Independence

Fresh context and a separate session: I started from the notes and the diff and have no memory of authoring any of this. Same model family as the author — `model:claude-opus-5[1m]`, recorded in `reviewed_by` on both notes as provenance. Per ADR-0013 the active ingredient is the context, not the weights: what I did not share with the author is the commitment, and every figure above was re-derived by running code rather than by reading a claim.

## Status — fixed 2026-08-04

**The blocking finding was mine and it was real.** Restating the skip-set claim across four surfaces, I replaced the *explanation* in `test-retention.py` but left the *number* behind, so the comment read "17 real notes … all zero-byte" — asserting seventeen zero-byte notes where three exist. That is worse than the text it replaced, which at least decomposed 17 into two checkable populations. Corrected to 3; all four surfaces now agree.

The pattern is worth naming because it is the third time in this chain: **a partial correction is a new error.** Round four's corrections reached the CHG note and not TST-0003. Round six's reached the prose and not the number. Each time the fix was right and its application incomplete, and each time a fresh reader caught what the author's own re-read did not.

Also corrected: the two drift figures round seven flagged — 1,350 → **1,352** removals, and the item count restated as "~1,818" with the reason it moves, since offering item counts as the stable alternative to bytes while quoting them to four figures repeats the false precision the sentence was warning against.

Round seven's method note is recorded for whoever runs mutations next: `importlib.spec_from_file_location` reuses `__pycache__` keyed on mtime and size, so an equal-length mutation silently executes the previous bytecode. Run with `-B`. That is a real trap for exactly this kind of verification and it cost that round a mis-scored condition.

Stays **open**: the author does not clear a verdict on their own work.
