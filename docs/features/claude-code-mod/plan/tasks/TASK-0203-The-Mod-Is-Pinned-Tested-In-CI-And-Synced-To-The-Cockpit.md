---
type: "[[task]]"
id: TASK-0203
aliases: ["TASK-0203"]
title: "The mod declares the Claude Code version it was tested on, CI validates and tests it, its change note is written, and the template is synced into project-os-cockpit"
status: done
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]]", "[[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface]]"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "S"
due: ""
depends: ["[[TASK-0200-A-File-Changed-From-The-Shell-Counts-As-A-Write-At-Close-Out]]", "[[TASK-0201-A-Session-On-The-Wrong-Model-Is-Named-At-Start]]", "[[TASK-0202-The-Project-Line-Above-The-Prompt]]"]
blocks: []
related: ["[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]", "[[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit]]"]
tests: []
---

# The mod is pinned, tested in CI, and synced to the cockpit

The mods interface is weeks old and can change between Claude Code releases. After this task the template's CI fails when the plugin no longer validates or its tests fail, the plugin says which version it was tested on, and project-os-cockpit carries the mod so cockpit FEAT-0157 can be seen working beside it.

## Definition of Done

- [x] The template's CI workflow runs `claude plugin validate tools/adapters/claude-code/plugin` and `claude plugin test tools/adapters/claude-code/plugin`, with Claude Code installed at a pinned version, and fails the build on either.
- [x] `plugin.json` names the tested version; ADAPTER.md says how to move the pin.
- [x] A change note in the template's record (this repository's `docs/changes/`) for the new behaviour: the line, the shell-edit check, the wrong-model warning, and the new `.claude/settings.json` registration.
- [x] [[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit|TST-0047]]'s procedure matches what was built.
- [x] The template is synced into project-os-cockpit with `tools/scripts/sync-project-os.sh ../project-os`, `generate-adapters.py --check` is clean there, and a session there shows the line. Other fleet repos take the mod on their next sync; this task does not sync them.
- [x] RISK-0006's mitigations are each marked done or still open.

## Steps

- [x] CI.
- [x] Change note and TST-0047.
- [x] Sync into project-os-cockpit and look.

## Result (2026-10-14)

- **CI** (project-os `5307fd6`): the template's `validate-docs.yml` installs `@anthropic-ai/claude-code@2.1.300` and runs `claude plugin validate` and `claude plugin test` on the plugin, in the template repository only, as its other self-tests do. It has not run yet: nothing is pushed.
- **The pin:** `plugin.json` says "Tested on Claude Code 2.1.300"; ADAPTER.md "Moving the tested version" says to change it there and in CI in one commit.
- **Change note:** [[CHG-20261014-Claude-Sessions-Load-The-Project-Os-Plugin]].
- **TST-0047** now reads the facts as they are built: from the snapshot and two greps of the validator, the route from the hint. A person cannot see the model's context, so step 6 asks Claude to quote it.
- **project-os-cockpit** synced (project-os-cockpit `032a6f8`): `generate-adapters.py --check` reports 70 artifacts current, the validator is clean, and a session there with the cockpit's own plugin also on `CLAUDE_CODE_PLUGIN_DIRS` showed `FEAT-0157 doing · PHASE-046 · 0 validator errors · 11 review-stale · route: implement here`, with both plugins in the debug log.
- **RISK-0006:** five mitigations done, one open by its nature (a key renamed on one side only), and one hazard found while building and recorded there (a clone shares its marketplace name).
