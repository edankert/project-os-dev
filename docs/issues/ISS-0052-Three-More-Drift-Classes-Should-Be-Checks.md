---
type: "[[issue]]"
id: ISS-0052
aliases: ["ISS-0052"]
title: "Three more drift classes should be checks, not sweep findings"
status: open
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
component: tooling
source: ["[[ADR-0026-When-A-Drift-Sweep-Stops]] acceptance criterion 1, decided 2026-09-04", "The ISS-0048 drift sweep, passes 11 and 12"]
related: ["[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]"]
tasks: []
tests: []
---

# Three more drift classes should be checks, not sweep findings

## Problem

[[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] decided that a finding class the sweep keeps rediscovering should become a mechanical check. It named five classes, decided four of them yes, and the first is built (`BASE-STATUS`). The remaining three are here.

Each one is a class an LLM pass found repeatedly and a check can state exactly. Until they exist, the only thing standing between the corpus and this drift is a sweep that now runs once per cadence rather than to exhaustion — which is a deliberate reduction in coverage, and these checks are what pays for it.

## The three

**1. A frontmatter field the validator enforces that no document defines.** Pass 12 found three: `waiver_expires:` (an error when missing, documented nowhere until 2026-09-04), `fixes:` (drives `PARENT-BACKLINK`, absent from `SCHEMAS.md` and from `feature.md`), and `docs/designs/` (`DESIGN-ASSET` and `DESIGN-ORPHAN` only fire inside a directory no document tells an author to create). The check: every frontmatter key the validator reads appears in `SCHEMAS.md`. A reader who follows the schema should never trip a check the schema never mentioned.

**2. A citation that does not resolve, or resolves to something that does not say what the citing file claims.** Twenty-two instances across passes 11 and 12: paths that resolve nowhere, section headings that do not exist, quoted sentences that appear in no file, and bare `ADR-####` references that mean a different decision in each repo. The check: resolve every backticked path and every cited heading against disk. Pass 12's agent ran exactly this sweep by hand, which is the argument for automating it.

**3. An index or README listing fewer entries than its directory holds.** Eight instances. `docs/INDEX.md` omitted `WRITING.md`, `OBSIDIAN.md` and `TESTING.md`; `tools/skills/README.md` omitted two skills; the reference `CLAUDE.md` omitted two more. The check: compare each index against its directory. `adapter-sync/SKILL.md` already makes this a required manual step, which is the tell that it should not be manual.

## Expected

Each class errors at pre-commit and CI, where it costs milliseconds, instead of waiting for a clean-context pass to notice it again.

## Actual

All three are found only by an LLM sweep, at roughly 290k tokens per pass, and only when a pass happens to sample that part of the corpus.

## Evidence

- `BASE-STATUS` in `tools/scripts/validate-docs.py`, the worked precedent: it reproduces the "Features (Open)" defect in milliseconds, and a negative test confirms it fails when the retired filter is reintroduced.
- ADR-0026's class table, with which passes found what.
- `test-pause-rule.sh`, the older precedent: one rule, asserted mechanically across ten named sites.

## Next Actions

- [ ] Check 1, undocumented enforced fields. Needs a list of the frontmatter keys the validator reads, which is derivable from the source.
- [ ] Check 2, unresolvable citations. Land it warning-first if the fleet has violations; the template's count decides (`STATUSES.md`, "Grandfathering").
- [ ] Check 3, stale indexes. Cheapest of the three.
- [ ] Once these exist, re-measure whether the drift dimension still earns a cadence slot. That is the real acceptance test for ADR-0026.

## Sibling search

Siblings found: [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]], the sweep that produced the evidence. Searched `docs/issues/` for: check, validator, mechanical, drift. Filed as one issue rather than three because they share a decision and a rationale; each Next Action is a separable piece of work.

## Risk scan

One hazard, and it is the reason for the grandfathering note above: a new check that errors from day one breaks every downstream repo already violating it. `BASE-STATUS` was safe because the template and this repo both measured zero after the fix. Checks 1 and 2 have not been measured across the fleet and should be, before they error rather than warn.
