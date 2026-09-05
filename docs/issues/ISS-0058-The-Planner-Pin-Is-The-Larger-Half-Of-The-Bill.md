---
type: "[[issue]]"
id: ISS-0058
aliases: ["ISS-0058"]
title: "The planner pin is the larger half of the bill"
status: fixed
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-09-05
updated: 2026-09-05
component: adapters-hooks
source: ["Edwin, 2026-09-05, in a project-os-cockpit session, immediately after ISS-0057"]
related: ["[[ISS-0057-The-Reviewer-Pin-Costs-Twice-What-The-Gate-Requires]]", "[[ISS-0044-The-Adapter-Calls-The-Pinned-Subagent-Model-The-Strongest]]", "[[ADR-0013-Independence-Is-Clean-Context]]"]
tasks: []
tests: []
---

# The planner pin is the larger half of the bill

## Problem

`PLANNER_MODEL` is still `claude-fable-5-1` at twice the per-token price of `claude-opus-5`, and the planner runs far more often than the reviewer. Preflight fires whenever a prompt implies work; review fires only at the gates `QUALITY.md` names. [[ISS-0057]] moved the reviewer an hour ago and said so in its Scope section: moving the cheap half of a bill is a small result.

> [!quote] As requested — 2026-09-05 (user:edwin)
> also change the planner to opus.

## Why this is a separate note

ISS-0057 is committed and accurate about what happened: the reviewer moved, the planner deliberately did not, because the request named the reviewer twice and never the planner. Widening that note now would erase the fact that the planner was held back and then released, which is the part a later reader needs. Two notes, in the order the two decisions were made.

## What is different about the planner

Nothing about the planner is a gate, so there is no equivalent of [[ADR-0013]] to check against. The planner classifies work, allocates IDs, updates the snapshot and writes notes; it is a capability question and a cost question, not a correctness one.

That makes the unmeasured claim from ISS-0057 matter *more* here, not less. [[ISS-0044]] argued for Fable on cost per task at low effort, and planning is exactly the kind of short, well-scoped task where a model that thinks less per answer could plausibly win on total tokens. Nobody has run a preflight both ways.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -n "^PLANNER_MODEL\|^REVIEWER_MODEL" tools/scripts/generate-adapters.py
grep -n "^model:" .claude/agents/planner.md
```

## Expected

`PLANNER_MODEL` is `claude-opus-5`, the regenerated `planner.md` pins it, and all twelve fleet repos carry the same file.

## Actual

`PLANNER_MODEL` is `claude-fable-5-1` in all twelve repos.

## Evidence

Verified 2026-09-05, after ISS-0057 landed: `.claude/agents/planner.md` is byte-identical across all twelve repos, as is `tools/scripts/generate-adapters.py`. The same two-file copy plus generator run that carried ISS-0057 carries this.

## Next Actions

- [x] Set `PLANNER_MODEL = "claude-opus-5"` in `~/Dev/repos/project-os/tools/scripts/generate-adapters.py`
- [x] Rewrite the pin comment block and the `ADAPTER.md` sentence, which both now describe a split that no longer exists
- [x] Regenerate and commit in each of the twelve repos

Both pins are now Opus 5 and no Fable model is left in the adapter surface, so the measurement ISS-0057 keeps open has lost its cheap comparison point. It stays open there and is not duplicated here:

- [ ] (on [[ISS-0057]]) Measure one real review both ways before the next pin decision

## Decision record

> [!note] Decide — 2026-09-05 (user:edwin)
> Move the planner to Opus 5 as well. Asked for directly, minutes after the reviewer change landed, with the cost figures already on the table.
