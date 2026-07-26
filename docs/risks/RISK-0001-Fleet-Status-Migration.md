---
type: "[[risk]]"
id: RISK-0001
aliases: ["RISK-0001"]
title: "The fleet status migration rewrites ~300 notes across 10 repos; a bad mapping silently relabels delivered work"
status: closed
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: ["review:2026-07-25-fleet-state-audit"]
likelihood: medium
impact: high
mitigation: []
related: [FEAT-0013, TASK-0055, ISS-0009, ADR-0008]
---

# Fleet status migration

## Description

[[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]] rewrites `status:` values in roughly 300 notes across 10 repos: 71 tasks at `superseded`, 50 issues at `done`, 30 at `pending`, 54 issues merging `closed → fixed`, plus test, phase, plan and reference drift.

Status is the field every downstream surface keys on — Bases views, cockpit bands, metric counts, and the validator's own gates. A wrong mapping does not fail loudly; it relabels an item into a state that reads as legitimate, and the note continues to validate.

The single largest bucket is the most ambiguous. **71 tasks sit at `superseded`**, which has never been a legal task status, so no convention says what it meant. It could mean the work was abandoned (`cancelled`) or absorbed into other work that shipped (`done`). Those map to opposite sides of the delivery line: `cancelled` resolves scope without claiming delivery, `done` claims it. Guessing globally will be wrong for one of the two populations, and the error is invisible afterwards.

A second hazard is mechanical rather than semantic. `sync-project-os.sh` and any bulk rewrite touch `updated:` across many notes at once — which, per [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]], re-arms the ADR-0007 `FEATURE-REQ` gate on every note it touches. A migration run over a repo carrying grandfathered debt can convert dozens of warnings into build failures in a single commit, with no relation to what the migration was for.

## Mitigation

- Dry-run mode producing a full per-note diff, reviewed before any write.
- Per-repo commits, never a single fleet-wide commit, so one bad mapping is revertible in isolation.
- The `superseded → ?` mapping established per repo from the notes' own bodies and git context, never guessed globally; ambiguous cases listed and decided explicitly rather than defaulted.
- Migration sequenced **after** [[TASK-0054-Validator-Collapsed-Taxonomy|TASK-0054]] so the validator can verify the result rather than the migration being trusted.
- Clean `validate-docs.py` run per repo before and after; the "before" run establishes which findings pre-date the migration.
- The ADR-0007 cutover decision ([[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]]) taken **before** any bulk rewrite, so migration does not detonate the gate as a side effect.

## Triggers

- Post-migration counts of `done`/`cancelled` per repo that differ materially from the pre-migration `superseded` split.
- A repo where the dry-run diff exceeds its total note count for a type (indicates a mapping applied too broadly).
- `FEATURE-REQ` or `REQ-BOXES` errors appearing during migration in a repo that had only warnings before.
- Cockpit or Bases views showing empty bands after migration (a value fell outside every filter).

## Outcome (2026-07-25) — realised and passed

The migration ran: **190 notes and 34 snapshot entries across 10 repos**. Every mitigation held.

- Dry-run reviewed before any write; the script refuses (not warns) any mapping that would move a completed work item out of completion — and it **fired once**, on a `reference` at `complete`. The guard was type-agnostic; scoping it to work-item types was the fix, and the refusal is what surfaced the flaw.
- The `superseded`-on-tasks bucket — the 71-note case this risk named as most dangerous — turned out to need **no mapping at all**: the notes carry `superseded_by:` and ADR-0008 was amended to add the status instead. The riskiest population was removed from the migration entirely.
- Post-migration invariant: **2,420 / 2,420 completed work items still terminal, 0 regressions.**
- ISS-0007 was resolved *before* any bulk rewrite, so the ADR-0007 gate never detonated on the `updated:` churn.

Closed. The residual — 53 flagged items that changed how they *read* (50 issue `done`→`fixed`, 3 change notes) — is recorded in CHG-20260725 rather than treated as invisible.
