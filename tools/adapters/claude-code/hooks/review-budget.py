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
  - PreToolUse past the budget denies the call with an instruction to write
    the report. Edits to notes under docs/ are still allowed, so the verdict
    and findings can be recorded, up to GRACE more calls; then everything is
    denied. Writing the report itself needs no tool call.

Round two has a smaller budget. The hook knows it is round two when the
reviewer reads a round-two packet (a path containing `review-packet-...-r2`),
which the skill makes its first call.

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


def is_note_edit(tool, tool_input):
    if tool not in ("Edit", "Write", "MultiEdit"):
        return False
    path = str(tool_input.get("file_path", ""))
    return "/docs/" in path.replace("\\", "/") or path.startswith("docs/")


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
        if ROUND_TWO_PACKET.search(json.dumps(tool_input)):
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
        if count <= budget + GRACE and is_note_edit(tool, tool_input):
            return 0
        emit("PreToolUse", permissionDecision="deny", permissionDecisionReason=(
            "Review budget reached (%d tool calls, round %d). Write your report now with what you have: "
            "the claims table, then at most five other observations. Mark every claim you did not finish "
            "*not checked*. You may still record the verdict in the feature note; nothing else runs."
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
