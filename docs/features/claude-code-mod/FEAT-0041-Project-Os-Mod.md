---
type: "[[feature]]"
id: FEAT-0041
aliases: ["FEAT-0041"]
title: "A project-os mod draws the project line above the Claude Code prompt, catches files edited from the shell, and names a session running on the wrong model"
status: doing
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["project-os-cockpit, 2026-10-08: Edwin asked for a review of Claude Code mods for project-os and the cockpit; the plan, cockpit PHASE-046, recorded two follow-ups for project-os and filed neither", "project-os-dev, 2026-10-14: Edwin asked which parts belong in project-os and which in the cockpit, then: 'yes, file them and update FEAT-0157'", "project-os-cockpit, 2026-10-14, Edwin choosing how to finish PHASE-046: 'Build FEAT-0041 too' (build project-os's mod and its line upstream first, then FEAT-0157, then test); he rejected building only the cockpit parts now, and the cockpit drawing its own temporary line"]
goal: "A Claude Code session in any project-os repo loads a small project-os mod that shows where the project stands on one line above the prompt, notices files changed from the shell, and warns when the session runs on a model other than the pinned one, in every repo and not only in cockpit terminals."
requirements: []
tasks:
  - "[[TASK-0198-Two-Plugins-Share-The-Line-Above-The-Prompt-Checked-Live]]"
  - "[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]"
  - "[[TASK-0200-A-File-Changed-From-The-Shell-Counts-As-A-Write-At-Close-Out]]"
  - "[[TASK-0201-A-Session-On-The-Wrong-Model-Is-Named-At-Start]]"
  - "[[TASK-0202-The-Project-Line-Above-The-Prompt]]"
  - "[[TASK-0203-The-Mod-Is-Pinned-Tested-In-CI-And-Synced-To-The-Cockpit]]"
issues: ["[[ISS-0106-Project-Os-As-A-Plugin]]"]
release: ""
acceptance_exception: ""
acceptance: "[[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit]]"
design: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
review_round: ""
related:
  - "[[ISS-0106-Project-Os-As-A-Plugin]]"
  - "[[REFERENCE-PROJECT-LINE-CONTRACT]]"
  - "[[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface]]"
  - "[[project-os-cockpit#PHASE-046-A-Claude-Session-Talks-To-The-Cockpit-Through-A-Plugin]]"
  - "[[project-os-cockpit#FEAT-0156-Claude-Sessions-Report-Through-The-Cockpit-Plugin]]"
  - "[[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt]]"
  - "[[project-os-cockpit#REFERENCE-FUNCTION-HOOKS-REVIEW]]"
---

# A project-os mod draws the project line, catches shell edits, and names a wrong model

