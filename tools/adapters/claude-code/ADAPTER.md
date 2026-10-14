---
type: adapter
tool: claude-code
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-07-17
---

# Claude Code Adapter

## Overview

Claude Code reads project instructions from `CLAUDE.md` in the repo root. It supports `@file` imports to include content from other files, making it well-suited for the project-os instruction model.

## Native instruction format

- **File**: `CLAUDE.md` (repo root)
- **Syntax**: Markdown with `@path/to/file.md` import directives
- **Overflow**: Additional rules in `.claude/rules/*.md` (auto-loaded, no import needed)
- **Limit**: Keep `CLAUDE.md` concise; Claude Code reads it at every session start

## Native skills, subagent, and one-step install (generated)

`python3 tools/scripts/generate-adapters.py --install-hooks` derives the full native adapter surface from the canonical playbooks in one idempotent step:

- `.claude/skills/<name>/SKILL.md` — one native skill per `tools/skills/*/SKILL.md` playbook, auto-discovered by Claude Code and invocable as `/<name>` (e.g. `/close-out`, `/issue-intake`). Each generated skill's `description` carries the playbook's "When to use" triggers so Claude invokes it unprompted; its body directs execution back to the canonical playbook, which stays the single source of truth.
- `.claude/agents/planner.md` — subagent implementing the LIFECYCLE.md preflight pass (classify, allocate IDs, update the snapshot, create notes), pinned to a fixed Claude model. See "Delegation and model pins" below.
- `.claude/agents/independent-reviewer.md` — subagent implementing the QUALITY.md independent-review pass, pinned to a fixed Claude model so `reviewed_by` is deterministic. What makes the review independent is a clean context, not a different vendor (`QUALITY.md`, "Independent review (clean-context)"); an external tool or a human may still review, with the frontmatter recorded by hand.
- `.claude/settings.json` hooks — installed by `--install-hooks` (copies `hooks.json` when the file is absent; merges the `hooks` key when other settings exist; never overwrites an existing `hooks` key unless `--force-hooks`).
- `.cursor/rules/*.mdc` — the Cursor adapter's rule files, generated from the same sources (see `../cursor/ADAPTER.md`).
- `.claude-plugin/marketplace.json` and two keys in `.claude/settings.json` — the repo's own marketplace for the project-os plugin, and its registration. See "The project-os plugin" below.

Generated files are marked with a do-not-edit header. `--check` verifies they are current without writing (usable at pre-commit/CI). Re-run the generator after any change to `tools/skills/` or `tools/instructions/` (`tools/skills/adapter-sync/SKILL.md` step 1).

## Import strategy

The `CLAUDE.md` file should import project-os instruction files using `@` imports. This keeps rules maintained in one place (`tools/instructions/`) while delivered natively to Claude Code.

### Reference CLAUDE.md

