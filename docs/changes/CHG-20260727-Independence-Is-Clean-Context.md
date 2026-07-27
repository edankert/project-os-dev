---
type: "[[change]]"
id: CHG-20260727-Independence-Is-Clean-Context
title: "Independent review gates on clean context, not model family; all phase-routed agents move to Opus"
status: merged
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["[[ADR-0013]]", "[[TASK-0077]]"]
commit: ""
pr: ""
impacts: ["tools/instructions/QUALITY.md", "tools/skills/independent-review/SKILL.md", "tools/scripts/generate-adapters.py", ".claude/agents/"]
issues: []
features: ["[[FEAT-0018]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0013]]", "[[TASK-0077]]", "[[ISS-0016]]"]
---

# Independence is clean context

## Summary

`QUALITY.md`'s independent-review gate changes from **"a different model family or a human"** to **"a clean context, and never the authoring session"**. A human pass still satisfies it and remains the strongest option. Self-review remains forbidden.

`PLANNER_MODEL` and `REVIEWER_MODEL` both move to `claude-opus-5`. The pins used to differ as a proxy for independence; that proxy is retired, so both phases get the strongest available model and the separation comes from context boundaries instead.

## Why

The family rule was asserted and never tested, and Claude Code subagents can only pin Claude models — so it was unsatisfiable by the fleet's own tooling. Every review note for months carried the same disclosure: same-family, harm reduction, cross-vendor pass still owed. That debt was never paid because it could not be.

[[TASK-0077]] tested it against the one case in the fleet with a known answer, on the tree where a genuinely doubled file existed — the rule's best case, since that defect was authored by Opus and the author's error was treating `ast.parse` success as structural proof. Clean-context Opus found it, rated it the run's only high-severity finding, and described it more accurately than the different-pin baseline had.

Full reasoning, alternatives and limits: [[ADR-0013]].

## What changed

- `tools/instructions/QUALITY.md` — the gate, and why family is no longer it
- `tools/skills/independent-review/SKILL.md` — the "why this exists" section now names shared *commitment* rather than shared *weights* as the thing review breaks; rule 1 rewritten
- `tools/scripts/generate-adapters.py` — both pins to Opus; the reviewer agent's independence caveat replaced with a statement of what actually was independent
- `.claude/agents/planner.md`, `.claude/agents/independent-reviewer.md` — regenerated

## Impact on existing notes

Reviews recorded before today remain accurate as written. They disclosed a real limitation under the rule then in force and are **not** retroactively upgraded. `reviewed_by` keeps recording the model as provenance rather than a compliance token.

## Not claimed

This does not establish that cross-family review is worthless. The different-family arm never got a fair run — sandboxed read-only on its first pass, cut off by a usage cap on its second. What it establishes is narrower: the fleet's rule rested on an untested premise, and its one direct test contradicted it. That is sufficient to replace a rule nothing could satisfy.
