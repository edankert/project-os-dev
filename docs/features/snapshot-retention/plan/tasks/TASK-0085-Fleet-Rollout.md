---
type: "[[task]]"
id: TASK-0085
aliases: ["TASK-0085"]
title: "Fleet rollout: ship both halves inert, then opt in one repo at a time, cheapest first"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["fleet measurement 2026-08-04: 12 repos, 3,162 items"]
parent: "[[FEAT-0022]]"
effort: L
due: ""
depends: ["[[TASK-0082]]", "[[TASK-0083]]", "[[TASK-0084]]"]
blocks: []
related: ["[[ADR-0018]]", "[[TASK-0072]]", "[[TASK-0055]]"]
tests: []
---

# Fleet rollout

## Why this needs its own task

`FEAT-0022` originally said only *"TASK-0072's fleet-rollout discipline applies"*. That is insufficient, because this rollout has a property TASK-0072's did not: **the code is shared and the readiness is per-repo.**

`tools/scripts/` is `template`-owned in `tools/sync/MANIFEST.yaml`, so the script itself propagates normally — and a repo with local edits is skipped and reported rather than silently overwritten, which is the protection this needs. But if either half arms on arrival:

- the prune fires in repos whose 657 drifted titles have not been triaged, destroying narrative `TASK-0084` exists to preserve;
- and every repo runs `sync-snapshot --check` in CI via `validate-docs.yml`, so **all twelve go red simultaneously** until each commits a pruned snapshot. That is a flag day across twelve repos for a change that has no deadline.

## The mechanism: inert by default, opt in per repo

Both halves ship disabled and are enabled per repo by that repo's own snapshot:

- **prune** runs only where the retention window key is present; absent → no-op (`TASK-0082`).
- **title derivation** ships in report mode; overwrite is enabled per repo (`TASK-0083`).

Consequences worth stating: the fleet can carry the code for weeks with zero behaviour change; CI stays green throughout; each repo's migration is one reviewable commit; and a repo nobody touches again keeps today's behaviour forever rather than silently changing.

## The worklist

Measured 2026-08-04 across all twelve repos. "Held" is entries kept back by non-empty `note:` under ADR-0018 rule 3.

| # | repo | items | title drift | terminal | held | prunable |
|---:|---|---:|---:|---:|---:|---:|
| 1 | project-os *(template)* | 0 | 0 | 0 | 0 | 0 |
| 2 | project-os-bench | 29 | 0 | 0 | 0 | 0 |
| 3 | obsidian-supernote-sync | 34 | 1 | 3 | 0 | **3** |
| 4 | edankert.com | 64 | 1 | 46 | 0 | 46 |
| 5 | articles | 55 | 3 | 1 | 0 | 1 |
| 6 | yourtrainer-mcp | 99 | 3 | 69 | 2 | 67 |
| 7 | your-sudoku | 254 | 29 | 97 | 0 | 97 |
| 8 | project-os-dev | 159 | 25 | 77 | 8 | 69 |
| 9 | your-applications.com | 237 | 25 | 120 | 10 | 110 |
| 10 | your-health | 573 | 17 | 274 | 34 | 240 |
| 11 | project-os-cockpit | 593 | 140 | 360 | 88 | 272 |
| 12 | **your-trainer** | 1,065 | **413** | 709 | **0** | **709** |
| | **fleet** | **3,162** | **657** | **1,756** | **142** | **1,614** |

The work is concentrated: `your-trainer` and `project-os-cockpit` hold **84% of the drift** and **61% of the pruning**.

## Order, and why

Ascending cost, so defects surface where they are cheap to fix.

1. **project-os, project-os-bench** — nothing to prune and nothing drifted. These prove the *inert* path and the key mechanism, not the prune.
2. **obsidian-supernote-sync** — the first genuine prune in the fleet, and it removes **three entries**. This is the one to inspect line by line; a bug here costs nothing and a bug at step 12 costs 709 entries.
3. **edankert.com, articles, yourtrainer-mcp** — 7 drifted titles between them.
4. **your-sudoku, project-os-dev, your-applications.com, your-health** — 96 drift, 516 prunable. `your-health` is the first repo where `note:` holds a meaningful number back (34), so it exercises rule 3 in anger.
5. **project-os-cockpit** — 140 drift, 88 held. Also the repo where `ISS-0026`/`TASK-0074` found a *bundled* copy of the validator that had drifted from its source; check whether anything bundles the sync script the same way **before** enabling here.
6. **your-trainer** — last. Largest snapshot, most drift, zero holds, and the 10 orphan titles that exist nowhere but the snapshot.

## Per-repo procedure

One commit per repo, following `TASK-0055`'s fleet-migration pattern:

1. `sync-project-os.sh` to pick up the (inert) script.
2. Run the drift report; triage per `TASK-0084` for this repo only.
3. Enable title overwrite; add the retention window key.
4. Let the prune fall out; **inspect the diff** rather than trusting it.
5. `sync-snapshot.py --check` and `validate-docs.sh` clean.
6. Record before/after snapshot size.

## Definition of Done

- [ ] Both halves confirmed inert on arrival: a repo that syncs the script and changes nothing shows a clean `--check`.
- [ ] All twelve repos migrated, in the order above, each as its own reviewable commit.
- [ ] Before/after sizes recorded per repo, so the predicted −28% in `your-trainer` is verified rather than assumed — this feature has already had one unmeasured size claim retracted (`ISS-0030`).
- [ ] The bundled-copy question settled for `project-os-cockpit` before it is enabled there.
- [ ] A note on whether the gating keys stay permanently or are removed once all twelve are migrated. Leaving a permanent opt-out that everyone has opted into is the [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] shape in configuration form, and should be decided rather than defaulted.
