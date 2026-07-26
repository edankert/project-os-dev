---
type: "[[task]]"
id: TASK-0055
aliases: ["TASK-0055"]
title: "Migrate ~300 notes across 10 repos to the collapsed vocabulary, dry-run first, per-repo commits"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0013-Status-Taxonomy-Collapse]]"
effort: L
due: ""
depends: [TASK-0053, TASK-0054]
blocks: []
related: [ISS-0009, RISK-0001, REQ-0016]
tests: []
---

# Fleet vocabulary migration

## Definition of Done

- [ ] Dry-run mode produces a full per-note diff for every repo, reviewed before any write.
- [ ] All 10 repos migrated; zero out-of-taxonomy statuses remain fleet-wide.
- [ ] One commit per repo, never a single fleet-wide commit.
- [ ] `validate-docs.py` clean per repo before and after; the "before" run recorded so pre-existing findings are distinguishable from migration-induced ones.
- [ ] The `superseded → done|cancelled` mapping applied per the per-repo decision from TASK-0053, with ambiguous cases listed and resolved individually rather than defaulted.
- [ ] `closed → fixed` merged for the 54 affected issues, landing **atomically with** the `VERIFY` gate change from TASK-0056 (see Notes).

## Steps

- [ ] Write the migration script with `--dry-run` as the default and an explicit `--write`.
- [ ] Confirm [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] is resolved before any bulk write (see Notes).
- [ ] Run dry-run across all 10 repos; review every diff; resolve ambiguous `superseded` cases by hand.
- [ ] Migrate repo by repo, validating after each.
- [ ] Re-run `validate-fleet.sh` and record the resulting warning counts.

## Notes

**Do not start before ISS-0007 is decided.** A bulk rewrite touches `updated:` on every note it edits, which re-arms the ADR-0007 `FEATURE-REQ` gate on each one. In repos carrying grandfathered debt (your-trainer 30, your-sudoku 15) that converts dozens of warnings into build failures in a single commit, unrelated to what the migration was for.

**`closed → fixed` must be atomic with the gate change.** The `VERIFY` check currently keys on issue `closed`. Migrating the data first would make 313 issues terminal without ever passing the gate; changing the gate first would fire it on 54 issues mid-migration. Land both in one commit per repo.

**Reversibility is the design constraint.** Per-repo commits exist so a single bad mapping is revertible in isolation. Resist the convenience of one fleet-wide commit — [[RISK-0001-Fleet-Status-Migration|RISK-0001]] is rated high-impact precisely because a wrong mapping validates cleanly and reads as legitimate afterwards.
