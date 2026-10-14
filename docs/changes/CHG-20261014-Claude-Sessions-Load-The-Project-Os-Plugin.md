---
type: "[[change]]"
id: CHG-20261014-Claude-Sessions-Load-The-Project-Os-Plugin
title: "Claude Code sessions in every synced repo load a project-os plugin: a line above the prompt, a warning on the wrong model, and shell edits counted at close-out"
status: merged
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]]"]
commit: "project-os 96cfc97, 1e09218, 5307fd6"
pr: ""
impacts: ["tools/adapters/claude-code/plugin/", "tools/scripts/generate-adapters.py", ".claude/settings.json", ".claude-plugin/marketplace.json", "tools/sync/MANIFEST.yaml", "tools/instructions/HOOKS.md", "tools/adapters/claude-code/ADAPTER.md", "tools/adapters/claude-code/hooks/session-touch.sh", ".github/workflows/validate-docs.yml"]
platforms: []
issues: ["[[ISS-0106-Project-Os-As-A-Plugin]]"]
features: ["[[FEAT-0041-Project-Os-Mod]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REFERENCE-PROJECT-LINE-CONTRACT]]", "[[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface]]", "[[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit]]", "[[ISS-0107-Two-Template-Tests-Fail-Since-The-Fix-What-You-Find-Rule]]"]
---

# Claude Code sessions load a project-os plugin

## Summary

After its next template sync, every project-os repo shows one line above the Claude Code prompt, for example `FEAT-0157 doing · PHASE-046 · 0 validator errors · 11 review-stale · route: implement here`. The line is drawn by a small plugin that project-os now ships, and the model never reads it, so it costs no tokens. The same plugin does two more things:

- **A session on a model other than the pin is named.** A warning row sits above the line, and the same sentence goes into the model's context.
- **A file changed through the shell counts as a write at close-out.** Before, only the Edit, Write and NotebookEdit tools reminded the close-out check.

Nobody installs anything. The sync copies the plugin and the generator registers it in the repo's own `.claude/settings.json`.

## Impact

- **New in every repo after a sync:** `tools/adapters/claude-code/plugin/`, and a generated `.claude-plugin/marketplace.json` naming a marketplace `project-os-<project>`, from `project.name` in `SNAPSHOT.yaml`.
- **`.claude/settings.json` gains two keys**, merged by `generate-adapters.py --install-hooks`: `extraKnownMarketplaces` (`"path": "./"`) and `enabledPlugins`. An entry set to `false` stays off. `generate-adapters.py --check` now also fails on a missing registration (`UNREGISTERED`), so a repo synced without `--install-hooks` fails CI until it is run.
- **Machine-wide:** Claude Code records each repo's marketplace once in `~/.claude/plugins/known_marketplaces.json`, on the first session there. No plugin is copied into `~/.claude`; it runs from the repo folder.
- **HOOKS.md:** HC-006 names the plugin as a second recorder of writes; new HC-011 (the pinned model) and HC-012 (the project line). Codex has none of the three.
- **ADAPTER.md:** how the plugin loads, how to turn it off in one repo, how to move the tested Claude Code version, the rules another plugin follows to add to the line, and a note that a second copy of a repo shares its marketplace name.
- **Template CI:** validates and tests the plugin on Claude Code 2.1.300, in the template repository only.
- **Each session runs** `git` at the start and end of every main-loop turn, and the validator in the background at session start and after a turn that changed `SNAPSHOT.yaml` or `docs/`.

## Documentation Coverage (All Types Considered)

- features: updated (FEAT-0041)
- requirements: not-applicable
- tasks: updated (TASK-0198 to TASK-0203)
- issues: updated (ISS-0106 fixed); new (ISS-0107, two template tests already failing before this work)
- tests: new (`test-plugin-registration.sh`, nine cases; `plugin/tests/project-os.test.ts`, sixteen cases; TST-0047 for the walk)
- workflows: not-applicable
- decisions: not-applicable (ISS-0106's option (a), recorded there)
- risks: updated (RISK-0006, mitigations marked)
- changes: new
- snapshot: updated
