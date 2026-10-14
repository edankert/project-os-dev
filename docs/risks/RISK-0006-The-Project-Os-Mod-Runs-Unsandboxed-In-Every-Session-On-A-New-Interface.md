---
type: "[[risk]]"
id: RISK-0006
aliases: ["RISK-0006"]
title: "The project-os mod runs unsandboxed in every Claude session of every repo, on an interface that is weeks old"
status: open
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]], risk scan 2026-10-14", "[[project-os-cockpit#PHASE-046-A-Claude-Session-Talks-To-The-Cockpit-Through-A-Plugin]], 'Risks found by the scan', items 1 and 2"]
likelihood: medium
impact: medium
mitigation: ["The plugin declares the Claude Code version it was tested on, and the template's CI runs claude plugin validate and claude plugin test at a pinned version (TASK-0203)", "The mod never answers a permission check and never changes a tool.check verdict", "Every reader fails quietly: a failed script leaves its fact off the line, and a failed git status leaves the turn as it is today", "Nothing slow runs while drawing; the validator runs at most once at a time, in the background", "ADAPTER.md says how to turn the plugin off in one repo (TASK-0199)"]
related: [FEAT-0041, ISS-0106, REFERENCE-PROJECT-LINE-CONTRACT]
---

# The project-os mod runs unsandboxed in every session, on a new interface

## Description

After FEAT-0041, every Claude Code session in every synced project-os repo runs project-os's TypeScript inside Claude Code's own process, with the person's permissions and no sandbox. Four things can go wrong:

1. **The interface changes under it.** Mods shipped in Claude Code 2.1.287 and the installed version is 2.1.300. A change to an event's name or shape can stop the shell-edit check without any error, so the close-out check stays quiet when it should not. A change to drawing can make the line disappear, or show stale facts.
2. **A defect runs everywhere at once.** A bug in the mod reaches all twelve repos on their next sync. A hook that throws is skipped by Claude Code, so the worst case is usually a missing line or check, not a broken session. A hook that hangs is bounded by Claude Code's per-hook time limit.
3. **Each repo's `.claude/settings.json` gains a plugin registration.** A person who already edits that file by hand may see the generator's keys appear. A repo that wants the mod off needs a documented way to say so that the next sync does not undo.
4. **Each turn runs `git status`, and each docs change runs the validator.** In a large repo the validator takes seconds. Run while drawing, it would freeze the prompt.

The drawing contract with the cockpit plugin ([[REFERENCE-PROJECT-LINE-CONTRACT]]) adds a fifth: a renamed key on either side silently stops the cockpit's facts joining the line. The cockpit's segment then draws on its own, which is visible but not wrong.

## Mitigation

- The plugin declares the version it was tested on. The template's CI runs `claude plugin validate` and `claude plugin test` at a pinned Claude Code version (TASK-0203).
- The mod never answers a permission check and never changes a `tool.check` verdict.
- Every reader fails quietly: a failed script leaves its fact off the line; a failed `git status` leaves the turn as it is today.
- Nothing slow runs while drawing. The validator runs at most once at a time, in the background.
- ADAPTER.md says how to turn the plugin off in one repo, in a way the sync respects (TASK-0199).
- A key in the drawing contract changes only in the template's ADAPTER.md and the cockpit's plugin on the same day.

## Triggers

- `claude plugin test` fails in CI after a Claude Code update.
- The line is missing in a synced repo, or shows a focus item that is no longer the focus.
- A shell edit at a set focus does not produce the close-out block (TST-0047 step 4).
