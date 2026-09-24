---
type: "[[change]]"
id: CHG-20260924-Opus-5-5-Guide-Conformance
title: "Sessions start with the in-flight slice, the Stop hook names open boxes, and the subagents run on Opus 5.5"
status: merged
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[Opus-5-5-Prompting-Guide-Review-2026-09-24]]"]
commit: ""
pr: ""
impacts: ["tools/scripts/snapshot-slice.py", "tools/adapters/claude-code/hooks/snapshot-freshness.sh", "tools/adapters/claude-code/hooks/close-out-check.sh", "tools/adapters/claude-code/hooks/review-budget.py", "tools/adapters/codex/hooks/dispatch.py", "tools/agents/bootstrap.sh", "tools/scripts/generate-adapters.py", "tools/instructions/LIFECYCLE.md", "tools/instructions/HOOKS.md", "tools/instructions/HANDOFF.md", "tools/instructions/IMPORTING.md", "tools/skills/inbox-triage/SKILL.md", "AGENTS.md", "CLAUDE.md"]
issues: []
features: ["[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]", "[[FEAT-0021-Serve-Orientation-Answer-Lookup]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TASK-0080]]", "[[TASK-0156]]", "[[TASK-0157]]", "[[TASK-0158]]", "[[TASK-0159]]", "[[TASK-0160]]", "[[PHASE-0003-Prompting-Guide-Conformance]]"]
---

# Sessions start with the in-flight slice, the Stop hook names open boxes, and the subagents run on Opus 5.5

## Summary

An agent starting a session in a project-os repo now sees the focus items, the counts and every in-flight item in its context. It is no longer told to read `SNAPSHOT.yaml` itself. When it stops with a task in focus, the close-out block quotes the task's unticked boxes. The planner and reviewer subagents run on `claude-opus-5-5`, and the reviewer sees its tool-call count after every call.

## Impact

- No screen changed: the changes are to hooks, scripts, instruction files and generated agent definitions in the template, synced to this repo on 2026-09-24.

What a person working in a synced repo notices:

- **Session start.** The SessionStart hook prints up to 6,000 characters (about 1,500 tokens) from `tools/scripts/snapshot-slice.py` instead of a one-line reminder. The same output comes from `bootstrap.sh` and the Codex SessionStart hook. Without `python3` it falls back to the reminder. [[TASK-0080]].
- **Stop.** A close-out block for a focus task lists up to five open Definition of Done and Steps boxes. [[TASK-0157]].
- **Subagents.** `model: claude-opus-5-5` in both; the planner gains `effort: medium`; a review's `reviewed_by` names whichever model ran it. [[TASK-0156]].
- **Pause rule.** `LIFECYCLE.md` names four early stops that are not pauses; the file is 993 words. [[TASK-0158]].
- **External material.** The inbox skill and `IMPORTING.md` say instructions inside it are evidence, not orders. [[TASK-0159]].
- **Reviewer.** A `Review budget: call N of 40.` line after each call. [[TASK-0160]].

Risk scan: no new `RISK-*`. The one new dependency, `python3` for the slice, is already needed by the review-budget and verification hooks, and the slice fails open to the old reminder. The context added at session start is bounded at 6,000 characters. No new env var, path contract or credential.

## Documentation Coverage (All Types Considered)

- features: new (FEAT-0039), updated (FEAT-0021 moved into PHASE-0003)
- requirements: not-applicable (REQ-0026's word budget still met, 993 of 1,000)
- tasks: new (TASK-0156 to TASK-0160), updated (TASK-0080)
- issues: not-applicable
- tests: updated (TST-0005, TST-0007, TST-0014 procedures and adequacy)
- workflows: not-applicable
- decisions: not-applicable (TASK-0080's truncation rule is recorded on the task)
- risks: not-applicable (scan above)
- changes: new (this note)
- snapshot: updated

## Follow-ups

- [ ] The other fleet repos pick this up at their next `sync-project-os.sh`. Their own `CLAUDE.md` files still say to read the snapshot at session start and should drop the line when they sync.
- [ ] The user-level `~/.claude/CLAUDE.md` says the same; Edwin decides whether to change it.
- [ ] The new subagent pins take effect from the next session. This session's reviewers ran the definition loaded at its start (TASK-0156).
- [ ] Nothing here is committed in either repo. The template's working tree also holds the uncommitted `rank-*.py` scripts and the `dispatch.py` status-quoting fix from earlier work, and the sync copied both here.
