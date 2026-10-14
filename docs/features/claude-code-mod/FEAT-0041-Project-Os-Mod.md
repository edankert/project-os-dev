---
type: "[[feature]]"
id: FEAT-0041
aliases: ["FEAT-0041"]
title: "A project-os mod catches files edited from the shell and a session running on the wrong model"
status: backlog
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["project-os-cockpit, 2026-10-08: Edwin asked for a review of Claude Code mods for project-os and the cockpit; the plan, cockpit PHASE-046, recorded two follow-ups for project-os and filed neither", "project-os-dev, 2026-10-14: Edwin asked which parts belong in project-os and which in the cockpit, then: 'yes, file them and update FEAT-0157'"]
goal: "A Claude Code session in any project-os repo loads a small project-os mod that notices files changed from the shell and warns when the session runs on a model other than the pinned one, so both are caught in every repo and not only in cockpit terminals."
requirements: []
tasks: []
release: ""
acceptance_exception: ""
acceptance: ""
design: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
review_round: ""
related:
  - "[[ISS-0106-Project-Os-As-A-Plugin]]"
  - "[[project-os-cockpit#PHASE-046-A-Claude-Session-Talks-To-The-Cockpit-Through-A-Plugin]]"
  - "[[project-os-cockpit#FEAT-0156-Claude-Sessions-Report-Through-The-Cockpit-Plugin]]"
  - "[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]"
  - "[[project-os-cockpit#REFERENCE-FUNCTION-HOOKS-REVIEW]]"
---

# A project-os mod catches files edited from the shell and a session running on the wrong model

## Goal

A Claude Code session in any project-os repo loads a small mod that project-os ships. A mod is TypeScript inside a Claude Code plugin, which Claude Code runs in its own process. The first version does two things the shell hooks cannot. It notices files that were changed from the shell, and it warns when the session runs on a model other than the pinned one. Both work in every repo, whether or not the session runs in a cockpit terminal.

## Scope

**The first version:**

1. **Files changed from the shell count as writes.** At the end of every turn (`turn.complete`), the mod runs `git status --porcelain` and compares it with the start of the turn. A file edited with `sed -i` or a script run through Bash then counts as a write, so the HC-006 close-out check applies to it. Today only the Edit and Write tools count. HC-001, the document-first gate, still cannot stop such an edit before it happens. The mod can only name it afterwards.
2. **A session on the wrong model is named at start.** At `session.start`, the mod compares the session's model with `model` in `.claude/settings.json` and draws a one-line warning when they differ. A resumed session keeps the model its transcript was saved with, whatever the pin says. project-os-cockpit's CLAUDE.md ("Model routing") describes the surprise and asks the person to check `/model` by hand.

**Later, once the first version has shown the interface can be pinned:**

- HC-006's session marker held in the mod's memory, not in a marker file.
- HC-010's review budget counted from `agent.spawn` and `tool.call` events, replacing `review-budget.sh` and `review-budget.py` for Claude Code.
- HC-008's routing hint drawn as a status line for the person, not added to the model's context. That also removes its 600-character cap.
- The project half of the band above the prompt: the focus item, its status and phase, and the validator's error count. All of it is read from the repo. The cockpit's half of the same line (what other projects owe, an "Open in cockpit" button) stays in [[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]. There is one line, drawn by this mod, which adds the cockpit's facts when the cockpit's terminal says its service is running.
- Commands that answer at once without starting an AI turn, prefixed so they do not clash with Claude Code's own (`/pos-q <ID>` runs `snapshot-query.py`, `/pos-validate` runs the validator, `/pos-where` shows where the focus phase stands). Code computes their answers, so the counts can be trusted in a way an AI's summary cannot.

**Out of scope:**

- HC-001 and HC-003 stay shell scripts. They work, they are tested, and Codex uses the same contracts.
- Everything that needs the cockpit's background service: telemetry, dispatch, and answering permission prompts. Those are cockpit PHASE-046.
- How project-os reaches each repo as a plugin. That is [[ISS-0106-Project-Os-As-A-Plugin]].

## Findings

- Mods shipped in Claude Code v2.1.287. The cockpit phase was planned on 2.1.292 on 2026-10-08, and the installed version on 2026-10-14 is 2.1.299. The interface is weeks old, so the mod declares the version it was tested on, and CI runs `claude plugin validate` and `claude plugin test`. Documentation: https://code.claude.com/docs/en/plugins/mods/overview.
- `tools/instructions/HOOKS.md` stays the source of each contract. The mod is the Claude Code way of meeting it, beside the shell hooks and Codex's `dispatch.py`. Each HC entry that the mod meets names it under "Implementations".
- A mod runs with the user's permissions and no sandbox. This mod never answers a permission check. It only reads events, runs `git status` and draws lines.
- Mods load `.ts` files directly, so the fleet repos would need no Node toolchain. That comes from the 2026-10-08 reading of the documentation and is not yet tried here.
- Drawing appears only in the terminal and the Desktop app. Hooks also run in VS Code, `claude -p` and cloud sessions, where nothing drawn is seen. So each warning is also written where the model and the transcript see it.
- The risk scan applies on two counts: a new external dependency with a version constraint, and code that runs unsandboxed with the user's permissions. Per feature-scaffold's short path, the `RISK-*` note is written when this feature starts.

## Open questions

1. How does the mod reach each repo before [[ISS-0106-Project-Os-As-A-Plugin]] is decided? The candidates are the `CLAUDE_CODE_PLUGIN_DIRS` environment variable, a plugin directory that the template sync copies, or waiting for the plugin route.
2. Does a shell edit with no focus item only produce a warning, or does it make the close-out check block, as an Edit-tool write does?
3. Should Codex get the same shell-edit check, for example `dispatch.py` running `git status` at Stop, so the two tools behave alike?
4. Do the band's project half and the instant commands stay in this feature, or become their own feature when they start?

## Links

- Cockpit plan: [[project-os-cockpit#PHASE-046-A-Claude-Session-Talks-To-The-Cockpit-Through-A-Plugin]], "Out of Scope", legs 5 and 6.
- Hook contracts: `tools/instructions/HOOKS.md` (HC-001, HC-006, HC-008, HC-010).