```markdown
# Project: <project-name>

The session-start hook prints the current focus and in-flight work from SNAPSHOT.yaml.
Read CONTEXT.md for the full project-os contract, edit policy, and invariants.

## project-os documentation system (core rules -- always active)

@tools/instructions/LIFECYCLE.md
@tools/instructions/STATUSES.md
@tools/instructions/QUALITY.md

## Reference instructions (read when relevant)

These files contain detailed rules. Read them when performing the related operation:
- Snapshot structure and update rules: tools/instructions/SNAPSHOT.md
- Allowed taxonomy values: tools/instructions/TAXONOMY.md
- Required link graphs: tools/instructions/TRACEABILITY.md
- ADR conventions: tools/instructions/DECISIONS.md
- Ownership rules: tools/instructions/OWNERSHIP.md
- Obsidian conventions: tools/instructions/OBSIDIAN.md
- Handoff/recovery: tools/instructions/HANDOFF.md
- Importing from existing projects: tools/instructions/IMPORTING.md
- Syncing template updates: tools/instructions/SYNCING.md
- Hook contracts: tools/instructions/HOOKS.md
- Markdown formatting: tools/instructions/MARKDOWN.md
- Writing clearly (prose, commit messages, replies): tools/instructions/WRITING.md
- Acceptance tests and the release test: tools/instructions/TESTING.md

## Skill playbooks (read before performing these operations)

- Issue intake: tools/skills/issue-intake/SKILL.md
- Phase planning: tools/skills/phase-planning/SKILL.md
- Feature scaffold: tools/skills/feature-scaffold/SKILL.md
- Task breakdown: tools/skills/task-breakdown/SKILL.md
- Close-out: tools/skills/close-out/SKILL.md
- Change note: tools/skills/change-note/SKILL.md
- Status transition: tools/skills/status-transition/SKILL.md
- Snapshot sync: tools/skills/snapshot-sync/SKILL.md
- Test authoring: tools/skills/test-authoring/SKILL.md
- ADR authoring: tools/skills/adr-authoring/SKILL.md
- Risk scan: tools/skills/risk-scan/SKILL.md
- Independent review: tools/skills/independent-review/SKILL.md
- Docs audit: tools/skills/docs-audit/SKILL.md
- Ad-hoc intake: tools/skills/ad-hoc-intake/SKILL.md
- Inbox triage: tools/skills/inbox-triage/SKILL.md
- Workflow authoring: tools/skills/workflow-authoring/SKILL.md
- Backlog grooming: tools/skills/backlog-grooming/SKILL.md
- Risk mitigation: tools/skills/risk-mitigation-planning/SKILL.md
- Impact analysis: tools/skills/impact-analysis/SKILL.md
- Release preparation: tools/skills/release-prep/SKILL.md
- Release verification: tools/skills/release-verification/SKILL.md
- Adapter sync: tools/skills/adapter-sync/SKILL.md
- Project init: tools/skills/project-init/SKILL.md
- Project derive: tools/skills/project-derive/SKILL.md
- Design authoring: tools/skills/design-authoring/SKILL.md
- Release test procedure: tools/skills/release-test-procedure/SKILL.md
- Release test preparation: tools/skills/release-test-prep/SKILL.md
```

### Notes

- The `@` imports inline the content of each file into Claude Code's context when the CLAUDE.md is loaded
- Core rules (LIFECYCLE) are always imported because it governs every interaction
- STATUSES and QUALITY are imported too in the reference CLAUDE.md above; the other instruction files are listed as references and read on demand
- Reference instructions are listed as paths (not imported) to keep context window lean
- Skill playbooks are listed as paths for the same reason

## Hook support

Claude Code supports shell hooks via project-level settings files. project-os hooks should be installed in the **project repo** (not `~/.claude/`) because they reference project-specific files (SNAPSHOT.yaml, note frontmatter).

### Where to install

| File | Committed | Scope | Use when |
|---|---|---|---|
| `.claude/settings.json` | Yes (shared) | Everyone who clones | **Default** — hooks enforce shared project rules |
| `.claude/settings.local.json` | No (gitignored) | Just you | Personal testing before committing |

**Use `.claude/settings.json`** (committed) as the default. project-os hooks enforce project rules (document-first, verification gating), so all team members should get them automatically.

### Installation

Preferred (installs hooks and regenerates the native skills/subagent/Cursor rules in one idempotent step):

```bash
python3 tools/scripts/generate-adapters.py --install-hooks
```

`--install-hooks` also sets the executable bit on every file in `hooks/`, and it does that even when it leaves an existing `hooks` key alone. Settings register each hook by bare path with no interpreter in front, so a hook without the bit fails with `Permission denied` on every event; re-run the command after any sync that brings in a new hook. If `git config core.fileMode` is `false` in your repo, git ignores the bit you just set, and a fresh clone gets an unexecutable hook again — record it once with `git update-index --chmod=+x tools/adapters/claude-code/hooks/*` and commit.

Manual fallback: copy `hooks.json` from this adapter directory into `.claude/settings.json` (merge the `hooks` key if the file already has other settings), then `chmod +x tools/adapters/claude-code/hooks/*`.

> **Note:** Hook commands use `$CLAUDE_PROJECT_DIR` for reliable path resolution. Claude Code does not guarantee hooks run from the project root, so relative paths are unreliable.

### Hook events and types

