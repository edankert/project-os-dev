---
type: "[[task]]"
id: TASK-0201
aliases: ["TASK-0201"]
title: "A Claude session that runs on a model other than the repo's pin shows a warning row above the prompt, and the model is told too"
status: backlog
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]], scope item 3"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "S"
due: ""
depends: ["[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]"]
blocks: ["[[TASK-0203-The-Mod-Is-Pinned-Tested-In-CI-And-Synced-To-The-Cockpit]]"]
related: []
tests: []
---

# A session on the wrong model is named at start

A resumed Claude session keeps the model its transcript was saved with, whatever `.claude/settings.json` pins. Today a person finds out only by typing `/model`. After this task, a session whose model differs from the pin shows one warning row above the prompt for as long as it runs, and the model's first context block says the same.

## Definition of Done

- [ ] At `session.start` the mod reads `model` from the repo's `.claude/settings.json` and the session's model. A repo with no pin, or a settings file that cannot be read: no warning.
- [ ] When they differ, a row in the theme's `warning` colour, drawn above the project line: "This session runs <model>; this repo pins <pin> (.claude/settings.json). Switch with /model, or start a new session." If the session's model changes to the pin, the row disappears.
- [ ] The same sentence is added to the model's context through `prompt.context`, so a session in VS Code or `claude -p`, where nothing is drawn, still records it.
- [ ] A new contract in HOOKS.md, HC-011 "The session runs on the pinned model", with Trigger, Rule, Check logic, Implementations (Claude Code: the mod; Codex: none, its profiles carry no pin) and On failure (warn only).
- [ ] `claude plugin test` cases: different model draws the row and adds the context; same model draws nothing; no pin draws nothing.
- [ ] Checked live: resume a session saved on another model and see the row.

## Steps

- [ ] The `session.start` read and the warning row.
- [ ] The context block.
- [ ] HC-011 and tests.

## Notes

Model names can differ in form between the pin and the session (an alias against a full ID). Compare in the form TASK-0198 or this task finds the session reports, and record the rule in the code comment.
