---
type: "[[change]]"
id: CHG-20260726-Phase-Resolved-Declined
aliases: ["CHG-20260726-Phase-Resolved-Declined"]
title: "ADR-0012's rename completed in all three status tables it missed — PHASE_RESOLVED fixed fleet-wide, REQ-PREMATURE and PLAN-FOLLOWS un-deadened, and STATUS-TABLE added so it cannot recur"
status: merged
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
source: ["downstream:your-sudoku/ISS-0096"]
commit: ""
pr: ""
impacts: ["tools/scripts/validate-docs.py", "project-os", "project-os-cockpit", "7 downstream repos"]
issues: [ISS-0011]
features: []
tests: [TST-0002]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: [ADR-0012, ADR-0008]
---

# PHASE_RESOLVED resolves on `declined`

## Summary

[[ADR-0012]] renamed the issue status `wont-fix` → `declined` and called it a pure rename. It listed the surfaces to migrate:

> "Every palette surface changes: `statuses.py`, `validate-docs.py`'s **ALLOWED_STATUS**, `base.css`, `cockpit.css`, `cockpit.js`, the Electron renderer, and STATUSES.md."

`validate-docs.py` holds a **second** status table that the list does not name: `PHASE_RESOLVED`, the map the `PHASE-CHILDREN` gate uses to decide whether a child note resolves its phase's scope. `ALLOWED_STATUS` was migrated; `PHASE_RESOLVED` kept `wont-fix`.

The result was a gate that resolved on a value no issue can hold and refused the one it can. An issue deliberately closed as no-action could not name a `done` phase — authoring the relationship the way `STATUSES.md` describes it, on the child in `phase:`, reported the closed phase as having unresolved children.

```diff
     PHASE_RESOLVED = {
         "task": {"done", "cancelled", "superseded"},
-        "issue": {"fixed", "wont-fix", "cancelled", "superseded"},
+        "issue": {"fixed", "declined", "cancelled", "superseded"},
         "requirement": {"implemented", "retired", "cancelled", "superseded"},
```

Found downstream in `your-sudoku` (its `ISS-0096`) while rebuilding that repo's phase registry: three `declined` iOS-parity issues belonged to a closed `PHASE-0008` and could not say so. See [[ISS-0011]] for the full analysis.

## Impact

- **`declined` now resolves a phase's scope**, as `STATUSES.md` has described since ADR-0012. Repos that worked around this by recording the relationship on the phase side only can now author it on the child, which is what `PHASE-CHILDREN` actually reads.
- **No repo's validation result changed.** All ten were clean before and after; the defect was latent everywhere except `your-sudoku`, since it only bites a repo that has both a closed phase and a declined issue belonging to it.
- **Nothing was loosened.** This restores the gate's intended strictness rather than relaxing it: before the fix, `wont-fix` was dead weight and `declined` was wrongly treated as unresolved.

## Files changed (11 across 10 repos)

Applied verbatim, one match per file, verified programmatically:

| Repo | File |
|---|---|
| project-os-dev | `tools/scripts/validate-docs.py` |
| project-os | `tools/scripts/validate-docs.py` |
| project-os-cockpit | `tools/scripts/validate-docs.py` |
| project-os-cockpit | `src/project_os_cockpit/validate_docs_bundled.py` |
| edankert.com | `tools/scripts/validate-docs.py` |
| obsidian-supernote-sync | `tools/scripts/validate-docs.py` |
| your-applications.com | `tools/scripts/validate-docs.py` |
| your-health | `tools/scripts/validate-docs.py` |
| your-sudoku | `tools/scripts/validate-docs.py` |
| your-trainer | `tools/scripts/validate-docs.py` |
| yourtrainer-mcp | `tools/scripts/validate-docs.py` |

The cockpit's bundled copy is a verbatim bundle, not a fork, enforced by `tests/test_status_vocabulary.py::test_bundled_validator_matches_the_canonical_one`. Both cockpit files were patched identically and `diff` confirms them byte-identical.

## Deliberately not changed

