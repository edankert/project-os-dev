---
type: "[[task]]"
id: TASK-0199
aliases: ["TASK-0199"]
title: "The template sync places the project-os plugin in every repo and registers it in .claude/settings.json, so a Claude session there loads it without any install step the person has to remember"
status: done
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

- [x] In the template: `tools/adapters/claude-code/plugin/` with `.claude-plugin/plugin.json` (name `project-os`, a version, "Tested on Claude Code 2.1.300" in the description), `hooks/hooks.json` naming `./register.ts`, and a `register.ts` that registers nothing yet.
- [x] `generate-adapters.py --install-hooks` writes the registration TASK-0198 found to work into `.claude/settings.json`, merging with what is there and never removing a key it did not write. `--check` reports a missing or changed registration.
- [x] `tools/sync/MANIFEST.yaml` lists the plugin folder as template-owned, so the sync copies it.
- [x] `tools/adapters/claude-code/ADAPTER.md` says how the plugin is loaded, what a person sees the first time, and how to turn it off in one repo.
- [x] A test in `tools/scripts/` that runs the generator on a fixture repo and asserts the registration; it fails when the registration is removed.
- [x] Checked in a real session in this repository after a local sync: `claude plugin list` (or the equivalent TASK-0198 found) shows the plugin loaded from the repo folder.
- [x] ISS-0106 set to `fixed`, with the chosen option and the evidence.

## Steps

- [x] Plugin folder and manifest entry.
- [x] Generator registration, `--check`, test.
- [x] ADAPTER.md.

## Notes

**TASK-0198 settled the registration (ISS-0106, "How a repo loads the mod: checked live").** It is a marketplace inside the repo, not `CLAUDE_CODE_PLUGIN_DIRS`, which project settings may not set. The generator writes `extraKnownMarketplaces` with `{ "source": "directory", "path": "./" }` and `enabledPlugins`, and a `.claude-plugin/marketplace.json` that lists `tools/adapters/claude-code/plugin` by relative path. The marketplace name must differ in every repo, for example `project-os-<repo folder name>`. Two repos sharing one name run each other's copy of the plugin. No per-machine install is needed. Checked only with the marketplace file at the repo root (`path: "./"`); if it is placed elsewhere, check that path in this task's live session.

If a project-scope registration had still needed a one-time `claude plugin install` per machine, the generator cannot do that step for the person. Then ADAPTER.md says so, the session-start orientation (HC-002) names the missing step when the plugin is not loaded, and Edwin is told before the task closes.

## Result (2026-10-14)

Built in project-os `96cfc97` and synced here. The generator names the marketplace `project-os-<project>` from `project.name` in `SNAPSHOT.yaml`, falling back to the folder name for the template's placeholder; this repo's is `project-os-project-os-dev`. With `--install-hooks` it merges `extraKnownMarketplaces` (`"path": "./"`) and `enabledPlugins` into `.claude/settings.json`. An entry already set to `false` stays off, and a registration under an older name is replaced with its on/off value carried over. `--check` reports `UNREGISTERED` when either key is missing, and `STALE` for an out-of-date `marketplace.json`.

Two things the plan did not foresee:

- **The template's own `marketplace.json` must never reach another repo.** It names `project-os-project-os`. The manifest now lists `.claude-plugin/` as `generated`, so the sync never copies it.
- **Claude Code writes type declarations beside a plugin it loads**, in `plugin/.claude-plugin/types/`, with their own `.gitignore`. The sync walks the template's files on disk, so it would have copied them into every repo. The manifest's `excludes:` now names `types` under the plugin folder; the sync's own `excluded()` was checked against both a types path and `register.ts`.

Tests: `tools/scripts/test-plugin-registration.sh`, nine cases on a fixture repo, run by the template's CI with the other `test-*.sh`. Three mutations of the generator each turned it red: registration never called (6 failing), an `enabledPlugins` value overwritten (2), `--check` ignoring the registration (1).

Live check in this repository after the sync, Claude Code 2.1.300, `--debug`: "Added marketplace source: project-os-project-os-dev", then "Loading plugin project-os from source: ./tools/adapters/claude-code/plugin", then "plugin.register: project-os ... admitted". Nothing was asked of the person.

Running every template `test-*.sh` before the commit found two failures that predate this task. Both came in with project-os `30e2486` (TASK-0197) and need Edwin's decision, so they are [[ISS-0107-Two-Template-Tests-Fail-Since-The-Fix-What-You-Find-Rule]].
