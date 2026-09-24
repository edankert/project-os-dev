---
type: "[[reference]]"
id: REFERENCE-OPUS-5-5-PROMPTING-REVIEW
aliases: ["Opus 5.5 prompting-guide review 2026-09-24"]
title: "project-os against the Opus 5.5 prompting guide (2026-09-24): six changes, five already aligned"
status: active
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
scope: "project"
source:
  - "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5"
  - "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5"
related:
  - "[[Prompting-Guide-Review-2026-09-03]]"
  - "[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]"
  - "[[FEAT-0021-Serve-Orientation-Answer-Lookup]]"
  - "[[PHASE-0003-Prompting-Guide-Conformance]]"
---

# project-os against the Opus 5.5 prompting guide

## Purpose

Edwin asked on 2026-09-24 how project-os should change the way it gives an agent context, from `CLAUDE.md` and `AGENTS.md` down to the notes and hooks, after the Opus 5.5 prompting guide was published. This note records the answer. It follows the 2026-09-03 review of the Claude 5 guides ([[Prompting-Guide-Review-2026-09-03]]), and its changes are PHASE-0003 work: [[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]] and [[TASK-0080]].

The short answer is that most of what the guide asks for is already in place. Six changes are worth making. Two correct stale settings, and four copy a specific wording or harness pattern from the guide.

## What does not apply

Much of the guide is for teams calling the API directly: thinking-disabled prompts, the `display: "updates"` setting, safeguard refusals, chat system prompts, frontend styling and visual inputs. Claude Code handles these for us. It already wraps pasted text in `<pasted_content>` tags, and it already sends the "the user hasn't heard from you" reminder the guide describes.

## Already aligned

- **Progress updates.** `AGENTS.md` asks for one line before starting and a recap at the end. That is the guide's third lever for progress updates.
- **When to pause.** `LIFECYCLE.md`, "When to pause for the user", already says to do everything that does not depend on the answer before asking.
- **No re-check instructions.** A search of every instruction file, skill and agent definition found no "think carefully", "double-check" or "re-verify" wording. The Opus 5 guide says such wording causes over-verification. Our verification steps run tools (the validator, CI, the independent review), which is a different thing.
- **Delegation.** The per-prompt hint recommends the planner only for a multi-item scaffold or an ambiguous request. That is the explicit delegation guidance the Opus 5 guide asks for.
- **Reviewer scope.** The Opus 5 guide says to ask a reviewer to "report everything" and filter afterwards. `independent-review/SKILL.md` forbids that wording, because it made reviews run 90 to 125 tool calls. We bound a review by its number of claims rather than by severity. Our measurement is kept over the guide's general advice.

## The six changes

1. **Both subagents were pinned to the previous model.** `generate-adapters.py` wrote `model: claude-opus-5` into the planner and the reviewer. The guide says Opus 5.5 at `medium` effort matches or beats Opus 5 at `high` with fewer tokens. The planner had no `effort:` line, and the reviewer's instructions hardcoded `reviewed_by: model:claude-opus-5`, so every review recorded the wrong model. [[TASK-0156]].
2. **The Stop hook named the focus task but not what was left in it.** The guide's pattern for long runs is to keep a checklist and, when the model ends a turn, reply by naming the open items. Our task notes already carry that checklist, as `## Definition of Done` and `## Steps`. The hook now quotes the unticked boxes. The guide also allows two or three automatic continuations; we keep one, because a second block would catch the handoff write the first block asks for. [[TASK-0157]].
3. **The pause rule did not name the early stops it forbids.** The guide says Opus 5.5 responds best when the prompt names the exact stops to avoid, and lists four: a summary that announces the next step without taking it; an offer to continue unless the user objects; a list of decisions none of which blocks the work; and stopping to report because a milestone is done. [[TASK-0158]].
4. **Four files told the agent to read a 141 KB snapshot at session start.** The guide's advice for multi-app work is to have the model open everything relevant before acting, including sources the request does not mention. Our equivalent is serving the in-flight part of the snapshot at session start and naming the notes to open. That was already planned as [[TASK-0080]] under [[FEAT-0021-Serve-Orientation-Answer-Lookup]], so this review picks that task up rather than filing a second one.
5. **External material had no rule saying it is evidence, not instructions.** The guide marks pasted text so the model does not follow instructions inside it. Our equivalents are `inbox/` items and material brought in by an import. [[TASK-0159]].
6. **The reviewer saw its tool-call count only near the limit.** The guide says a running `elapsed 340s / 1200s` line makes agents pace themselves and usually finish early. `review-budget.py` spoke once, four calls before the limit, and measured reviews stopped at about 34 of 40 calls. A count on every call is the same idea using calls instead of seconds. This is our adaptation and the guide did not test it. [[TASK-0160]].

## Not taken

- **Listing recently modified notes at session start.** PHASE-0008 found that sorting by modification date recalls about as well as the BM25 ranker, and both recall about a quarter of what a session goes on to read. That is not worth a fixed cost on every session start.
- **The guide's full "keep working" paragraph.** The guide says to leave it out where a person is present to answer, and Edwin's sessions are interactive. TASK-0158 takes only the four named stops.
- **Editing the user-level `~/.claude/CLAUDE.md`.** It also tells the agent to read the snapshot at session start. It is Edwin's own file and covers every repo, so the change is proposed to him rather than made.

## Maintenance

This note is a dated review and is not kept current. A later guide gets its own review note.
