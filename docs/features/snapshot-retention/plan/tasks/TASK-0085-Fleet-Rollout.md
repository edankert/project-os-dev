---
type: "[[task]]"
id: TASK-0085
aliases: ["TASK-0085"]
title: "Fleet rollout: ship both halves inert, then opt in one repo at a time, dogfood repo first and the largest last"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["fleet measurement 2026-08-04: 12 repos, 3,164 items"]
parent: "[[FEAT-0022]]"
effort: L
due: ""
depends: ["[[TASK-0082]]", "[[TASK-0083]]", "[[TASK-0084]]"]
blocks: []
related: ["[[ADR-0018]]", "[[TASK-0072]]", "[[TASK-0055]]"]
tests: []
---

# Fleet rollout

## What someone actually does

FEAT-0022 edits **one file** — `tools/scripts/sync-snapshot.py` in the template — which then copies into twelve repos. But the code is one thing and the readiness is twelve things: each repo has its own drifted titles to migrate before its snapshot can safely be pruned.

So the change ships **switched off**. It arrives everywhere and does nothing. Then, one repo at a time, someone:

1. pulls in the new script — it is inert
2. runs the migration that records that repo's old snapshot titles (`TASK-0084`)
3. switches the feature on for that repo — enable title overwrite, add the retention window key
4. looks at the resulting diff before committing
5. commits

Twelve times, in an order that puts the risky repos last. That is the whole task. Everything below is the worklist and the argument for the order.

## Why it cannot simply arm on arrival

`tools/scripts/` is `template`-owned in `tools/sync/MANIFEST.yaml`, so the script propagates normally, and a repo with local edits is skipped and reported rather than silently overwritten. But if either half starts working the moment it lands:

- the prune fires in repos whose titles have not been migrated, deleting text that exists nowhere else;
- and every repo runs `sync-snapshot --check` in CI via `validate-docs.yml`, which fails as soon as the committed file differs from what the script would now produce — so **all twelve go red the same day**, for a change with no deadline.

Shipping inert removes both problems and costs nothing: the fleet can carry the code for weeks with zero behaviour change, and a repo nobody touches again keeps today's behaviour indefinitely.

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
| 3 | **project-os-dev** *(dogfood)* | 161 | 26 | 77 | 8 | 69 |
| 4 | obsidian-supernote-sync | 34 | 1 | 3 | 0 | 3 |
| 5 | edankert.com | 64 | 1 | 46 | 0 | 46 |
| 6 | articles | 55 | 3 | 1 | 0 | 1 |
| 7 | yourtrainer-mcp | 99 | 3 | 69 | 2 | 67 |
| 8 | your-sudoku | 254 | 29 | 97 | 0 | 97 |
| 9 | your-applications.com | 237 | 26 | 120 | 10 | 110 |
| 10 | your-health | 573 | 17 | 274 | 34 | 240 |
| 11 | project-os-cockpit | 593 | 140 | 360 | 88 | 272 |
| 12 | **your-trainer** | 1,065 | **413** | 709 | **0** | **709** |
| | **fleet** | **3,164** | **659** | **1,756** | **142** | **1,614** |

The work is concentrated: `your-trainer` and `project-os-cockpit` hold **84% of the drift** and **61% of the pruning**.

## Order, and why

Two principles, and they pull in different directions. *Fewest entries at risk* says start with the smallest repo. *Fastest detection* says start where someone is actually watching. The second wins for the first real migration, because a defect nobody notices is worse than a defect that costs three entries.

1. **project-os, project-os-bench** — nothing drifted, nothing to prune. These prove the code stays **inert**, which is the property everything else depends on.
2. **project-os-dev** — the first repo with real content, and deliberately so. This is where the template is developed and where its validator runs dozens of times a day, so a defect here is found within minutes by whoever caused it. 26 drifted titles is one sitting's work, and its 8 `note:` holds exercise ADR-0018 rule 3 early rather than leaving it untested until `your-health`.
3. **obsidian-supernote-sync, edankert.com, articles, yourtrainer-mcp** — 8 drifted titles between them, and the smallest genuine prunes in the fleet. Cheap confirmation that the migration works somewhere nobody is watching.
4. **your-sudoku, your-applications.com, your-health** — 72 drift, 447 prunable. `your-health` carries 34 `note:` holds, the largest population outside the cockpit.
5. **project-os-cockpit** — 140 drift, 88 holds. Also the repo where `ISS-0026`/`TASK-0074` found a *bundled* copy of the validator that had drifted from its source; settle whether anything bundles the sync script the same way **before** enabling here.
6. **your-trainer** — last. Largest snapshot, 413 drifted titles, 709 prunable, zero holds, and the 8 orphan titles that exist nowhere but the snapshot.

An earlier draft ordered this purely by blast radius, which put `project-os-dev` eighth. That was wrong: it is the dogfooding repo, and postponing it meant the fleet's own maintainers would be among the last to encounter any defect.

## Per-repo procedure

One commit per repo, following `TASK-0055`'s fleet-migration pattern:

1. `sync-project-os.sh` to pick up the (inert) script.
2. Run `TASK-0084`'s migration for this repo: record its old snapshot titles to `docs/reference/`. No per-item judgement.
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
