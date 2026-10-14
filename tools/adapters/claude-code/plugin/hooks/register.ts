// project-os plugin for Claude Code (project-os-dev FEAT-0041).
//
// Every project-os repo loads this module in every Claude Code session, inside
// a cockpit terminal or not. The template sync places this folder and
// generate-adapters.py registers it in the repo's .claude/settings.json, as a
// marketplace that lives in the repo (tools/adapters/claude-code/ADAPTER.md,
// "The project-os plugin"). Claude Code runs it from this folder, so a sync
// that changes it changes what runs at the next session.
//
// It registers nothing yet. TASK-0200 adds the shell-edit marker, TASK-0201
// the wrong-model warning, and TASK-0202 the project line.

import type { Register } from 'claude-code'

export const register: Register = () => {}