| Event | Hooks | Type | Purpose |
|---|---|---|---|
| `PreToolUse` | HC-001 Document-First | `command` | Reads SNAPSHOT.yaml, blocks code edits without focus |
| `PreToolUse` | HC-003 Verification Gate | `command` | **Blocking**: denies a transition to a terminal status while linked TST-* notes are not `passing` (the statuses are listed once in HOOKS.md HC-003) (recorded `verification_waiver` escapes; no linked test → `ask`) |
| `PostToolUse` | HC-004 Phase Alignment | `command` | Detects status→doing, reminds about phase check |
| `PostToolUse` | HC-005 Risk Scan Trigger | `command` | Detects package/env/CI file changes |
| `PostToolUse` | HC-006 Session Touch | `command` | Records that the session wrote a file, so the Stop hook can tell a turn that did work from one that did not |
| `Stop` | HC-006 Close-out Check + HC-007 Docs Validation | `command` | Runs `tools/scripts/validate-docs.sh` and blocks stop on violations every time; checks focus is cleared, and forces close-out if not — but only on a stop that follows a write |
| `SessionStart` | HC-002 Startup orientation | `command` | Prints focus, counts and in-flight items from `tools/scripts/snapshot-slice.py`; the old reminder only when that fails |
| `UserPromptSubmit` | HC-008 Delegation Hint | `command` | Advisory: states the focus item, its status and its phase, and who writes the note for new work; names the planner only for a multi-item scaffold or an ambiguous ask, the reviewer only in review states |

**All hooks are `command` type** (fast shell scripts, no API calls). This avoids LLM cost/latency and 529 overload errors. Stop hooks use `{decision: "block", reason: "..."}` to force continuation. All scripts use `$CLAUDE_PROJECT_DIR` for path resolution. HC-003 and HC-007 need `python3` on PATH (stdlib only); they fail open with a note if it is missing, so a broken runtime never bricks edits — but treat that note as a setup error.

Session hooks are the innermost of the three enforcement layers `tools/instructions/QUALITY.md` "Documentation Fidelity" names; `bash tools/scripts/install-git-hooks.sh` installs the pre-commit one.

See `tools/instructions/HOOKS.md` for the full hook contract specifications and `hooks/` in this directory for the implementations.

## Delegation and model pins (lifecycle phase → agent)

Claude Code has no built-in "model A for planning, model B for execution" split for project-os phases; the only native combo alias is `opusplan` (Opus in plan mode → Sonnet for execution), and it governs the main loop only. project-os routes by lifecycle phase through the two generated subagents instead, since a subagent's `model` frontmatter is the one place a model can be pinned declaratively — and it takes precedence over the session model, so the pins hold whatever the session runs.

| Lifecycle phase | Runs in | Model |
|---|---|---|
| Preflight / planning (LIFECYCLE preflight) | the main loop for a single issue or task; the `planner` subagent for a multi-item scaffold or an ambiguous ask | pinned — `PLANNER_MODEL` in `tools/scripts/generate-adapters.py` |
| Implementation | main session loop | the session model (`model` in `.claude/settings.json`, or `/model`) |
| Independent review (LIFECYCLE close-out, QUALITY gate) | `independent-reviewer` subagent | pinned — `REVIEWER_MODEL` in the same file |

The pins are a choice revisited at each model release, not a standing claim about the strongest model available. As of 2026-09-24 both are `claude-opus-5-5` at `effort: medium` (project-os-dev TASK-0156; before that `claude-opus-5`, ISS-0057 and ISS-0058): the Opus 5.5 prompting guide reports that at `medium` it matches or beats Opus 5 at `high` with fewer tokens. Opus 5 was first chosen because it lists at half of Fable 5.1 per token, ADR-0013 makes the reviewer's model a preference rather than a gate, and nothing about the planner is a gate at all. Which model is cheaper *per task* is unmeasured — fewer tokens at a higher price can win — so treat the pins as a current choice, not a finding. Planning and adversarial review reward capability; the model guides also say review quality holds at lower effort, so the reviewer does not need the highest effort the harness allows. Measure on your own work before raising it.

