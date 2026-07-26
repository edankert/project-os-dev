---
type: "[[test]]"
id: TST-0002
aliases: ["TST-0002"]
title: "Status table consistency: no status table in the validator can drift from the allowed taxonomy"
status: passing
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
source: ["ISS-0011", "ISS-0012", "ISS-0013"]
scope: system
kind: automated
level: unit
entrypoint: "tools/scripts/validate-docs.py"
command: "python3 tools/scripts/validate-docs.py --self-check"
last_run: "2026-07-26T21:28Z"
exit_code: 0
requirements: []
features: []
issues: [ISS-0011, ISS-0012, ISS-0013]
tasks: []
artifacts: []
evidence: []
adequacy: "Verified by inversion across three rounds, 2026-07-26: 21 failure branches induced and observed — three reproducing the ISS-0011 misses verbatim, one ISS-0012's, one ISS-0013's, and five confirming the completeness assertion fires on tuple, list, set, frozenset and comprehension-built collections regardless of name case. The metrics rewrite was separately shown behaviour-preserving: identical counts on all 18 metrics across all 11 fleet repos."
related: [ADR-0012, ADR-0010, TST-0001]
reviewed_by: ""
review_date: ""
review_verdict: ""
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
| `CLOSED_PHASE_STATUSES` | flat tuple | `phase` |
| `DESCOPED_STATUSES` | flat tuple | `requirement` |
| `RISK_OPEN_STATUSES` | flat tuple | `risk` |
| `TERMINAL` | collection → terminal status | each value against `TERMINAL_TYPES[collection]` |
| `TEST_RUNNER_STATUSES` | flat tuple | `test` |
| `REQ_UNADVANCED_STATUSES` | flat tuple | `requirement` |
| `METRIC_STATUS_FILTERS` | metric → (prefix, statuses) | each against `METRIC_PREFIX_TYPE[prefix]` |

Flat tables are registered in `FLAT_STATUS_TABLES`, a name → (values, applicable types) map. Adding a status table means adding a row there rather than hand-writing another check.

**And then a third assertion checks the registry itself.** `validate_status_tables` walks every module-level uppercase tuple of strings and requires each one to be either registered or named in `_NON_STATUS_TUPLES`. That is not belt-and-braces; it is the direct lesson of [[ISS-0012]], below. Registration is manual, so it can be forgotten, and a forgotten table reads exactly like a covered one.

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

## Three rounds of the same mistake

Worth stating before the detail, because the pattern is the finding:

| | The miss | Shipped green? |
|---|---|---|
| [[ISS-0011]] | ADR-0012's rename missed three status tables | yes, across a 41-value fleet migration |
| [[ISS-0012]] | the *fix for ISS-0011* missed a table it had just created | yes |
| [[ISS-0013]] | the *guard against ISS-0012* missed a table **type** | yes |

Each time, a coverage claim was written wider than the code, and each time every mechanical check passed. All three were found by an independent reviewer attacking the guard rather than reading it. That is the argument for adversarial review as a gate: the checks cannot audit their own reach, and prose describing their reach is exactly the artifact that keeps being wrong.

## What ISS-0012 taught, and why the coverage table above is not the whole answer

The first version of this check shipped with a hole, and the hole was in a
constant the same commit had just created.

`CLOSED_PHASE_STATUSES` was hoisted to module scope by the ISS-0011 fix and then
not registered in `FLAT_STATUS_TABLES`. Renaming `done` there and nowhere else
left `--self-check` green while `PHASE-CHILDREN` silently stopped firing against
done phases — the exact failure this note's title says it makes impossible,
reintroduced by the fix for it. Two smaller cases came with it: `DESCOPED` was
still a local inside `validate()` while this note claimed every collection was
module-level, and the `risks_open` metric filtered on `{open, mitigating,
monitoring}`, two thirds retired vocabulary, so it had been counting one status
while reading as though it counted three.

None of that was caught by any check. It was caught by an independent reviewer
who tried to break the guard instead of reading its docstring, and the docstring
was the problem: it asserted "covers every status collection in this file" and
was wrong at the moment it was written.

So the completeness assertion exists because **a guard cannot be trusted to
describe its own coverage in prose**. The registry is now checked against the
module rather than against the author's memory. It failed on `ID_PREFIXES` the
first time it ran, which is right — `_NON_STATUS_TUPLES` is a record of
decisions, and being forced to make one is the whole mechanism.

## Coverage boundary

This guards the *validator's own* internal consistency. It does not verify that `ALLOWED_STATUS` matches `STATUSES.md` — `load_allowed_status()` overlays the repo's file at runtime, and the cockpit's `tests/test_status_vocabulary.py` covers the palette surfaces.

It cannot see a status literal written **inside a function**. A local is not in `globals()`, so no amount of walking finds it — `DESCOPED` was exactly that shape until [[ISS-0012]], and `TEST_RUNNER_STATUSES` and `REQ_UNADVANCED_STATUSES` until [[ISS-0013]]. As of ISS-0013 no inline status literal remains in the file, but nothing stops the next one; that case is caught by review or not at all.

