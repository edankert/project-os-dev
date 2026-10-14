---
type: "[[task]]"
id: TASK-0198
aliases: ["TASK-0198"]
title: "Two plugins' drawings are checked in a live Claude Code session: which one is outer, whether it sees the other's line, and how a repo's settings load a plugin from a folder"
status: done
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]]", "[[REFERENCE-PROJECT-LINE-CONTRACT]], 'What the declarations say, and what they leave open'"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "S"
due: ""
depends: []
blocks: ["[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]", "[[TASK-0202-The-Project-Line-Above-The-Prompt]]"]
related: ["[[ISS-0106-Project-Os-As-A-Plugin]]", "[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]"]
tests: []
---

# Two plugins share the line above the prompt, checked live

The contract for the line assumes three things the type declarations do not settle. This task finds out, in Claude Code 2.1.300, before either repository builds on them. It writes no product code: two throwaway plugins in a scratch folder, and the findings in the notes.

## Definition of Done

- [x] Two scratch plugins, A and B, both hook `ui.render` on `AbovePrompt` and are loaded together the way the real ones will be: one through the repo's `.claude/settings.json`, one through `CLAUDE_CODE_PLUGIN_DIRS`. Recorded: which is outer (from `next.trace`), and whether that is stable across a restart and a `/reload`-style plugin refresh.
- [x] Recorded: whether the outer hook's `next(e)` returns the inner hook's tree as plain data with `key` props intact, and whether an element appended to it is drawn.
- [x] Recorded: whether a Button that B drew, moved by A into A's tree, still reaches B through `on("ui.press", { element: "<key>" }, ...)` in B, and whether its own `onPress` still fires.
- [x] Recorded: whether `$.ui.invalidate("ui.render")` from either plugin redraws the joined line.
- [x] Recorded: whether `.claude/settings.json` can offer a plugin from a folder inside the repo (`claude plugin marketplace add --scope project <folder>` and the enable step), what keys that writes, and what a person sees the first time a session starts there. Does it need a per-machine install, and does a template sync that rewrites the folder update it without one?
- [x] Recorded: whether a `.ts` hooks module runs with no Node toolchain in the repo, and whether `$.process.run` can run `git` and `python3` from a hook.
- [x] The findings are written into [[REFERENCE-PROJECT-LINE-CONTRACT]] ("What the declarations say") and [[ISS-0106-Project-Os-As-A-Plugin]] ("What is true today"), each with the Claude Code version.
- [x] Not triggered: the outer hook sees the inner tree, and neither tree is dropped. If the outer hook cannot see the inner tree, or one of two `user` plugins' trees is dropped: stop, and put the contract's fallback to Edwin before TASK-0202 or cockpit TASK-0673 starts.

## Steps

- [x] Scratch plugins in the session's scratch folder, not in the template.
- [x] Run each check in a real terminal session and keep the commands and the `next.trace` output in the notes.

## Notes

The cockpit's own plugin (`project-os-cockpit/desktop/plugin/claude-code/`) is already loaded by `CLAUDE_CODE_PLUGIN_DIRS` in cockpit terminals, so plugin B can be loaded the same way.

## Result (2026-10-14, Claude Code 2.1.300)

The contract works in either order, and a repo can load the mod by itself through a marketplace inside the repo, provided each repo gives that marketplace a name of its own. The findings are in [[REFERENCE-PROJECT-LINE-CONTRACT]] ("What a live session showed") and [[ISS-0106-Project-Os-As-A-Plugin]] ("How a repo loads the mod: checked live").

How it was run: two scratch plugins, A (a Box keyed `project-os:line`) and B (a Box keyed `segment:cockpit` with a Button), each logging every render, its `next.trace` and every press to a file. `claude` ran in a detached tmux server on its own socket (`tmux -L t198`), so no cockpit tmux session was touched, and the screen was read with `tmux capture-pane`. `--debug --debug-file` recorded what Claude Code loaded and why. Two throwaway git repos tested loading from the repo's settings. Not tried: whether the order holds after a plugin refresh without a restart, and whether the outer plugin's `$.ui.invalidate` redraws as the inner one's does.

The scratch plugins and repos stay in the session's scratch folder and are not part of the template.
