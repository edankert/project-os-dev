---
type: "[[issue]]"
id: ISS-0035
aliases: ["ISS-0035"]
title: "Round-three review of the ISS-0034 fixes: both blocking defects are genuinely fixed and the fleet is clean, but the metric fix never reached the two bundled validator copies — project-os-cockpit's own cockpit reports `ERROR [METRICS] features_done is 55 but computed 54` today — and `TST-0003`/`CHG-20260804` still describe round two's artifact while six of ISS-0034's next actions are ticked without being done"
status: open
severity: medium
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-round-three-FEAT-0022", "23 mutations + fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0026, ISS-0032, ISS-0033, ISS-0034, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Round-three review findings on the FEAT-0022 fixes

Third clean-context independent review (fresh session; notes and diff only, no access to the authoring session's reasoning and none to rounds one or two beyond the two issue notes, which were read as claims to refute). Verdict: **changes-requested**.

**The engineering asks of round two are met.** Both of `ISS-0034`'s blocking findings are resolved on the merits, verified by mutation and by re-measurement rather than from tick-marks, and both defects the author self-reported while fixing them are genuinely gone. The fleet is in the healthiest state any of the three rounds has measured: twelve repos, no `internal error`, no validator error but the standing `REVIEW` verdict, `--check` clean everywhere, byte-identical across two consecutive *real* syncs, `test-retention.py` green in all twelve, and **1,350 pruned entries fleet-wide with zero whose note cannot supply its terminal status**.

What blocks is one code path the fix did not reach and a handoff surface that still describes the previous round's artifact. The pattern is the same one rounds one and two found and is now on its third repetition: the claim is written wider than the work.

## Blocking

### 1. The `compute_metric_counts` fix never reached the two bundled validator copies, and `project-os-cockpit`'s own cockpit reports the defect as an ERROR today

The fix landed in `tools/scripts/validate-docs.py` in all twelve repos. It did **not** land in `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py`, which exists in both `project-os-dev` and `project-os-cockpit`. Run in the cockpit repo, that copy still says:

```
ERROR [METRICS] metrics.counts.features_done is 55 but computed 54 (run validate-docs.sh --fix-metrics)
```

This is `ISS-0034`'s blocking finding 1, unfixed, in the code path the cockpit *application* ships. It is a regression the migration introduced: before the prune, `FEAT-0009`'s snapshot entry supplied `done` and the index fallback was never consulted, so the bundled validator agreed at `48ea49e~1`.

`validation.py:10-17` documents the locate order — the browsed repo's own `tools/scripts/validate-docs.py` first, the bundled copy second — so the live blast radius is a repo that has no validator of its own, and every one of the twelve has one. That is why this is `medium` and not `high`. But `validation.py:15` and `:79` both call the bundled file *"a verbatim copy of the canonical script"*, and `diff` says it was verbatim before this change: the **only** 36 diff lines between the two files in `project-os-cockpit` are this change. So the invariant was intact and this broke it, and `ISS-0026-Bundled-Validator-Drift` is the issue that already exists for exactly this failure mode.

The root cause is visible one line up: `CHG-20260804`'s `impacts:` is `["tools/scripts/sync-snapshot.py", "SNAPSHOT.yaml (all 12 repos)"]`. `tools/scripts/validate-docs.py` changed in twelve repos and is not listed, so nothing pointed at its copies.

Fix: apply the change to both bundled copies (or re-vendor them), and add `tools/scripts/validate-docs.py` to `impacts:`.

### 2. `TST-0003`'s `adequacy` claims a mutation that this round's own change made survive, and condition (3) is now unreachable while three documents say it is live

`adequacy` lists five mutations as the evidence for the suite: four hold when performed individually, and **"the deferred check deleted" does not**. Deleting `sync-snapshot.py:477-478` now leaves the suite green.

The cause is this round's tightening of condition (5). With `if statuses.get(the_id) != terminal`, an entry whose note says `deferred` is already rejected by (5) — `"deferred" != "done"` — so (3) can never be the deciding check. The condition-3 assertion still passes, but it now passes for the wrong reason, and the branch it names is dead code. `ISS-0034` #4 predicted this precisely (*"Closing (5) to `statuses.get(the_id) == terminal` would close (3)'s last real caller too, and the pair should be decided together"*), the next action was ticked, and (5) was closed while (3) was left in place with its record unchanged. The record is now not merely absent but wrong:

- `sync-snapshot.py:471-477` — *"They can disagree before the status sync has run, and that is precisely when a deferred item is at risk"*. They can, and (5) now catches it first.
- `TST-0003:46` presents condition 3 as an inverted, guarded condition.
- `test-retention.py:8-12` and `:92-95` justify the illegal fixture on the same grounds.

Either delete (3) and its assertion together, or record that it is redundant-by-design and stop counting it as mutation evidence.

### 3. `TST-0003` and `CHG-20260804` were not updated for this round at all

`git diff` on both notes shows only round-two content. The two notes under review are the handoff surface, and they describe an artifact that no longer exists:

- `TST-0003:38` — *"## Assertions (18)"*. The suite prints **23**.
- `TST-0003` `last_run: "2026-08-04T10:34Z"` — round two's timestamp, predating the suite it now stamps.
- `TST-0003`'s assertion table gained nothing for the three new condition-5 fixtures or the braced block-style derivation assertion, which are the two guards this round added and the reason it can be approved at all.
- `CHG-20260804:68` — *"Eleven assertions"* (23) and *"every prune condition is violated in turn"* (condition 4 is not; deleting it leaves the suite green — mutation performed).
- `CHG-20260804:70` — *"three independent breaks"*; `adequacy` says five.
- `CHG-20260804:90` — *"18 assertions"*.
- `CHG-20260804`'s Impact table, re-measured: `project-os-cockpit` `593 → 346` items and `199,970 → 133,882` bytes against the stated `343` / `132,874`; `your-sudoku` `→ 191` / `47,202` against `190` / `46,999`; `project-os-dev` `71,076 → 68,284` against `70,962 → 64,829`; `yourtrainer-mcp` `→ 19,558` against `20,089`; `your-trainer` `→ 112,931` against `112,952`; `your-health` `→ 130,012` against `130,033`; `your-applications.com` `→ 129,801` against `129,821`; `edankert.com` `→ 18,698` against `18,718`. Eight of ten byte figures and three of ten item figures are wrong.
- Fleet total, re-measured: `1,151,665 → 710,977` bytes = **1,152 KB → 711 KB, −38.3%**, against the stated `707 KB` / `−39%`. The `1,152 KB` pre-migration figure is exact.
- `commit:` is still empty, now ticked as done twice.
- Nothing in the body describes what this round changed: the `claimants`-first counter, the tightening of condition (5), `_focus_ids`, the banner de-duplication, or the two self-reported defects. A reader of the change note cannot reconstruct the change.

`CHG-20260804:56` — *"Both are back to their pre-migration values"* — is now **true** for `tools/scripts/validate-docs.py` and false for the bundled copy (finding 1).

### 4. Six of `ISS-0034`'s next actions are ticked `[x]`; four are not done

Verified individually: the `FEAT-0009` decision is done (in one of three copies — finding 1); the two suite guards are done; `_focus_ids` is done. Not done: bringing `CHG-20260804`'s verification section, impact table, fleet figure and `commit:` up to date (finding 3); refreshing `SNAPSHOT.yaml`'s `focus.note`, which still reads *"Fleet snapshots 1,158KB -> 707KB (-39%)"* — the `1,158` that `CHG-20260804:52` retracts — and still names `ISS-0032` as the open round with no mention of `ISS-0033`, `ISS-0034` or `ISS-0035`; merging `ISS-0033`'s duplicate `## Status` sections, which are still two, at lines 196 and 202; and deciding (5) and (3) together, which is finding 2.

This is the third round in which a completion tick has been the thing that was wrong. A tick that is written before the check is the same defect as a `review_verdict` written before the reviewer returns (`independent-review` rule 2).

## Non-blocking

### 5. This round's own fixes are unguarded, by round two's own standard

Round two blocked on *"the suite guards NEITHER fix this round produced"*. The same sentence is true of this round, and it is recorded rather than blocked only because both fixes are now demonstrably correct against the real fleet:

- Reverting condition (5) to `if the_id not in statuses` — round two's form, the one that let an inline quoted `status: "done"` prune an entry whose note said `backlog` — leaves the suite green.
- Nothing anywhere tests `compute_metric_counts`. The only automated suite in the repo is `test-retention.py`; the `FEAT-0009` fix has no regression guard in any repo, which is part of why finding 1 could go unnoticed.

### 6. `compute_metric_counts` re-parses every claimant from disk, costing ~35% of validator runtime

The `claimants` loop calls `parse_frontmatter(paths[0])` for every claimed ID although `note_index` already holds the parsed frontmatter for the first claimant — `note_statuses` avoids exactly this with its `entry[0] != paths[0]` check and `compute_metric_counts` does not. Measured on `your-trainer` (the largest corpus): `4.81s → 6.57s` user time, +37%, and `sync-snapshot` calls it up to twice per run. Both run at pre-commit.

### 7. `your-health` has taken a **second** provenance sweep, after the note said the procedure now prevents it

`4df030d` — *"fix(sweep): discard the backoff a hand-driven backfill accumulates…"* — carries `tools/scripts/sync-snapshot.py`, `test-retention.py`, `validate-docs.py` and the rewritten migration record alongside Kotlin application work and an unrelated issue note. `CHG-20260804`'s provenance section records `bc04a44` and states that `TASK-0085`'s procedure *"now requires confirming the tree is clean before migrating a repo"*. The same hazard then recurred during the fixing round. `your-health` is also the only repo where this round's script changes are committed at all; in the other eleven they sit uncommitted.

### 8. A note whose `title:` is an empty string is unguarded

Mutating the fail-safe to `if isinstance(v, str)` (accepting `title: ""`) leaves the suite green; the fixture note has no `title:` key at all, which the mutation `vals[field] = str(v).strip() if isinstance(v, str) else ""` does catch. Production behaviour is correct — a note with `title: ""` leaves the snapshot value alone, verified end to end through `main()` — so this is a coverage gap, not a defect, and `adequacy`'s fourth claim is defensible under the "absent title" reading.

### 9. Mutation coverage overall: 9 of 23 caught

Each performed individually against the working-tree suite (23 assertions, green).

| mutation | suite |
|---|---|
| condition (5) reverted to `if the_id not in index` — round one's defect | **caught** (3 assertions) |
| `_scalar_span` reverted to `body.find("{")` — round one's defect | **caught** (2 assertions) |
| `prune_entries` → `return []` | caught |
| `sync_derived_fields` → `return []` | caught |
| the `note:` hold deleted | caught |
| the verification hold deleted | caught |
| `_yaml_quote` emitting unquoted | caught |
| `_value_end` replaced with a naive comma search | caught |
| blank titles accepted where the note has no `title:` | caught |
| condition (3) deleted | SURVIVED (finding 2) |
| condition (5) reverted to `if the_id not in statuses` — round two's form | SURVIVED (finding 5) |
| condition (4) deleted | SURVIVED |
| focus scan reverted to top-level exact strings | SURVIVED |
| `_owes_verification` reverted to fail-open | SURVIVED |
| retention window off by one | SURVIVED |
| `prune_entries`' `in_items` guard deleted | SURVIVED |
| `_value_end`'s doubled-single-quote handling deleted | SURVIVED |
| `title: ""` accepted in the fail-safe | SURVIVED (finding 8) |
| `PRUNABLE_TERMINAL` widened to `requirements`/`risks` | SURVIVED |
| `prune_entries` over-deleting by four columns of indent | SURVIVED |
| the prune banner never emitted | SURVIVED |
| `note_fields`' ambiguous-claim guard deleted | SURVIVED |
| `note_statuses`' ambiguous-claim guard deleted | SURVIVED |

## What was checked and held

Stated as checked, not assumed. Every figure below was measured in this session from the working trees or from git.

- **`ISS-0034` blocking 1 is resolved in the canonical validator.** `project-os-cockpit`'s `metrics.counts` is **identical to `48ea49e~1` on all fifteen keys**, not only `features_done` — re-read from both snapshots and independently recomputed by `compute_metric_counts` against the current tree, where all twelve computed keys match what is written. `FEAT-0009` is absent from `items.features` (legitimately pruned), its sole claimant is `docs/features/native-shell-layout/FEAT-0009-Native-Shell-Layout.md` saying `done`, and the index slot is still held by `CHG-20260525-FEAT-0009-Chrome-Polish.md`.
- **The `claimants`-first change cannot mis-count anything else.** Old and new resolution compared ID-by-ID across all twelve repos: **exactly one ID differs fleet-wide** (`FEAT-0009`, `merged → done`) and nothing is dropped anywhere. The three awkward shapes were then constructed synthetically: an ID claimed by **zero** notes and reachable only through a composite filename now counts in no total (it counted as a phantom feature before); an ID claimed by **two** notes falls through to the index exactly as before, with `NOTE-DUP-ID` reporting it; a claimant supplying **no status** falls through to the index. Zero-byte and unparseable claimants count in `*_total` and not in `*_done`.
- **`ISS-0034` blocking 2 is resolved.** Both mutations performed individually: condition (5) → `index` fails three assertions; `_scalar_span` → `find("{")` fails two, and the strengthened assertion (checking the *derived* string rather than that a brace survives) is what makes the second one bite.
- **The validator crash is gone.** Greped for `internal error` case-insensitively, not counted by `^ERROR`: **0 occurrences in all twelve repos**, with `validate-docs.py` exiting 0 everywhere except `project-os-dev`'s standing `REVIEW` error.
- **`your-health`'s validator is its own version plus only the metric fix.** `git diff bc04a44 4df030d -- tools/scripts/validate-docs.py` is four hunks, all of them the metric fix. Both of its local advances survive: the `REF` prefix in `ID_PREFIXES` with its ten-line rationale, and the `TEST-FIELDS` carve-out for `status: ready`. (The canonical copy in `project-os-dev` is behind on both — pre-existing, `ISS-0026`.)
- **`_focus_ids` does not over-protect and does not crash.** Across the twelve, focus resolves to 0-17 canonical IDs per repo and holds back **exactly one** otherwise-prunable entry fleet-wide: `your-sudoku`'s `ISS-0068`, which is the item the change was written for. The walk touches only `str`/`dict`/`list` and ignores every other scalar, so numeric and null focus fields pass through.
- **Condition (5)'s tightening does not wrongly prune or wrongly retain.** The inline quoted-status case `ISS-0034` #4 demonstrated (`TASK-0001: { status: "done" }` whose note says `backlog`) was run end to end through `main()`: the entry now **survives**. No repo has a prunable entry left, so `--check` is clean in all twelve.
- **The banner is de-duplicated, not dropped, and corrupted nothing.** Exactly **one** `# Pruned by retention policy` line in each of the nine pruned repos, **zero** surviving numbered `# Pruned N terminal item(s)` lines, and every curated `# Pruned: FEAT-0001…` comment untouched (three such lines still in `project-os-dev` and `your-sudoku`). Deleting the de-duplication guard leaves the suite green (finding 9), so the banner is unguarded, but it is correct.
- **Nothing has been lost across the three rounds.** For every one of the twelve repos, the set of item IDs present at the pre-migration commit and absent now was computed and each removed ID checked against `note_statuses`: **1,350 removals, 0 whose note fails to supply exactly the collection's terminal status**. Per repo: `your-trainer` 653, `project-os-cockpit` 247, `your-health` 219, `your-applications.com` 86, `your-sudoku` 63, `yourtrainer-mcp` 38, `project-os-dev` 30, `edankert.com` 14, and 0 in the four unpruned repos.
- **The ten migration records still reconcile.** All ten parsed and cross-checked against each repo's own pre-migration snapshot: **709 rows, 0 mismatches**, and each record's header count equals its row count. The migration commits were re-derived independently with `git log -S"prune_window" -- SNAPSHOT.yaml` and match `ISS-0034`'s list exactly.
- **The fleet is healthy.** All twelve: `validate-docs.py` exit 0 (`project-os-dev` exit 1 on the standing `REVIEW` error alone), `sync-snapshot --check` exit 0, `test-retention.py` exit 0 at 23 assertions, and **two consecutive real syncs producing a snapshot byte-identical to the one they started from**. No repo was left dirtied by the verification: every `SNAPSHOT.yaml` was restored from a pre-run copy and every hash matched anyway.

## Next actions

- [ ] Apply the `compute_metric_counts` fix to `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` in both `project-os-dev` and `project-os-cockpit`, and add `tools/scripts/validate-docs.py` to `CHG-20260804`'s `impacts:`.
- [ ] Decide condition (3): delete it with its assertion, or record it as redundant-by-design and remove it from `adequacy`'s mutation list. Correct `sync-snapshot.py:471-477`, `TST-0003:46` and `test-retention.py`'s docstring either way.
- [ ] Bring `TST-0003` up to the suite it stamps: 23 assertions, a fresh `last_run`, table rows for the three condition-5 fixtures and the braced derivation assertion.
- [ ] Bring `CHG-20260804` up to the change it records: assertion counts, condition (4)'s honest status, the impact table, the `711 KB` / `−38.3%` fleet figure, `commit:`, and a body that describes the round-two and round-three fixes.
- [ ] Refresh `SNAPSHOT.yaml`'s `focus.note`; merge `ISS-0033`'s duplicate `## Status` sections.
- [ ] Optional, recorded rather than asked for: guard condition (5)'s terminal-status form, add any test at all over `compute_metric_counts`, and reuse `note_index`'s parsed frontmatter in the `claimants` loop.

## Status

Open. Findings 1-4 block; the verdict is recorded on `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003` as `changes-requested`, replacing round two's. Per the convention `ISS-0022`/`ISS-0023` established and `ISS-0032`/`ISS-0033`/`ISS-0034` follow, the author fixing these does not close the issue.

**Independence of this pass**: fresh context and a separate session. Started from the notes and the diff, with no access to the authoring session's reasoning; `ISS-0033` and `ISS-0034` were read as records of claims to be refuted, and every tick-mark in `ISS-0034` was re-derived by mutation, construction or measurement rather than trusted — which is how findings 1, 2 and 4 surfaced. No memory of authoring any of this work exists in this session. Not independent: the **model**, and this time not even the model *string*. This is `claude-opus-5[1m]`, the same identifier round two recorded, so `reviewed_by` alone cannot distinguish round three from round two — `review_date` and the `review_note` are what separate them, and a reader should know that. Under `ADR-0013` context is the mechanism and family is not the gate, so the pass is independent in the sense the skill requires; three rounds have now run without a different-family check, and that remains worth having.

## Status — fixes applied 2026-08-04

1. **Bundled validators.** Fixed — and the count was worse than reported: **twelve** copies carried the stale `compute_metric_counts`, not two. All patched; the cockpit's bundled copy now agrees with the canonical one and reports no METRICS error. `CHG-20260804`'s `impacts:` now lists `validate-docs.py`, the bundled copies and the test script, which is why the omission mattered.
2. **Condition (3) unreachable.** Resolved by deleting it rather than describing it: (5) requires the note's terminal status, so `deferred` can never reach (3). An unreachable rule reads as protection while providing none — the shape ADR-0011 refuses. `sync-snapshot.py`, `TST-0003` and the suite docstring all now say the protection is structural, and the assertion tests the **outcome** rather than a line.
3. **Both notes stale.** Rewritten against figures re-measured after all three rounds: 23 assertions (not 11 or 18), nine mutations caught (not three), every impact-table row corrected, and the fleet figure restated as **1,152 KB → 713 KB, −38.1%** — earlier drafts said −39% and ~707 KB, both measured mid-flight.
4. **Four false ticks on ISS-0034.** Owned and corrected there; all four now genuinely done.
5. **Non-blocking.** `compute_metric_counts` re-parsing every claimant costs runtime at pre-commit — recorded as a known cost rather than optimised under review pressure, since correctness came first and the measurement (+37% on the largest repo) is now on record to act on deliberately.

Stays **open** pending round four; the author does not clear a verdict on their own work.