- **No repo was force-synced.** Each got the surgical change; see the note on `your-sudoku` below.
- **The cockpit's `ALLOWED_STATUS`** still carries the full legacy vocabulary. ADR-0012 sanctions that explicitly: "Downstream tools may keep them for tolerance; that is their decision, not this one."
- **No repo was force-synced at the time.** Each got the surgical one-line change; `your-sudoku` was then 146 lines behind upstream (predating the `PLAN-STATE` / `PLAN-ID` checks), and rolling a real sync into a one-word fix would have hidden it. That sync was done separately the same day — see the follow-up below.

## Documentation Coverage (All Types Considered)

- features: not-applicable — a defect fix, no new capability
- requirements: not-applicable
- tasks: not-applicable — single-edit fix, tracked by the issue
- issues: new — [[ISS-0011]]
- tests: new — [[TST-0002]], the `STATUS-TABLE` guard. Before it, `PHASE_RESOLVED` was referenced by no test in any repo, which is why this shipped green
- workflows: not-applicable
- decisions: not-applicable — this completes [[ADR-0012]] rather than deciding anything new
- risks: not-applicable
- changes: new — this note
- snapshot: updated — `items.issues.ISS-0011`, `items.tests.TST-0002`, `counters.ISS`, `counters.TST`, `counters.CHG.last_date`

## Verification

- `bash tools/scripts/validate-docs.sh` run in all ten repos: **OK** in every one.
- The 11 patched files were confirmed to contain exactly one match of the old line before rewriting; a fleet-wide re-grep afterwards found zero surviving `wont-fix` inside any `PHASE_RESOLVED` block, and confirmed all 11 files that define the map were reached.
- Cockpit bundle byte-identical to its source (`diff -q`), so the drift test holds.

## Second change: the regression guard (same day)

The rename was the fix. The reason it was *possible* is that `PHASE_RESOLVED` was a local inside the check function, reachable by no test in any repo — so a second change followed:

- `PHASE_RESOLVED` and `CLOSED_PHASE_STATUSES` **hoisted to module scope**, beside `ALLOWED_STATUS`.
- New `validate_status_tables()` runs **first in `validate()`**, before any repo state is read, asserting that every note type in `PHASE_RESOLVED` exists in `ALLOWED_STATUS` and every status value in it is allowed for that type. Violations report `ERROR [STATUS-TABLE]`.
- The issue row **tightened** to `{fixed, declined}` — `cancelled` and `superseded` are not allowed issue statuses, and the new check correctly rejects them. This reverses a "deliberately not changed" from the first pass; the test made the case. Confirmed safe first: no issue note in any of the ten repos carries either value.
- Module docstring's invariant list updated to name `STATUS-TABLE`.

It lives in the validator rather than a separate suite because `project-os-dev` has no pytest harness, and this way it runs wherever `validate-docs` runs — hooks, pre-commit, CI, every repo. Recorded as [[TST-0002]].

A new `--self-check` flag runs `validate_status_tables()` alone, with no `SNAPSHOT.yaml` and no repo, and is what [[TST-0002]]'s `command:` executes. That was not the first design: the note initially pointed at `validate-docs.sh --quiet` and **deadlocked**. That command reports every repo error, so the moment `run-tests.py` stamped the note `failing`, the `VERIFY` gate on [[ISS-0011]] — fixed, linking a non-passing test — became one more error, and no later run could ever return 0. A test whose command observes its own result cannot converge. Worth remembering as a general rule for ADR-0010 test notes: scope `command:` to the invariant the note names, and leave "the whole repo validates" to [[TST-0001]].

Checked against the `ALLOWED_STATUS` **constant**, not `load_allowed_status()`'s per-repo overlay: both tables ship in the same file, so their agreement is an internal invariant a downstream repo's taxonomy customisation must neither break nor mask.

**Scope of this second change: `project-os-dev` and `project-os` only.** The two are byte-identical and are the template pair; the eight other repos pick `STATUS-TABLE` up on their next `sync-project-os.sh`. The one-line `declined` fix is already in all of them.

### Verified by inversion

Both failure branches induced deliberately and reverted:

