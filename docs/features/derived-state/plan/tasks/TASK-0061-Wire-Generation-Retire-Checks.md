---
type: "[[task]]"
id: TASK-0061
aliases: ["TASK-0061"]
title: "Wire generation into pre-commit and CI; delete ITEM-STATUS, COUNTER and METRICS"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: M
due: ""
depends: [TASK-0060]
blocks: [TASK-0065]
related: [ADR-0009, REQ-0019]
tests: []
---

# Wire generation, retire the sync checks

## Definition of Done

- [ ] Pre-commit runs the generator and stages the result, alongside the existing validator hook.
- [ ] CI runs `--check` and fails on divergence.
- [ ] `ITEM-STATUS`, `COUNTER` and `METRICS` deleted from `validate-docs.py` — deleted, not disabled.
- [ ] `--fix-metrics` removed; its job is now the generator's.
- [ ] LIFECYCLE's "Atomic Sync Rule" and "Counter Integrity" rules removed — they instruct an agent to do what the generator now does.
- [ ] Per-repo rollout, not a single fleet sync.
- [ ] A hand-edited snapshot is still detected as divergence by `--check` rather than silently overwritten.

## Steps

- [ ] Extend `tools/scripts/hooks/pre-commit`; confirm ordering (generate, then validate, so the validator sees final content).
- [ ] Update `.github/workflows/validate-docs.yml`.
- [ ] Delete the three checks and their tests.
- [ ] Update `QUALITY.md` ("Documentation Fidelity"), `LIFECYCLE.md`, `SNAPSHOT.md`.
- [ ] Roll out one repo at a time, validating after each.

## Notes

**Delete rather than disable.** A check kept as dead code invites re-enabling against a model where its premise no longer holds. These three detect two copies of state disagreeing; after generation there is one copy, and the checks would be comparing the generated file to itself.

**Hook ordering matters.** Generate first, then validate — otherwise the validator inspects the pre-generation file and passes on content the commit will not contain.

**Keep `--check` permanently available.** It is what lets a hand-edited snapshot surface as an error rather than being quietly reverted by the next generation run, which would look like the tool eating someone's work.