**What makes the review independent is stated once, in `QUALITY.md` "Independent review (clean-context)"** (ADR-0013), and a subagent provides it by construction. The pinned model being the same as the authoring model is expected and is not a defect; what must never happen is the authoring session reviewing its own work. `reviewed_by` records the model as provenance, not as a compliance token.

`HC-008` (`hooks/model-routing-hint.sh`) injects a per-prompt line stating the focus item, its status and its phase, and who writes the note for new work; it recommends the planner only for a multi-item scaffold or an ambiguous ask and the reviewer only in review states. A hook cannot change the session model, so the hint is advisory and the pins do the routing. The script keeps its filename so existing `.claude/settings.json` files keep resolving.

Two Claude Code behaviours to know when relying on this. A **resumed** session keeps the model its transcript was saved with, regardless of the `model` key in `.claude/settings.json`; check `/model` if it matters, or start a fresh session. And the agent-file watcher only covers directories that **existed at session start**: creating `.claude/agents/` for the first time needs a new session before the subagents resolve. Edits to an agent file were expected to hot-reload, but on 2026-09-24 two reviewers launched after `planner.md` and `independent-reviewer.md` were regenerated both ran the old definition, body and model pin (project-os-dev TASK-0156). After retargeting the pins, start a new session before relying on them.

To retarget the pins, edit `PLANNER_MODEL`/`REVIEWER_MODEL` and re-run the generator. Downstream repos inherit both the hook and the pins through the template sync plus a generator run (`tools/skills/adapter-sync/SKILL.md`).

## The project-os plugin

Every Claude Code session in a project-os repo loads a small plugin that project-os ships, in `tools/adapters/claude-code/plugin/` (project-os-dev FEAT-0041). A plugin is the only way Claude Code lets code draw above the prompt or read the session's model, and it runs inside Claude Code's own process rather than as a script per event. The shell hooks above stay: they also serve Codex, and they work today.

**How a repo loads it.** The template sync copies the plugin folder, and `generate-adapters.py --install-hooks` (which the sync runs) registers it. Registering takes two files:

- `.claude-plugin/marketplace.json` at the repo root, generated, lists the plugin folder by a path inside the repo. It names a marketplace of the repo's own: `project-os-<project>`, from `project.name` in `SNAPSHOT.yaml` (the folder name when that is the template's placeholder).
- `.claude/settings.json` gets two keys, merged with whatever else is there: `extraKnownMarketplaces` declares that marketplace with `{ "source": "directory", "path": "./" }`, and `enabledPlugins` turns on `project-os@project-os-<project>`.

Claude Code runs the plugin from the repo's folder; it makes no copy. A sync that changes the plugin therefore changes what runs from the next session on, with no version bump and no install. `generate-adapters.py --check` reports a stale `marketplace.json` and a missing registration.

**Why the name differs in every repo.** Claude Code records each marketplace once per machine (`~/.claude/plugins/known_marketplaces.json`), by name, with the absolute path of the repo that registered it. Two repos sharing a name ran each other's copy of the plugin (TASK-0198, Claude Code 2.1.300). If a project is renamed, the generator replaces the old registration with the new name. Claude Code may still hold the old name for that folder; `claude plugin marketplace remove project-os-<old name>` clears it.

**What a person sees the first time.** Nothing to install. On the first session in a repo, Claude Code registers the marketplace in the background and the plugin loads in that same session. Claude Code asks its usual question about trusting a new folder, and nothing else.

**Turning it off in one repo.** Set `"project-os@project-os-<project>": false` under `enabledPlugins`: in `.claude/settings.local.json` for yourself only, or in `.claude/settings.json` for everyone. The generator never turns it back on.

**What Claude Code writes beside it.** Each time it loads the plugin, Claude Code writes its type declarations into `plugin/.claude-plugin/types/`, with a `.gitignore` of their own. The sync neither copies nor deletes that folder (`tools/sync/MANIFEST.yaml`, `excludes:`). The plugin's `tsconfig.json` extends the one there, so an editor can check `register.ts` once a session has loaded it.

**Inside a cockpit terminal** the cockpit's own plugin loads as well, through `CLAUDE_CODE_PLUGIN_DIRS`. The two share the line above the prompt without either naming the other; the contract is in project-os-dev REFERENCE-PROJECT-LINE-CONTRACT.

