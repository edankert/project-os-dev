---
type: "[[issue]]"
id: ISS-0054
aliases: ["ISS-0054"]
title: "Nine residue findings have no open item carrying them"
status: open
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
component: docs
source: ["Found by the independent review of REQ-0027, 2026-09-04"]
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]"]
tasks: []
tests: []
---

# Nine residue findings have no open item carrying them

## Problem

[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]] closed `fixed` on a 14-row residue table. Five of those rows are fixed or filed elsewhere. The other nine are real, unfixed, and recorded only inside a closed note.

That is a gap in how the new rule was applied, not in the rule. [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] says a sweep records its residue and that a decision owed becomes an `ISS-*`. The residue was recorded; the items were not opened. Once retention prunes the closed entry and `focus.note` moves on, nothing at an open status points at these.

## The nine

Row numbers are ISS-0048's residue table.

1. `sync-snapshot.py` derives `goal:` while four documents say it leaves that alone, and `SNAPSHOT.md` contradicts itself between lines 61 and 79. **Needs a decision on which behaviour is right.**
2. `SNAPSHOT.md` still tells authors to write a feature's `tests:` and a test's `features:`, both removed by ADR-0032 in favour of `covers:`.
3. `docs/requirements/README.md` says `implements:` may hold features, scripts, tests or workflows; `STATUSES.md` says at most one feature, and REQ-OWNER errors on two.
6. `metrics.counts` computes 18 keys; `SNAPSHOT.md` defines 16.
7. `SNAPSHOT.md`'s required-keys list omits `template:`, which two hooks branch on, plus `docs_system:` and two `retention.*` keys.
8. `CONTEXT.md`'s edit policy files `docs/requirements/` and `docs/risks/` under "do not change casually" while LIFECYCLE requires the agent to create and update exactly those, and omits five more directories.
12. `SCHEMAS.md` defines no fields for `design.md`, `design-system.md` or `surface.md`, three shipped templates; no `SUR` counter exists though `SUR` is a live prefix.
13. The Bases "Open" views use three different exclusion strategies; `implemented` appears in an "All (Open)" view, and `deferred` appears in none though `SNAPSHOT.md` calls it active.
14. `compass_artifact_wf-84fa61ff-...md` sits at the template root with no frontmatter, type or ID, and is the source of claims quoted in the instruction files — including the quiescence rule ADR-0026 removed.

Rows 1, 3, 6, 7, 8 and 12 share a shape: a document tells a reader something the code does not do.

## Expected

Each surviving finding is carried by an item at an open status, or is explicitly declined with a reason.

## Actual

They live in a table inside a `fixed` note, which no status check reaches and retention will eventually prune from the snapshot.

## Resolution

Triaged 2026-09-04 against user:edwin's rule — a duplicate is a defect when the copies disagree, and tolerated when they agree.

**Fixed** (template `ef1f29f`), because they disagreed: row 1 (`goal:` derivation, the contradiction confirmed empirically), row 2 (`SNAPSHOT.md` on the edges ADR-0032 removed), row 3 (`implements:`), row 8 (`CONTEXT.md`'s edit policy against LIFECYCLE), row 13 (`implemented` inside an "Open" view), and the two READMEs that turned a mandatory rule into a preference.

**Left in place**, because they agree: rows 6, 7 and 12 are incomplete lists rather than disagreements — `metrics.counts` defines 16 of 18 keys, `SNAPSHOT.md`'s required-keys list omits `template:`, `SCHEMAS.md` has no section for three shipped templates. Nothing states a rule twice and differently; a reader is under-served, not misled. Under the owner's rule these are not defects, and they are recorded here rather than fixed.

**Still open**, one row: row 14, the `compass_artifact_...md` research report at the template root with no frontmatter, type or ID. Not a duplicated rule at all — a placement question, and the source of claims quoted inside the instruction files including the quiescence rule ADR-0026 removed.

## Next Actions

- [ ] Row 14: move the research report under `docs/reference/` as a `reference` note, or delete it if its claims are now carried by ADR-0026 and ADR-0013.
- [ ] Consider whether closing a sweep should require its residue rows to be filed, not merely written down. This issue is the evidence that recording is not the same as carrying, and `docs-audit/SKILL.md` step 7 could say so.

## Sibling search

Sibling: [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]], which this carries the remainder of. Searched `docs/issues/` for: residue, drift, restatement. Filed as one issue rather than nine because they arrived together and several may be declined together; each Next Action row is separable.

## Risk scan

No new dependency, env var, path or credential. The hazard is the one this issue exists to stop: findings that decay because nothing open points at them.
