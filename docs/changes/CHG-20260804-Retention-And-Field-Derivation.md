---
type: "[[change]]"
id: CHG-20260804-Retention-And-Field-Derivation
aliases: ["CHG-20260804-Retention-And-Field-Derivation"]
title: "Retention runs on every sync and `title`/`goal` are derived from the notes; migrated across twelve repos, fleet snapshots down 39%"
status: merged
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["FEAT-0022", "ADR-0018"]
commit: ""
pr: ""
impacts: ["tools/scripts/sync-snapshot.py", "SNAPSHOT.yaml (all 12 repos)"]
issues: [ISS-0030, ISS-0031, ISS-0032]
features: [FEAT-0022]
tests: [TST-0003]
reviewed_by: ""
review_date: ""
review_verdict: ""
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
| your-trainer | 1,065 → 412 | 386,546 → 112,952 (**−71%**) |
| project-os-cockpit | 593 → 343 | 199,970 → 132,874 (−34%) |
| your-health | 573 → 354 | 184,029 → 130,033 (−29%) |
| your-applications.com | 237 → 151 | 153,865 → 129,821 (−16%) |
| your-sudoku | 254 → 190 | 58,468 → 46,999 (−20%) |
| project-os-dev | 161 → 133 | 70,962 → 64,829 (−9%) |
| yourtrainer-mcp | 99 → 61 | 32,204 → 20,089 (−38%) |
| edankert.com | 64 → 50 | 22,111 → 18,718 (−15%) |
| articles, obsidian-supernote-sync, project-os-bench, project-os | unchanged | everything inside the window |

Fleet snapshot bytes: **~1,158 KB → 707 KB (−39%)**.

Verified per repo: 0 validator errors, `sync-snapshot --check` clean, idempotent on re-run, `metrics.counts` byte-identical before and after, and **no validator check silenced**.

## Two things the implementation found that the plan had not

**Pruning silences checks.** Eighteen validator codes are emitted from the walk over `items.*`, so a pruned entry stops being checked at all. Measured: pruning silenced 12 `VERIFY-WAIVED` warnings in `project-os-dev` whose notes still carried `waiver_expires: 2026-10-23` — that expiry would never have fired again — and 3 `VERIFY` warnings in `your-trainer` on issues closed against tests still at `ready`. Retention was erasing outstanding obligations by forgetting them.

The rule became: **retention removes finished business, never unfinished.** An entry is held back by non-empty `note:`, by an outstanding `verification_waiver`, or by a linked test that is not passing. With the holds in place, no check is silenced in any of the twelve repos.

**A first attempt at that fix did nothing at all.** It read `verification_waiver` from the snapshot entry only, while the waiver is usually written in the note and the validator reads note-first. The symptom was silent: the same 12 warnings kept disappearing. It is now checked in both places, and `TST-0003` fails if the hold is removed.

## Verification

[[TST-0003-Retention-And-Derivation-Invariants|TST-0003]], stamped `passing` by the runner (ADR-0010). Eleven assertions, structured as an inversion suite — every prune condition is violated in turn and the entry must survive, because a happy-path test cannot distinguish a working rule from a missing one.

Adequacy shown by mutation, three independent breaks each caught: removing the verification hold, accepting blank titles in the derivation fail-safe, and replacing the flow-scalar scanner with a naive comma search (which returned a corrupted, truncated title).

## Migration safety

- Nothing is lost. Every replaced `title`/`goal` was written to a per-repo `docs/reference/snapshot-field-migration-2026-08-04.md` before derivation overwrote it, so the migration needed no per-item judgement and no similarity test.
- No note file was modified or deleted. The notes remain the archive; only snapshot entries were removed.
- Derivation fails safe: a note that is missing, zero-byte, unparseable, or has no `title:` leaves the snapshot value untouched. Seventeen real notes fleet-wide are in that state, plus 161 `CHG-*` entries no note claims by ID.
- Pruning is escapable with `--no-prune`, and a repo that never adds the keys keeps its previous behaviour indefinitely.

## Provenance note: `your-health`

Eleven repos carry this change under a commit that names it. **`your-health` does not.** A concurrent session committed there while the migrated files sat in its working tree, and swept them into `bc04a44` — *"fix(iss-0068): a day's HRV falls back to its own rows when no roll-up exists"* — which contains the gate keys, the new script and the pruned snapshot alongside unrelated application work.

The migration itself is correct there and was verified after the fact: 0 validator errors, `sync-snapshot --check` clean, `TST-0003` passing, 573 → 354 items. Only the record is wrong, and history was left alone rather than rewritten because that commit carries someone else's work.

Recorded because a later reader searching `your-health` for when retention arrived will find nothing, and the answer is `bc04a44`. The general lesson is worth keeping too: **a fleet-wide migration that edits working trees is unsafe against concurrent sessions**, and `TASK-0085`'s per-repo procedure should say so — check the tree is clean before migrating a repo, not just after.

## Open

- `ISS-0032` remains open pending a re-review round; the author fixing review findings does not close them.
- Whether the gating keys stay permanently once all twelve have opted in is undecided — a permanent opt-out everyone has opted into is [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]]'s shape in configuration form (`TASK-0085`).
