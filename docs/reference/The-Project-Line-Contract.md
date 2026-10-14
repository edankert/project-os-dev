---
type: "[[reference]]"
id: REFERENCE-PROJECT-LINE-CONTRACT
aliases: ["REFERENCE-PROJECT-LINE-CONTRACT", "The project line contract"]
title: "How the project-os mod and the cockpit plugin share one line above the Claude Code prompt, without project-os knowing the cockpit exists"
status: active
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
scope: "The contract between FEAT-0041 (the project-os mod, in the template) and project-os-cockpit FEAT-0157 (the cockpit plugin's facts on the same line). Both features link here; TASK-0202 copies the settled version into the template's tools/adapters/claude-code/ADAPTER.md."
source:
  - "Edwin 2026-10-14, in project-os-cockpit: 'Build FEAT-0041 too', and 'only when non-zero' for the other projects' count"
  - "The mod type declarations Claude Code 2.1.299 writes, read 2026-10-14 in project-os-cockpit desktop/plugin/claude-code/.claude-plugin/types/claude-code/index.d.ts: ui.render and AbovePrompt (~10649), RenderElement (~9755), the five tiers (~13214), On (~6893)"
  - "The coordinating session in project-os-cockpit, 2026-10-14: prefer composing through the render chain over the mod calling the sidecar, so project-os never names the cockpit"
related:
  - "[[FEAT-0041-Project-Os-Mod]]"
  - "[[ISS-0106-Project-Os-As-A-Plugin]]"
  - "[[TASK-0198-Two-Plugins-Share-The-Line-Above-The-Prompt-Checked-Live]]"
  - "[[TASK-0202-The-Project-Line-Above-The-Prompt]]"
  - "[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]"
---

# The project line contract

There is one line above the Claude Code prompt. The project-os mod draws it. When the session runs in a cockpit terminal, the cockpit's plugin adds its own facts to the end of the same line. Neither plugin calls the other, and project-os never names the cockpit, its service or its environment variables. The two meet only in the drawing that Claude Code passes from one plugin's hook to the next.

This note is the plan's version of the contract. [[TASK-0198-Two-Plugins-Share-The-Line-Above-The-Prompt-Checked-Live|TASK-0198]] checks it in a live session before either side builds on it. [[TASK-0202-The-Project-Line-Above-The-Prompt|TASK-0202]] then writes the settled version into the template's `tools/adapters/claude-code/ADAPTER.md`, which becomes the durable home.

## Why the plugins meet in the drawing and not through the cockpit's service

The first idea was that the project-os mod would ask the cockpit's service (the sidecar, a small local web server per project) for the cockpit's facts whenever the terminal said a sidecar was running. That would put cockpit knowledge into project-os:

- The cockpit plugin does not read the sidecar's address from its environment. It reads it from a file the shell rewrites, `$COCKPIT_INSTRUMENT_DIR/hook-env`, on every call, because the sidecar can restart on a new port. It also refuses any address that is not on this machine, and it honours `COCKPIT_NO_INSTRUMENT` (project-os-cockpit `desktop/plugin/claude-code/hooks/register.ts`, `sidecarUrl`). The mod would have to repeat all three rules, in a different repository, and keep them in step.
- The other projects' count does not come from any sidecar. A sidecar knows only its own project. Only the shell knows every project.

Drawing is different. Claude Code passes the drawing down a chain of hooks, and each hook can read and change what the hooks beneath it drew. So the cockpit plugin can add its facts to the line project-os drew, using only facts it already has.

## What the declarations say, and what they leave open

Read on 2026-10-14 from the declarations Claude Code 2.1.299 writes (Claude Code 2.1.300 is installed):

1. **A drawing is plain data.** A hook on `ui.render` gets `next(e)`, which resolves to the tree the hooks beneath drew: Boxes, Texts and Buttons with their props and children. "Return it, wrap it, draw your own, or rewrite `props`." So an outer hook can find an element by its `key` and add children to it.
2. **The band above the prompt has one instance.** `AbovePrompt`: "A hook draws a tree, or passes; one instance." Two plugins that each drew their own tree without calling `next(e)` would leave only the outer one's.
3. **Hooks nest by tier, outermost first: `prepend`, `user`, `append`, `builtin`, `core`.** "Same-event hooks nest in this order and no other way." Within one plugin, registrations nest in the order they were made.
4. **Left open: the order of two plugins in the same tier.** Both the project-os mod and the cockpit plugin are things a person installs, so both sit in the `user` tier. The declarations do not say which of two `user` plugins is outer. The contract below is written so that either order works, and TASK-0198 records which one Claude Code actually uses.
5. **Left open: whether a Button keeps working inside another plugin's tree.** A Button's `onPress` "stays in the plugin's own environment under `press.handle`". Whether the press still reaches the cockpit plugin after project-os has moved the Button into its own Box is not stated. The contract does not rely on it (rule 6).

## What a live session showed (TASK-0198, Claude Code 2.1.300)

Checked on 2026-10-14 with two scratch plugins in a real terminal session, read through `tmux capture-pane`, `--debug` and each plugin's own log. Plugin A stood for the project-os mod (a Box keyed `project-os:line`); plugin B stood for the cockpit (a Box keyed `segment:cockpit` with a Button). The contract works, in either order. Five findings, which the rules below now take into account:

