---
type: "[[change]]"
id: CHG-20260804-Retention-And-Field-Derivation
aliases: ["CHG-20260804-Retention-And-Field-Derivation"]
title: "Retention runs on every sync and `title`/`goal` are derived from the notes; migrated across twelve repos, fleet snapshots down about a third"
status: merged
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["FEAT-0022", "ADR-0018"]
commit: "52328fe..HEAD (project-os-dev); see each repo's `Adopt retention pruning` commit"
pr: ""
impacts: ["tools/scripts/sync-snapshot.py", "tools/scripts/validate-docs.py", "tools/cockpit/**/validate_docs_bundled.py", "tools/scripts/test-retention.py", "SNAPSHOT.yaml (all 12 repos)"]
issues: [ISS-0030, ISS-0031, ISS-0032, ISS-0033, ISS-0034, ISS-0035, ISS-0036, ISS-0037, ISS-0038, ISS-0039]
features: [FEAT-0022]
tests: [TST-0003]
reviewed_by: "model:claude-opus-5[1m]"
review_date: 2026-08-04
review_verdict: approved
review_note: "Round-EIGHT clean-context review (fresh session, never saw the author's reasoning; same model family as the author, recorded here as provenance per ADR-0013). APPROVED. Round seven's one blocking line is fixed and introduced no new error: test-retention.py:134-136 now reads '3 real notes ... all zero-byte', and 3 is what I measure. FIFTH consecutive round with NO code defect; I inherited nothing from rounds four to seven and re-derived every property by running code, with `python3 -B` throughout. Skip set decomposed by CAUSE, not by prefix: 203 skipped = 200 with no claimant at all + 3 claimed by a zero-byte note, and the 'claimed, parses, no usable title' bucket is EMPTY — so ':57's 200/3 split is not merely arithmetically right, it is causally right. The 3 are cockpit TASK-0182/0183/0187, the only zero-byte .md files under docs/ in the twelve. The 14 PyYAML-rejecting files are exactly 8/5/1 across your-trainer/your-health/your-applications.com and all 14 supply titles via the fallback; ':59 is accurate. Four surfaces agree and all four are correct. Both other corrected figures verified: 3,146 pre-migration items EXACT, and 1,352 removals EXACT measured parent->today with 0 whose note fails to supply the collection's terminal status. Losslessness proved in the stronger direction too: across 430 surviving entries whose title/goal was overwritten, 0 are unrecorded — every replaced value is in its repo's migration record with the exact prior string. 709 migration rows, every `was:` string-compared against that repo's own snapshot at the migration commit's parent, 0 mismatches, every header equal to its section count (413/140/33/26/44/3/8/30/1/0/0/11). Fleet: 12/12 validate exit 0 bar this repo's standing REVIEW error, 0 ^ERROR and 0 internal error anywhere; --check exit 0 in all twelve; 23 assertions green in all twelve; two consecutive REAL syncs byte-identical in all twelve AND identical to the pre-run file, every snapshot hashed and restored. Before-bytes 1,151,665 exact and every per-repo before-row exact. The load-bearing safety property REPRODUCED rather than read: deleting condition (7) and re-syncing silences exactly 12 VERIFY-WAIVED warnings in project-os-dev (19->7) and exactly 3 VERIFY in your-trainer (3->0), the two numbers ':62 states. Twelve bundled validators, byte-identical to one another, all carrying the claimants fix and differing from canonical by 15 lines that are entirely comments (identical once comments are stripped). Cockpit tasks_done 271 / features_done 55 identical to 48ea49e~1. Mutation: my own 22 score 9/22, and written the way ':122 and TST-0003 describe them the score is exactly 10 caught / 12 survived; all twelve named survivors confirmed. The three recorded debts (ADR-0018 six-vs-seven, the 15-line bundled drift, the latent index-vs-claimants issue) are TRUE as stated and not held against this verdict. Non-blocking, none of them a false statement about behaviour: the title still says 'down 39%' where the body says 'about -38%' and today measures -37.43%; ':54's 'a few hundred bytes per round' is nearer 1,100 (70,098 -> 77,919 over the rounds) and '~1,818' measures 1,820 — all disclosed drift; ':70 enumerates conditions 1,2,3,5,6 as inverted and omits (7), which TST-0003's table includes and which I confirmed is guarded; the '## Eight review rounds' heading now covers seven; SNAPSHOT.yaml's focus.note still says 'Four clean-context review rounds' and '1,351 removals' and should be refreshed at close-out; and I could not independently confirm 'Eighteen validator codes' (my static scan finds 16), though the mechanism it supports is proven above. Eight rounds is past proportionate for a change whose engineering has now been independently re-derived five times without a defect." replaces round six's verdict, which carried the same reviewed_by string — review_date and this note distinguish the rounds. FOURTH consecutive round with NO code defect; I inherited nothing from rounds four to six and re-derived every property by running code. ':78 is now CORRECT: measuring the fleet myself, through each repo's own sync-snapshot.py, note_fields fails to supply 203 registered entries = 200 CHG-* + 3 TASK, the 3 being cockpit TASK-0182/0183/0187, which are the only zero-byte .md files under docs/ anywhere in the twelve. Both retracted readings independently refuted: the 14 PyYAML-rejecting files are real at exactly 8 your-trainer / 5 your-health / 1 your-applications.com and ALL 14 supply titles via load_yaml's parse_yaml_subset fallback — your-health's SNAPSHOT:1506 carries the derived REQ-0024 title today — and the 14 your-health REF-* entries are registered yet absent from that repo's 39-entry skip set, which is all CHG-*. ':80 and TST-0003:53 are accurate, and round six's paste artifact is gone (backticks even, bold balanced on ':78/':80 and TST:51/:53). Re-measured from scratch: 3,146 pre-migration items, 1,352 removals, 0 whose note fails to supply exactly the collection's terminal status; 709 migration rows, every `was:` string-compared against that repo's own snapshot at the migration commit's parent, 709 faithful, 0 mismatches, every header equal to its section count (413/140/33/26/44/3/8/30/1/0/0/11); 12/12 validate exit 0 bar this repo's standing REVIEW error, 0 ^ERROR and 0 internal error elsewhere; --check exit 0 in all twelve; 23 assertions green in all twelve; two consecutive REAL syncs byte-identical in all twelve AND identical to the pre-run file, every snapshot hashed and restored; before 1,151,665 exact and every per-repo row exact; twelve bundled validators all carrying the claimants fix. Mutation: my own 22 score 8 caught / 14 survived, and the gap from ':122's '10 of 22' is my formulations, not the suite — written as the notes describe them, the stubbed prune_entries, the missing-title-as-empty-string (2 assertions) and the scanner-as-comma-search are all caught, which substituted for two survivors gives exactly 10/12; all twelve named survivors confirmed to survive. The three recorded debts (ADR-0018 six-vs-seven, the 15-line bundled drift, the latent index-vs-claimants issue) are TRUE as stated and are not held against this verdict. What blocks is ONE line, and it is not in this note: test-retention.py:133-136, the fourth of the four surfaces round six named, was edited but kept the number — it now reads '17 real notes are in this state fleet-wide, all zero-byte', asserting 17 zero-byte notes where 3 exist. That is worse than the text it replaced, which at least decomposed 17 into two checkable populations. No measurement yields 17 (3 zero-byte; 203 skipped; 567 of 5,087 docs/ files with no usable title, 370 of those with an id). Replace '17 real notes' with '3'. Non-blocking: ':54's 'stable measure: 3,146 -> 1,817' now measures 1,819 with the project-os-dev row at 136 — the drift is disclosed for bytes, and this is the one sentence offering item counts as the figure that does not drift; ':85's 1,352 removals now measures 1,352 and was true when round three measured it. One line in one file and this change is done."
related: [ADR-0018, ADR-0009, ADR-0010, ADR-0005]
---