| Induced | Result |
|---|---|
| `PHASE_RESOLVED["issue"] = {"fixed", "wont-fix"}` (the exact ISS-0011 regression) | `ERROR [STATUS-TABLE] ... resolves on 'wont-fix', which is not an allowed issue status` — FAIL |
| `"epic": {"done"}` added to the map | `ERROR [STATUS-TABLE] ... names note type 'epic', which has no entry in ALLOWED_STATUS` — FAIL |
| restored | OK |

Separately confirmed the hoist did not change `PHASE-CHILDREN`: the new validator run against `your-sudoku` (three `declined` issues on a closed `PHASE-0008`) reports no `PHASE-CHILDREN` error, while temporarily re-homing an `open` issue onto that phase still produces one.

## Third change: STATUS-TABLE extended to every status table (same day)

Extending the check to the file's other status collections was expected to be bookkeeping. It found **two further instances of the same ADR-0012 miss**, both live:

- **`REQ-PREMATURE` was dead for the case it exists to catch.** It compared feature statuses against an inline `("in-progress", "in-review", "done")` literal, written out twice. Post-ADR-0012 the first two cannot occur, so "requirement still draft but the feature is already being implemented" could only fire once the feature was `done` — never mid-build.
- **`PLAN-FOLLOWS` never fired at all.** Its `follows` map was keyed by feature status on the same two retired values, so `follows.get(parent_status)` returned `None` for every actively-built feature and the guarded `if expected:` skipped silently. This one shipped *in the same commit as ADR-0012* — the PLAN checks were written against the vocabulary that commit was retiring.

Both became module-level constants with corrected values (`FEATURE_ACTIVE_STATUSES`, `PLAN_FOLLOWS_FEATURE`), and `RESOLVED_STATUSES` moved up beside them. `validate_status_tables` now walks all four:

| Table | Checked against |
|---|---|
| `PHASE_RESOLVED` | each key's values, against that type |
| `RESOLVED_STATUSES` | `task` and `feature` — both types it is applied to |
| `FEATURE_ACTIVE_STATUSES` | `feature` |
| `PLAN_FOLLOWS_FEATURE` | keys against `feature`, values against `plan` |

`RESOLVED_STATUSES` and `FEATURE_ACTIVE_STATUSES` are registered in `FLAT_STATUS_TABLES`, so adding a table means adding a row rather than remembering to write another check. `plan` was also added to the `ALLOWED_STATUS` constant — it was consumed by `validate_plan_notes` through `load_allowed_status()` but missing from the defaults, and is needed here to check `PLAN_FOLLOWS_FEATURE`'s values at all.

### What re-arming those checks surfaced

Measured across the ten repos immediately afterwards. All **warnings** — no repo's error count changed, nothing breaks:

| Check | Warnings | Where |
|---|---|---|
| `PLAN-FOLLOWS` | 15 | project-os-cockpit 9, your-health 6 — plans still `active`/`draft` under features closed months ago |
| `REQ-PREMATURE` | 4 | obsidian-supernote-sync, your-health, your-sudoku, your-trainer — requirements at `draft` while their feature is mid-build |

Six inversion branches were induced and reverted, three reproducing the three real misses verbatim; recorded on [[TST-0002]].

## Independent review (2026-07-26, model:claude-fable-5)

Authored by model:claude-opus-5 (commit trailer on 610eb16), reviewed by model:claude-fable-5 — same model family; this is harm reduction, not the cross-vendor independence QUALITY.md requires, and a different-family or human pass is still owed.

**Verified:** the one-word `PHASE_RESOLVED` fix and the tightened `{fixed, declined}` row are present and identical in all 11 fleet files (10 repos + the cockpit bundle, which is byte-identical to its source); the only surviving `wont-fix` in any fleet validator is a doc comment; no issue-typed note anywhere in the fleet carries `cancelled`/`superseded`; all six inversion branches reproduce verbatim; `--self-check` needs no repo; the re-arm numbers (15 `PLAN-FOLLOWS`, 4 `REQ-PREMATURE`, warnings only) reproduce exactly; your-sudoku's declined-issues-on-closed-phase scenario now validates clean.

