---
type: "[[issue]]"
id: ISS-0056
title: "The close-out hook blocks on every stop while focus.task is set, so a repo with a parked focus item pays a forced continuation on every turn, including turns that wrote nothing"
status: triage
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-04
updated: 2026-09-04
source: ["user:edwin, relayed from a your-trainer session, 2026-09-04"]
severity: medium
component: adapters-hooks
parent: ""
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]", "[[ISS-0055-The-Delegation-Hint-Is-Not-Executable-In-Any-Repo]]"]
tests: ["[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]"]
---

# The close-out hook fires on stops that did no work

## Problem

Every turn in `your-trainer` ends with a forced continuation. `close-out-check.sh` blocks whenever `focus.task` is non-empty, and `your-trainer` has had `focus.task: TASK-0783` set since 2026-08-15. The hook reads two things and nothing else: the `focus` block of `SNAPSHOT.yaml`, and `stop_hook_active`. It has no way to tell a session that spent the turn implementing the focus task from one that answered a question, so it treats both the same.

The cost is one extra model turn per user turn, in that repo, indefinitely. `stop_hook_active` caps it at one block per turn rather than an infinite loop, but it resets every turn, so the tax is paid again on the next one.

`HOOKS.md` states HC-006's trigger as *"before final response after implementation work"*. The shipped hook fires before every final response. That gap between the stated contract and the code is the defect; the same class as [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make|ISS-0049]] and [[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them|ISS-0050]].

> [!quote] As reported — 2026-09-04 (relayed by user:edwin from a your-trainer session)
> The hook fired on focus.task: TASK-0783 for the third time. Nothing to change there again: TASK-0783 is untouched by this session, still legitimately doing, and its note already carries the 2026-09-03 handoff naming the one open decision on it.
>
> Worth flagging since it has now happened three times in a row: close-out-check.sh treats any set focus.task as unfinished business at every stop, so it fires on turns that never touched the focus item — two questions and now a scaffolding turn. The focus item is parked, not abandoned. If you want the check to stay useful, it probably needs to compare against whether the session actually wrote to the focus task's note or its feature's files.

## Not the finding retracted in ISS-0048

[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]] carries a retraction dated 2026-09-04: an earlier finding claimed the hook keeps no record of a written handoff and therefore blocks every stop, *"making its own message false"*. That was withdrawn, correctly — the loop guard is real, `close-out-check.sh:16-19` exits 0 on `stop_hook_active`, and `test-hooks.sh` asserts it.

This is a different claim and the retraction does not cover it. The retraction's reasoning was that *"each stop followed new work and was a fresh stop"*. Here, two of the three stops followed **no work at all**. The loop guard is not in question; what is in question is that a fresh stop after a question is treated as a fresh stop after implementation.

## Repro

```bash
cd ~/Dev/repos/your-trainer
grep -A2 '^focus:' SNAPSHOT.yaml | grep 'task:'    # task: "TASK-0783"
printf '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR=. ./tools/adapters/claude-code/hooks/close-out-check.sh
# {"decision": "block", "reason": "Close-out check (HC-006): focus.task is still TASK-0783 ..."}
```

The payload carries no information about the turn, so the output is identical whether the session wrote fifty files or none.

## Expected

A turn that changed nothing ends without a forced continuation. A turn that did work while a focus item is set still gets the close-out reminder.

## Actual

Both get the block. Three consecutive turns in one session were blocked: two questions and one scaffolding turn, none of which touched TASK-0783.

## Evidence

- `tools/adapters/claude-code/hooks/close-out-check.sh:53-64` — the focus branch. Its only inputs are `focus_value task` and the `stop_hook_active` guard above it.
- `tools/instructions/HOOKS.md`, HC-006 — *"Trigger: before final response after implementation work."* The hook cannot observe "after implementation work".
- `your-trainer/docs/tasks/TASK-0783-SeatSelectionScreenAndWarnings.md` — `status: doing`, `updated: 2026-09-03`, code complete since 2026-08-15 and held open deliberately because its linked manual test is a judgement about whether a rider understood a warning.
- Claude Code hook reference, [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) — `Stop` and `PostToolUse` both receive `session_id` and `prompt_id`. So a per-session or per-turn record is available without parsing the transcript.

**One correction to the report.** It says the note "already carries the 2026-09-03 handoff". It does, and it names exactly one open decision — but under a heading called `## Next Actions`, not `## Handoff`. Any fix that tries to detect a written handoff structurally would miss this note. That rules out the shape of option 3 below.

Sibling search: no sibling found (searched `docs/issues/` for HC-006, close-out-check, stop hook). The nearest prior is the retracted finding inside ISS-0048, which is not a filed issue, so this is not a second instance and no rule-ADR harvest is triggered.

## Options

**1. Block only when the session wrote something since the last block. Recommended.** A `PostToolUse` hook on `Write|Edit` touches a marker keyed by `session_id` under `$TMPDIR`; the Stop hook blocks only when the marker exists, and removes it when it does. A question-only turn finds no marker and stays silent. A turn that wrote files is reminded once. Nothing is weakened: work still gets its reminder, and the reminder is not spent on a turn that did nothing.

**2. Block at most once per session.** Cheaper — one marker, no `PostToolUse` change. Rejected as the primary fix: the single block gets consumed by whichever stop comes first, so a session that answers a question and *then* does real work is reminded about the question and silent about the work. Option 1 costs a little more and does not have that ordering hazard.

**3. Let a written handoff discharge the block.** This is what the hook's message already implies. Rejected: there is no structural convention for a handoff. TASK-0783's is prose under `## Next Actions`, so a heading check would not find it, and a date check would need dates parsed out of prose.

**4. Change the data instead — set TASK-0783 `deferred` and clear focus.** Zero code, and `STATUSES.md` does define `deferred` as a parked, non-terminal state. Rejected: the task is code-complete awaiting a verification decision, not parked work, and its note argues at length against promoting it on the evidence available. Changing a status to quiet a hook is the wrong direction, and it would leave the same tax on the next repo with a legitimately-set focus.

Whichever is chosen, two things go with it: keep the HC-007 validator branch blocking on **every** stop, since a broken docs invariant is a real failure and not advisory; and rewrite HC-006's trigger line in `HOOKS.md` so the stated contract matches what the hook can observe.

## Next Actions

- [ ] Edwin picks the predicate. Option 1 is a change to the HC-006 contract, which propagates to twelve repos, so it is his call rather than a judgement to make here.
- [ ] Implement in the template, extend [[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]] with the question-only case, and correct HC-006's trigger line in `HOOKS.md`.