# Retention and field derivation

## Summary

`sync-snapshot.py` gained two powers under [[ADR-0018-What-The-Generator-Owns|ADR-0018]], both **inert until a repo opts in**:

- **`title` and `goal` are derived from the note**, like `status`. The test for what is derivable is whether the field has a counterpart in the note's frontmatter — `title` and `goal` do, item-level `note:` does not.
- **Terminal entries are removed by a reproducible rule** on every sync, so retention stops being a duty nobody performed ([[ISS-0030-Retention-Is-Policy-Nothing-Performs|ISS-0030]]) and becomes a property.

Two new keys gate them: `retention.derive_fields` and `retention.prune_window`. Absent means off. The three `keep_*` flags that no code ever read are gone.

## Impact

All twelve repos migrated, in ascending order of risk, each verified before the next:

| repo | items | snapshot bytes |
|---|---|---|
| your-trainer | 1,065 → 412 | 386,546 → 112,931 (**−71%**) |
| project-os-cockpit | 593 → 346 | 199,970 → 133,882 (−33%) |
| your-health | 573 → 354 | 184,029 → 130,012 (−29%) |
| your-applications.com | 237 → 151 | 153,865 → 129,801 (−16%) |
| your-sudoku | 254 → 191 | 58,468 → 47,202 (−19%) |
| yourtrainer-mcp | 99 → 61 | 32,204 → 19,558 (−39%) |
| edankert.com | 64 → 50 | 22,111 → 18,698 (−15%) |
| project-os-dev | 161 → 134 | 71,076 → 70,098 (−1%) |
| obsidian-supernote-sync, project-os-bench, project-os | not pruned | everything inside the window |
| articles | 37 → 55 | 12,079 → 19,025 (**+58%**) — see the dirty-tree note; the growth is not this change |

