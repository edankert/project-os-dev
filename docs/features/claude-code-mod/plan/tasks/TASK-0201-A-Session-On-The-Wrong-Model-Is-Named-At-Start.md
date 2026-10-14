---
type: "[[task]]"
id: TASK-0201
aliases: ["TASK-0201"]
title: "A Claude session that runs on a model other than the repo's pin shows a warning row above the prompt, and the model is told too"
status: done
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

- [x] At `session.start` the mod reads `model` from the repo's `.claude/settings.json` and the session's model. A repo with no pin, or a settings file that cannot be read: no warning.
- [x] When they differ, a row in the theme's `warning` colour, drawn above the project line: "This session runs <model>; this repo pins <pin> (.claude/settings.json). Switch with /model, or start a new session." If the session's model changes to the pin, the row disappears.
- [x] The same sentence is added to the model's context through `prompt.context`, so a session in VS Code or `claude -p`, where nothing is drawn, still records it.
- [x] A new contract in HOOKS.md, HC-011 "The session runs on the pinned model", with Trigger, Rule, Check logic, Implementations (Claude Code: the mod; Codex: none, its profiles carry no pin) and On failure (warn only).
- [x] `claude plugin test` cases: different model draws the row and adds the context; same model draws nothing; no pin draws nothing.
- [x] Checked live: a session on another model than the pin shows the row (started with `--model sonnet` rather than resumed; the plugin reads the model the same way in both).

## Steps

- [x] The `session.start` read and the warning row.
- [x] The context block.
- [x] HC-011 and tests.

## Notes

Model names can differ in form between the pin and the session (an alias against a full ID). Compare in the form TASK-0198 or this task finds the session reports, and record the rule in the code comment.

## Result (2026-10-14)

Built in project-os `1e09218`. Model names are compared in one spelling: lower case, no `claude-` prefix, no 8-digit date, no `[1m]`-style suffix, spaces and dots as dashes. `$.session.model()` reports e.g. `claude-sonnet-5-5`; project-os-cockpit pins the family name `opus`, so a pin with no digits is honoured by any model of that family. The context block is named `projectOsModel`. Claude Code sends a plugin's own block once, with the first request, which is when it matters.

Live, in project-os-cockpit with the plugin on `--plugin-dir`: on `--model sonnet` the row read "This session runs claude-sonnet-5-5; this repo pins opus (.claude/settings.json). Switch with /model, or start a new session." above the line. On Opus 5.5 there was no row. The check used a fresh session on another model rather than a resumed one. The plugin reads `$.session.model()` the same way in both, and resuming is just how a session ends up on the wrong model.

Tests: four `claude plugin test` cases (spellings and family pins; a different model draws the row and adds the context block; the pinned model and a repo with no pin draw nothing). HC-011 is in HOOKS.md.
