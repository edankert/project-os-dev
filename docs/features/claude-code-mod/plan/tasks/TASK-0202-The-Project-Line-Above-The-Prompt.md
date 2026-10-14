---
type: "[[task]]"
id: TASK-0202
aliases: ["TASK-0202"]
title: "One line above the Claude prompt shows the focus item, its status and phase, the validator's error and REVIEW-STALE counts and the routing hint, and takes another plugin's segment at its end"
status: backlog
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]], scope items 4 and 5", "[[REFERENCE-PROJECT-LINE-CONTRACT]]"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "M"
due: ""
depends: ["[[TASK-0198-Two-Plugins-Share-The-Line-Above-The-Prompt-Checked-Live]]", "[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]"]
blocks: ["[[TASK-0203-The-Mod-Is-Pinned-Tested-In-CI-And-Synced-To-The-Cockpit]]"]
related: ["[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]"]
tests: []
---

# The project line above the prompt

After this task a person in any synced repo sees one line above the Claude prompt, for example `FEAT-0157 doing · PHASE-046 · 2 validator errors · 61 review-stale · route: planner`. It comes from the repo's own scripts and costs no tokens, because the model never reads it. Another plugin can add its own facts to the end of the line under the rules in [[REFERENCE-PROJECT-LINE-CONTRACT]]; the cockpit plugin is the first to do so.

## Definition of Done

- [ ] The mod hooks `ui.render` on `AbovePrompt`. It calls `next(e)` first, yields to a survey (`hasSurvey`), and draws a row Box keyed `project-os:line`, cut from the right within `bodyColumns`.
- [ ] Facts and their sources, as plan/PLAN.md "How the line gets its facts" states: focus item, status and phase from `snapshot-query.py`; error and REVIEW-STALE counts from one validator run; the routing hint's first line from `model-routing-hint.sh`. Each is refreshed in the background at `session.start` and after a turn that changed `SNAPSHOT.yaml` or `docs/`, never while drawing.
- [ ] A fact that has not been read yet, or whose script failed, is left out of the line. A count of zero is shown only when the script ran and counted zero. With no focus item the line says "no focus item".
- [ ] Every element keyed `segment:*` in the tree `next(e)` returned is appended to the end of the line in the order found. Any other tree beneath is drawn under the line, not dropped.
- [ ] The wrong-model row from TASK-0201 sits above the line in the same band.
- [ ] The template's `tools/adapters/claude-code/ADAPTER.md` gains the settled contract, and REFERENCE-PROJECT-LINE-CONTRACT says it is now the history.
- [ ] A new contract in HOOKS.md, HC-012 "The project line", with Implementations (Claude Code: the mod; Codex: none; the session-start orientation HC-002 remains the text equivalent).
- [ ] `claude plugin test` cases: the line's text for a fixture repo; a `segment:test` element beneath is joined to the end; a survey passes through untouched; a failed validator run omits its count; a narrow `bodyColumns` cuts from the right.
- [ ] Checked live in this repository and in project-os-cockpit with its plugin loaded (after TASK-0203's sync, or with the plugin on `CLAUDE_CODE_PLUGIN_DIRS`).

## Steps

- [ ] The background readers and their cache.
- [ ] The render hook and the join.
- [ ] HC-012, ADAPTER.md, tests, live look.

## Notes

The validator can take seconds in a large repo. Run it with `$.process.run` from a promise the hook does not await, at most one run at a time, and redraw with `$.ui.invalidate("ui.render")` when it finishes.