Fleet snapshot bytes: **1,151,665 → ~714,800, about −38%**.

The *before* figure is git-immutable — the sum of every repo's `SNAPSHOT.yaml` at its own pre-migration parent — and is exact. The *after* figure is not: `project-os-dev` gains notes as this work is reviewed, so it drifts upward by a few hundred bytes per round, and three earlier drafts of this line (−39% / ~707 KB, then 713 KB) were each accurate when measured and stale by the next round. Quoting it to four significant figures implies a precision the number does not have. **Item counts are the more stable measure: 3,146 → ~1,818 across the fleet** — 'more' rather than 'fully' stable, because this repo gains an item each review round, which is exactly why every figure in this note carries the date it was taken rather than a false precision. Measured drift is about 1,100 bytes per round, not a few hundred.

Verified per repo: 0 validator errors, `sync-snapshot --check` clean, idempotent on re-run, and **no validator check silenced** — the validator's output across the prune is byte-identical in `your-trainer`.

`metrics.counts` was **not** identical everywhere, which an earlier draft claimed. `project-os-cockpit` fell `tasks_done` 271→268 and `features_done` 55→54 because the prune removed entries it should not have; see the review below. Both are back to their pre-migration values.

## Two things the implementation found that the plan had not

**Pruning silences checks.** Validator codes emitted from the walk over `items.*` — sixteen by static count, so a pruned entry stops being checked at all. Measured: pruning silenced 12 `VERIFY-WAIVED` warnings in `project-os-dev` whose notes still carried `waiver_expires: 2026-10-23` — that expiry would never have fired again — and 3 `VERIFY` warnings in `your-trainer` on issues closed against tests still at `ready`. Retention was erasing outstanding obligations by forgetting them.

The rule became: **retention removes finished business, never unfinished.** An entry is held back by non-empty `note:`, by an outstanding `verification_waiver`, or by a linked test that is not passing. With the holds in place, no check is silenced in any of the twelve repos.

**A first attempt at that fix did nothing at all.** It read `verification_waiver` from the snapshot entry only, while the waiver is usually written in the note and the validator reads note-first. The symptom was silent: the same 12 warnings kept disappearing. It is now checked in both places, and `TST-0003` fails if the hold is removed.

## Verification

[[TST-0003-Retention-And-Derivation-Invariants|TST-0003]], stamped `passing` by the runner (ADR-0010). **23 assertions**, structured as an inversion suite: conditions 1, 2, 3, 5, 6 and 7 are each violated in turn and the entry must survive, because a happy-path test cannot distinguish a working rule from a missing one. **Condition 4 (`focus`) has no fixture** — deleting it leaves the suite green — and that is recorded below among the gaps rather than glossed.

Adequacy shown by mutation. Ten independent breaks are caught, including the two that three rounds of review proved a weaker suite missed: reverting condition (5) to a bare index-membership test (fails 4 assertions) and reverting `_scalar_span` to `find("{")` (fails 2). The suite drives both destructive writers end to end — an earlier version passed against writers stubbed to do nothing.

