---
type: "[[test]]"
id: TST-0002
aliases: ["TST-0002"]
title: "Status table consistency: no status table in the validator can drift from the allowed taxonomy"
status: passing
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
source: ["ISS-0011"]
scope: system
kind: automated
level: unit
entrypoint: "tools/scripts/validate-docs.py"
command: "python3 tools/scripts/validate-docs.py --self-check"
last_run: "2026-07-26T21:28Z"
exit_code: 0
requirements: []
features: []
issues: [ISS-0011]
tasks: []
artifacts: []
evidence: []
adequacy: "Verified by inversion 2026-07-26: six failure branches induced and observed, three of them reproducing the three real ISS-0011 misses verbatim."
related: [ADR-0012, ADR-0010, TST-0001]
---

# Status table consistency

## Purpose

`validate-docs.py` ships `ALLOWED_STATUS`, the taxonomy — and then **four more** collections of status literals that are compared against it: `PHASE_RESOLVED` (`PHASE-CHILDREN`), `RESOLVED_STATUSES` (`VERIFY`, `REQ-STALE`), `FEATURE_ACTIVE_STATUSES` (`REQ-PREMATURE`) and `PLAN_FOLLOWS_FEATURE` (`PLAN-FOLLOWS`).

A value renamed in one and not the other fails in the worst available way — silently. The gate does not error; it simply stops recognising the renamed status, and every repo keeps validating green. That is not hypothetical: [[ADR-0012]] renamed the issue status `wont-fix` → `declined`, its consequence list named `ALLOWED_STATUS` but not `PHASE_RESOLVED`, and the miss survived a 41-value fleet migration across ten repos. It surfaced only when a downstream repo happened to need a `declined` issue to name a closed phase ([[ISS-0011]]) — and once this check was written, it turned out the same rename had been missed in **two further tables**, both of which had been quietly dead ever since.

This test makes that class of drift impossible to ship.

## Procedure

Automated, and part of the validator itself rather than a separate suite — so it runs wherever `validate-docs` runs: session hooks, pre-commit, CI, and every repo carrying the validator.

`validate_status_tables()` runs first in `validate()`, before any repo state is read, and is also reachable on its own via `--self-check`, which is what this note executes. For every status collection in the file it asserts:

1. Every note type it is compared against has an entry in `ALLOWED_STATUS`.
2. Every status value in it is a member of `ALLOWED_STATUS[type]`.

Violations report as `ERROR [STATUS-TABLE]`.

### Tables covered

| Table | Shape | Checked against |
|---|---|---|
| `PHASE_RESOLVED` | type → set | each key's values, against that type |
| `RESOLVED_STATUSES` | flat tuple | `task` and `feature` — both types it is applied to |
| `FEATURE_ACTIVE_STATUSES` | flat tuple | `feature` |
| `PLAN_FOLLOWS_FEATURE` | feature status → plan statuses | keys against `feature`, values against `plan` |

`RESOLVED_STATUSES` and `FEATURE_ACTIVE_STATUSES` are registered in `FLAT_STATUS_TABLES`, a name → (values, applicable types) map. Adding a status table means adding a row there, not remembering to hand-write another check — the failure mode this note exists to prevent is precisely "a table nobody thought to check".

## Design notes

