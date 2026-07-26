---
type: "[[issue]]"
id: ISS-0011
aliases: ["ISS-0011"]
title: "ADR-0012's `wont-fix` -> `declined` rename missed three status tables in validate-docs.py: PHASE-CHILDREN refused declined issues, and REQ-PREMATURE and PLAN-FOLLOWS were silently dead"
status: fixed
severity: medium
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
component: tooling
source: ["downstream:your-sudoku/ISS-0096", "review:2026-07-26-phase-registry-rebuild"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0012, ADR-0008, ISS-0009]
tests: [TST-0002]
---

# PHASE_RESOLVED kept the pre-ADR-0012 word

## Problem

`tools/scripts/validate-docs.py` defines the map that the `PHASE-CHILDREN` gate uses to decide whether a child note resolves its phase's scope:

```python
PHASE_RESOLVED = {
    "task": {"done", "cancelled", "superseded"},
    "issue": {"fixed", "wont-fix", "cancelled", "superseded"},
    ...
}
```

`wont-fix` has not been an issue status since [[ADR-0012]] renamed it to `declined`. `STATUSES.md` allows exactly `triage`, `open`, `fixed`, `declined`, `deferred` for `[[issue]]` — so of the four values in that row, only `fixed` is reachable, and the terminal status that replaced `wont-fix` is absent.

The user-visible consequence: **an issue deliberately closed as no-action cannot name a `done` phase.** Authoring the link the way `STATUSES.md` describes it — on the child, in `phase:` — reports the closed phase as having unresolved children.

## Root cause

ADR-0012 is explicit that this was a pure rename with unchanged meaning:

> "`in-review` → `review` and `wont-fix` → `declined` are pure renames; the band membership of each is unchanged (`review` active, `declined` archived)."

Its consequence list enumerates the surfaces to migrate:

> "Every palette surface changes: `statuses.py`, `validate-docs.py`'s **ALLOWED_STATUS**, `base.css`, `cockpit.css`, `cockpit.js`, the Electron renderer, and STATUSES.md."

`PHASE_RESOLVED` is a **second, independent status table inside that same file**, and the list does not name it. `ALLOWED_STATUS` was migrated correctly; `PHASE_RESOLVED` was not seen. `migrate-status-vocabulary.py` line 114 carries `("issue", "wont-fix"): "declined",  # rename`, but that script rewrites *notes* and `SNAPSHOT.yaml`, never the validator's own constants — so it could not have caught this.

**Nothing tests it.** `PHASE_RESOLVED` is referenced by no test in `project-os`, `project-os-dev`, or `project-os-cockpit`. The parity suite ADR-0012 relied on to "mechanically prove every surface agrees" enumerates palette surfaces, and this table is not one of them. That is why a 41-value vocabulary migration shipped green over a stale value.

## Repro

In any repo with a `done` phase and a `declined` issue:

1. Set `phase: "[[PHASE-####]]"` in the declined issue's frontmatter, naming the closed phase.
2. Run `bash tools/scripts/validate-docs.sh`.

## Expected

Clean. `declined` is terminal and deliberate — it resolves the item's place in the phase's scope exactly as `fixed` does. `STATUSES.md` lists it under the transitions that close an issue: "`triage`/`open` → `declined` (deliberate no-action, keep the note)".

## Actual

Verified 2026-07-26 in `your-sudoku`, where three declined iOS-parity issues belong to a closed `PHASE-0008`:

```
ERROR [PHASE-CHILDREN] PHASE-0008 is 'done' but 1 item(s) still name it as their phase
without a resolved status: ISS-0019 (declined); resolve them, or re-home each to the phase
that now owns its work (docs/phases/PHASE-0008-iOS-Native-Port.md)
validate-docs: FAIL (1 error)
```

The downstream workaround was to record the relationship on the phase side only (in its `issues:` list) and leave the children's `phase:` empty — which is precisely the shape the `PHASE-CHILDREN` comment warns about, since that gate reads the children rather than the phase's own list.

## Blast radius

Every repo carrying the validator. Confirmed identical `PHASE_RESOLVED["issue"]` in 11 files across 10 repos at the time of the fix: `project-os`, `project-os-dev`, `project-os-cockpit` (both `tools/scripts/validate-docs.py` and the verbatim `src/project_os_cockpit/validate_docs_bundled.py`), `edankert.com`, `obsidian-supernote-sync`, `your-applications.com`, `your-health`, `your-sudoku`, `your-trainer`, `yourtrainer-mcp`.

