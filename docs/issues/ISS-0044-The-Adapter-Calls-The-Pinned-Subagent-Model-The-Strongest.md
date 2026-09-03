---
type: "[[issue]]"
id: ISS-0044
aliases: ["ISS-0044"]
title: "The adapter calls the pinned subagent model the strongest available"
status: open
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: adapters-hooks
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 1.4", "https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc"]
related: ["[[ADR-0013-Independence-Is-Clean-Context]]", "[[FEAT-0002-Hook-Contracts]]"]
tasks: []
tests: []
---

# The adapter calls the pinned subagent model the strongest available

## Problem

`generate-adapters.py` pins both the planner and the reviewer subagent to `claude-opus-5`, and ADAPTER.md explains the choice as "the strongest available Claude model". That was true when it was written. Claude Fable 5.1 now exists, and the prompting guides report it competitive with Opus on cost per task at low effort while scoring higher. So the adapter states a fact about the world that has expired, and a reader takes the pin as settled rather than as a choice with a review date.

The same paragraph tells the reader to spend the highest available effort on review. The guides say review accuracy holds at lower effort.

## Repro

```bash
cd ~/Dev/repos/project-os
sed -n '60,61p' tools/scripts/generate-adapters.py    # PLANNER_MODEL / REVIEWER_MODEL
sed -n '156p' tools/adapters/claude-code/ADAPTER.md   # "the strongest available Claude model"
```

## Expected

Either the pins name the model actually preferred today, or the adapter describes them as a deliberate choice revisited at each model release, with a pointer to the effort guidance.

## Actual

The pins name `claude-opus-5` and the prose asserts that this is the strongest model available.

## Evidence

Verified in the template on 2026-09-03. `.claude/settings.json` sets the session model to `opus`.

## Next Actions

- [ ] Retarget `PLANNER_MODEL` and `REVIEWER_MODEL` in `tools/scripts/generate-adapters.py` to `claude-fable-5-1` (decided 2026-09-03, record below).
- [ ] Re-run the generator and check the regenerated `.claude/agents/*.md` into the same commit.
- [ ] Reword ADAPTER.md: the pins are a choice revisited per model release, not "the strongest available", and the reviewer does not need the highest effort the harness allows.
- [ ] Downstream repos pick the pins up at the next template sync plus generator run; note that in the change note.

## Decision record

> [!note] Decide — 2026-09-03 (user:edwin)
> Retarget the sub-agent.

## Sibling search

No sibling found (searched `docs/issues/` for: model, pin, adapter, subagent, opus). Not a member of the restatement family the other three contradictions belong to: this is a fact that expired, not a rule stated twice.

## Risk scan

Run against the LIFECYCLE.md triggers. One trigger fires if the pins are retargeted: the pinned model is an external dependency and a version constraint, and every downstream repo inherits it through the sync plus a generator run. No `RISK-*` yet, because the retarget is not decided; if it is taken, the risk scan runs again at that point.
