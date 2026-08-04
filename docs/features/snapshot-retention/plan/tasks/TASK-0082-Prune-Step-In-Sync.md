---
type: "[[task]]"
id: TASK-0082
aliases: ["TASK-0082"]
title: "Prune step in sync-snapshot.py: remove entries by reproducible rule on every run"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018"]
parent: "[[FEAT-0022]]"
effort: L
due: ""
depends: ["[[TASK-0084]]"]
blocks: []
related: ["[[ADR-0018]]", "[[ADR-0005]]", "[[ISS-0030]]"]
tests: []
---

# The prune step

## What

A step in `sync-snapshot.py`, after status sync, that removes entries satisfying [[ADR-0018-What-The-Generator-Owns|ADR-0018]]'s six conditions. It runs wherever sync runs — pre-commit hook, CI, manual — so retention stops being a duty and becomes a property.

## The rule, restated once for implementation

Remove an entry when **all** hold. Anything else stays.

1. terminal for its type — `done` task, `fixed` issue, `done` feature
2. not among the **N most recent by ID** in its collection
3. not `deferred` — ADR-0005, `DEFER-RETENTION`
4. not named in `focus`
5. its note exists and parses
6. its item-level `note:` field is **empty** (`goal:` is derived under rule 1 and does not hold)

Condition 6 is a **hold, not an exemption** (ADR-0018 rule 3). An entry with non-empty `note:`/`goal:` stays and is **reported** as pending relocation: the prose is scratch context, the note file is the archive, and clearing the field is the author's statement that the durable copy exists. The report is what makes the hold a closable backlog rather than a resting state, so it is part of this task and not a nicety.

**Do not attempt to detect whether the prose is "already in the note."** Measured 2026-08-04, `note:` is mostly but not always present in the note body — 32/32 here, 102/120 in project-os-cockpit, 86/96 in your-health, leaving 28 orphans. A similarity heuristic deletes those on a false positive. Emptiness is the only signal with no false positives.

Where `N` lives is a decision this task must make and record. `retention.recent_changes_max: 25` already exists and is read by nothing (ISS-0030); reusing it is tempting but it is named for `items.changes`. Prefer a new explicit key, and delete or repurpose the three dead `keep_*` flags in the same change rather than leaving four keys of which one is live.

## The properties that must hold

- **Idempotent.** Two consecutive runs produce one diff, not two. Count-based window only — a date-keyed rule makes output depend on the day, so an untouched repo drifts overnight and CI `--check` fails on any repo that has not committed recently. This is `REQ-0019`'s zero-diff property and it is the acceptance criterion, not a nicety.
- **Fail safe.** Unparseable note, missing note, ambiguous status → keep. Never remove on uncertainty.
- **Never touches `docs/`.** The note is the archive; only the snapshot entry goes.
- **Surgical.** Delete whole entries in place. Do not re-emit the file — that is the whole-file generation ADR-0018 explicitly does not revive.
- **Legible.** Emit a `# Pruned:` comment in the fleet's existing style, and report removals on stdout as counter and metric changes already are.
- **Escapable.** `--no-prune` disables it.

## Verification

- Inversion: a fixture repo where each of the six conditions is violated in turn, asserting the entry survives in every case.
- Idempotence: run twice, assert zero diff on the second; run `--check` against an untouched tree with a simulated later date, assert clean.
- Deferral regression: `ISS-0002` is the failure this area exists to prevent — assert a deferred item is never removed, and that `DEFER-RETENTION` stays silent.
- Metrics parity: `compute_metric_counts` reads notes plus snapshot, so `tasks_done` must be unchanged by pruning. Assert before/after equality across the fleet.
- Fleet dry-run before any commit, per `TASK-0072`.

## Definition of Done

- [ ] Prune step implemented, running automatically after status sync.
- [ ] Window key decided and recorded; the dead `keep_*` flags resolved in the same change.
- [ ] Idempotence proven by test, including the next-day case.
- [ ] All six conditions covered by inversion tests, including that a held entry (non-empty `note:`) survives *and is reported*.
- [ ] Clearing an entry's `note:` makes it prunable on the next run — the hold releases, proving it is a backlog rather than an exemption.
- [ ] Metrics unchanged fleet-wide; `validate-docs` clean in all twelve repos.
- [ ] `--no-prune` works and is documented.
- [ ] `sync-snapshot.py`'s header updated — it currently disclaims making membership decisions.
- [ ] A `TST-*` with a `command:`, per ADR-0010.
