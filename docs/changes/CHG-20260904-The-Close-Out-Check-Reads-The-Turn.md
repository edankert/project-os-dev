---
type: "[[change]]"
id: CHG-20260904-The-Close-Out-Check-Reads-The-Turn
aliases: ["CHG-20260904-The-Close-Out-Check-Reads-The-Turn"]
title: "The close-out hook blocks only a stop that follows a write, and the harness now checks a hook's git mode and its gitignore status as well as its disk mode"
status: merged
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
source: ["user:edwin, relayed from a your-trainer session, 2026-09-04"]
commit: "b164e02, 358b5a5, 0f73f9e, 1e0aef1 (template); one per downstream repo"
pr: ""
impacts: ["tools/adapters/claude-code/hooks/close-out-check.sh", "tools/adapters/claude-code/hooks/session-touch.sh", "tools/adapters/claude-code/hooks/shared/session-marker.sh", "tools/adapters/claude-code/hooks.json", "tools/instructions/HOOKS.md", "tools/adapters/claude-code/ADAPTER.md", "tools/scripts/test-hooks.sh", ".claude/settings.json"]
issues: ["[[ISS-0056-The-Close-Out-Hook-Fires-On-Stops-That-Did-No-Work]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]", "[[CHG-20260904-Hooks-Ship-Executable]]", "[[ISS-0055-The-Delegation-Hint-Is-Not-Executable-In-Any-Repo]]"]
---

# The close-out check reads the turn

## Summary

A question no longer costs a forced continuation. `close-out-check.sh` blocked whenever `focus.task` was set, and `your-trainer` has had `TASK-0783` in focus since 2026-08-15, so every turn there ended with a block — three in a row on two questions and a scaffolding turn, none of which touched the task.

`focus` is durable project state. It survives sessions on purpose: it is how the next session learns where the work stands. The hook was reading it as if it described the turn.

`session-touch.sh`, a new `PostToolUse` hook on `Write|Edit|NotebookEdit`, records the session's first write as a zero-byte marker in the temp directory keyed by session and project. `close-out-check.sh` consumes that marker when it blocks, so the reminder arrives once per burst of work rather than once per turn. The HC-007 validator half still blocks every stop — a broken docs invariant is a failure, not a reminder. Every path that cannot answer the question blocks exactly as before: no `session_id` in the payload, no marker helper on disk.

## Impact

- **A repo with a legitimately parked focus item stops paying a forced continuation on every turn.** That was the reported cost.
- **All twelve repos have it**, template plus eleven, each downstream commit containing only tooling paths.
- **A session that edits through the shell is not reminded.** Only the three editing tools set the marker. Guessing which shell commands write would be a string match that ages badly, so the limit is recorded rather than papered over. What is lost is a reminder, not a check.
- [[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]] goes from 45 to 74 assertions. Three mutations against the write test were run and each killed: dropping it (3 failures), not spending the marker (4), failing open without a `session_id` (5).

## Two defects found while implementing

**`session-touch.sh` went in at mode `100644`** — [[ISS-0055-The-Delegation-Hint-Is-Not-Executable-In-Any-Repo|ISS-0055]] recurring within the hour. The guard added there reads the working tree, and a repo with `core.fileMode = false` records a new file as `100644` whatever its local mode, so a clone would have got `Permission denied` again while the harness stayed green. The harness now asserts the index mode of every tracked hook too.

**The shared helper was first written to `hooks/lib/`.** `obsidian-supernote-sync/.gitignore` carries a bare `lib/`, which matches a directory of that name at any depth, so the file would never have been committed there — and a repo missing it falls back to blocking every stop. It is `hooks/shared/` now, checked against all twelve `.gitignore` files rather than assumed. The harness asserts that no hook file is gitignored, and that assertion had to be written twice: the first version used `check-ignore` without `--no-index`, which reports nothing for an already-tracked file, so it passed under its own mutation.

Both are the same shape as ISS-0055: a hook that is correct in the working tree and broken in a fresh clone. `generate-adapters.py` already had `untracked_artifacts()` for that shape on generated files; the hooks now have their own three checks.

## Documentation Coverage (All Types Considered)
Set each item to one of: `updated`, `new`, `not-applicable`, `deferred`.

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable
- issues: new
- tests: updated
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups

- [ ] Watch whether one reminder per burst of work is too few in a long implementation session. The marker is re-armed by the next write, so the frequency now tracks writing rather than turns.
