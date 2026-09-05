---
type: "[[change]]"
id: CHG-20260905-The-Reviewer-Runs-On-Opus
aliases: ["CHG-20260905-The-Reviewer-Runs-On-Opus"]
title: "The independent reviewer runs on Opus 5; the planner stays on Fable 5.1"
status: merged
owner: user:edwin
created: 2026-09-05
updated: "2026-09-05"
source: ["user:edwin, a project-os-cockpit session, 2026-09-05"]
commit: ""
pr: ""
impacts: ["tools/scripts/generate-adapters.py", "tools/adapters/claude-code/ADAPTER.md", ".claude/agents/independent-reviewer.md"]
issues: ["[[ISS-0057-The-Reviewer-Pin-Costs-Twice-What-The-Gate-Requires]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ISS-0044-The-Adapter-Calls-The-Pinned-Subagent-Model-The-Strongest]]", "[[ADR-0013-Independence-Is-Clean-Context]]"]
---

# The reviewer runs on Opus

## Summary

Independent reviews now run on Claude Opus 5 instead of Claude Fable 5.1, in all twelve repos. Opus 5 lists at $5 per million input tokens and $25 per million output; Fable 5.1 lists at $10 and $50. Every review gate therefore costs half of what it did, on list price.

Nothing about the gate objects to this. [[ADR-0013]] says independence is a clean context and a separate session, not a different model, so the reviewer's pin has been a preference since that decision landed. The agent file already tells the reviewer that sharing a model with the author is expected rather than a defect.

**The planner did not move.** `PLANNER_MODEL` is still `claude-fable-5-1`. The request named the reviewer, so only the reviewer changed. This is the smaller half of the bill: the planner runs at every preflight and the reviewer only at gates.

## What changed

- `tools/scripts/generate-adapters.py` — `REVIEWER_MODEL` is `claude-opus-5`, and the comment block above the constants explains the split instead of asserting both pins are Fable.
- `tools/adapters/claude-code/ADAPTER.md` — the sentence that read "As of 2026-09-03 both are `claude-fable-5-1`" now names the two pins separately and says which figure is unmeasured.
- `.claude/agents/independent-reviewer.md` — regenerated. `model:` and the `reviewed_by:` value it instructs the reviewer to record both become `claude-opus-5`.

Future notes will therefore carry `reviewed_by: model:claude-opus-5`. Existing notes keep whatever model actually reviewed them; nothing was rewritten.

## How it reached the fleet

Not by a template sync. `tools/scripts/` and `tools/adapters/` are `template` in `tools/sync/MANIFEST.yaml`, and a full sync would have brought every other pending template change with it. Instead the two changed files were copied from `~/Dev/repos/project-os` into each repo and the generator re-run there.

That is provably the same result for this change, and the proof was taken before the edit: `generate-adapters.py` was byte-identical across all twelve repos (sha256 prefix `f42762f03ab0`), `.claude/agents/independent-reviewer.md` likewise (`c5ab870594256`), and `ADAPTER.md` in all eleven downstream repos matched `project-os` at HEAD (`945364da9438`). Identical inputs, identical generator, identical output.

## What is still open

Which pin is cheaper **per review** is unmeasured, and this change does not settle it. [[ISS-0044]] moved both pins to Fable two days earlier on the opposite argument — that Fable 5.1 is competitive on cost per task at low effort while scoring higher — which counts tokens spent rather than price per token. A model at twice the price that finishes in under half the tokens is the cheaper reviewer. Nobody has run a real review both ways on this fleet. [[ISS-0057]] carries that measurement as an open action, so the next pin decision can be a finding rather than a third argument between two unmeasured numbers.

## Not included

`tools/scripts/close-out-commit.sh` exists only in `project-os-cockpit`; FEAT-0055 was never upstreamed. The eleven other repos were committed with explicit-path `git add`, which is the same discipline by hand.
