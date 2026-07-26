---
type: "[[task]]"
id: TASK-0072
aliases: ["TASK-0072"]
title: "Fleet rollout: propagate scripts, hooks and the CI workflow to 10 repos; close the MANIFEST seed gap"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: M
due: ""
depends: [TASK-0060, TASK-0061]
blocks: []
related: [REQ-0019, ADR-0009]
tests: []
---

# Fleet rollout: scripts, hooks, CI

## Definition of Done

- [ ] **`.github/workflows/validate-docs.yml` ownership changed from `seed` to `template`** in `tools/sync/MANIFEST.yaml`, or an explicit alternative propagation path is recorded (see Notes — this is the actual gap).
- [ ] `sync-snapshot.py` and `run-tests.py` reach all 10 repos and are verified present and runnable in each.
- [ ] Git hooks reinstalled in every repo (`install-git-hooks.sh` runs post-sync; confirm rather than assume).
- [ ] The CI workflow in every repo runs the generator's `--check` mode.
- [ ] A rollout report records, per repo: sync outcome (up-to-date / fast-forwarded / **skipped as diverged**), and any hand-merges required.
- [ ] Diverged template-owned copies are hand-merged, not `--force`d, unless the divergence is confirmed worthless.

## Steps

- [ ] Fix the manifest ownership; re-read the `seed` list for the same defect in `.prettierrc`, `.markdownlint.jsonc`, `.yamllint.yml`, `link-check.yml`.
- [ ] Dry-run `sync-project-os.py` against all 10 repos; record the divergence table.
- [ ] Sync per repo, validating after each.
- [ ] Confirm hooks and CI actually fire (make a trivial violating commit in one repo and watch it fail).

## Notes

**The gap this task exists for.** `tools/scripts/`, `tools/adapters/`, `tools/instructions/`, `tools/skills/` and `tools/cockpit/` are all `template`-owned, so new scripts propagate automatically. But `.github/workflows/validate-docs.yml` is **`seed`** — *"copied once when missing downstream; never overwritten after that."* All nine downstream repos already have that file, so a CI change made in the template reaches **none of them**, silently. [[TASK-0061-Wire-Generation-Retire-Checks|TASK-0061]] wires `--check` into CI; without this fix that wiring stops at the template.

Seed ownership was the right call when the workflow was a starting point repos were expected to customise. It is the wrong call once the workflow carries enforcement the template owns. If some repos genuinely have local CI customisations, the answer is to split the file (a template-owned reusable workflow, called by a seed-owned local one) rather than to leave enforcement unpropagatable.

**Verify, don't assume.** The sync script reinstalls hooks and regenerates adapters after a non-dry run — but a repo whose copy has diverged is *skipped and reported*, not updated. A rollout that reports "9 skipped" and is read as "9 done" is exactly the failure mode this task's per-repo report exists to prevent.