The defect is latent in most of them: it only bites a repo that has both a closed phase and a declined issue that belongs to it.

## Fix

One word, in `PHASE_RESOLVED`:

```diff
-        "issue": {"fixed", "wont-fix", "cancelled", "superseded"},
+        "issue": {"fixed", "declined", "cancelled", "superseded"},
```

Applied here and propagated verbatim to all ten repos. See [[CHG-20260726-Phase-Resolved-Declined]].

## Two more instances, found by the test (2026-07-26)

Extending `STATUS-TABLE` to the file's other status tables was expected to be bookkeeping. It was not: **the same ADR-0012 rename had been missed twice more**, and both misses were live bugs that had silently disabled a check since the day the vocabulary changed.

**REQ-PREMATURE was dead for the case it exists to catch.** The check tested feature statuses against an inline `("in-progress", "in-review", "done")` literal, written out twice. After ADR-0012 the first two values cannot occur, so the warning "requirement still draft but the feature is already being implemented" could only fire once the feature had reached `done` — never while it was actually being built.

**PLAN-FOLLOWS never fired at all.** Its `follows` map — a local, keyed by feature status — used the same two retired values. `follows.get(parent_status)` returned `None` for every actively-built feature, and the code reads `if expected:`, so the check silently skipped. This one shipped *in the same commit as ADR-0012*: the PLAN checks were written against the vocabulary the same commit was retiring.

Both are now module-level constants (`FEATURE_ACTIVE_STATUSES`, `PLAN_FOLLOWS_FEATURE`) with corrected values, and both are covered by `STATUS-TABLE`.

### What re-arming them surfaced

Measured across the ten repos immediately after the fix — all **warnings**, no repo's error count changed:

| Check | Warnings | Where |
|---|---|---|
| `PLAN-FOLLOWS` | 15 | project-os-cockpit 9, your-health 6 — plans still `active`/`draft` under features closed months ago |
| `REQ-PREMATURE` | 4 | obsidian-supernote-sync, your-health, your-sudoku, your-trainer — requirements at `draft` while their feature is mid-build |

`plan` was also added to the `ALLOWED_STATUS` constant. It was consumed by `validate_plan_notes` via `load_allowed_status()` but absent from the defaults, so a repo whose `STATUSES.md` lacked a `[[plan]]` section would get an empty allowed set and flag every plan it found.

## Deliberately not changed

- ~~**`cancelled` and `superseded` stay in the issue row.**~~ Reversed on 2026-07-26 when `STATUS-TABLE` landed: they are not allowed issue statuses, so the new check correctly rejects them. See "Guarded by a test" above.
- **`RESOLVED_STATUSES`** (`done`, `cancelled`, `superseded`) keeps its values: it governs task and feature scope resolution, where all three are legal, so the issue rename never applied to it. It is now covered by `STATUS-TABLE` against both types it is used for.
- **The cockpit's `ALLOWED_STATUS`** in `validate_docs_bundled.py` still carries the full legacy vocabulary (`in-progress`, `closed`, `reopened`, `wont-fix`). ADR-0012 sanctions that explicitly: "Downstream tools may keep them for tolerance; that is their decision, not this one."

## Next Actions

- [x] Rename the value in `PHASE_RESOLVED`.
- [x] Propagate verbatim to the other nine repos, keeping the cockpit's bundled copy byte-identical to its source (enforced by `tests/test_status_vocabulary.py`).
- [x] Add a regression test over `PHASE_RESOLVED` — [[TST-0002]]; `validate_status_tables()` / `STATUS-TABLE`, in the validator so it runs everywhere the validator does. Verified by inversion on both failure branches, including this exact regression.
- [x] Hoist `PHASE_RESOLVED` and `CLOSED_PHASE_STATUSES` to module scope so the table is reachable at all.
- [x] Extend `STATUS-TABLE` to every other status table in the file — `RESOLVED_STATUSES`, `FEATURE_ACTIVE_STATUSES`, `PLAN_FOLLOWS_FEATURE`. Doing so found two *further* instances of the same ADR-0012 miss, both live bugs; see below.
- [ ] Consider whether ADR-0012's consequence list should be amended to name `PHASE_RESOLVED`, so the record of which surfaces exist is accurate for the next rename.
- [ ] Downstream repos pick up `STATUS-TABLE` on their next `sync-project-os.sh`; only `project-os-dev` and `project-os` carry it today.
