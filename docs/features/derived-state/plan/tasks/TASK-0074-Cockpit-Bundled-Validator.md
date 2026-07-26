---
type: "[[task]]"
id: TASK-0074
aliases: ["TASK-0074"]
title: "Cockpit: the bundled validator copy must track every retired and re-severitied check"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: M
due: ""
depends: [TASK-0061]
blocks: []
related: [ADR-0009, ADR-0011, REQ-0019, REQ-0024]
external: "../project-os-cockpit/docs/issues/ISS-0026-Bundled-Validator-Drift.md"
tests: []
---

# Cockpit bundled validator

## Definition of Done

- [ ] `src/project_os_cockpit/validate_docs_bundled.py` carries the same check set as the template validator after `ITEM-STATUS`, `COUNTER` and `METRICS` are retired ([[TASK-0061-Wire-Generation-Retire-Checks|TASK-0061]]).
- [ ] The collapsed `ALLOWED_STATUS` ([[TASK-0054-Validator-Collapsed-Taxonomy|TASK-0054]]) and the severity dispositions ([[TASK-0069-Triage-Validator-Warnings|TASK-0069]]) are reflected there too.
- [ ] **The duplication is addressed structurally, not just re-synced** — a mechanism exists that fails when the two copies diverge (see Notes).
- [ ] The existing 10-line drift is reconciled and its cause identified.

## Steps

- [ ] Diff the bundled copy against the template validator; establish what the 10 lines are and which copy is correct.
- [ ] Decide the structural fix (options in Notes).
- [ ] Apply the check retirements and vocabulary changes to whichever copies survive.
- [ ] Release and propagate the three hops (cockpit → project-os → 9 repos).

## Notes

**The finding.** The cockpit does not call the template's validator — it **bundles its own copy**, `validate_docs_bundled.py`, complete with its own `ALLOWED_STATUS`, its own `FEATURE_REQ_GATE_FROM = "2026-07-25"`, and its own `ITEM-STATUS`/`COUNTER`/`METRICS` checks. So validator logic exists in **three** places across the fleet: the template's `tools/scripts/validate-docs.py`, each downstream repo's synced copy of it, and this bundled copy inside the cockpit package.

**It has already drifted**: 875 lines against the template's 885. That drift predates this phase, which is the point — nothing detected it, and every check change in [[FEAT-0015-Derived-State|FEAT-0015]] and [[FEAT-0017-Enforcement-Severity|FEAT-0017]] would silently widen it. The in-app validation panel would then disagree with pre-commit and CI in the same repo, which is worse than either being wrong alone: a user would see green in the cockpit and red in CI, with no indication which to believe.

Structural options, to be decided:

1. **Import rather than bundle** — the cockpit reads the repo's own `tools/scripts/validate-docs.py` at runtime. One copy per repo, always the version that repo's CI enforces. Risk: the cockpit must tolerate older/newer validator versions across repos.
2. **Generate the bundle** — vendored copy produced by a build step from the template, with a `--check` mode in CI that fails on divergence. Same pattern already used for adapters (`generate-adapters.py --check`), so the machinery and the idiom both exist.
3. **Keep both, add a parity test** — cheapest, and the weakest: it detects drift without preventing it, which is the pattern [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] argues against.

Option 2 fits the repo's existing conventions best. Whichever is chosen, "re-sync it by hand this once" is not a completion criterion — that is what produced the current 10-line gap.