## Migration safety

- Nothing is lost. Every replaced `title`/`goal` was written to a per-repo `docs/reference/snapshot-field-migration-2026-08-04.md` before derivation overwrote it, so the migration needed no per-item judgement and no similarity test.
- No note file was modified or deleted. The notes remain the archive; only snapshot entries were removed.
- Derivation fails safe: a note that is missing, zero-byte, unparseable, or has no `title:` leaves the snapshot value untouched. Derivation skips **203** registered entries fleet-wide, and the composition was mis-stated for three review rounds before measurement settled it. **200** are `CHG-*` entries that no note claims by ID, because change notes are keyed by date-slug rather than a numeric one. The other **3** are `project-os-cockpit`'s zero-byte notes (`TASK-0182/0183/0187`), which is the whole population that genuinely cannot supply a title.

Earlier drafts said "seventeen files", counting 14 whose frontmatter PyYAML rejects. That was wrong: `load_yaml` falls back to `parse_yaml_subset`, so all 14 *do* supply titles — `your-health`'s `REQ-0024` derives "AI Coach: chat-based training recommendations" today. A review round proposed a different fourteen (`your-health` `REF-0001..REF-0014`, unclaimed because `REF` is absent from `ID_PREFIXES`); measurement refuted that too — all 14 are supplied. Both the claim and its correction were wrong, in opposite directions, and only running the code decided it.
- Pruning is escapable with `--no-prune`, and a repo that never adds the keys keeps its previous behaviour indefinitely.

## Eight review rounds

Reviewed clean-context **eight times**, approved on the eighth. Rounds one to three found real engineering defects. Rounds four to seven each found **none** — every property they attacked held — and blocked on the record: a figure repeated inconsistently, a partial correction that reached three surfaces of four, a stale number in a comment. That distribution is the useful result: the code stabilised early and the *description of it* took five more rounds. What the third round confirmed on re-measurement: **nothing was lost** — 1,352 removals across twelve repos, none whose note fails to supply exactly the collection's terminal status — and the ten migration records reconcile at **709 rows, 0 mismatches**.

### Round one found five blocking defects

Reviewed clean-context on 2026-08-04 (verdict `changes-requested`, findings on [[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them|ISS-0033]]). Two caused real damage and are the reason this note's original claims were wrong:

- **The prune deleted three entries whose notes are zero-byte files.** Condition 5 tested that a note was *indexed*, not that it *parsed* — and `build_note_index` stores `{}` for an unparseable file and matches IDs as substrings. `project-os-cockpit`'s `TASK-0182`, `TASK-0183` and `TASK-0187` went, and with empty notes behind them the items existed nowhere but git. These are the same zero-byte notes ISS-0032 identified: the fail-safe written in response went onto the derivation path and not the destructive one. Condition 5 now requires a note that parses and genuinely claims the ID; all three entries are restored.
- **Derivation was silently dead in block style.** `_scalar_span` chose its branch on `find("{")` over the whole line, so `title: "a {braced} value"` took the inline path, found no key, and returned without writing or reporting. Ten of twelve repos are block style. It now decides on the line's shape.

### Round two and three

**The metric counter had the same substring bug the prune did.** `compute_metric_counts`'s archive fallback resolved `FEAT-0009` through `build_note_index`, where the composite `CHG-20260525-FEAT-0009-Chrome-Polish.md` holds the slot and lends its `merged`. Pruning the entry then let that manufactured claim decide the count. It now consults `claimants` first. Rejecting the impostor alone was not enough — it holds the index slot, so the real note was absent and the item counted by nobody, which is what a first attempt produced. **The same fix had to reach twelve bundled `validate_docs_bundled.py` copies**, which is the `ISS-0026` shape a third time and the reason `impacts:` now lists them.

**The test suite guarded neither of round one's fixes.** Reverting condition (5) to an index test, or `_scalar_span` to `find("{")`, both left it green — the condition-5 fixture used a *missing* note, which the index rejects identically, and the block fixture's assertion checked only that a brace survived, which it does whether or not derivation runs. Both are now guarded, with the assertions checking derived values rather than incidental substrings.

