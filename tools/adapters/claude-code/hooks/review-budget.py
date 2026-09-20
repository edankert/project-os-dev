#!/usr/bin/env python3
"""Review budget: the hard stop behind the procedure in independent-review/SKILL.md.

Measured on 2026-09-18 (project-os-dev REFERENCE-REVIEW-COST-AND-ISSUE-DEBT), a
review ran 90-125 tool calls with nothing telling it to stop. The skill now
gives it a budget; this hook is what holds it.

For the `independent-reviewer` subagent only, counted per `agent_id`:
  - PostToolUse at the warning point (call 36 of 40, 12 of 15) adds context:
    calls left, finish up. It was call 30 until 2026-09-18, when measured
    reviews (project-os-dev TASK-0130) all stopped at about 34 calls: an early
    warning to finish makes the real budget the warning point, not the limit.
  - PreToolUse past the budget denies the call and tells the reviewer to hand
    its report back. Edits to notes under docs/ are still allowed for GRACE
    more calls; then everything is denied. **That grace is not for the
    reviewer**, which `independent-review/SKILL.md` tells to write nothing in
    the notes and file no issues -- the deny message used to invite exactly
    that, which a round-two reviewer caught (FEAT-0034, 2026-09-20). It is for
    an author who runs the same agent type over their own notes.
  - **The call that returns the report is never denied.** A subagent hands its
    report back with a tool call (`SubagentHandback`), so denying it past the
    budget loses the whole review: the reviewer is told to write its report
    and then refused the only way to deliver it. Seen on 2026-09-20, when a
    FEAT-0034 reviewer was denied nine handbacks in a row and about 120k
    tokens of finished review went nowhere, four runs running. This exemption
    has no grace limit, because a reviewer that has spent its grace still owes
    its report.

Round two has a smaller budget. The hook knows it is round two when the
reviewer READS a round-two packet (a path containing `review-packet-...-r2`),
which the skill makes its first call. It looks only at the fields that name a
file, and only on a read: matching the whole tool input let a round-one reviewer
whose `Bash` command merely mentioned an `-r2` path drop to the round-two budget
for the rest of its run, since the switch never flips back (project-os-dev
FEAT-0034 review, 2026-09-20).

Budgets come from PROJECT_OS_REVIEW_BUDGET (default 40) and
PROJECT_OS_REVIEW_BUDGET_ROUND2 (default 15), so a repo can set its own in
.claude/settings.json "env". State lives in the system temp directory, one file
per agent_id, so parallel reviews never share a count.

Fails open on anything unexpected: a broken budget must not block work.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

AGENT_TYPE = "independent-reviewer"
GRACE = 10
ROUND_TWO_PACKET = re.compile(r"review-packet-[^\"'\s]*-r2")

#: Only a read of a file can announce round two, and only through the field that
#: names the file. A `Bash` command that mentions an `-r2` path is talking about
#: a packet, not opening one.
ROUND_TWO_TOOLS = ("Read", "View", "Open")
ROUND_TWO_FIELDS = ("file_path", "path", "notebook_path")


def budgets():
    def num(name, default):
        try:
            return max(1, int(os.environ.get(name, default)))
        except ValueError:
            return default
    return num("PROJECT_OS_REVIEW_BUDGET", 40), num("PROJECT_OS_REVIEW_BUDGET_ROUND2", 15)


def state_path(agent_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", agent_id)[:120]
    return Path(tempfile.gettempdir()) / ("project-os-review-budget-%s.json" % safe)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"count": 0, "round": 1}


#: The tool a subagent uses to hand its report back to the author. Never
#: denied: see the module docstring.
REPORT_TOOLS = ("SubagentHandback",)


def is_report(tool):
    return tool in REPORT_TOOLS


def is_note_edit(tool, tool_input):
    if tool not in ("Edit", "Write", "MultiEdit"):
        return False
    path = str(tool_input.get("file_path", ""))
    return "/docs/" in path.replace("\\", "/") or path.startswith("docs/")


def announces_round_two(tool, tool_input):
    if tool not in ROUND_TWO_TOOLS:
        return False
    return any(ROUND_TWO_PACKET.search(str(tool_input.get(f, "") or ""))
               for f in ROUND_TWO_FIELDS)


def emit(event, **fields):
    print(json.dumps({"hookSpecificOutput": dict(hookEventName=event, **fields)}))


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if data.get("agent_type") != AGENT_TYPE or not data.get("agent_id"):
        return 0
    event = data.get("hook_event_name", "")
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    path = state_path(str(data["agent_id"]))
    state = load(path)
    first, second = budgets()

    if event == "PreToolUse":
        if announces_round_two(tool, tool_input):
            state["round"] = 2
        budget = second if state.get("round") == 2 else first
        count = state.get("count", 0) + 1
        state["count"] = count
        state["budget"] = budget
        try:
            path.write_text(json.dumps(state), encoding="utf-8")
        except OSError:
            return 0
        if count <= budget:
            return 0
        if is_report(tool):
            return 0
        if count <= budget + GRACE and is_note_edit(tool, tool_input):
            return 0
        emit("PreToolUse", permissionDecision="deny", permissionDecisionReason=(
            "Review budget reached (%d tool calls, round %d). Hand your report back now with what you "
            "have: the claims table, then at most five other observations. Mark every claim you did not "
            "finish *not checked*. Returning your report is never denied; nothing else runs."
            % (budget, state.get("round", 1))))
        return 0

    if event == "PostToolUse":
        budget = state.get("budget") or first
        count = state.get("count", 0)
        warn_at = budget - max(3, budget // 10)
        if count == warn_at:
            emit("PostToolUse", additionalContext=(
                "Review budget: %d of %d tool calls used, %d left. Finish the claims you have started; "
                "mark the rest *not checked*, then write the report." % (count, budget, budget - count)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # fail open: a broken budget must not block work
        sys.exit(0)
