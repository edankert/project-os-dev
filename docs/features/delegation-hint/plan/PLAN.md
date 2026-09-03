---
type: "[[plan]]"
title: "Delivery plan — the hooks, and their overlap with FEAT-0021"
status: done
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"]
implements: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"]
related: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[Prompting-Guide-Review-2026-09-03]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — the hooks, and their overlap with FEAT-0021

## Where the work lands

`~/Dev/repos/project-os`: two hook scripts, `HOOKS.md`, `ADAPTER.md`, the adapter generator, one template and two skills.

## The overlap that has to be settled first

[[FEAT-0021-Serve-Orientation-Answer-Lookup]] is in the backlog, and [[TASK-0080]] rewrites the SessionStart hook to emit the in-flight slice instead of a reminder. [[TASK-0103]] rewrites the per-prompt hint to serve focus state. Both serve state, and done independently they serve it twice per session — once at start and once on every prompt. TASK-0080's own note records the budget problem: one repo's slice is 11,573 tokens.

**The division this plan proposes:** SessionStart serves the slice once (FEAT-0021). The per-prompt hint carries only what changes within a session — the current item, its status, and whether the state calls for the planner or the reviewer — in a few lines, never the slice. [[TST-0007]] asserts the upper bound so the hint cannot quietly grow into the slice.

That division is a proposal, not a decision. If the owner would rather merge the two, this feature's [[TASK-0103]] should move into FEAT-0021 instead.

## Sequence

1. **[[TASK-0102]]** is independent of everything and can go first; it is a message change in one hook.
2. **[[TASK-0103]]** after [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]], which renames HC-008 and rewrites the same contract line in `HOOKS.md`.
3. **[[TASK-0104]]** touches the generator's hint text and planner prompt; it lands with or after TASK-0103.
4. **[[TASK-0105]]** is independent.
5. The harness behind [[TST-0007]] is written with TASK-0102, so the second and third tasks land against an existing test.

## What ADAPTER.md must not be allowed to become

The adapter's routing table says preflight runs in the planner subagent. [[TASK-0103]] makes that conditional. If the table is not updated in the same commit, this work creates a fifth contradiction of exactly the kind [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]] is filed about.