**Started 2026-10-14.** Edwin chose to finish cockpit PHASE-046 by building this feature first, upstream, then cockpit [[project-os-cockpit#FEAT-0157-The-Project-State-Sits-Above-The-Claude-Prompt|FEAT-0157]], then testing both. The delivery plan is `plan/PLAN.md`; the acceptance check is [[TST-0047-A-Claude-Session-Shows-The-Project-Line-And-Names-A-Wrong-Model-And-A-Shell-Edit|TST-0047]].

## Goal

A Claude Code session in any project-os repo loads a small mod that project-os ships. A mod is TypeScript inside a Claude Code plugin, which Claude Code runs in its own process. The first version does three things the shell hooks cannot. It shows where the project stands on one line above the prompt. It notices files that were changed from the shell. It warns when the session runs on a model other than the pinned one. All three work in every repo, whether or not the session runs in a cockpit terminal.

## Scope

**The first version:**

1. **The mod reaches every repo.** The template sync places the plugin in each repo and registers it in `.claude/settings.json`, the way it already generates `.claude/agents/` and `.claude/skills/`. This is [[ISS-0106-Project-Os-As-A-Plugin]]'s option (a). Without it the mod would load only where something sets `CLAUDE_CODE_PLUGIN_DIRS`, which today is only a cockpit terminal.
2. **Files changed from the shell count as writes.** Before the close-out check runs at the end of a turn, the mod compares `git status --porcelain` with the start of the turn. A file edited with `sed -i` or by a script run through Bash then counts as a write, so the HC-006 close-out check applies to it as it does to an Edit-tool write. HC-001, the document-first gate, still cannot stop such an edit before it happens. The mod can only name it afterwards.
3. **A session on the wrong model is named at start.** At `session.start`, the mod compares the session's model with `model` in `.claude/settings.json`. When they differ it draws a warning row above the prompt and tells the model too. A resumed session keeps the model its transcript was saved with, whatever the pin says.
4. **The project line.** One line above the prompt shows the focus item with its status and phase, the validator's error count, the REVIEW-STALE count, and the routing hint (HC-008). Every fact is computed in the background by the repo's own scripts, never while drawing.
5. **Room for the cockpit's facts on the same line.** The line is drawn so that another plugin can add a segment to its end through Claude Code's drawing chain. The cockpit plugin uses this to add what needs the person and an "Open in cockpit" button. project-os never names the cockpit. The rules are [[REFERENCE-PROJECT-LINE-CONTRACT]].

**Later, once the first version has shown the interface can be pinned:**

- HC-006's session marker held in the mod's memory, not in a marker file.
- HC-010's review budget counted from `agent.spawn` and `tool.call` events, replacing `review-budget.sh` and `review-budget.py` for Claude Code.
- Taking the routing hint out of the model's context. The first version shows it to the person on the line and leaves the UserPromptSubmit hook alone, because the model reads the hint to decide when to delegate.
- Commands that answer at once without starting an AI turn, prefixed so they do not clash with Claude Code's own (`/pos-q <ID>` runs `snapshot-query.py`, `/pos-validate` runs the validator, `/pos-where` shows where the focus phase stands).
- The same shell-edit check for Codex, for example `dispatch.py` running `git status` at Stop.

**Out of scope:**

- HC-001 and HC-003 stay shell scripts. They work, they are tested, and Codex uses the same contracts.
- Everything that needs the cockpit's background service: telemetry, dispatch, answering permission prompts, and the cockpit's facts on the line. Those are cockpit PHASE-046.
- A plugin marketplace (ISS-0106 options (b) and (c)).

## Findings

- Mods shipped in Claude Code v2.1.287. The installed version on 2026-10-14 is 2.1.300. The interface is weeks old, so the mod declares the version it was tested on, and CI runs `claude plugin validate` and `claude plugin test` ([[RISK-0006-The-Project-Os-Mod-Runs-Unsandboxed-In-Every-Session-On-A-New-Interface|RISK-0006]]).
- `tools/instructions/HOOKS.md` stays the source of each contract. The mod is the Claude Code way of meeting it, beside the shell hooks and Codex's `dispatch.py`. HC-006 gains the mod under "Implementations"; the wrong-model warning and the project line become two new contracts, because no existing one describes them.
- A mod runs with the user's permissions and no sandbox. This mod never answers a permission check. It reads events, runs `git status` and the repo's own scripts, writes the HC-006 session marker, and draws.
- `claude plugin marketplace add` takes `--scope project`, which declares a marketplace in the repo's own `.claude/settings.json`. A folder inside the repo can therefore be offered to every session there. Whether a person must still confirm the install once per machine is not yet tried; TASK-0198 checks it.
- Drawing appears only in the terminal and the Desktop app. Hooks also run in VS Code, `claude -p` and cloud sessions, where nothing drawn is seen. So the wrong-model warning is also added to the model's context (`prompt.context`), where the transcript keeps it.
- **No phase.** This repo's phase rule (phase-planning, "When a phase is too small") says one feature and one issue do not make a phase, and no standing phase covers the Claude Code adapter. [[PHASE-0006-Codex-Native-Adapter]] is about Codex.

## Decisions

- **Loading is ISS-0106 option (a)**, decided at start as that issue asked. The sync generates the plugin; nothing is renamed; no marketplace is published. ISS-0106 said an ADR is needed only for (b) or (c), so none is written. Recorded by the planning session on 2026-10-14; Edwin may overturn it.
- **Open question 2 (a shell edit with no focus item: warn or block?)** is answered by scope item 2. A shell edit writes the same session marker an Edit-tool write does, so HC-006 treats it exactly the same way. The mod adds no rule of its own.
- **Open question 3 (Codex parity)** is deferred to "Later". The first version is Claude Code only, like HC-010's budget.
- **Open question 4 (do the line and the commands stay here?)** The line is in the first version, because cockpit FEAT-0157 needs it. The `/pos-*` commands stay under "Later".
- **The cockpit's facts arrive through the drawing, not through a call from the mod** ([[REFERENCE-PROJECT-LINE-CONTRACT]]). The cockpit coordinator asked for this on 2026-10-14 so project-os stays free of cockpit knowledge.

## Links

- Plan: `plan/PLAN.md`
- Cockpit plan: [[project-os-cockpit#PHASE-046-A-Claude-Session-Talks-To-The-Cockpit-Through-A-Plugin]].
- Hook contracts: `tools/instructions/HOOKS.md` (HC-002, HC-006, HC-008, HC-010).
