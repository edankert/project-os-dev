---
type: "[[issue]]"
id: ISS-0032
aliases: ["ISS-0032"]
title: "Independent review of FEAT-0022/ADR-0018: ADR-0018 still publishes the pre-amendment hold table, TASK-0082 contradicts itself on whether `goal:` holds, three tasks carry Definitions of Done that require the task depending on them, and title derivation has no fail-safe for the 9 notes fleet-wide that yield no title"
status: open
severity: high
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
component: docs
source: ["review:2026-08-04-independent-review-FEAT-0022", "fleet re-measurement 2026-08-04 over 12 repos"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [FEAT-0022, ADR-0018, TASK-0082, TASK-0083, TASK-0084, TASK-0085, ADR-0005, ADR-0009, ISS-0002, ISS-0030]
tests: []
---

# Independent review findings on FEAT-0022 and ADR-0018

Clean-context independent review (fresh session, notes + diff only, no access to the authoring session's reasoning) of `ADR-0018` and the five notes of `FEAT-0022`, per `tools/skills/independent-review/SKILL.md`. Verdict: **changes-requested**, recorded on `FEAT-0022`.

The design is sound and most of its measurement is exact. Every quantitative claim was independently re-measured against the twelve repos; the headline figures — 659 drifted titles, 1,756 terminal, 142 held, 1,614 prunable, 75/659 verbatim containment, the −28% and +2% size effects, `goal:` drift, and every cell of `TASK-0085`'s per-repo terminal/held/prunable table — reproduce exactly. What does not survive is a layer of leftovers from the four amendments, plus one genuine gap in the design.

## Blocking

### 1. `ADR-0018`'s hold table is the pre-amendment measurement

`ADR-0018:98-103` and the consequence at `ADR-0018:24` report `project-os-dev` as **19 held / 58 removable** and `your-health` as **36 held / 238 removable**. Measured 2026-08-04 under the rule the ADR now states (condition 6: item-level `note:` empty), the figures are **8 / 69** and **34 / 240**. `TASK-0085:63,70` has them right.

The stale numbers are not noise — they are reproducible under the *superseded* rule. Counting entries held by non-empty `note:` **or** `goal:` returns exactly 19 and 36. That was the first draft's rule, which commit `dc101e5` removed. The table was never re-measured, so the ADR's own evidence still argues for the rule it abandoned.

### 2. `TASK-0082` contradicts itself on `goal:` two lines apart

- `TASK-0082:36` — "its item-level `note:` field is **empty** (`goal:` is derived under rule 1 and does not hold)"
- `TASK-0082:38` — "An entry with non-empty `note:`/`goal:` stays and is **reported** as pending relocation"

`ADR-0018:74` is unambiguous that `goal:` is not a hold condition. The same leftover appears in `FEAT-0022:69` as an acceptance criterion. As written, an implementer reading either note gets the wrong condition set, and the acceptance criterion certifies it.

### 3. Three Definitions of Done require the task that depends on them

Declared ordering is `TASK-0083` → `TASK-0084` → `TASK-0082`, with `TASK-0085` depending on all three. Each of the first three then puts fleet-completion in its own DoD:

- `TASK-0083:58-59` — "Fleet-wide: snapshot `title` equals note `title` for every registered item"; "`--check` clean in all twelve repos after migration"
- `TASK-0084:57-58` — "Derivation enabled; `--check` clean fleet-wide"; "Per-repo commits … sequenced by `TASK-0085`"
- `TASK-0082:69` — "Metrics unchanged fleet-wide; `validate-docs` clean in all twelve repos"

The fleet migration *is* `TASK-0085`, and `TASK-0085` depends on all three. No task can be ticked before the task that waits on it, so under `QUALITY.md`'s feature gate `FEAT-0022` can never close. Either the fleet clauses move to `TASK-0085`, or the three tasks state their DoD against the dogfood repo and the rollout owns the rest.

### 4. `FEAT-0022`'s `tasks:` list omits `TASK-0085`

`FEAT-0022:14` lists `TASK-0082`, `TASK-0083`, `TASK-0084`. The body's Scope (`:42`) and Risks (`:60`) both name `TASK-0085`, `TASK-0085:12` declares `parent: FEAT-0022`, and `SNAPSHOT.yaml:78` carries all four.

No validator check binds a child's `parent:` to the parent's `tasks:` list — the VERIFY gate reads the snapshot's list only (`tools/scripts/validate-docs.py:1417`), so this is mechanically invisible. The snapshot copy is the one the gate consults and it is correct; the note copy is the one a reader consults and it is not. This is the same one-fact-two-places defect the feature exists to remove, in the feature's own frontmatter.

### 5. Title derivation has no fail-safe; the prune does

`TASK-0082:47` states one explicitly: "Unparseable note, missing note, ambiguous status → keep. Never remove on uncertainty." `TASK-0083`, `TASK-0084` and `ADR-0018` §1 state no equivalent for derivation, and the population is real. Measured fleet-wide, **9 registered entries carry a snapshot title that no note can supply**:

- three **zero-byte** note files in `project-os-cockpit` — `TASK-0182`, `TASK-0183`, `TASK-0187`;
- six notes whose frontmatter does not parse as YAML — `your-health` `REQ-0017`, `REQ-0020`, `REQ-0024`, `REQ-0025`, `REQ-0026`, and `your-applications.com` `REQ-0028`.

A literal implementation of "write each entry's `title` from its note's `title`" blanks those nine. `TASK-0084`'s migration record preserves the text, so nothing is unrecoverable — but the outcome is a snapshot entry with no title at all, which is worse than the drift being fixed, and `--check` would then be clean on it.

Related and unstated: neither note says **how an entry is matched to its note**. `file:` is absent on most entries in several repos, and the ID index does not resolve composite change IDs — `build_note_index` keys `CHG-20260724-Implemented-Rejoins-Done` as `CHG-20260724` (`validate-docs.py` `ID_RE`), so **161 `CHG-*` entries fleet-wide** resolve to no note by ID. They are outside the prune (condition 1 covers only task/issue/feature) but inside "every registered item" for derivation.

## Non-blocking

### 6. The condition-3 inversion test cannot fail

`TASK-0082:56` asks for "a fixture repo where each of the six conditions is violated in turn, asserting the entry survives in every case". Condition 3 is "not `deferred`". `STATUSES.md:53` makes `deferred` and `done` mutually exclusive task statuses, and the prune runs after status sync, so any entry violating condition 3 already violates condition 1. A fixture violating **only** condition 3 cannot be constructed, and an implementation that omits condition 3 entirely passes the suite — while `ISS-0002` is named on the next line as the failure the area exists to prevent.

The system is safe regardless: `DEFER-RETENTION` exists and does what the task assumes (`validate-docs.py:1642` errors when a deferred item is absent from the snapshot). But the test is not the thing keeping it safe, and the notes should not imply it is.

The fix needs something the notes do not currently say: **which source each condition reads**. Conditions 1 and 3 read the same field and can only disagree when the snapshot entry and the note disagree — which happens when `NOTE-DUP-ID` makes sync skip an ID. State that, and condition 3 becomes both meaningful and testable.

### 7. Two `FEAT-0022` acceptance criteria are unachievable under the rollout the feature adopted

- `FEAT-0022:66` — "disappears from `items.*` on the next sync, **in every repo**, without anyone invoking anything." `TASK-0085:44` says a repo that never adds the key "keeps today's behaviour indefinitely". The criterion also says "older than the retention window", wall-clock phrasing for what `ADR-0018:76` insists is count-based.
- `FEAT-0022:70` — "…and drifting one is a validator finding." `TASK-0083:51` decides the opposite: delete the check after migration rather than keep a permanently-silent one, citing `ADR-0011`.

### 8. `TASK-0085` says one gating key in the procedure and two in the mechanism

`TASK-0085:31` — "adds **one key** to that repo's `SNAPSHOT.yaml`, which switches the feature on." `TASK-0085:50-51` describes two independent gates (retention window key for the prune; per-repo overwrite enablement for titles), and `TASK-0085:96` restores both: "Enable title overwrite; add the retention window key."

The inert-by-default design is coherent — **both** halves are genuinely gated and neither arms on arrival — but the numbered walkthrough a reader would follow understates it, and it is the section that tells someone what to do.

### 9. The `405 / 227 / 168 / 10` bands do not reproduce, and contradict the 413 two lines above

`FEAT-0022:48` states `your-trainer` has **413** drifted titles; `FEAT-0022:50` states "**405** measurable divergences", split 227 (>90% present) / 168 (partial) / 10 (nowhere else). Re-measured: 413 drifted pairs, all measurable — every title contains words. Under the only method the notes state (`TASK-0084:51`, "under 50% word overlap with their note"):

| haystack | ≥90% | 50-90% | <50% |
|---|---:|---:|---:|
| whole note file | 244 | 164 | **5** |
| body only | 125 | 277 | **11** |
| body only, stopwords removed | 116 | 287 | **10** |
| *claimed* | *227* | *168* | *10* |

No single method yields the claimed triple, and none yields 405. The "10 orphans" is load-bearing — `FEAT-0022:50`, `TASK-0084:38`, `TASK-0084:51`, `TASK-0084:56`, `TASK-0085:86`, and `SNAPSHOT.yaml:78` — and `TASK-0084` makes flagging exactly ten of them a DoD tick an implementer cannot reproduce. Record the method alongside the number, or state the count as approximate.

### 10. `ADR-0018`'s "28 orphans" has no stated method and did not reproduce

`ADR-0018:92` reports `note:` prose already present in the note body as 32/32 here, 102/120 in `project-os-cockpit`, 86/96 in `your-health`, leaving 28 orphans. Strict verbatim containment — the method the same ADR names at `:94` for titles — gives 0/33, 0/120, 0/96, i.e. 249 orphans. A ~70% word-overlap threshold is the closest reconstruction: 33/33, 98/120, 85/96, i.e. **33** orphans.

The argument survives — orphans exist, and a similarity heuristic would delete them — but this is the ADR's central safety rule and the figure supporting it cannot be re-derived from the ADR. (`32 of 32` is also now `33 of 33`; the repo gained an entry.)

### 11. Item counts stale by one

`TASK-0085:63` gives `project-os-dev` 159 items and `:73` the fleet 3,162. Measured: **160** and **3,163**. The snapshot held 159 at `d06a4ae` and 160 from `d10e063` — the commit that created `TASK-0085`. The table did not count its own entry.

### 12. `SNAPSHOT.yaml` disagrees with itself on `TASK-0084`'s effort

`SNAPSHOT.yaml:253` reads `effort: L`. `TASK-0084:13` reads `effort: S`, and `SNAPSHOT.yaml:254` — the same entry's own `note:` — reads "Now fully mechanical (effort L -> S)". `f7fa1b3` resized the task and wrote the prose but not the field. `effort` is not in the derived set, so nothing compares the two copies: an instance of the exact defect class `FEAT-0022` exists to remove, sitting in the feature's own snapshot entry.

## What was checked and held

Recorded so a later reader can tell verification from assumption. All figures re-measured 2026-08-04 across the twelve repos, resolving notes by `file:` where present and by ID index otherwise.

- **659 drifted titles fleet-wide** — exact. Every cell of `TASK-0083:31-38` and the per-repo list at `TASK-0084:25` reproduces exactly (413 / 140 / 29 / 26 / 26 / 17 / 3 / 3 / 1 / 1).
- **1,756 terminal, 142 held, 1,614 prunable** — exact, and every per-repo terminal/held/prunable cell in `TASK-0085`'s table.
- **`your-trainer` titles are 60% of its file** — 233,232 of 386,546 bytes today (60.3%); the ADR's 231,506/386,354 (59.9%) was measured a day earlier.
- **−28% for `your-trainer`** — derivation replaces 233,204 bytes of title text with 125,089, saving 108,115 = **27.97%** of the file.
- **~+2% for `project-os-cockpit` and `project-os-dev`** — +2.41% and +1.94%.
- **75 of 659 (11%) verbatim containment** — exact (11.4%).
- **0 of `your-trainer`'s 709 terminal items carry `note:`** — exact; only 2 items in the entire repo carry it, neither terminal.
- **All 22 feature notes carry `goal:`; 4 of the 12 snapshot entries carrying it have drifted** — exact (`FEAT-0007`, `FEAT-0009`, `FEAT-0010`, `FEAT-0020`).
- **84% of drift and 61% of pruning in `your-trainer` + `project-os-cockpit`** — 83.9% and 60.8%.
- **Count-based-by-ID is idempotent.** Everything removable ranks below the top-N by ID, so the surviving top-N is unchanged and a second run is a no-op. The insistence on count over wall-clock is correct and `REQ-0019:53` already recorded the hazard.
- **`resolves()` falls back to `note_index`** (`validate-docs.py:1298-1302`), so pruning an entry does not break link-graph checks — provided condition 5 holds, which it does by construction.
- **`compute_metric_counts` reads snapshot items then `setdefault`s from `note_index`** (`validate-docs.py:663-675`), so pruning cannot distort metrics — provided status sync runs first, which `TASK-0082:25` specifies.
- **`sync-snapshot.py`'s header does disclaim membership** — "which items a snapshot carries is the curation decision this script deliberately does not make". Note its `LEFT ALONE` list names `retention` and `goal/note prose` too, so `TASK-0082:71` has three lines to change, not one.
- **CI runs `sync-snapshot.py --check`** (`.github/workflows/validate-docs.yml:19`), so `TASK-0085`'s "all twelve go red the same day" hazard is real.
- **`tools/scripts/` is `template`-owned** (`tools/sync/MANIFEST.yaml:18`).
- **`DEFER-RETENTION` exists and does what `TASK-0082` assumes** (`validate-docs.py:1642`).
- **Every cross-reference resolves** — `TASK-0055`, `TASK-0072`, `TASK-0063`, `TASK-0080`, `ISS-0002`, `ISS-0026`, `TASK-0074`, `ADR-0010`, `ADR-0011`, `REQ-0018`, `REQ-0019`.
- **Baseline repo state clean** — `validate-docs` 0 errors, `sync-snapshot --check` clean, before and after this review's edits.

## Next actions

- [x] Re-measure `ADR-0018:98-103` and `:24` under the amended rule (8/69 and 34/240), or state the table as pre-amendment. — re-measured under the amended rule: your-health 34/240, project-os-dev 8/69; consequence :24 corrected to 8 of 77, and the basis (`note:` only, 2026-08-04) now stated
- [x] Delete `/goal:` from `TASK-0082:38` and `FEAT-0022:69`. — both now read `note:` only, with FEAT-0022 noting goal: is derived under rule 1
- [x] Move the fleet-completion clauses out of `TASK-0082`/`TASK-0083`/`TASK-0084`'s DoDs into `TASK-0085`. — all three now assert the CODE is fleet-safe via dry-run; migrating the fleet is TASK-0085's and gates nothing
- [x] Add `TASK-0085` to `FEAT-0022:14`. — added
- [x] Give derivation a stated fail-safe: a note that is missing, empty, unparseable or has no `title:` leaves the snapshot title alone. Say how an entry is matched to its note. — new section in TASK-0083; matching is by note `id:`; count re-measured as 17 malformed notes fleet-wide, not 9 — 3 zero-byte plus 14 unparseable — and the 161 CHG-* entries are called out for explicit disposition
- [x] State which source each prune condition reads, and either drop condition 3's inversion test or make it constructible. — TASK-0082 verification now says condition 3 needs a deliberately illegal fixture, since deferred and done are mutually exclusive
- [x] Reconcile `FEAT-0022:66` and `:70` with the opt-in rollout and with `TASK-0083:51`. — both criteria rewritten to say 'in a repo that has opted in'; the drift-check question handed to TASK-0083 rather than asserted
- [x] Fix `TASK-0085:31` to name both gates. — step 3 now reads 'enable title overwrite, add the retention window key'
- [x] Record the method behind the `405/227/168/10` bands and `ADR-0018:92`'s 28, or restate them as approximate. — bands re-measured with the method stated in the note (>4-char words, case-folded, set coverage by note title+body): 413 drifted, 212 / 193 / 8
- [x] Correct 159 → 160 and 3,162 → 3,163 in `TASK-0085`. — corrected to 161 and 3,164 — both had moved again by the time of the fix, which is why the note now carries a measurement date
- [x] Fix `SNAPSHOT.yaml:253` to `effort: S`. — done

## Status

All twelve findings addressed by the authoring session on 2026-08-04. The issue stays **open**: the author fixing findings does not close them, and a fresh clean-context round is what settles whether the fixes hold — the pattern ISS-0022/ISS-0023 established on ADR-0017.

One finding was worse than reported. #5 counted 9 entries whose notes cannot supply a title; re-measuring found **17** — 3 zero-byte in project-os-cockpit and 14 with unparseable frontmatter across your-trainer (8), your-health (5) and your-applications.com (1).
