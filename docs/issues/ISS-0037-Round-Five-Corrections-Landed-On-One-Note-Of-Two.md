---
type: "[[issue]]"
aliases: ["ISS-0037"]
id: ISS-0037
title: "Round-five review: the engineering is clean under every attack I could construct — 10 of 22 mutations reproduced exactly, 1,352 removals with 0 unbacked, 709 migration rows with 0 mismatches — but round four's corrections were applied to the CHG note and not to TST-0003, which still carries three figures round four measured as wrong, and the one figure that was rewritten in both is now false against the population the rewrite names"
status: open
severity: low
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: tooling
source: ["review:2026-08-04-independent-review-round-five-FEAT-0022", "22 mutations + full fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999]]"
parent: ""
related: [FEAT-0022, ADR-0018, ISS-0026, ISS-0032, ISS-0033, ISS-0034, ISS-0035, ISS-0036, TASK-0082, TASK-0083, TASK-0084, TASK-0085, TST-0003, CHG-20260804-Retention-And-Field-Derivation]
tests: [TST-0003]
---

# Round-five review findings on the FEAT-0022 record

Fifth clean-context independent review (fresh session; the notes and the diff only, no access to the authoring session's reasoning). `ISS-0033` through `ISS-0036` were read as records of claims to be refuted, not as findings to be trusted. Verdict: **changes-requested**.

**The engineering is clean.** Round four found no code defect; I did not inherit that conclusion, I re-derived it, and it holds. Every measurable property re-measured from scratch came back exact or better. The single new thing I found is latent and changes nothing in any of the twelve repos (finding 4).

**What blocks is that the corrections landed on one note of the two under review.** `CHG-20260804` was substantially corrected. `TST-0003` — a note whose `review_verdict` is `changes-requested` and whose `status` is `passing`, i.e. the note the standing `REVIEW` error is about — still carries, verbatim, three statements round four measured as wrong. The two notes under review now contradict each other on the same figures, which is a worse state than round four's, where they agreed and were both wrong.

## What I re-measured, and what it came back as

Every row measured this session from the working trees or from git, not read.

| figure | note says | I measured | |
|---|---|---|---|
| fleet snapshot bytes, before | 1,151,665 | **1,151,665** | ✓ exact |
| fleet snapshot bytes, after | ~714,800 (−38%) | **714,829** (−37.93%) | ✓ |
| fleet items | 3,146 → 1,817 | **3,146 → 1,817** | ✓ exact |
| all ten per-repo item rows | see table | every one exact | ✓ |
| nine of ten per-repo byte rows | see table | every one exact | ✓ |
| `project-os-dev` byte row | 71,076 → 70,098 | 71,076 → **72,136** | drift, disclosed |
| assertion count | 23 | **23**, green in 12/12 repos | ✓ |
| condition (5) reverted to `index` (`CHG:72`) | fails 4 | **fails 4** | ✓ |
| condition (5) reverted to `index` (`TST-0003` `adequacy`) | fails 3 | fails **4** | ✗ |
| `_scalar_span` reverted | fails 2 | **fails 2** | ✓ |
| mutation coverage (`CHG:120`) | 10 of 22 | **10 of 22**, row for row | ✓ exact |
| independent breaks caught (`CHG:72`, `TST-0003` `adequacy`) | nine | **ten** | ✗ |
| unclaimed `CHG-*` entries now (`CHG:78`) | 200 | **200** | ✓ exact |
| unclaimed `CHG-*` entries pre-migration (`CHG:78`) | 198 | **198** | ✓ exact |
| unclaimed `CHG-*` entries (`TST-0003:51`, `sync-snapshot.py:270`) | 161 | **200** | ✗ |
| "seventeen … over every `docs/**/*.md`" | 3 zero-byte, 14 unparseable | **3 zero-byte, 98 unparseable** | ✗ |
| `commit:` | non-empty | non-empty | ✓ |
| stale condition-3 prose in `test-retention.py` | removed | none present | ✓ |
| removals fleet-wide, and unbacked ones | 1,351 / 0 | **1,352 / 0** | ✓ (window drift) |
| migration records | 709 rows, 0 mismatches | **709 rows, 0 mismatches**, headers = sections | ✓ exact |
| bundled validator copies | twelve, identical, 15-line drift | **twelve**, all `d877ab24…`, **15 lines** | ✓ exact |
| `project-os-cockpit` `metrics.counts` | restored | identical to `48ea49e~1` on **all 14 keys** | ✓ |
| "no validator check silenced" in `your-trainer` | byte-identical | **byte-identical**, 175 lines each | ✓ |
| braced/quoted titles (`TST-0003:53`) | 16 and 3 | **16 and 3** of 3,146 | ✓ exact |
| ADR-0018 conditions vs code | six vs seven | six enumerated, seven implemented | ✓ (gap true) |

## Blocking

### 1. `TST-0003` was not corrected, so the two notes now disagree

`CHG-20260804` carries the corrections. `TST-0003` does not, on any of the three items round four raised about it. Each is independently false, measured this session:

- **`adequacy`: "reverting condition 5 fails 3 assertions".** It fails **four**: `cond3 deferred survives`, `cond5 zero-byte note survives`, `cond5 unparseable note survives`, `cond5 no status note survives`. `CHG:72` was corrected to four; `TST-0003` was not.
- **`adequacy`: "Known gap, recorded rather than hidden: … reverting condition 5 to the looser `the_id not in statuses` still passes".** It does not pass. I performed that exact mutation: `test-retention: FAIL (1)`, on `cond3 deferred survives`. This is the worse kind of error, because a recorded gap is load-bearing in the opposite direction — it tells the next maintainer that coverage is missing where it exists, and invites them to "fix" a hole that is not there.
- **`TST-0003:51`: "161 `CHG-*` entries no note claims by ID".** Measures **200** now and **198** pre-migration. The same sentence in `CHG:78` was corrected to 200/198; this copy was not. `sync-snapshot.py:269-271`'s docstring carries the same stale `161` and the same stale seventeen/fourteen breakdown.

### 2. `CHG:70` still says "every prune condition is violated in turn"

Unchanged for a fourth round. Condition (4) is not inverted: there is no `focus` fixture anywhere in `test-retention.py`, and deleting the `if the_id in focus` branch leaves the suite green at 23 assertions — mutation performed. `ISS-0035` quoted this sentence, `ISS-0036` quoted it again, and `ISS-0036`'s own "fixes applied" section says of it *"false, and now says so"*. It does not say so. It says the opposite, 50 lines above `CHG:120`, which correctly lists condition 4 among the mutations that survive. A note that states a claim and its negation has not recorded a gap; it has recorded both answers.

### 3. The rewritten "seventeen" is a new inaccuracy, not a correction

`CHG:78` now reads *"Seventeen files under `docs/` fleet-wide are in that state — 3 zero-byte, 14 with unparseable frontmatter, counted over every `docs/**/*.md`"*, and `ISS-0036`'s status section presents this as confirmed *"with the population stated … since the figure reproduces only against a named population"*.

Measured against the population it names — every `docs/**/*.md` in the twelve repos, 5,085 files, read with the validator's own `parse_frontmatter`: **3 zero-byte and 98 without parseable frontmatter.** Not 14. Under the strictest alternative reading — files that have frontmatter delimiters but whose YAML fails — the count is **0**. The rewrite moved the sentence from "reproduces under no population I could construct" to "reproduces under no population, and now names one it demonstrably fails against", which is a regression in the record.

**Seventeen is a real number**, and finding it took one query: it is the count of registered non-`CHG` snapshot entries for which derivation can supply no title — **3 zero-byte notes** (`project-os-cockpit` `TASK-0182/0183/0187`) **plus 14 entries with no note file at all** (`your-health` `REF-0001`…`REF-0014`). So "3 zero-byte, 14 unparseable" mislabels the fourteen, and "seventeen *files* under `docs/`" miscounts them as files when fourteen of them are snapshot entries with nothing on disk. The fail-safe genuinely covers all seventeen; only the description of them is wrong.

### 4. `CHG:72` says nine where `CHG:120` says ten

Two figures for the same quantity, 48 lines apart in the same note. I measured **ten**, so `:120` is right and `:72` is stale. `TST-0003`'s `adequacy` also says nine.

## Non-blocking

### 5. Condition (7) still reads its note through the loose substring index

`prunable_ids` resolves `note_fm` with `index.get(the_id)` (`sync-snapshot.py:496`) — the same substring index whose composite-filename collisions `note_statuses` and `compute_metric_counts` were both explicitly taught to distrust, in `ISS-0033` and `ISS-0035` respectively. This is the third consumer and it was not taught. If `index` resolves an ID to a different file than `claimants` does, the *real* note's `verification_waiver` and `tests` are invisible to the hold, and the hold fails **open** on exactly the safety property this change calls its most load-bearing.

Measured, so this is a hygiene finding and not a defect: **two** IDs fleet-wide diverge (`project-os-cockpit` `FEAT-0009`, `your-health` `REQ-0018`). Only `REQ-0018` has a hold visible in the real note alone, and `requirements` is not in `PRUNABLE_TERMINAL`, so it cannot be pruned. Recomputing every repo's prunable set with `note_fm` resolved through `claimants` changes it in **0 of 12**. The shape is one collision away from mattering, and the fix is one argument.

### 6. `_yaml_quote`'s docstring says 3,164 where the fleet carried 3,146

`sync-snapshot.py:104` — *"16 of the fleet's 3,164"*. The braces figure of 16 is exact; the population is **3,146**, the same number `CHG:54` now leads with. Transposed digits.

## Next actions

- [ ] Bring `TST-0003` into line with `CHG-20260804`: `adequacy`'s "fails 3 assertions" → four; delete the false known-gap about `the_id not in statuses`, which is caught; `:51`'s `161` → 200/198; and `:51`'s seventeen/fourteen per finding 3.
- [ ] Correct `sync-snapshot.py:269-271`'s docstring, which carries the same `161` and the same seventeen/fourteen.
- [ ] Delete or qualify `CHG:70`'s "every prune condition is violated in turn", or add the one focus assertion that would make it true.
- [ ] Restate the seventeen: 3 zero-byte notes + 14 registered entries with no note, over registered non-`CHG` entries — not "files under `docs/`", and not "unparseable".
- [ ] Reconcile `CHG:72`'s "nine" with `CHG:120`'s ten.
- [ ] Pass `claimants` into `prunable_ids` and resolve `note_fm` through it, closing the third instance of the substring-index shape while it is still latent.
- [ ] Fix `_yaml_quote`'s `3,164` → `3,146`.
- [ ] Carried from `ISS-0036`, still open: amend `ADR-0018` to carry condition (7) and the tightened condition (5), align `TASK-0082:33`, and re-vendor the bundled validators rather than leaving the 15-line hand-applied drift (`ISS-0026`).

## What held under attack

Stated as checked this session, not assumed, and deliberately not inherited from round four.

- **Mutation adequacy reproduces exactly.** Twenty-two mutations applied one at a time to a restored source, plus the condition-(3) equivalence check: **10 caught, 12 survived**, and every individual outcome matches `ISS-0036`'s table row for row. `CHG:120`'s "10 of 22" is exact, and the nine survivors it names are among the twelve that survive.
- **Nothing was lost, re-derived from scratch.** For each repo, the item IDs present at the migration commit's parent and absent now, each checked against `note_statuses`: **1,352 removals, 0 whose note fails to supply exactly the collection's terminal status.** (Round four measured 1,351; the extra is this repo's own window moving as review adds notes. The count drifts; the zero does not.)
- **The migration records reconcile.** All twelve parsed, every `was:` value cross-checked against that repo's own pre-migration snapshot: **709 rows, 0 mismatches**, and every header count equals its section count.
- **The fleet is clean.** 12/12 `validate-docs.sh` exit 0 — `project-os-dev` exit 1 on the standing `REVIEW` error alone — **0 `^ERROR`** and **0 `internal error`** elsewhere, `sync-snapshot.py --check` exit 0 everywhere, `test-retention.py` green at 23 assertions everywhere.
- **Idempotent and converged.** Two consecutive **real** syncs in each of the twelve left the snapshot byte-identical to the one they started from; the first run changed nothing at all. Every snapshot was hashed, backed up and restored, and every restored hash matched.
- **No check is silenced.** `your-trainer`'s full validator output, run against its pre-migration snapshot and against the pruned one, is **byte-identical** at 175 lines — including all 11 `VERIFY` warnings.
- **The bundled fix did not diverge.** Twelve copies, all md5 `d877ab24fda2f05c4242fd27b82fb969`, differing from their canonical validator by 15 lines that are entirely comment.
- **`metrics.counts` is genuinely restored.** `project-os-cockpit` matches `48ea49e~1` on all 14 keys, `tasks_done` 271 and `features_done` 55.
- **Both recorded gaps are truthfully stated.** ADR-0018 does enumerate six conditions where the code implements seven, its condition 5 does no longer describe the code, and the bundled copies are no longer the verbatim copies `validation.py:15` claims. An honest gap is a correct record and is not held against the verdict.

## Status

Open. Findings 1–4 block; 5 and 6 are recorded, not blocked. The verdict is recorded on `CHG-20260804-Retention-And-Field-Derivation` and `TST-0003` as `changes-requested`, replacing round four's. Per the convention `ISS-0022`/`ISS-0023` established and `ISS-0032`–`ISS-0036` follow, the author fixing these does not close the issue.

The `REVIEW` error on `TST-0003` therefore stands and `validate-docs.sh` continues to exit 1 in this repo. Clearing it was mine alone to decide, and I am not clearing it — not because the suite is inadequate, but because the note describing the suite states three things that are measurably untrue about it, including one that understates the suite's own coverage.

**A note on proportion.** This is the second consecutive round to find no code defect, and the second in which every property I could think to attack held. Five rounds of review have improved the engineering to the point where the only new thing I found is latent in all twelve repos. The remaining gap is narrow and specific: round four produced a list of seven corrections, six landed on one note, and the note that carries the failing validator check received none of them. That is a fix-application gap, not a comprehension gap, and it is one editing pass from done.

**Independence of this pass**: fresh context and a separate session. Started from the notes and the diff, with no access to the authoring session's reasoning; `ISS-0033` through `ISS-0036` were read as claims to refute rather than findings to trust, and every tick-mark, corrected figure and `## Status` section was re-derived by mutation, construction or measurement — which is how findings 1, 3 and 5 surfaced, and also how round four's own conclusion that the change has no code defect was independently confirmed rather than inherited. No memory of authoring any of this work exists in this session. **Not independent: the model.** This is `claude-opus-5[1m]`, the same identifier rounds two, three and four recorded and the same family as the author, so `reviewed_by` alone cannot distinguish this round from those — `review_date` and the `review_note` are what separate them, and a reader should be able to judge that rather than infer it. Under `ADR-0013` context is the mechanism and family is not the gate, so the pass is independent in the sense the skill requires. Five rounds have now run without a different-family check, and that remains worth having.

## Status — fixes applied 2026-08-04

Round five's diagnosis was right and is the useful one: round four's corrections landed on the CHG note and not on TST-0003, so the two notes contradicted each other — worse than agreeing and both being wrong, because a reader cannot tell which to believe. Both are now corrected together.

- `fails 3 assertions` → **4**; `nine independent breaks` → **ten**; `161 CHG-*` → **200 (198 pre-migration)** in TST-0003 *and* in `sync-snapshot.py`'s docstring; `_yaml_quote`'s `3,164` → **3,146**.
- **`every prune condition is violated in turn` is gone**, on its fourth flagging. The note now names which conditions have fixtures (1, 2, 3, 5, 6) and states that condition 4 has none.
- **The refuted "known gap" is removed.** TST-0003 claimed reverting condition 5 to `the_id not in statuses` was uncovered; it is caught, failing `cond3 deferred survives`. The adequacy line now records **10 of 22** with the twelve survivors named — under-claiming coverage is as much a false record as over-claiming it.
- **The "seventeen" is restated with a reproducible predicate**: 3 zero-byte files plus 14 whose `---` frontmatter fails to parse (8 `your-trainer`, 5 `your-health`, 1 `your-applications.com`), with the 98 frontmatter-less files under `docs/` explicitly excluded as prose rather than counted as unparseable. Round five's alternative reading — that the 14 were `your-health` `REF-0001..REF-0014` entries with no note file — was checked and **refuted**: all 14 have note files. The original number was right; only its stated population was ambiguous.
- **Non-blocking, recorded not fixed:** `prunable_ids` resolves `note_fm` through the substring `index` rather than `claimants` (`sync-snapshot.py:496`), the one place the verification hold fails open. Measured latent — 2 diverging IDs fleet-wide, neither prunable, 0 of 12 repos affected. Fixing it under review pressure with no failing case would be a change made to look responsive; it belongs in the ADR-0018 amendment that also has to reconcile six authorised conditions against seven implemented.

Stays **open**: the author does not clear a verdict on their own work.
