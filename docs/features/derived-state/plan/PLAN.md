---
type: "[[plan]]"
status: done
parent: "[[FEAT-0015-Derived-State]]"
implements: [REQ-0019, REQ-0020, REQ-0021]
related: []
---

# Plan: Derived state

Everything lands in `~/Dev/repos/project-os` (template). Rollout is per-repo and reversible: the generator is run in `--check` mode against each repo's existing hand-written snapshot **before** it is given write authority anywhere, so any divergence is a finding rather than a silent rewrite.

- [ ] [[TASK-0060-Snapshot-Generator|TASK-0060]] — build sync-snapshot.py (items/counters/metrics, deterministic order, --check)
- [ ] [[TASK-0061-Wire-Generation-Retire-Checks|TASK-0061]] — pre-commit + CI wiring; delete ITEM-STATUS/COUNTER/METRICS
- [ ] [[TASK-0062-Derive-Deferral-Bookkeeping|TASK-0062]] — derive origin + parent deferred lists; retire 3 DEFER checks, keep DEFER-SCOPE
- [ ] [[TASK-0063-Retention-In-Generator|TASK-0063]] — retention as generator policy; drop manual pruning from close-out
- [ ] [[TASK-0064-Evidence-Driven-Transitions|TASK-0064]] — focus implies doing; close-out stamps done
- [ ] [[TASK-0065-Rewrite-Snapshot-Sync-Skill|TASK-0065]] — snapshot-sync skill rewritten against the generator
- [ ] [[TASK-0072-Fleet-Rollout-Scripts-Hooks-CI|TASK-0072]] — fleet rollout; close the MANIFEST `seed` gap on the CI workflow
- [ ] [[TASK-0074-Cockpit-Bundled-Validator|TASK-0074]] — the cockpit's bundled validator copy must track the retired checks (external)

## Delivery sequence

1. TASK-0060 first and alone. Until the generator reproduces all 10 existing snapshots under `--check` with only explainable diffs, nothing else in this feature is safe to start.
2. TASK-0061, 0062, 0063 in parallel once the generator is trusted — each retires a different hand-maintained surface.
3. TASK-0064 last of the mechanical work: it writes to *notes*, not just the snapshot, so it carries the highest blast radius and should land on a system that is otherwise already stable.
4. TASK-0065 closes out the skill surface.

## Dependencies

- **Hard:** TASK-0060 blocks 0061, 0062, 0063, 0065.
- **Soft:** [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]] should land first — generating a snapshot from a vocabulary that is about to change means regenerating everything twice.
- **Rollout:** TASK-0072 and TASK-0074 close the two propagation gaps found on 2026-07-25 — the CI workflow is `seed`-owned (never overwritten downstream), and the validator has a third copy bundled inside the cockpit package that has already drifted.

## Open questions

- **Retention and generation interact badly if naive.** Pruning a terminal item out of `items.*` while its note still exists means the generated file is not a pure function of `docs/**` — it also depends on the retention window and therefore on the current date. Either the window is expressed in commits/counts rather than wall-clock, or generation is not reproducible across days. Decide in TASK-0063.
- **How much does `focus` really imply?** Setting `focus.task` mid-session would flip a note to `doing` and dirty the working tree on every context switch. Options: stamp only at commit time; stamp only forward (never back out of `doing`); or make it opt-in per repo.
- **`origin:` derivation is lossy.** Git history recovers the previous parent, but only if the deferral was committed as a distinct change. For the 22 currently-deferred notes, derive once and freeze the result rather than recomputing from history on every run.