1. **The plugin loaded first is the outer hook.** With `--plugin-dir A --plugin-dir B`, A was index 0 in `next.trace` and B index 1, with the engine at index 2. Swapping the flags swapped them. When one plugin came from `CLAUDE_CODE_PLUGIN_DIRS`, as the cockpit plugin does, and the other from the repo's settings, as the project-os mod will, the environment one was outer. The order was the same on every restart. A plugin refresh without a restart was not tried.
2. **`next(e)` hands over the inner tree as plain data, `key` props intact, and frozen.** Changing it in place threw "Attempted to assign to readonly property", and Claude Code skipped the hook. A hook that joins has to build a new tree from copies.
3. **Joining works when the new tree keeps everything beneath it.** The bottom of the chain is the engine's own node, `{ "type": "engine", "ref": 1 }`. A join that rebuilt the tree around it was drawn: `A-line r2 p0  B-seg r2 p0 [ Open ]`. An earlier join that returned only the line, leaving that node out, was not drawn; Claude Code drew B's tree instead. The cause of that one refusal was not isolated, so rule 4 now says to keep it.
4. **A Button moved into another plugin's tree still belongs to the plugin that drew it.** Pressing B's button inside A's line raised `ui.press` with `plugin=t198-b`, and B's own `onPress` ran. Rule 6 is kept anyway: it costs nothing and does not depend on this.
5. **One plugin's `$.ui.invalidate("ui.render")` redraws the whole joined line.** B's press handler called it, and the next drawing showed B's new count inside A's line.

## The rules

1. **The project-os mod draws its line as one Box keyed `project-os:line`**, laid out as a row. Its children are Text elements, the project facts first.
2. **Another plugin's facts are a Box keyed `segment:<plugin>`**, for example `segment:cockpit`, laid out as a row, at most one row high. Its first child starts with the separator ` · `.
3. **Every hook on the band calls `next(e)` first.** If `e.props.hasSurvey` is true, it returns what `next(e)` gave, unchanged. A survey owns the band while it is shown.
4. **Whichever hook is outer joins the two.** The hooks do not need to know their order:
   - The project-os mod looks in the tree `next(e)` returned for elements keyed `segment:*`. It builds a new tree in which its line takes the place of the first segment it found, with every segment found appended to the line in order. Everything else beneath is kept where it was, the engine's own node (`{ type: "engine" }`) included. When there is no segment, it returns a column Box holding what was beneath and then its line.
   - The cockpit plugin looks in the tree `next(e)` returned for the element keyed `project-os:line`. If it finds it, it builds a new tree in which that Box has its segment as the last child, and returns it. If it does not, it returns a column Box holding what was beneath and then its segment. If project-os is the outer hook, project-os then joins it to the line. If the project-os mod is not loaded at all, the segment is the whole band.
   - The tree from `next(e)` is frozen. Neither side changes it in place; both build new trees from copies (live finding 2).
5. **The project facts come first, and the line is cut from the right.** The line uses `wrap: "truncate-end"` within `e.props.bodyColumns`, so a narrow terminal loses the cockpit's facts before it loses the focus item.
6. **A plugin answers presses on its own Buttons through `ui.press`, by key.** The cockpit plugin registers `on("ui.press", { element: "cockpit:open" }, ...)` and does not rely on the Button's `onPress` closure surviving the move into another plugin's tree. Keys of Buttons inside a segment start with the plugin's name.
7. **Each plugin refreshes the band itself.** When its facts change, a plugin calls `$.ui.invalidate("ui.render")`. That re-runs the whole chain, so the other plugin's part is redrawn from its own cached facts. No hook computes anything slow while drawing: every fact is read in the background and cached.
8. **A fact that cannot be read is left out, never shown as zero.** This applies to both sides. A validator that has not finished yet shows nothing for its count; a cockpit service that does not answer shows no cockpit count.

## What the line looks like

On a terminal 120 columns wide, in project-os-cockpit, with both plugins loaded:

```
FEAT-0157 doing · PHASE-046 · 2 validator errors · 61 review-stale · route: planner · 3 need you · 5 in other projects  [ Open in cockpit ]
```

The part from `3 need you` on is the cockpit's segment. "5 in other projects" appears only when the number is above zero and fresh (Edwin, 2026-10-14). In a repo with no cockpit, or a session outside a cockpit terminal, the line stops after `route: planner`.

The wrong-model warning is not part of the line. It is its own row above it, in the theme's `warning` colour, drawn by the project-os mod for as long as the session runs on the wrong model.

## If TASK-0198 finds that this does not work

TASK-0198 found that it works (see "What a live session showed"), so this fallback is not needed. It is kept for the day a Claude Code release changes how the chain passes trees. If the outer hook cannot see the inner hook's tree, or Claude Code drops one of two `user` plugins' trees on the band, the fallback is the contract first proposed: the project-os mod reads one file named by an environment variable that project-os defines (not a cockpit one), and draws whatever segments it lists. That is Edwin's call when it arises, because it changes what project-os knows. TASK-0198 stops and records the finding; neither side builds its half of the line until it is settled.

## Maintenance

- TASK-0202 copies the settled rules into `tools/adapters/claude-code/ADAPTER.md` in the template and marks this note as the history of how they were chosen.
- A change to a key name or a rule here is a change to both plugins. Change it in the template's ADAPTER.md and in project-os-cockpit's plugin in the same day, and say so in both change notes.
