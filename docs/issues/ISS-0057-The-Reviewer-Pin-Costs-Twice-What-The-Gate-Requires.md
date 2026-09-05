---
type: "[[issue]]"
id: ISS-0057
aliases: ["ISS-0057"]
title: "The reviewer pin costs twice what the gate requires"
status: fixed
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-09-05
updated: 2026-09-05
component: adapters-hooks
source: ["Edwin, 2026-09-05, in a project-os-cockpit session"]
related: ["[[ISS-0044-The-Adapter-Calls-The-Pinned-Subagent-Model-The-Strongest]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"]
tasks: []
tests: []
---

# The reviewer pin costs twice what the gate requires

## Problem

Every independent review runs on Claude Fable 5.1, which costs twice as much per token as Claude Opus 5, and the review gate does not ask for the more expensive model. [[ADR-0013]] says independence is a clean context, not a model family, so the reviewer's pin is a preference rather than a gate. Edwin asked for the reviewer to default to Opus on 2026-09-05.

The list prices, read from the current model catalogue on 2026-09-05: Fable 5.1 is $10 per million input tokens and $50 per million output; Opus 5 is $5 and $25. Half, on both.

> [!quote] As requested — 2026-09-05 (user:edwin)
> can we make the independent reviewer opus by default, since it is significantly cheaper?

## This reverses part of a two-day-old decision

[[ISS-0044]] moved **both** pins from `claude-opus-5` to `claude-fable-5-1` on 2026-09-03, with Edwin's decision recorded in the note. Its argument was not list price. It was that the prompting guides reported Fable 5.1 "competitive with Opus on cost per task at low effort while scoring higher" — cost per completed task, which counts the tokens a model actually spends, not the price of each one.

Those two measures can disagree. A model at twice the price that finishes in less than half the tokens is cheaper per review. **Neither figure has been measured on this fleet's reviews.** ISS-0044 took the guides' claim on trust and this issue takes list price on trust, and until somebody measures a real review both ways, the honest statement is that the cheaper pin is unknown.

What settles it for now is that Edwin asked, having been given both prices. That is recorded below rather than argued away.

## Scope

The reviewer only. `PLANNER_MODEL` stays at `claude-fable-5-1` because the request named the reviewer, twice, and never the planner. This is worth revisiting on its own: the planner runs at every preflight and the reviewer only at gates, so the planner is almost certainly the larger share of the Fable spend, and moving the cheap half of a bill is a small result.

**It was revisited the same day.** Edwin asked for the planner minutes after this landed, and [[ISS-0058]] moved it. This note is left as written because what it records - that the planner was deliberately held back at this point - is true and is the reason ISS-0058 exists.

## Repro

```bash
cd ~/Dev/repos/project-os
sed -n '62,63p' tools/scripts/generate-adapters.py    # PLANNER_MODEL / REVIEWER_MODEL
grep -n "^model:" .claude/agents/independent-reviewer.md
```

## Expected

`REVIEWER_MODEL` is `claude-opus-5`, the regenerated `independent-reviewer.md` pins it, and all twelve fleet repos carry the same file.

## Actual

Both constants are `claude-fable-5-1`, and all twelve repos carry that pin.

## Evidence

- Verified 2026-09-05: `tools/scripts/generate-adapters.py` is byte-identical across all twelve `SNAPSHOT.yaml`-bearing repos (sha256 prefix `f42762f03ab0`), and so is `.claude/agents/independent-reviewer.md` (`c5ab870594256`). A one-line patch plus a generator run in each repo therefore produces exactly what a template sync plus generator run would produce, without dragging unrelated template drift into the commit.
- `claude-fable-5-1` is a real model id. The installed Claude Code binary (v2.1.261) lists it alongside `claude-opus-5`, so nothing here is broken by an unknown pin.
- The pins did reach the fleet. All twelve repos already carry ISS-0044's `claude-fable-5-1`, so the sync half of that issue worked.

## Next Actions

- [x] Set `REVIEWER_MODEL = "claude-opus-5"` in `~/Dev/repos/project-os/tools/scripts/generate-adapters.py`
- [x] Reword `tools/adapters/claude-code/ADAPTER.md`: it states both pins are `claude-fable-5-1` as of 2026-09-03, which stops being true
- [x] Regenerate and commit in each of the twelve repos
The measurement below is deliberately left open and is tracked as the reason the next pin decision should be a finding rather than an argument:

- [ ] Measure one real review both ways before the next pin decision

## Decision record

> [!note] Decide — 2026-09-05 (user:edwin)
> Move the independent reviewer to Opus 5. Asked for after being shown that Fable is the higher-capability tier and Opus is half the price, and reaffirmed with "make the change upstream and then merge into the downstream projects".