### What the plugin does

- **A file changed from the shell counts as a write at close-out** (HC-006). The plugin fingerprints the working tree with `git` when a main-loop turn starts and when it stops, and leaves the marker `hooks/session-touch.sh` leaves when the two differ, at the path `hooks/shared/session-marker.sh` gives.
- **A session on the wrong model is named** (HC-011): a warning row above the project line, and the same sentence in the model's context.
- **The project line above the prompt** (HC-012): for example `FEAT-0157 doing · PHASE-046 · 2 validator errors · 61 review-stale · route: implement here`.

Its tests run with `claude plugin test tools/adapters/claude-code/plugin`. Use the binary itself: a shell alias that puts an option before `plugin` makes the command refuse to run.

### Moving the tested version

`plugin.json`'s description names the Claude Code version the plugin was tested on, and the template's CI (`.github/workflows/validate-docs.yml`) installs exactly that version to run `claude plugin validate` and `claude plugin test`. To move to a newer release: install it, run both commands and a live session, then change the version in both places in one commit. The interface is early access and may change between releases, so the pin moves on purpose, never by itself.

### A copy of a repo in a second folder

A clone or worktree of a repo carries the same marketplace name. Claude Code keeps one registration per name per machine, so a session started in the second folder re-points it there, and the next session in the first folder points it back. Each session still loads a plugin, but possibly the other folder's copy until that happens. This matters only when the two copies' plugins differ. `claude plugin marketplace list` shows which folder a name points at.

### The project line

There is one line above the Claude Code prompt, and the project-os plugin draws it. Another plugin may add its own facts to the end of the same line. The two never call each other; they meet only in the drawing that Claude Code passes from one plugin's `ui.render` hook to the next. The cockpit's plugin is the first to do this. These rules were checked live in Claude Code 2.1.300 (project-os-dev TASK-0198); the history of how they were chosen is project-os-dev REFERENCE-PROJECT-LINE-CONTRACT.

1. **The project-os plugin draws its line as one Box keyed `project-os:line`**, laid out as a row. Its first child is a Text holding the project facts, with `wrap: "truncate-end"`, so a narrow terminal cuts the line from the right.
2. **Another plugin's facts are a Box keyed `segment:<plugin>`**, for example `segment:cockpit`, laid out as a row, at most one row high. Its first child starts with the separator ` · `. Keys of Buttons inside it start with the plugin's name.
3. **Every hook on the band calls `next(e)` first.** If `e.props.hasSurvey` is true, it returns what `next(e)` gave, unchanged.
4. **Whichever hook is outer joins the two, so their order does not matter.** The plugin Claude Code loads first is the outer one: a plugin from `CLAUDE_CODE_PLUGIN_DIRS` is outer to one from the repo's settings.
   - The project-os plugin takes every `segment:*` element out of the tree beneath and appends them to its line, in the order found. The line goes where the first segment stood. With no segment, it returns a column Box holding the tree beneath and then its line.
   - Another plugin looks for `project-os:line` in the tree beneath. If it is there, it appends its segment as that Box's last child. If not, it returns a column Box holding the tree beneath and then its segment.
5. **The tree from `next(e)` is frozen, and the engine's own node must stay in it.** Build a new tree from copies; changing it in place throws, and Claude Code skips the hook. Keep the `{ "type": "engine" }` node where it was. A join that dropped it was not drawn.
6. **A plugin answers presses on its own Buttons through `ui.press`, by key.** A Button moved into another plugin's tree still raises `ui.press` for the plugin that drew it, and its own `onPress` runs. Matching by key keeps working even if a later release changes that.
7. **Each plugin refreshes the band itself**, with `$.ui.invalidate("ui.render")` when its facts change; the whole chain redraws. No hook computes anything slow while drawing.
8. **A fact that cannot be read is left out, never shown as zero.**
9. **The wrong-model warning is not part of the line.** It is a row of its own just above it.

## Project-specific customization

After copying the reference CLAUDE.md, projects should add:
1. A "Role of this repo" section describing the project
2. Any project-specific rules not covered by project-os instructions
3. References to project-specific skills or workflows
