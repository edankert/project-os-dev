---
type: "[[change]]"
id: CHG-20260905-Both-Subagents-Run-On-Opus
aliases: ["CHG-20260905-Both-Subagents-Run-On-Opus"]
title: "The planner moves to Opus 5 as well, leaving no Fable pin in the adapter surface"
status: merged
owner: user:edwin
created: 2026-09-05
updated: "2026-09-05"
source: ["user:edwin, a project-os-cockpit session, 2026-09-05"]
commit: ""
pr: ""
impacts: ["tools/scripts/generate-adapters.py", "tools/adapters/claude-code/ADAPTER.md", ".claude/agents/planner.md"]
issues: ["[[ISS-0058-The-Planner-Pin-Is-The-Larger-Half-Of-The-Bill]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[CHG-20260905-The-Reviewer-Runs-On-Opus]]", "[[ISS-0057-The-Reviewer-Pin-Costs-Twice-What-The-Gate-Requires]]", "[[ISS-0044-The-Adapter-Calls-The-Pinned-Subagent-Model-The-Strongest]]"]
---

# Both subagents run on Opus

## Summary

The `planner` subagent now runs on Claude Opus 5, in all twelve repos. Together with [[CHG-20260905-The-Reviewer-Runs-On-Opus]] a few hours earlier, both pinned subagents are Opus 5 and no Fable model remains anywhere in the adapter surface.

This is the larger of the two savings. Preflight fires whenever a prompt implies work; review fires only at the gates `QUALITY.md` names, so the planner is the pin that runs most.

Nothing here is a correctness question. [[ADR-0013]] governed the reviewer's pin and said the model is a preference rather than a gate; the planner has no equivalent gate at all. It classifies work, allocates IDs, updates the snapshot and writes notes, and the choice of model is cost and capability only.

## What changed

- `tools/scripts/generate-adapters.py` — `PLANNER_MODEL` is `claude-opus-5`. The comment block above the constants described a planner/reviewer split that existed for a few hours; it now describes two equal pins and states the debt below.
- `tools/adapters/claude-code/ADAPTER.md` — the same correction to the sentence naming the pins.
- `.claude/agents/planner.md` — regenerated.

`.claude/agents/independent-reviewer.md` was already correct and did not change.

## The debt this creates

[[ISS-0044]] moved both pins to Fable on 2026-09-03 arguing cost **per task** at low effort. [[ISS-0057]] moved the reviewer back arguing cost **per token**. Those measure different things and can point opposite ways, and neither has been run on this fleet's work.

Planning is exactly where the ISS-0044 argument was most plausible: short, well-scoped tasks are where a model that thinks less per answer can win on total tokens. Moving the planner on list price alone therefore closes the question by fiat rather than by measurement, and with no Fable pin left there is no longer a cheap way to run the comparison — it now costs a deliberate experiment rather than a look at two live pins.

That is a fair trade for halving a sticker price on the pass that runs most, and it is recorded here so the next pin decision knows what it is missing. The action stays open on [[ISS-0057]] and is not duplicated.

## How it reached the fleet

The same route as the reviewer change, for the same reason: the two changed template files were copied from `~/Dev/repos/project-os` into each repo and the generator re-run there, rather than a full template sync that would have carried unrelated pending changes. Inputs were byte-identical fleet-wide beforehand, so the outputs are too.
