---
type: "[[task]]"
id: TASK-0200
aliases: ["TASK-0200"]
title: "A file changed from the shell during a turn triggers the close-out check, exactly as an Edit-tool write does"
status: backlog
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["[[FEAT-0041-Project-Os-Mod]], scope item 2 and open question 2", "plan/PLAN.md, 'How the shell-edit check works'"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "S"
due: ""
depends: ["[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]"]
blocks: ["[[TASK-0203-The-Mod-Is-Pinned-Tested-In-CI-And-Synced-To-The-Cockpit]]"]
related: []
tests: []
---

# A file changed from the shell counts as a write at close-out

Today, if an agent changes a file with `sed -i` or a script run through Bash, the close-out check (HC-006) is not reminded, because only the Edit, Write and NotebookEdit tools write its session marker. After this task the project-os mod compares `git status` at the start and end of each turn, and writes the same marker when a file changed. The close-out check then behaves as it does after an Edit.

## Definition of Done

- [ ] At `turn.start` the mod records `git status --porcelain=v1 -z` for the session; on `classic.Stop`, before `next(e)`, it runs it again.
- [ ] When the two differ, it writes the marker at the path `hooks/shared/session-marker.sh` gives for the session, by calling that script, so the path rule stays in one place.
- [ ] A repo that is not a git repository, a `git` that fails, or a missing marker script: the mod does nothing and the turn ends as today.
- [ ] `hooks/session-touch.sh`'s "Known limit" comment and HC-006's sentence "A session that writes through the shell ... is not reminded" are updated to say the Claude Code mod now covers it, and Codex does not.
- [ ] HOOKS.md HC-006 "Implementations" names the mod.
- [ ] A `claude plugin test` case: a turn whose Bash call changes a tracked file leaves the marker; a turn that reads only leaves none; a turn with no git repository does not throw.
- [ ] Checked in a real session: `sed -i` on a tracked file with focus set, then the turn ends, and the close-out check blocks once.

## Steps

- [ ] The two hooks in `register.ts`.
- [ ] Tests, then the live check.
- [ ] HOOKS.md and the script comment.
