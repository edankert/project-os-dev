---
type: adapter
tool: codex
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-09-16
---

# Codex adapter

## Native files

Codex reads the project contract from `AGENTS.md`. `python3 tools/scripts/generate-adapters.py --install-hooks` also creates:

- `.agents/skills/<name>/SKILL.md` from every canonical `tools/skills/<name>/SKILL.md`, matching the Claude skill wrappers.
- `.codex/agents/planner.toml` and `.codex/agents/independent-reviewer.toml` from the same agent instructions used by the Claude adapter. They inherit the session model; no Codex model is pinned. Call an agent only when the task warrants delegation or independent review.
- `.codex/hooks.json` from `tools/adapters/codex/hooks.json`, pointing to `tools/adapters/codex/hooks/dispatch.py`.

The generated skills and agents are checked by `python3 tools/scripts/generate-adapters.py --check` at pre-commit and in CI. Edit their canonical sources, then regenerate. The hook installation leaves an existing `.codex/hooks.json` untouched; `--force-hooks` replaces it after a deliberate review. If a repository already has hooks, merge the project-os entries manually to retain both sets.

## Activation

Project-local hooks load only after Codex trusts the repository's `.codex` config layer. Each changed hook definition must also be reviewed and trusted through `/hooks`. A new session may be needed after installing or changing hooks. See the [Codex hooks guide](https://learn.chatgpt.com/docs/hooks), [skills guide](https://learn.chatgpt.com/docs/build-skills), and [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).

The hook command resolves `tools/adapters/codex/hooks/dispatch.py` from the git root, so a session opened from a subdirectory still reaches the adapter. Python 3.9 or newer is sufficient for the hook runner. Run `bash tools/scripts/test-codex-adapter.sh` to exercise its fixtures, then `bash tools/scripts/validate-docs.sh` for the mechanical document gate.

## Hook contract coverage

| Contract | Native Codex behavior |
|---|---|
| HC-001 document-first | `PreToolUse` denies confidently identified code edits without a focused task or issue. Target repositories are evaluated independently; the untouched template placeholder is exempt. |
| HC-002 startup | `SessionStart` reminds the agent of read order, bootstrap, branch, and work state. |
| HC-003 verification | `PreToolUse` denies terminal status edits with failing linked manual tests or an open-ended waiver. Executable and acceptance tests use the same exemptions as the validator. Missing links produce a reminder because Codex does not currently support the `ask` decision for `PreToolUse`. |
| HC-004 phase alignment | `PostToolUse` reminds the agent to compare a task newly set to `doing` with the focus phase. |
| HC-005 risk scan | `PostToolUse` flags identifiable dependency, environment, and deployment configuration edits. The full risk trigger list still needs agent review. |
| HC-006 close-out | `PostToolUse` records recognized edits per session. `Stop` checks active focus once after a write and asks for completion or a handoff. |
| HC-007 validation | `Stop` runs `validate-docs.sh`; pre-commit and CI remain the hard backstop. |
| HC-008 delegation | `UserPromptSubmit` states the focus and recommends planner or independent reviewer only where useful. |
| HC-009 test execution | The shared pre-push hook and CI runner execute declared tests. |

Codex hook tool coverage includes `apply_patch` and Bash, but an arbitrary shell script may write files without an identifiable target. The adapter detects patch file headers and simple shell redirects; it does not pretend to parse all shell programs. Some specialized tools also bypass tool hooks. The git hook and CI validator therefore remain required, and `/hooks` should be checked when an expected reminder does not appear. This is tracked as project-os-dev RISK-0003.

## Synchronizing

Follow `tools/skills/adapter-sync/SKILL.md` whenever canonical lifecycle rules or skills change. `sync-project-os.py` regenerates the native files after a template sync and installs the Codex hook file only when that target is absent. Existing downstream Codex hooks need a manual merge.