**Why changes-requested:** the heading "STATUS-TABLE extended to every status table" is refuted by counterexample — `CLOSED_PHASE_STATUSES`, hoisted by this same commit, is walked by nothing: mutating it to a non-status leaves `--self-check` green and would silently disable `PHASE-CHILDREN` for done phases, the exact ISS-0011 failure mode. `DESCOPED` (FEATURE-REQ) also remains a local status tuple, and the `risks_open` metrics filter still carries the retired `mitigating`/`monitoring` values. Fix is one line (register `CLOSED_PHASE_STATUSES` in `FLAT_STATUS_TABLES` with `("phase",)`) plus either covering or explicitly descoping the others; details on [[TST-0002]].

**Stale follow-up (round one, now resolved):** the your-sudoku note below asserted present-tense that the repo was 146 lines behind with plan notes failing `PLAN-ID`. That stopped being true in its commit `3ba52ec`. Ticked and rewritten in round three — it survived round two's rewrite, three lines below the review section that flagged it, which is its own small lesson about editing around a finding rather than acting on it.

## Independent re-review (2026-07-26, model:claude-fable-5, round two, commit 12a7c70)

Authored by model:claude-opus-5 (commit trailer on 12a7c70), reviewed by model:claude-fable-5 — same model family; this remains harm reduction, not the cross-vendor independence QUALITY.md requires, and a different-family or human pass is still owed.

**Verified:** every [[ISS-0012]] Next Action is done as evidenced — `CLOSED_PHASE_STATUSES`, `DESCOPED_STATUSES` (the local is gone), and `RISK_OPEN_STATUSES` registered in `FLAT_STATUS_TABLES`; `TERMINAL` covered via `TERMINAL_TYPES`; all six inversion branches re-induced independently and each fails with the claimed message and exit 1; the completeness assertion fires on a newly-added unregistered tuple and on a registered tuple rebound after registration; all 11 fleet files byte-identical (`cmp`, including `src/project_os_cockpit/validate_docs_bundled.py`); `validate-docs.sh` OK in all ten repos.

**Why changes-requested again:** three residuals, filed as [[ISS-0013]], all cheap. The completeness assertion sees only `tuple`s, so a module-level `set`/`frozenset`/`list`/`dict` of statuses evades it while [[TST-0002]] says it covers "a new module-level constant that nobody registered" (refuted by demonstration); the validator docstring retains the "covers every status collection in this file" phrase that ISS-0012's own post-mortem branded, and it remains refutable via the inline `("passing", "failing")` and `("draft", "approved")` tuples plus the surviving inline metric-set literals; and this note's your-sudoku follow-up checkbox — flagged as stale in the round-one section directly above — still asserts, present-tense, two claims that are now false. The shipped code is sound for everything that exists in the file today; the request is to make the boundary prose exact (or widen the walker to match it) and to stop this note carrying a false present-tense claim.

## Independent re-review (2026-07-26, model:claude-fable-5, round three, commit 4943af3)

Authored by model:claude-opus-5 (commit trailer on 4943af3), reviewed by model:claude-fable-5 — same model family; this remains harm reduction, not the cross-vendor independence QUALITY.md requires, and a different-family or human pass is still owed.

**Verified:** every [[ISS-0013]] Next Action is done on the merits — all nine inversion branches re-induced independently and caught (the set-shaped repro verbatim, frozenset, list, lowercase name, comprehension-built tuple, both hoisted-literal drifts, metric-filter drift, and the prefix-map removal for prefixes carrying real filters); the metrics rewrite independently shown behaviour-preserving (old `compute_metric_counts` at 12a7c70 vs new, run against all 11 repos: all 18 metrics identical; key order changed but both consumers are order-insensitive; corrupt → `ERROR [METRICS]` → `--fix-metrics` → clean exercised end-to-end); all 12 fleet files byte-identical including the cockpit bundle; all 11 repos validate 0, `--self-check` 0, `sync-snapshot --check` 0; cockpit vocabulary suite 24/24; the your-sudoku checkbox tick below is legitimate.

