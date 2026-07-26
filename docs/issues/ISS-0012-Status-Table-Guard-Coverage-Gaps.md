---
type: "[[issue]]"
id: ISS-0012
aliases: ["ISS-0012"]
title: "STATUS-TABLE does not cover every status collection: CLOSED_PHASE_STATUSES can drift green, DESCOPED is still a local, and risks_open carries retired vocabulary"
status: fixed
severity: medium
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
component: tooling
source: ["review:2026-07-26-independent-review-TST-0002"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [ISS-0011, ADR-0012, TST-0002]
tests: [TST-0002]
---

# STATUS-TABLE coverage gaps found in independent review

## Problem

Independent review of [[TST-0002]] / [[CHG-20260726-Phase-Resolved-Declined]] (commit 610eb16, reviewed by model:claude-fable-5) refuted the note's headline claim that "no status table in the validator can drift from the allowed taxonomy". Three status collections in `tools/scripts/validate-docs.py` are outside `validate_status_tables()`'s reach:

1. **`CLOSED_PHASE_STATUSES`** — hoisted to module scope *by the same commit that added the guard*, but registered nowhere: not in `FLAT_STATUS_TABLES`, no explicit check. It holds phase statuses, and drifting it kills `PHASE-CHILDREN` for done phases in exactly the silent way ISS-0011 describes.
2. **`DESCOPED = ("deferred", "cancelled", "superseded")`** — still a *local* tuple inside `validate()` (the FEATURE-REQ check, applied to requirement statuses), contradicting TST-0002's "every status collection is now a module-level constant".
3. **`count("RISK", {"open", "mitigating", "monitoring"})`** in the metrics builder — `mitigating` and `monitoring` are not in `ALLOWED_STATUS["risk"]` (`{open, closed}`), and STATUSES.md explicitly records them as retired ("written once and never, respectively"). A live stale-vocabulary literal surviving in the same file the guard ships in; harmless today only because dead values in a counting filter cannot match.

Lower-severity, same class: the `TERMINAL` map (collection → terminal status) is module-level but unchecked.

## Repro

```
sed -i '' 's/CLOSED_PHASE_STATUSES = ("done", "superseded")/CLOSED_PHASE_STATUSES = ("completed", "superseded")/' tools/scripts/validate-docs.py
python3 tools/scripts/validate-docs.py --self-check   # exits 0, "status tables consistent"
```

`completed` is not a phase status; the mutated validator would never run `PHASE-CHILDREN` against a `done` phase, and `--self-check` stays green.

## Expected

`--self-check` fails on any status collection in the file carrying a value that is not a legal status for the type it is applied to — which is what TST-0002's title and coverage-boundary section claim.

## Actual

Only `PHASE_RESOLVED`, `RESOLVED_STATUSES`, `FEATURE_ACTIVE_STATUSES` and `PLAN_FOLLOWS_FEATURE` are walked. The four collections above are invisible to the guard.

## Evidence

- Review findings recorded on [[TST-0002]] ("Independent review" section) and [[CHG-20260726-Phase-Resolved-Declined]].
- Mutation demonstrated 2026-07-26 on a scratch copy; exit 0 with `validate-docs: self-check OK`.

## Next Actions

- [x] Register `CLOSED_PHASE_STATUSES` in `FLAT_STATUS_TABLES` with `("phase",)` — evidence: `tools/scripts/validate-docs.py` `FLAT_STATUS_TABLES`
- [x] Hoist `DESCOPED` to module scope as `DESCOPED_STATUSES` and register it with `("requirement",)` — evidence: same table; the local inside `validate()` is gone
- [x] Drop `mitigating`/`monitoring` from the `risks_open` filter — now `RISK_OPEN_STATUSES = ("open",)`, module-level and registered. STATUSES.md records both as retired, so re-legalising them was not considered
- [x] Cover `TERMINAL` — via a `TERMINAL_TYPES` sibling mapping each collection to its note type, so the check reports which collection drifted rather than flattening the values and losing that
- [x] Amend TST-0002 and the CHG to match actual coverage — evidence: both notes rewritten, re-reviewed
- [x] Propagate to `project-os` and the fleet — evidence: all 11 repos `--self-check` ok, 0 errors; cockpit bundle byte-identical

## Resolution

Fixed 2026-07-26, in the same session the review found it.

The four named collections are registered, and one thing the review did not ask for was added: a **completeness assertion**. Registration in `FLAT_STATUS_TABLES` is a manual step, and this issue is precisely what a forgotten one costs — an unguarded table reads exactly like a guarded one. So `validate_status_tables` now walks every module-level uppercase tuple of strings and requires each to be either registered or named in `_NON_STATUS_TUPLES`. A new status constant is loud on its first run rather than at the next rename.

That assertion earned its place immediately: it failed on `ID_PREFIXES` the first time it ran, which is the correct behaviour — the allow-list is a record of decisions, not a suppression list.

Verified by inversion, six branches induced and reverted, including this issue's repro verbatim:

| Induced | Reported |
|---|---|
| `CLOSED_PHASE_STATUSES = ("completed", "superseded")` — **this issue, verbatim** | `'completed' … is not an allowed phase status` |
| `DESCOPED_STATUSES` gains `wont-fix` | `'wont-fix' … is not an allowed requirement status` |
| `RISK_OPEN_STATUSES` back to the pre-fix literal | `'mitigating', 'monitoring' … are not allowed risk statuses` |
| `TERMINAL["issues"] = "closed"` (pre-ADR-0008) | `TERMINAL['issues'] contains 'closed' …` |
| `TERMINAL_TYPES` loses a key | `names collection 'requirements', which has no entry in TERMINAL_TYPES` |
| a new unregistered `NEW_GATE_STATUSES` tuple | `is a module-level tuple of strings that no status table registers` |

Each returned exit 1; the restored file returns 0.

## What this issue is really about

ISS-0011 was a rename that missed a table. ISS-0012 is the *fix for ISS-0011* missing a table — and missing one that the same commit had just created. The guard was written, documented as complete, and shipped with a hole in it, and every mechanical check stayed green.

That is worth recording plainly, because it is evidence about a class of work rather than about one file. A guard's own coverage is not self-evident from reading it; the docstring said "covers every status collection in this file" and was wrong at the moment it was written. It took someone trying to break it to find out. Hence the completeness assertion: the check now verifies its own coverage instead of asserting it in prose.
