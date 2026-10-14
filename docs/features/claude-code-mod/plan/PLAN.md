---
type: "[[plan]]"
title: "Delivery plan: the project-os mod, its line above the prompt, the shell-edit check and the wrong-model warning"
status: active
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]]", "project-os-cockpit, Edwin 2026-10-14: 'Build FEAT-0041 too'"]
implements: ["[[FEAT-0041-Project-Os-Mod]]"]
related: ["[[ISS-0106-Project-Os-As-A-Plugin]]", "[[REFERENCE-PROJECT-LINE-CONTRACT]]", "[[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface]]", "[[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit]]", "[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]", "[[REQ-0003-Hook-Contracts]]", "[[REQ-0004-Tool-Specific-Hook-Implementations]]", "[[ADR-0002-Hook-Contract-Pattern]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:`; see docs/__templates__/plan.md. -->
# Delivery plan: the project-os mod

After this plan, every Claude Code session in a synced project-os repo shows one line above the prompt: the focus item, its status and phase, the validator's error and REVIEW-STALE counts, and the routing hint. A file changed through the shell triggers the close-out check like an Edit-tool write. A session running on a model other than the pin gets a warning row and a note in the model's context. All the code lands in the template, `~/Dev/repos/project-os`. This repository holds only the notes. The work is six tasks.

## Where the code goes

All paths are in the template. The template sync carries them to each repo.

- `tools/adapters/claude-code/plugin/` is the plugin: `.claude-plugin/plugin.json` (name `project-os`, the version, "Tested on Claude Code 2.1.300"), `hooks/hooks.json` naming `./register.ts`, `hooks/register.ts`, and `tests/`. It is template-owned, so a repo never edits it.
- `tools/scripts/generate-adapters.py --install-hooks` registers the plugin in `.claude/settings.json`. The exact keys depend on TASK-0198's finding; the expected shape is a project-scope marketplace entry pointing at the folder, plus the plugin enabled. `--check` reports drift in the registration, as it already does for the agent files.
- `tools/instructions/HOOKS.md` gains the mod under HC-006 "Implementations", and two new contracts: HC-011, the session's model matches the pin, and HC-012, the project line. `tools/adapters/claude-code/ADAPTER.md` gains a section on the mod and the settled [[REFERENCE-PROJECT-LINE-CONTRACT]].

## Delivery sequence

1. **Check the two open facts live, before building on them** ([[TASK-0198-Two-Plugins-Share-The-Line-Above-The-Prompt-Checked-Live|TASK-0198]]). With two throwaway plugins loaded together in Claude Code 2.1.300, find out which of two `user`-tier plugins is outer on `ui.render`, whether the outer hook sees the inner hook's tree through `next(e)`, and whether a Button moved into the other plugin's tree still reaches its owner through `ui.press`. Also find out whether `.claude/settings.json` can load a plugin from a folder inside the repo, and what a person sees the first time. Record the answers in the contract note and in ISS-0106. **If the drawing chain does not behave as the contract assumes, stop and ask Edwin** (the contract's fallback changes what project-os knows).
2. **The mod reaches every repo** ([[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync|TASK-0199]]). The plugin folder with an empty `register.ts`, the registration in `generate-adapters.py`, `--check`, `tools/sync/MANIFEST.yaml`, and ADAPTER.md. Fixes [[ISS-0106-Project-Os-As-A-Plugin]].
3. **Shell edits count as writes** ([[TASK-0200-A-File-Changed-From-The-Shell-Counts-As-A-Write-At-Close-Out|TASK-0200]]) and **the wrong model is named** ([[TASK-0201-A-Session-On-The-Wrong-Model-Is-Named-At-Start|TASK-0201]]). Independent of each other; either order.
4. **The project line** ([[TASK-0202-The-Project-Line-Above-The-Prompt|TASK-0202]]). The line, its background refresh, and its half of the contract: it joins any `segment:*` it finds beneath it.
5. **Pinned, tested in CI, and synced to the cockpit** ([[TASK-0203-The-Mod-Is-Pinned-Tested-In-CI-And-Synced-To-The-Cockpit|TASK-0203]]). CI runs `claude plugin validate` and `claude plugin test`; HOOKS.md and the change note; the template synced into project-os-cockpit, which cockpit FEAT-0157 needs before it can be seen working. [[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit|TST-0047]] ready to run.

## How the shell-edit check works

Today `hooks/session-touch.sh` writes a per-session marker file after an Edit, Write or NotebookEdit call (`PostToolUse`). `hooks/close-out-check.sh`, the Stop hook, blocks once if the marker exists and focus is set. A Bash command that changes files leaves no marker.

1. At `turn.start`, the mod runs `git status --porcelain=v1 -z` and keeps the result in memory, keyed by the session.
2. On `classic.Stop`, before calling `next(e)`, it runs the same command again. The chain for classic events is "managed settings hooks, then hooks modules, then the other settings hooks", so the mod's hook runs **before** `close-out-check.sh`.
3. If any path changed that the turn's Edit and Write calls did not already account for, it writes the same marker `session-touch.sh` writes, at the same path. The path comes from `hooks/shared/session-marker.sh`, called through `$.process.run` so the rule for the path is stated once.
4. It then calls `next(e)`, and `close-out-check.sh` sees the marker as it would after an Edit.

A path that changed and changed back within the turn is not caught. That is accepted: the check is about a file left changed.

## How the line gets its facts

No fact is computed while drawing. The mod keeps the line's facts in memory and calls `$.ui.invalidate("ui.render")` when they change.

- **The focus item, its status and phase**: from `python3 tools/scripts/snapshot-query.py`, at `session.start` and after each turn that changed `SNAPSHOT.yaml` or anything under `docs/`.
- **The validator's error count and the REVIEW-STALE count**: from one run of `bash tools/scripts/validate-docs.sh`, at the same moments, counting `ERROR` lines and `REVIEW-STALE` lines. While a run is in progress the line shows the last counts; before the first run finishes it shows neither.
- **The routing hint**: the first line of what `hooks/model-routing-hint.sh` prints for the current focus. The hook keeps adding it to the model's context as before.

## Dependencies

- **Hard:** Claude Code 2.1.300 or newer, the version tested. Nothing in this repository or the template must land first.
- **Downstream:** project-os-cockpit [[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt|FEAT-0157]] needs TASK-0198's answer before it builds its segment, and TASK-0203's sync before its acceptance check can be walked.
- **No phase.** No later-phase dependency exists.

## Impact analysis (2026-10-14)

Checked against the requirements and decisions that cover hooks and adapters: [[REQ-0001-Tool-Agnostic-Rules]], [[REQ-0003-Hook-Contracts]], [[REQ-0004-Tool-Specific-Hook-Implementations]], [[REQ-0030-Codex-Receives-Native-Project-OS-Integration]], [[ADR-0001-Tool-Adapter-Architecture]], [[ADR-0002-Hook-Contract-Pattern]]. **No contradiction.**

- REQ-0003 and ADR-0002 require each enforcement point to be a tool-agnostic contract in HOOKS.md, with tool bindings on "Implementations" lines. The plan meets this: the shell-edit check is a new implementation of HC-006, and the model warning and the line get contracts of their own (HC-011, HC-012) before their code.
- REQ-0001 requires rules written once and delivered to every tool. The mod carries no rule. It runs the repo's own scripts and the shared marker path.
- **Tension, accepted and recorded:** REQ-0030 and PHASE-0006 aim at Codex parity. After this feature, Claude Code catches shell edits and Codex does not. HC-010's review budget already has the same gap. The Codex half is listed under "Later" in the feature note.

## Risk scan (2026-10-14)

Three triggers apply, all recorded in [[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface|RISK-0006]]:

1. **A new external dependency with a version constraint**: the mods interface, weeks old.
2. **A new configuration surface**: plugin registration in every repo's `.claude/settings.json`.
3. **Unsandboxed code in every session of every repo**, and a new step at each turn (`git status`) and after each docs change (the validator).

No new environment variable, credential, or licence exposure.

## What the implementation must not do

- Answer a permission check, or change any verdict on `tool.check`.
- Name the cockpit, its service, `COCKPIT_*` variables, or the sidecar anywhere in the template.
- Run anything slow inside a `ui.render` hook.
- Show a count of zero for a fact it could not read.
- Write anything outside the repo except what `session-touch.sh` already writes.
