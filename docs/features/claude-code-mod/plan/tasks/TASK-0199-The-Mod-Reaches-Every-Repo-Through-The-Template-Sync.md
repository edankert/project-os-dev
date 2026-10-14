---
type: "[[task]]"
id: TASK-0199
aliases: ["TASK-0199"]
title: "The template sync places the project-os plugin in every repo and registers it in .claude/settings.json, so a Claude session there loads it without any install step the person has to remember"
status: backlog
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]], scope item 1", "[[ISS-0106-Project-Os-As-A-Plugin]], option (a)"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "M"
due: ""
depends: ["[[TASK-0198-Two-Plugins-Share-The-Line-Above-The-Prompt-Checked-Live]]"]
blocks: ["[[TASK-0200-A-File-Changed-From-The-Shell-Counts-As-A-Write-At-Close-Out]]", "[[TASK-0201-A-Session-On-The-Wrong-Model-Is-Named-At-Start]]", "[[TASK-0202-The-Project-Line-Above-The-Prompt]]"]
related: ["[[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface]]"]
tests: []
---

# The mod reaches every repo through the template sync

Today a repo gets project-os's Claude Code hooks from `.claude/settings.json`, which `generate-adapters.py --install-hooks` writes after every template sync. After this task the same step also registers the project-os plugin, which lives in a template-owned folder. A session in any synced repo loads it. This fixes [[ISS-0106-Project-Os-As-A-Plugin]] with its option (a).

## Definition of Done

- [ ] In the template: `tools/adapters/claude-code/plugin/` with `.claude-plugin/plugin.json` (name `project-os`, a version, "Tested on Claude Code 2.1.300" in the description), `hooks/hooks.json` naming `./register.ts`, and a `register.ts` that registers nothing yet.
- [ ] `generate-adapters.py --install-hooks` writes the registration TASK-0198 found to work into `.claude/settings.json`, merging with what is there and never removing a key it did not write. `--check` reports a missing or changed registration.
- [ ] `tools/sync/MANIFEST.yaml` lists the plugin folder as template-owned, so the sync copies it.
- [ ] `tools/adapters/claude-code/ADAPTER.md` says how the plugin is loaded, what a person sees the first time, and how to turn it off in one repo.
- [ ] A test in `tools/scripts/` that runs the generator on a fixture repo and asserts the registration; it fails when the registration is removed.
- [ ] Checked in a real session in this repository after a local sync: `claude plugin list` (or the equivalent TASK-0198 found) shows the plugin loaded from the repo folder.
- [ ] ISS-0106 set to `fixed`, with the chosen option and the evidence.

## Steps

- [ ] Plugin folder and manifest entry.
- [ ] Generator registration, `--check`, test.
- [ ] ADAPTER.md.

## Notes

**TASK-0198 settled the registration (ISS-0106, "How a repo loads the mod: checked live").** It is a marketplace inside the repo, not `CLAUDE_CODE_PLUGIN_DIRS`, which project settings may not set. The generator writes `extraKnownMarketplaces` with `{ "source": "directory", "path": "./" }` and `enabledPlugins`, and a `.claude-plugin/marketplace.json` that lists `tools/adapters/claude-code/plugin` by relative path. The marketplace name must differ in every repo, for example `project-os-<repo folder name>`. Two repos sharing one name run each other's copy of the plugin. No per-machine install is needed. Checked only with the marketplace file at the repo root (`path: "./"`); if it is placed elsewhere, check that path in this task's live session.

If a project-scope registration had still needed a one-time `claude plugin install` per machine, the generator cannot do that step for the person. Then ADAPTER.md says so, the session-start orientation (HC-002) names the missing step when the plugin is not loaded, and Edwin is told before the task closes.