- **Checked against the `ALLOWED_STATUS` constant, not `load_allowed_status()`'s per-repo overlay.** Both tables ship in the same file, so their agreement is an internal invariant of the validator. A downstream repo customising its own `STATUSES.md` must not be able to turn this red — and equally must not be able to hide a real mismatch by widening its own allowed set.
- **One-directional on purpose.** Every value in a table must be a real status; a status need not appear in any table. `deferred`, `open` and `triage` are all legal and all correctly absent from `PHASE_RESOLVED`.
- **Every covered table was hoisted to module scope.** `PHASE_RESOLVED` was a local inside its check function; `PLAN_FOLLOWS_FEATURE` was a local named `follows`; `FEATURE_ACTIVE_STATUSES` was not a constant at all, just an inline tuple written out twice. None could be reached by anything. That is the structural reason [[ISS-0011]] went unnoticed three times over — a constant no test can reach is a constant no test guards.
- **`plan` was added to the `ALLOWED_STATUS` constant** (`draft`, `active`, `done`, `superseded`, per `STATUSES.md`). It was consumed by `validate_plan_notes` through `load_allowed_status()` but missing from the defaults, so a repo whose `STATUSES.md` lacked a `[[plan]]` section would get an empty allowed set and see every plan flagged. Needed here so `PLAN_FOLLOWS_FEATURE`'s values can be checked at all.
- **The issue row was tightened** from `{fixed, declined, cancelled, superseded}` to `{fixed, declined}`. `cancelled` and `superseded` are not allowed issue statuses, so they were dead entries that this check correctly rejects. Confirmed safe first: no issue note in any of the ten repos carries either value.
- **`command:` is `--self-check`, not the full validator — and that was learned the hard way.** This note first pointed at `validate-docs.sh --quiet`, the same command as [[TST-0001]]. That deadlocked: the command reports *every* repo error, so once `run-tests.py` stamped this note `failing`, the `VERIFY` gate on [[ISS-0011]] (fixed, linking a non-passing test) became one more error, and no subsequent run could return 0. A test whose command observes its own result cannot converge. `--self-check` runs `validate_status_tables()` alone, needs no `SNAPSHOT.yaml` and no repo at all, and leaves "the whole repo validates" where it belongs, on [[TST-0001]]. The general rule: scope a test note's command to the invariant it names.

## Expected results

- Exit 0 while both tables agree.
- Non-zero the moment they do not.

## Adequacy (who verifies this test?)

A test that cannot fail does not guard. Verified by inversion on 2026-07-26 — six branches induced deliberately, observed, and reverted. Three of them reproduce the three real misses:

| Induced | Reported |
|---|---|
| `PHASE_RESOLVED["issue"] = {"fixed", "wont-fix"}` — **miss 1, verbatim** | `'wont-fix' … is not an allowed issue status` |
| `"epic": {"done"}` added to `PHASE_RESOLVED` | `names note type 'epic', which has no entry in ALLOWED_STATUS` |
| `RESOLVED_STATUSES` gains `"fixed"` | two errors, one per applicable type (`task`, `feature`) |
| `FEATURE_ACTIVE_STATUSES = ("in-progress", "in-review", "done")` — **miss 2, verbatim** | `'in-progress', 'in-review' … are not allowed feature statuses` |
| `PLAN_FOLLOWS_FEATURE` re-keyed on `in-progress`/`in-review` — **miss 3, verbatim** | `PLAN_FOLLOWS_FEATURE keys contains 'in-progress', 'in-review' …` |
| `PLAN_FOLLOWS_FEATURE` maps `done → passing` | `'passing' … is not an allowed plan status` |

Each returned exit 1; the restored file returns 0.

Separately confirmed that hoisting the tables did not change behaviour: the new validator run against `your-sudoku` — which has three `declined` issues naming a closed `PHASE-0008` — reports no `PHASE-CHILDREN` error, while temporarily re-homing an `open` issue onto that phase still produces one.

## What the extension found

Covering the other tables was not bookkeeping. Two of the three were **actively broken**, and both had been silently dead since [[ADR-0012]]:

- `FEATURE_ACTIVE_STATUSES` (then an inline literal, written out twice) matched `in-progress`/`in-review`/`done`, so `REQ-PREMATURE` could only fire once a feature was already `done` — never while it was being built, which is the entire case the warning exists for.
- `PLAN_FOLLOWS_FEATURE` (then the local `follows`) was keyed the same way, so `follows.get(parent_status)` returned `None` for every actively-built feature and `PLAN-FOLLOWS` never fired at all.

Fixing them re-armed both checks. Measured across the ten repos immediately afterwards: **15 `PLAN-FOLLOWS` and 4 `REQ-PREMATURE`** warnings that had been suppressed — including plans still `active` under features closed months ago, and four requirements sitting at `draft` while their feature was mid-build. All warnings; no repo's error count changed.

## Coverage boundary

This guards the *validator's own* internal consistency. It does not verify that `ALLOWED_STATUS` matches `STATUSES.md` — `load_allowed_status()` overlays the repo's file at runtime, and the cockpit's `tests/test_status_vocabulary.py` covers the palette surfaces.

It also cannot see a status literal that is not in a registered table. The defence there is structural rather than analytical: every status collection is now a module-level constant, registered in `FLAT_STATUS_TABLES` or checked explicitly, so evading this check means writing a fresh inline literal — which is what the comment on each constant warns against.