At module scope the assertion is type-agnostic and case-agnostic: tuple, list, set and frozenset are all walked, whatever the name looks like. It checked only `tuple` and only `.isupper()` names until ISS-0013, which is how a module-level `set` of statuses evaded the guard against unregistered status collections.

This boundary is stated this precisely because the imprecise version has been wrong twice. See below.

## Independent review (2026-07-26, model:claude-fable-5)

Authored by model:claude-opus-5 (per the commit trailer on 610eb16), reviewed by model:claude-fable-5 — same model family, so this pass is harm reduction, not the cross-vendor independence QUALITY.md asks for; a different-family or human pass is still owed.

**What held up under attack:** all six inversion branches were re-induced independently on a scratch copy and every one failed with exactly the message and exit code this note claims, including the two-errors-one-per-type behaviour for `RESOLVED_STATUSES`; `--self-check` runs clean from a directory with no `SNAPSHOT.yaml` and no `docs/` (genuinely repo-independent); the fleet-wide re-arm numbers reproduce exactly (15 `PLAN-FOLLOWS`: project-os-cockpit 9 + your-health 6; 4 `REQ-PREMATURE`: one each in obsidian-supernote-sync, your-health, your-sudoku, your-trainer; all warnings, zero errors); no issue-typed note in any of the ten repos carries `cancelled` or `superseded`, so the issue-row tightening is safe; and the original regression scenario is confirmed live — your-sudoku's three `declined` issues naming the `done` PHASE-0008 validate clean.

**Why changes-requested — the title claim is refuted by counterexample.** `CLOSED_PHASE_STATUSES` is a status collection (phase statuses), hoisted to module scope *by this very commit*, and `validate_status_tables()` does not walk it: it is not in `FLAT_STATUS_TABLES` and has no explicit check. Demonstrated: mutating it to `("completed", "superseded")` — `completed` is not a phase status — leaves `--self-check` green, and would silently kill `PHASE-CHILDREN` for done phases, which is the exact ISS-0011 failure mode this test says it makes impossible. One-line fix: register it in `FLAT_STATUS_TABLES` with `("phase",)`.

**Secondary findings, same class:** (1) `DESCOPED = ("deferred", "cancelled", "superseded")` is still a *local* status tuple inside `validate()` (FEATURE-REQ, applied to requirement statuses), contradicting this note's "every status collection is now a module-level constant"; (2) the `TERMINAL` map (collection → terminal status) is module-level but unchecked; (3) the metrics filter `count("RISK", {"open", "mitigating", "monitoring"})` carries two values STATUSES.md explicitly retired ("written once and never") — a live stale-vocabulary literal surviving in the same file today, harmless only because dead values in a counting filter cannot match. Either cover these or narrow this note's title and coverage-boundary claim to the four registered tables.

## Independent re-review (2026-07-26, model:claude-fable-5, round two, commit 12a7c70)

Authored by model:claude-opus-5 (commit trailer on 12a7c70), reviewed by model:claude-fable-5 — same model family, so this remains harm reduction, not the cross-vendor independence QUALITY.md asks for; a different-family or human pass is still owed.

**Every round-one finding is verified fixed.** All six ISS-0012 inversion branches were independently re-induced on a scratch copy and each fails with exactly the message and exit code [[ISS-0012]]'s Resolution table claims — including the ISS-0012 repro verbatim (`CLOSED_PHASE_STATUSES` → `completed`), the `TERMINAL_TYPES` missing-key branch, and the new-unregistered-tuple branch. `_NON_STATUS_TUPLES` is correctly scoped (both entries genuinely non-status; `RELATIONSHIP_FIELDS`'s `deferred`/`superseded` are field names). No existing module-level container evades the guard — verified by AST scan of every module-level assignment (`COLLECTION_TYPE`, `PROMOTIONS`, `METRIC_PREFIXES` hold no status values). A registered tuple rebound after registration is caught (the `id()`-based registry is conservative in the right direction), as is a comprehension-built tuple. All 11 fleet validators are byte-identical (`cmp`, including the cockpit bundle) and all ten repos validate OK.

**Why changes-requested again — narrower, and the same shape one level up.** (1) The completeness assertion walks only `tuple`s: a module-level `set`, `frozenset`, `list`, or `dict` of statuses evades it — demonstrated, `NEW_SET_STATUSES = {"bogus", "done"}` leaves `--self-check` green — which refutes this note's "What the assertion covers is the next-most-likely mistake: a new module-level constant that nobody registered" and the singular "That is the remaining gap". (2) The validator docstring still opens with "Covers every status collection in this file" — the exact phrase [[ISS-0012]]'s post-mortem records as "wrong at the moment it was written" — and by that issue's own standard it is still refutable: inline `("passing", "failing")` (TEST-FIELDS) and `("draft", "approved")` (REQ-STALE) drift silently (demonstrated), and `compute_metric_counts` retains nine inline single-status set literals, siblings of the exact `risks_open` literal ISS-0012 hoisted; this note's Procedure section echoes the phrase. (3) The CHG's stale your-sudoku follow-up, flagged in round one in the section directly above it, was left unaddressed in the same rewrite. Findings and the two-line fixes are filed as [[ISS-0013]]; the guard itself is sound for everything that exists in the file today.
