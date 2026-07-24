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
- `.claude/agents/planner.md` — subagent implementing the LIFECYCLE.md preflight pass (classify, allocate IDs, update the snapshot, create notes), pinned to a fixed Claude model. See "Model routing" below.
- `.claude/agents/independent-reviewer.md` — subagent implementing the QUALITY.md independent-review pass, pinned to a fixed Claude model so `reviewed_by` is deterministic. Subagents can only pin Claude models; when full cross-vendor independence is required, run the review in an external tool and record the frontmatter manually.
- `.claude/settings.json` hooks — installed by `--install-hooks` (copies `hooks.json` when the file is absent; merges the `hooks` key when other settings exist; never overwrites an existing `hooks` key unless `--force-hooks`).
- `.cursor/rules/*.mdc` — the Cursor adapter's rule files, generated from the same sources (see `../cursor/ADAPTER.md`).

Generated files are marked with a do-not-edit header. `--check` verifies they are current without writing (usable at pre-commit/CI). Re-run the generator after any change to `tools/skills/` or `tools/instructions/` (`tools/skills/adapter-sync/SKILL.md` step 1).

## Import strategy

The `CLAUDE.md` file should import project-os instruction files using `@` imports. This keeps rules maintained in one place (`tools/instructions/`) while delivered natively to Claude Code.

### Reference CLAUDE.md

```markdown
# Project: <project-name>

Read SNAPSHOT.yaml at session start to understand current project state and focus.
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
- Workflow authoring: tools/skills/workflow-authoring/SKILL.md
- Backlog grooming: tools/skills/backlog-grooming/SKILL.md
- Risk mitigation: tools/skills/risk-mitigation-planning/SKILL.md
- Impact analysis: tools/skills/impact-analysis/SKILL.md
- Release preparation: tools/skills/release-prep/SKILL.md
- Release verification: tools/skills/release-verification/SKILL.md
- Adapter sync: tools/skills/adapter-sync/SKILL.md
- Project init: tools/skills/project-init/SKILL.md
- Project derive: tools/skills/project-derive/SKILL.md
```

### Notes

- The `@` imports inline the content of each file into Claude Code's context when the CLAUDE.md is loaded
- Core rules (LIFECYCLE) are always imported because it governs every interaction
- STATUSES and QUALITY are listed as reference instructions — Claude Code reads them on demand when relevant
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
chmod +x tools/adapters/claude-code/hooks/*.sh
```

Manual fallback: copy `hooks.json` from this adapter directory into `.claude/settings.json` (merge the `hooks` key if the file already has other settings).

> **Note:** Hook commands use `$CLAUDE_PROJECT_DIR` for reliable path resolution. Claude Code does not guarantee hooks run from the project root, so relative paths are unreliable.

### Hook events and types

| Event | Hooks | Type | Purpose |
|---|---|---|---|
| `PreToolUse` | HC-001 Document-First | `command` | Reads SNAPSHOT.yaml, blocks code edits without focus |
| `PreToolUse` | HC-003 Verification Gate | `command` | **Blocking**: denies status→done/closed/verified while linked TST-* notes are not `passing` (recorded `verification_waiver` escapes; no linked test → `ask`) |
| `PostToolUse` | HC-004 Phase Alignment | `command` | Detects status→doing, reminds about phase check |
| `PostToolUse` | HC-005 Risk Scan Trigger | `command` | Detects package/env/CI file changes |
| `Stop` | HC-006 Close-out Check + HC-007 Docs Validation | `command` | Runs `tools/scripts/validate-docs.sh` and blocks stop on violations; checks focus is cleared, forces close-out if not |
| `SessionStart` | HC-002 Snapshot Freshness | `command` | Reminds agent to read SNAPSHOT.yaml |
| `UserPromptSubmit` | HC-008 Model Routing Hint | `command` | Advisory: maps the focus item's status to the agent that should do the work (planner / main loop / independent-reviewer) |

**All hooks are `command` type** (fast shell scripts, no API calls). This avoids LLM cost/latency and 529 overload errors. Stop hooks use `{decision: "block", reason: "..."}` to force continuation. All scripts use `$CLAUDE_PROJECT_DIR` for path resolution. HC-003 and HC-007 need `python3` on PATH (stdlib only); they fail open with a note if it is missing, so a broken runtime never bricks edits — but treat that note as a setup error.

Session hooks are the innermost of three enforcement layers: the same validator also runs at git pre-commit (`bash tools/scripts/install-git-hooks.sh` to install) and in CI (`.github/workflows/validate-docs.yml`). Session hooks and pre-commit can be bypassed; CI cannot — that layering is deliberate.

See `tools/instructions/HOOKS.md` for the full hook contract specifications and `hooks/` in this directory for the implementations.

## Model routing (lifecycle phase → model)

Claude Code has no built-in "model A for planning, model B for execution" split for project-os phases; the only native combo alias is `opusplan` (Opus in plan mode → Sonnet for execution), and it governs the main loop only. project-os gets per-phase routing from the two generated subagents instead, since a subagent's `model` frontmatter is the one place a model can be pinned declaratively — and it takes precedence over the session model, so the pins hold whatever the session runs, `opusplan` included.

| Lifecycle phase | Runs in | Model |
|---|---|---|
| Preflight / planning (LIFECYCLE preflight) | `planner` subagent | pinned — `PLANNER_MODEL` in `tools/scripts/generate-adapters.py` |
| Implementation | main session loop | the session model (`model` in `.claude/settings.json`, or `/model`) |
| Independent review (LIFECYCLE close-out, QUALITY gate) | `independent-reviewer` subagent | pinned — `REVIEWER_MODEL` in the same file |

Both pins default to the strongest available Claude model, because planning and adversarial review are the phases where capability pays off most.

**These pins do not make the review independent.** `QUALITY.md` and `../../skills/independent-review/SKILL.md` require a *different model family* or a human; Claude Code subagents can only pin Claude models, so every pinned reviewer is same-family with every Claude session that authored the work. Setting the session model to something other than `REVIEWER_MODEL` is still worth doing — it avoids the strictly worse case where the reviewer is literally the authoring model — but it buys less same-model overlap, not independence. A cross-vendor or human pass, recorded manually, is what closes the QUALITY.md gate. The generated reviewer is briefed to disclose this rather than let a differing pin pass for the guarantee. Note also that `PLANNER_MODEL` and `REVIEWER_MODEL` default to the same value, so planning artifacts reviewed by this subagent are same-model reviewed — escalate those.

`HC-008` (`hooks/model-routing-hint.sh`) injects a per-prompt hint derived from the focus item's status so the delegation actually happens; a hook cannot change the session model, so the hint is advisory and the pins do the routing.

Two Claude Code behaviours to know when relying on this. A **resumed** session keeps the model its transcript was saved with, regardless of the `model` key in `.claude/settings.json` — so the "keep the session model off `REVIEWER_MODEL`" advice above silently stops holding after a resume; check `/model`, or start a fresh session. And the agent-file watcher only covers directories that **existed at session start**: creating `.claude/agents/` for the first time needs a new session before the subagents resolve (edits to files in an already-present directory hot-reload within seconds).

To retarget the pins, edit `PLANNER_MODEL`/`REVIEWER_MODEL` and re-run the generator. Downstream repos inherit both the hook and the pins through the template sync plus a generator run (`tools/skills/adapter-sync/SKILL.md`).

## Project-specific customization

After copying the reference CLAUDE.md, projects should add:
1. A "Role of this repo" section describing the project
2. Any project-specific rules not covered by project-os instructions
3. References to project-specific skills or workflows