**Why changes-requested a third time — filed as [[ISS-0014]]:** (1) the ISS-0013 fix commit **doubled the validator's second half** — `validate-docs.py` went 1514 → 2560 lines, lines 1560–2560 a verbatim duplicate of 556–1556 appended after the `if __name__` block, dead as a script and identical on import, shipped byte-identical to all 12 fleet files and mentioned in no note; (2) the bolded claim **"no inline status literal remains in the file" is false** — `(("tests", {"passing"}), ("changes", {"merged"}))` sits inline in `validate()` (line 1446) plus at least eight single-status comparisons; (3) the walker's boundary prose is still a shade wider than the code — a module-level **dict** of statuses, an **underscore-prefixed** name, a **nested** tuple and an **empty** collection all evade `--self-check` (demonstrated), against a docstring saying "every module-level string collection" and a TST-0002 sentence saying "type-agnostic … whatever the name looks like". The substance of the fix is real; the requested change is to un-double the file and, for the fourth time, make the coverage sentence exactly as wide as the code.

## Follow-ups

- [ ] Consider amending [[ADR-0012]]'s consequence list to name `PHASE_RESOLVED`, so the record of which surfaces exist is accurate for the next rename.
- [x] `your-sudoku` should run `sync-project-os.sh` — done 2026-07-26 (its commit `3ba52ec`): validator now byte-identical to project-os's, and the one plan note carrying an ID was migrated by `tools/scripts/migrate-plan-ids.py`. Repo validates with 0 errors.

## Follow-up: ISS-0012

Independent review of this change (2026-07-26, model:claude-fable-5) refuted its central claim. The guard did not cover every status table: `CLOSED_PHASE_STATUSES` — hoisted to module scope by this very change — was registered nowhere, so mutating it left `--self-check` green while `PHASE-CHILDREN` silently stopped firing. Two smaller gaps came with it (`DESCOPED` still a local, `risks_open` filtering on retired vocabulary).

Fixed the same day as [[ISS-0012]], which also added a completeness assertion so the registry is checked against the module rather than against prose. Corrected coverage is recorded in [[TST-0002]]; the claim in this note's summary should be read as describing the state after that follow-up, not before it.

The sequence is worth keeping visible: a change that fixed a missed-table bug shipped with a missed table of its own, and every mechanical check passed. That is the argument for adversarial review as a gate, not a formality.

## Follow-up: ISS-0013 (round three)

Round two of review accepted every round-one fix and then broke the new guard: the completeness assertion shipped checking only `tuple`, and only names passing `.isupper()`, so a module-level `set` of statuses walked straight past the thing whose whole job is catching unregistered status collections.

Three rounds, three versions of the same mistake — a coverage claim written wider than the code. ISS-0011 was a rename that missed a table. ISS-0012 was the fix for ISS-0011 missing a table it had just created. ISS-0013 was the guard against ISS-0012 missing a *type* of table. Each shipped green.

Fixed in [[ISS-0013]]: the walker takes tuple/list/set/frozenset and ignores case; the last two inline literals and the eight remaining inline metric filters are hoisted and registered; and the docstring now names its boundary exactly — module scope — because the imprecise version has been wrong twice.

## Follow-up: ISS-0014 (round four)

Round three found something rounds one and two had not: **the ISS-0013 commit silently doubled the validator.** Lines 1560–2560 were a byte-for-byte duplicate of 556–1556, appended after `sys.exit(main())` — inert when run as a script, so the validator, the self-check, the cockpit suite and eleven repos all passed over it, and it propagated to all twelve fleet files.

The cause was ad-hoc string surgery on the source during the metrics rewrite. `ast.parse` confirmed the result was valid Python, which a doubled file is. That is the lesson worth keeping: a syntax check is not a structure check.

Round three also refuted ISS-0013's "no inline status literal remains" (one was left inside `validate()`, now hoisted as `REVIEW_SETTLED_STATUSES`) and defeated the widened walker three more ways — a module-level `dict`, an underscore-prefixed name, a nested container. All closed, and the type tables are now asserted too, which immediately found that the live `decision` note type had no `ALLOWED_STATUS` entry.

Four rounds, four versions of one mistake: a coverage claim written wider than the code, agreed with by every mechanical check, caught only by a reviewer attacking the guard. Recorded in [[ISS-0014]].
