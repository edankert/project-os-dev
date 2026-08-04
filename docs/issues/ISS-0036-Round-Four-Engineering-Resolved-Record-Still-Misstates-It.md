---
type: "[[issue]]"
id: ISS-0036
aliases: ["ISS-0036"]
title: "Round-four review of the ISS-0035 fixes: all four blocking items are resolved on the merits — twelve bundled validators patched, deferred protection structural and now genuinely guarded, 1,351 removals with nothing lost — but the rewritten fleet figure is 100 bytes off a git-immutable constant, the condition-(4) sentence round three quoted as false is unchanged, and ADR-0018 still authorises a six-condition rule the code no longer implements"
status: open
severity: low
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-round-four-FEAT-0022", "23 mutations + full fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0026, ISS-0032, ISS-0033, ISS-0034, ISS-0035, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Round-four review findings on the FEAT-0022 fixes

Fourth clean-context independent review (fresh session; notes and diff only, no access to the authoring session's reasoning). `ISS-0033`, `ISS-0034` and `ISS-0035` were read as records of claims to be refuted, not as findings to be trusted. Verdict: **changes-requested**.

**All four of round three's blocking items are resolved on the merits.** Verified by mutation, by construction and by fleet re-measurement rather than from tick-marks. The engineering on this change is, as far as I can break it, correct — and it is now better than either note claims for it.

What blocks is the same thing that blocked rounds two and three, on its fourth appearance: **the record does not state what was measured.** One sentence round three quoted verbatim as false is unchanged. One number was rewritten and is wrong in a way that proves the stated re-measurement did not happen. And the ADR that authorises a rule which deletes lines from a tracked file on every run in twelve repos describes a different rule.

The severity is `low` — not `medium` as rounds two and three — because nothing here is a code defect. Every finding is on the handoff surface.

## Round three's four blocking items

### 1. Bundled validators — RESOLVED, and the count of twelve is right

Counted independently: **twelve** copies of `validate_docs_bundled.py` exist across the fleet — one under `tools/cockpit/src/project_os_cockpit/` in each of eleven repos, plus `project-os-cockpit/src/project_os_cockpit/`, which is the cockpit application's own source. `articles` has none. All twelve carry the `claimants`-first fix and all twelve are **byte-identical to each other** (`md5 d877ab24fda2f05c4242fd27b82fb969`), so the patch did not diverge across the copies.

Run in `project-os-cockpit`, both its copies now exit 0 with **0 `^ERROR` and 0 `internal error`**. The METRICS error round three reported is gone. Checked further, because "the error is gone" is weaker than "the number is right":

- `project-os-cockpit`'s `metrics.counts` is identical to `48ea49e~1` on **all 14 keys** (round three said fifteen; the snapshot carries fourteen). `features_done` 55 → 55, `tasks_done` 271 → 271.
- Every written key matches what `compute_metric_counts` recomputes against the current tree (18 computed keys, 0 mismatches).
- The canonical validator, the cockpit's bundled source and the vendored copy return **identical** count dictionaries.

`impacts:` now lists `tools/scripts/validate-docs.py`, `tools/cockpit/**/validate_docs_bundled.py` and `tools/scripts/test-retention.py`. The omission that let this reach round three is closed.

### 2. Condition (3) — RESOLVED, and the protection is real rather than re-described

Deleting the condition rather than documenting it was the right call, and the protection that replaces it is structural, falsifiable and stronger than the note claims.

**Constructed, end to end through `main()`** (not through `prunable_ids` in isolation, which is where a fixture can lie):

| entry status | note status | style | outcome |
|---|---|---|---|
| `done` | `deferred` | block | **survives** |
| `done` | `deferred` | inline, quoted status | **survives** |
| `done` | `deferred` | inline, bare status | **survives** |
| `deferred` | `deferred` | block | **survives** |
| `done` | `cancelled` | block | **survives** |
| `done` | `done` | block | pruned (control — the test discriminates) |

The inline-quoted row is the adversarial one: it is the shape `ISS-0034` #4 identified as the only path on which `sync_statuses` cannot rewrite the entry, and therefore the only way a `deferred` note reaches the rule with a terminal entry status. It survives.

**And it is guarded.** Reverting condition (5) to `the_id not in index` fails **four** assertions, one of which is `cond3 deferred survives`. So the deferred assertion is not passing for the wrong reason — remove the structural protection and it goes red. That is exactly what round three asked for and it is met.

**Nothing can now be pruned that could not before.** Two independent checks:

- Condition (3) sat *after* condition (1). (1) requires `status == terminal`, and `PRUNABLE_TERMINAL` is `{tasks: done, issues: fixed, features: done}` — never `deferred`. So `status == "deferred"` was unreachable by construction, before and after the (5) tightening. Reinstating the branch changes the prunable set in **0 of 12** repos.
- The replacement is strictly narrower, not merely different. New (5) is `statuses.get(the_id) == terminal`; old (5) was `the_id in index`. Measured across all twelve: **0 IDs** are in `statuses` but not in `index`, so the new condition admits nothing the old one rejected.

**One residual.** `test-retention.py:96-99` still reads *"The entry must be TERMINAL (so condition 1 passes) and deferred (so only condition 3 can stop it) … a well-formed corpus cannot exercise condition 3 at all."* That contradicts the corrected comment three lines above it and names a condition that no longer exists. The module docstring was fixed; this inline comment was not, and `ISS-0035`'s next action named *"`test-retention.py`'s docstring"* as one of three places to correct.

### 3. The CHG note and TST-0003 — PARTIALLY resolved

Re-measured, not read. What is now right:

| claim | stated | measured | |
|---|---|---|---|
| assertion count (CHG:68, TST-0003:38) | 23 | 23 | ✓ |
| `last_run` | 2026-08-04T11:23Z | post-dates the suite | ✓ |
| your-trainer | 1,065 → 412 / 386,546 → 112,931 | exact | ✓ |
| project-os-cockpit | 593 → 346 / 199,970 → 133,882 | exact | ✓ |
| your-health | 573 → 354 / 184,029 → 130,012 | exact | ✓ |
| your-applications.com | 237 → 151 / 153,865 → 129,801 | exact | ✓ |
| your-sudoku | 254 → 191 / 58,468 → 47,202 | exact | ✓ |
| yourtrainer-mcp | 99 → 61 / 32,204 → 19,558 | exact | ✓ |
| edankert.com | 64 → 50 / 22,111 → 18,698 | exact | ✓ |
| articles | 37 → 55 / 12,079 → 19,025 | exact | ✓ |
| three unpruned repos | 0 removals each | 0, 0, 0 | ✓ |
| mutations caught | nine | **ten** | ✓ (conservative) |
| condition (3) removed from `adequacy`'s list | — | removed | ✓ |
| TST-0003 table rows for the four condition-5 fixtures and the braced derivation | — | present | ✓ |

Nine of ten impact rows are now exact, against eight of ten wrong last round. That is real work. What is still wrong:

**(a) The fleet figure was rewritten and is wrong.** `CHG:52` says `1,151,765 → 712,791`. Measured from the parent of each of the twelve migration commits — history that cannot drift — the pre-migration total is **1,151,665**. Rounds two and three both stated that figure and both called it exact. The post figure measures **712,884**; the 93-byte gap is `project-os-dev`'s own snapshot, which grew when `ISS-0033`/`0034`/`0035` were registered and `focus.note` refreshed, i.e. after the measurement was taken. The percentage (−38.1%) survives because the two errors nearly cancel.

This is the finding, and it is not about 100 bytes. `ISS-0035`'s status section says the notes were *"Rewritten against figures re-measured after all three rounds"*. A re-measurement cannot return 1,151,765 for a constant that measures 1,151,665. The number was adjusted rather than measured, which is the same act the previous three rounds each blocked on.

**(b) `CHG:68` still says *"every prune condition is violated in turn"*.** Condition (4) is not. Mutation performed: deleting the `if the_id in focus` branch leaves the suite green at 23 assertions. `ISS-0035` finding 3 quoted this sentence and named condition (4) explicitly; `ISS-0034` finding 5 quoted it before that. `TST-0003`'s own table honestly omits condition 4, so the two notes under review still contradict each other on the same point, three rounds running.

**(c) Two descriptive figures do not reproduce.** Both appear in both notes (`CHG:76`, `TST-0003:51`):

- *"161 `CHG-*` entries no note claims by ID"* — measured **200** today, and **198** at the pre-migration commits. Every `CHG-*` entry in the fleet is unclaimed, because the composite ID shape is not canonical, so the true figure is simply the number of `CHG-*` entries. 161 does not correspond to either point in time.
- *"Seventeen real notes fleet-wide are in that state (3 zero-byte, 14 with unparseable frontmatter)"* — does not reproduce under any population I could construct. Among notes that claim a snapshot ID: 3 zero-byte, 3 unparseable. Across every `docs/**/*.md` in the fleet: 3 zero-byte, 98 unparseable. Among registered non-`CHG` entries whose claiming note yields no derivable title: **3**, all of them `project-os-cockpit`'s zero-byte notes. The zero-byte count of 3 is right in every reading; the 14 and the 17 are not.

**(d) `commit:` is still empty**, for the third round in a row, having been ticked as done twice. It may well be *correct* to leave it empty — the change is uncommitted in eleven of twelve repos — but the note does not say so, and round two supplied the twelve migration hashes. An empty field that three reviews have asked about needs one sentence either way.

**(e) The note understates its own evidence.** `CHG:70` and `TST-0003`'s `adequacy` say reverting condition (5) *"fails 3 assertions"*. It fails **four**, and the fourth is `cond3 deferred survives` — the assertion that proves the deferred protection is structurally real. That is the strongest single piece of evidence this change has, and the note rounds it away.

### 4. ISS-0034's four false ticks — THREE of four resolved

Verified individually:

- `SNAPSHOT.yaml`'s `focus.note` — **done**. Now reads `1,152KB -> 713KB (-38.1%)` and names all four review rounds.
- `ISS-0033`'s duplicate `## Status` sections — **done**. One section remains, at line 196.
- Deciding (5) and (3) together — **done**, and correctly (finding 2).
- Bringing `CHG-20260804` up to date — **not complete** (finding 3). `ISS-0034`'s correction section states *"All are now genuinely done"* of all four.

So the tick that was wrong in round three about a tick that was wrong in round two is, in one of its four parts, still wrong. This is the fourth consecutive round in which a completion claim has been the defect.

## New findings

### 5. ADR-0018 authorises a six-condition rule; the code implements seven

`ADR-0018:66-72` enumerates the conditions under which an entry is removable. It lists six. The implementation has seven, and the missing one is condition (7), the verification hold — *"an entry is held back by … an outstanding `verification_waiver`, or by a linked test that is not passing"*. That is the single most important safety property this change added; it is the reason the CHG can say *"retention removes finished business, never unfinished"*; and it is measurably load-bearing (verified this session: `project-os-dev` retains 19 `VERIFY-WAIVED` warnings and `your-trainer` retains exactly 3 `WARN [VERIFY]` on issues closed against `ready` tests — the 3 the CHG names). It appears nowhere in the decision.

`ADR-0018`'s condition 5 also reads *"its note exists on disk and parses"*, which is no longer what the code does — it now requires the note to supply the collection's terminal status. `TASK-0082:33` carries the same six-condition list.

Neither divergence is a hazard: the implementation is strictly stricter than the ADR in both directions, so nothing is deleted that the ADR permits keeping. But a destructive rule's authorising record should describe the rule, and an ADR that is silent on the safety condition is an ADR a future maintainer can remove that condition against.

Recorded as non-blocking on the engineering; it is the same class as finding 3.

### 6. The bundled copies are no longer verbatim copies

`validation.py:15` and `:79` describe `validate_docs_bundled.py` as *"a verbatim copy of the canonical script"*, and `ISS-0035` established that it was byte-identical before this change. It is not now: all twelve copies differ from their repo's `tools/scripts/validate-docs.py` by **15 lines**, because the fix was hand-applied with an abridged comment rather than re-vendored. (`your-health` differs by 22, the extra 7 being its own two local advances, which is pre-existing and correct.)

Functionally this is nothing — verified: canonical, bundled and vendored return identical metric counts. But `ISS-0026-Bundled-Validator-Drift` is the issue for exactly this invariant, drift was the reason finding 1 existed, and the fix for the drift introduced a smaller drift. Re-vendor rather than hand-edit.

### 7. Mutation coverage: 10 of 22 caught

Each performed individually against the working-tree suite (23 assertions, green). Two mutations round three recorded as surviving are now **caught**, which neither note claims:

| mutation | round three | round four |
|---|---|---|
| condition (5) → `the_id not in index` (round one's defect) | caught (3) | **caught (4)** |
| `_scalar_span` → `body.find("{")` (round one's defect) | caught (2) | **caught (2)** |
| `prune_entries` → `return []` | caught | **caught** |
| `sync_derived_fields` → `return []` | caught | **caught (4)** |
| the verification hold deleted | caught | **caught** |
| the `note:` hold deleted | caught | **caught** |
| `_yaml_quote` emitting unquoted | caught | **caught (2)** |
| `_value_end` → naive comma search | caught | **caught** |
| condition (5) → `the_id not in statuses` (round two's form) | SURVIVED | **caught** |
| retention window off by one | SURVIVED | **caught (2)** |
| condition (4) deleted | SURVIVED | SURVIVED (finding 3b) |
| fail-safe accepts a blank `title:` | SURVIVED | SURVIVED |
| fail-safe accepts a non-string `title:` | — | SURVIVED |
| `_owes_verification` reverted to fail-open | SURVIVED | SURVIVED |
| focus scan → top-level exact strings | SURVIVED | SURVIVED |
| `prune_entries`' `in_items` guard deleted | SURVIVED | SURVIVED |
| `_value_end`'s doubled-single-quote handling deleted | SURVIVED | SURVIVED |
| `PRUNABLE_TERMINAL` widened to requirements/risks | SURVIVED | SURVIVED |
| `prune_entries` over-deleting by four columns | SURVIVED | SURVIVED |
| the prune banner never emitted | SURVIVED | SURVIVED |
| `note_statuses`' ambiguous-claim guard deleted | SURVIVED | SURVIVED |
| condition (1) deleted | — | SURVIVED |
| condition (3) **reinstated** (equivalence check) | — | SURVIVED, as designed |

The two newly-caught mutations both fall to `cond3 deferred survives`, which is the assertion round three judged to be passing for the wrong reason. It is now the suite's most productive assertion. That is worth recording precisely because it inverts round three's conclusion, and it is the strongest argument that deleting condition (3) was right.

`condition (1) deleted` surviving is a coverage gap, not a defect: with (5) requiring the note's terminal status and `sync_statuses` running first, (1) is redundant on any corpus where the entry and note agree. It is worth keeping as a cheap guard against an unsynced entry, and worth an assertion.

## What was checked and held

Every figure below was measured in this session, from the working trees or from git. Stated as checked, not assumed.

- **The fleet is clean.** All twelve: `validate-docs.sh` exit 0 — `project-os-dev` exit 1 on the standing `REVIEW` error alone — **0 `internal error`** anywhere, `sync-snapshot --check` exit 0, `test-retention.py` exit 0 at **23 assertions** in every repo.
- **Idempotent, and already converged.** Two consecutive **real** syncs in each of the twelve produced a snapshot byte-identical to the one they started from — the first run changed nothing at all, so the committed and working states are at the fixed point. Every `SNAPSHOT.yaml` was copied before the runs and restored after, and every restored hash matched the original.
- **No snapshot is corrupted.** All twelve parse through the script's own loader, with items intact.
- **Nothing has been lost, re-derived from scratch.** For each repo the set of item IDs present at the migration commit's parent and absent now was computed, and every removed ID checked against `note_statuses`: **1,351 removals fleet-wide, 0 whose note fails to supply exactly the collection's terminal status.** Per repo: `your-trainer` 653, `project-os-cockpit` 247, `your-health` 219, `your-applications.com` 86, `your-sudoku` 63, `yourtrainer-mcp` 38, `project-os-dev` 31, `edankert.com` 14, and 0 in the four unpruned repos. (Round three measured 1,350; the extra one is `project-os-dev`'s `ISS-0008`, pushed out of the 25-wide window by registering `ISS-0033`/`0034`/`0035`. The count is a moving target in the dogfood repo; the zero is not.)
- **The migration records reconcile, re-derived independently.** The twelve migration commits were re-found with `git log -S"prune_window" -- SNAPSHOT.yaml` and match `ISS-0034`'s list. All ten non-empty records parsed and every `was:` value cross-checked against that repo's own pre-migration snapshot: **709 rows, 0 mismatches**, and each record's header count equals its section count exactly.
- **The prune banner is de-duplicated and destroyed nothing.** Exactly **one** `# Pruned by retention policy` line in each of the eight repos that lost entries, **zero** surviving numbered `# Pruned N terminal item(s)` lines, and every curated `# Pruned: …` comment intact (6 fleet-wide, in `project-os-dev`, `your-sudoku` and `obsidian-supernote-sync`).
- **The verification hold is load-bearing in production, not just in the suite.** `project-os-dev` still emits 19 `VERIFY-WAIVED` warnings and `your-trainer` exactly 3 `WARN [VERIFY]` on issues closed against `ready` tests — the population the CHG says pruning would have silenced.
- **The scanner's motivating measurement is real.** The pre-migration snapshots carry **16** titles containing braces and **3** with embedded double quotes, exactly as `TST-0003:53` says. (Post-derivation the fleet carries 3 and 3; the note's present tense is the pre-migration figure.)
- **`TST-0003` is registered** in `items.tests`, so `QUALITY.md`'s gate on `FEAT-0022` resolves, and the suite's self-count is derived rather than hard-coded.
- **The fail-safe holds end to end.** A note that is missing, zero-byte, unparseable or status-less leaves the snapshot value untouched and reports no change, verified through `sync_derived_fields` and through `main()`.

## Next actions

- [ ] Correct `CHG:52`'s fleet figure to the measured `1,151,665 → 712,884` (or re-measure and state what you measured); note that the post figure moves whenever `project-os-dev`'s own snapshot does.
- [ ] Delete or qualify `CHG:68`'s *"every prune condition is violated in turn"* — condition (4) is not inverted — or add the focus inversion to the suite, which costs one assertion.
- [ ] Correct the `161` and `Seventeen` figures in `CHG:76` and `TST-0003:51`, or drop them.
- [ ] Fill `commit:`, or state in one sentence why it is empty.
- [ ] Delete `test-retention.py:96-99`, the stale comment that still says only condition 3 can stop the fixture.
- [ ] Amend `ADR-0018` to carry condition (7) and the tightened condition (5), and align `TASK-0082:33`.
- [ ] Correct *"fails 3 assertions"* to four in `CHG:70` and `TST-0003`'s `adequacy` — it understates the evidence.
- [ ] Optional: re-vendor the bundled validators rather than leaving a 15-line comment drift (`ISS-0026`); add a focus inversion and a condition-(1) assertion; add any test at all over `compute_metric_counts`.

## Status

Open. Findings 3 and 4 block; findings 5 and 6 are recorded, not blocked. The verdict is recorded on `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003` as `changes-requested`, replacing round three's. Per the convention `ISS-0022`/`ISS-0023` established and `ISS-0032`/`ISS-0033`/`ISS-0034`/`ISS-0035` follow, the author fixing these does not close the issue.

The `REVIEW` error on `TST-0003` therefore stands, and `validate-docs.sh` continues to exit 1 in this repo. That is the gate working: a suite stamped `passing` against an unresolved verdict is exactly what the check exists to catch, and clearing it would have been the review-level version of ticking a box to fit.

**A note on proportion.** Three rounds found code defects; this one found none. Every property I could think to attack — deferred protection, losslessness, idempotence, metric parity, bundled-copy divergence, the widening question — held under direct test. If the seven items above are fixed, the engineering needs nothing. It would be wrong to read this verdict as saying the change is not ready; it says the record of it is not yet true.

**Independence of this pass**: fresh context and a separate session. Started from the notes and the diff, with no access to the authoring session's reasoning; `ISS-0033`, `ISS-0034` and `ISS-0035` were read as claims to refute rather than findings to trust, and every tick-mark was re-derived by mutation, construction or measurement — which is how findings 3 and 4 surfaced, and also how two of round three's own conclusions (that `cond3 deferred survives` passes for the wrong reason, and that condition (5)'s round-two form is unguarded) were shown to be superseded. No memory of authoring any of this work exists in this session. **Not independent: the model.** This is `claude-opus-5[1m]`, the same identifier rounds two and three recorded and the same family as the author, so `reviewed_by` alone cannot distinguish this round from those — `review_date` and the `review_note` are what separate them, and a reader should know that rather than infer it. Under `ADR-0013` context is the mechanism and family is not the gate, so the pass is independent in the sense the skill requires. Four rounds have now run without a different-family check, and that remains worth having.

## Status — fixes applied 2026-08-04

Round four found **no code defect**; every property it attacked held. These are record corrections.

- **Fleet byte figure.** The *before* is git-immutable and was wrong by 100 bytes because repos with no migration commit were measured at their current size rather than their pre-change one — `project-os` had gained the two gate keys. Corrected to **1,151,665**. The *after* is a moving target that drifts upward every time this review adds a note, which is why three drafts each read differently and each was accurate when taken. The line now says so and leads with **item counts (3,146 → 1,817)**, which are stable.
- **"Every prune condition is violated in turn"** — false, and now says so: condition 4 (`focus`) is uncovered and deleting it leaves the suite green. Recorded as a gap rather than removed as an embarrassment.
- **"Fails 3 assertions"** → 4. **"161 `CHG-*` entries"** → 200 now, 198 pre-migration, with the reason (date-slug keys). **Seventeen notes** confirmed at 3 zero-byte + 14 unparseable, with the population stated — *every* `docs/**/*.md` — since the figure reproduces only against a named population.
- **`commit:`** filled. **`test-retention.py`'s** stale condition-3 prose removed.
- **Two gaps promoted from findings to recorded debt**: ADR-0018 authorises six conditions where the code implements seven, and its condition 5 no longer describes the code; and the twelve bundled validators are no longer verbatim copies. Both are in the CHG note's "Known gaps" section with the fix named, because the honest close is to record them, not to let a fifth round rediscover them.

Stays **open**: the author does not clear a verdict on their own work.