**Condition (3) became unreachable and is gone.** Tightening (5) to require the note's *terminal* status meant `deferred` could never reach (3). An unreachable rule reads as protection while providing none — the shape ADR-0011 refuses — so the check is folded into (5) and the test now asserts the outcome (a deferred note is never pruned) rather than a line.

Also fixed: `_value_end` mishandled YAML's doubled single-quote escape, producing unparseable output; `_owes_verification` treated an unresolvable test as passing, failing *open* on the one input it cannot verify; `prune_entries` lacked the `items:` scoping guard its sibling walkers have; and `focus` protection matched only top-level strings, so `your-sudoku`'s `ISS-0068` — named in `focus.note` — was pruned. It is restored and focus now protects any ID it mentions at any depth.

**The migration records were incomplete in four repos.** The rollout re-ran the recorder *after* migrating, when there was no drift left, overwriting good records with "0 value(s) replaced" — including in `project-os-dev`, the repo the ordering deliberately put first. All ten records have been reconstructed from git and now hold **709** values, matching the measured drift.

**`TST-0003` executed neither destructive writer.** Stubbing `prune_entries` and `sync_derived_fields` to return `[]` left the suite green, and its condition-3 fixture used an ordinary `deferred` entry that condition 1 already rejects, so the deferred branch could be deleted unnoticed. The suite now runs both writers end to end and uses the illegal `done`+`deferred` entry the design actually requires; 18 assertions, and both mutations fail it.

## Provenance note: `your-health` and `articles`

Eleven repos carry this change under a commit that names it. **`your-health` does not.** A concurrent session committed there while the migrated files sat in its working tree, and swept them into `bc04a44` — *"fix(iss-0068): a day's HRV falls back to its own rows when no roll-up exists"* — which contains the gate keys, the new script and the pruned snapshot alongside unrelated application work.

The migration itself is correct there and was verified after the fact: 0 validator errors, `sync-snapshot --check` clean, `TST-0003` passing, 573 → 354 items. Only the record is wrong, and history was left alone rather than rewritten because that commit carries someone else's work.

`articles` is the same hazard in the opposite direction: it held 18 uncommitted snapshot entries before I touched it, and **my** commit swept them in — which is why its row reads 37 → 55 rather than "unchanged". Neither the growth nor the entries are this change's work.

Recorded because a later reader searching `your-health` for when retention arrived will find nothing, and the answer is `bc04a44`. The general lesson: **a fleet-wide migration that edits working trees is unsafe against concurrent sessions in both directions** — it can lose its own provenance, and it can absorb work that is not its own. `TASK-0085`'s procedure now requires confirming the tree is clean *before* migrating a repo, not just after.

## Known gaps, recorded rather than closed

- **ADR-0018 authorises six prune conditions; the code implements seven.** The seventh — the verification hold, which is this change's most load-bearing safety property — was discovered during implementation and never written back into the decision. ADR-0018's condition 5 ("exists on disk and parses") also no longer describes the code, which now requires the note to supply the collection's *terminal* status. The ADR and `TASK-0082` both need amending; the code is stricter than the decision in both directions, so nothing is unsafe, but the decision no longer documents what runs.
- **The twelve bundled `validate_docs_bundled.py` copies are no longer verbatim** — they differ from their canonical validator by 15 comment lines, because the fix was hand-applied rather than re-vendored, while `validation.py` still calls them "a verbatim copy". That is `ISS-0026`'s shape reintroduced by the fix for `ISS-0026`'s shape. Functionally identical; the vendoring step is the real fix.
- **Mutation coverage is 10 of 22.** Condition 1, condition 4, the blank-title fail-safe, the fail-open `_owes_verification`, the focus scan, the `in_items` guard, the doubled-quote handling, a widened `PRUNABLE_TERMINAL` and a 4-column over-delete all survive. `compute_metric_counts` has no test at all.

## Open

- `ISS-0032` remains open pending a re-review round; the author fixing review findings does not close them.
- Whether the gating keys stay permanently once all twelve have opted in is undecided — a permanent opt-out everyone has opted into is [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]]'s shape in configuration form (`TASK-0085`).
