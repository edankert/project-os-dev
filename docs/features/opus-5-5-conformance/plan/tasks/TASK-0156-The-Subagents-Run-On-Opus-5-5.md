---
type: "[[task]]"
id: TASK-0156
aliases: ["TASK-0156"]
title: "The subagents run on Opus 5.5 and record the model they ran as"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[Opus-5-5-Prompting-Guide-Review-2026-09-24]]"]
parent: "[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]"
effort: S
due: ""
depends: []
blocks: []
related: []
tests: ["[[TST-0012]]"]
---

# The subagents run on Opus 5.5 and record the model they ran as

## Definition of Done
- [x] `PLANNER_MODEL` and `REVIEWER_MODEL` in `tools/scripts/generate-adapters.py` are `claude-opus-5-5` — evidence: `.claude/agents/planner.md` and `independent-reviewer.md` regenerated with `model: claude-opus-5-5`, in the template and in this repo after the sync
- [x] The planner's generated frontmatter carries `effort: medium`, the guide's default for Opus 5.5 — evidence: `.claude/agents/planner.md` line 5
- [x] The reviewer's body tells the author to record `reviewed_by` as the model the reviewer ran as, instead of naming `model:claude-opus-5` — evidence: step 3 now reads "with `reviewed_by` naming the model you ran as (`model:<its ID>`)". The Codex substitution had nothing left to replace and was removed; `.codex/agents/independent-reviewer.toml` carries the same model-neutral sentence
- [x] `ADAPTER.md`'s pin paragraph says the pins were revisited on 2026-09-24 and why
- [x] `generate-adapters.py --check` is clean and TST-0012's command passes — evidence: "all 65 artifacts current"; `run-tests.py` 2026-09-24, TST-0012 OK (15 tests)

## Steps
- [x] Change the two constants and the planner template.
- [x] Rewrite the reviewer's step 3 sentence and check the Codex rewrite.
- [x] Regenerate `.claude/agents/` and `.codex/agents/`, run `--check`.

## Notes
Found at FEAT-0039's review: both reviewers, launched after the regeneration in the same session, ran the old definition. They reported themselves as Opus 5, and one quoted the old `reviewed_by` wording from its brief. `ADAPTER.md` had said edits to agent files hot-reload; it now records this and says to start a new session after retargeting the pins. The pins on disk are correct; they take effect from the next session.

The guide: "Claude Opus 5.5 at `medium` matches or exceeds Claude Opus 5 at `high` on coding and knowledge-work evaluations." The reviewer keeps `effort: medium`. `ADAPTER.md` already says the pins are revisited at each model release, and this is that revisit.
