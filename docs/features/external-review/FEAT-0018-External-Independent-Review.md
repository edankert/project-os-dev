---
type: "[[feature]]"
id: FEAT-0018
title: "External independent review — run the QUALITY.md gate on a non-Claude model"
status: doing
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["session:2026-07-27", "QUALITY.md 'Independent review (different-model)'"]
goal: "Give the independent-review gate a reviewer that is actually a different model family, by running an agent CLI with tool access in an isolated worktree and returning a verdict whose every finding carries a reproduction."
requirements: []
tasks: ["[[TASK-0075]]", "[[TASK-0076]]"]
release: ""
related: []
tests: []
---

# External independent review

## Goal

`QUALITY.md` requires "a different model family or a human, never a second pass by the authoring model". Every review this fleet has recorded is a Claude subagent reviewing Claude-authored work, because Claude Code subagents can only pin Claude models. That is harm reduction, and the notes say so, but the gate has never actually been satisfied.

This runs the reviewer outside Claude.

## Scope

- A runner that assembles the review context (the `independent-review` skill, the notes under review, the diff), executes an agent CLI headless in a detached worktree, and returns a structured verdict.
- Model-agnostic invocation, so the same runner drives Kimi Code CLI, Codex or Gemini CLI.
- Schema enforcement: a finding with no `repro` command and no `observed` output is dropped.
- A calibration run against a case with a known answer.

## Out of Scope

- **Auto-stamping the verdict into note frontmatter.** `independent-review/SKILL.md` rule 2: a verdict is transcribed from what the review returned, never anticipated. A script that writes back whatever came out turns a judgement into a pipeline step, and the field it would write is exactly the one ADR-0011 gates close-out on.
- Replacing the Claude reviewer. It found real defects five times over ISS-0011..0015; this is additive.
- Paying per token. Subscription-covered CLI only (user constraint, 2026-07-27).

## Acceptance

- A review runs end to end against a non-Claude model and returns parseable JSON.
- Findings lacking a reproduction are dropped and the drop is reported, not silent.
- The reviewer works in a worktree; the real tree is byte-identical after a run.
- The calibration run against ISS-0011..0015 is recorded with its outcome, whatever that outcome is — including "found nothing new", which is a result about the method.

## Why a shell, not a chat completion

Recorded because it is the design's load-bearing assumption. The five same-family rounds on the ISS-0011 status-table guard found real defects only because the reviewer *executed*: it induced mutations and re-ran `--self-check`, swept `PYTHONHASHSEED` across twelve values to prove a check was nondeterministic, and found a silently doubled file by comparing line counts against a known-good commit. None of that is reachable by reading a diff. A text-in/text-out judge would have approved every round.

## Links
- Tasks: [[TASK-0075]], [[TASK-0076]]
- Consumes: `tools/skills/independent-review/SKILL.md`
- Shares its isolation primitive with project-os-bench FEAT-0001 / TASK-0002 (candidate adapter) — deliberately one component, not two.
