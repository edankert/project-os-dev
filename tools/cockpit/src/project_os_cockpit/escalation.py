"""Nothing waits silently without bound (FEAT-0076).

The single sharpest failure mode of a system *designed* to escalate is that one
unanswered question stalls the loop forever. The invariant this module exists
to establish is one sentence:

    **Everything either times out into a recorded assumption, or alarms.**

Not "most things". A queue entry whose kind has no policy line does not get a
silent pass — it falls to the **alarm** path, because a kind nobody wrote a
timeout for is a kind nobody decided about, and the safe reading of an
undecided kind is *ask a person*, never *proceed quietly*.

Two paths, and which one an entry takes is a property of its **kind**:

* a kind with a `timeout` and a `default` → lapses into a recorded assumption
* a kind with no policy, or one that **reserves judgment** → alarms

Both are visible. Neither is silence.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

#: Per-kind escalation policy. `default` is the assumption a lapse records;
#: `reserves_judgment` marks a kind that must never proceed on an assumption
#: however long it waits — the timeout then decides only *when it alarms*.
#:
#: Stated here rather than in a config file for the same reason
#: `MAX_CHECKPOINTS` is: the number is the decision, and a decision nobody can
#: find is a decision nobody reviews.
DEFAULT_POLICY: dict[str, dict[str, Any]] = {
    # An offered design waiting on accept/reject. Lapsing is safe: nothing was
    # built on it, and the offer stays on the record to be accepted later.
    "review": {"timeout_hours": 48, "default": "left unaccepted; no work proceeded on it"},
    # A question blocking an agent. Lapses into "proceed on the stated
    # assumption", which is the whole point of ADR-0009's escalation defaults —
    # but the work carries the tag and the digest lifts it.
    "question": {"timeout_hours": 24, "default": "proceeded on the assumption stated in the question"},
    # A comment on a design. It waits as long as it likes: nothing is blocked
    # on it, so alarming would be noise — but it is NOT silent, because it
    # sits in the queue with its age.
    "annotation": {"timeout_hours": None, "default": None},
    # A tool-permission prompt (ISS-0094). **No default, deliberately**: a
    # permission request asks to take an action with effects outside the
    # record, so lapsing it into "yes" would be the system granting itself
    # authority nobody delegated, and lapsing into "no" would silently change
    # what the agent did. It has a short timeout that makes it ALARM.
    #
    # This is the entry that closes the hole: without it, the most likely way
    # an unattended worker stops — "may I run this command?" — is the one way
    # the alarm could not see, because a permission prompt is not a queue entry.
    "permission": {"timeout_hours": 1, "default": None},
}

#: Kinds whose judgment may never be assumed. Empty today and deliberately
#: present: the moment a delegated *acceptance* kind exists it belongs here,
#: and a set that has to be created later is a set somebody forgets.
RESERVES_JUDGMENT: frozenset[str] = frozenset()

#: Past this multiple of its timeout with no default available, an entry stops
#: being late and starts being an alarm.
ALARM_MULTIPLE = 2


def _parse(ts: str) -> _dt.datetime | None:
    raw = (ts or "").strip()
    if not raw:
        return None
    try:
        parsed = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=_dt.timezone.utc)


def assess(
    entry: dict[str, Any],
    *,
    now: _dt.datetime | None = None,
    policy: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """What should happen to one waiting entry, and why.

    Returns a state plus the reasoning, so a surface can show the clock the
    system is on rather than only its verdict — TASK-0329's *"the human sees
    the clock"*.
    """
    table = policy if policy is not None else DEFAULT_POLICY
    now = now or _dt.datetime.now(_dt.timezone.utc)
    kind = str(entry.get("kind") or "")
    started = _parse(str(entry.get("ts") or ""))
    line = table.get(kind)

    if started is None:
        # An entry with no timestamp cannot be aged, and an un-ageable entry
        # that stayed quiet would be exactly the silent wait this forbids.
        return {"state": "alarm", "kind": kind, "age_hours": None,
                "why": "no timestamp, so it cannot be aged"}

    age_hours = (now - started).total_seconds() / 3600.0

    if line is None:
        return {"state": "alarm", "kind": kind, "age_hours": age_hours,
                "why": f"no policy line for kind {kind!r}; an undecided kind asks a person"}

    timeout = line.get("timeout_hours")
    if timeout is None:
        return {"state": "waiting", "kind": kind, "age_hours": age_hours,
                "why": "this kind has no timeout; it waits visibly, blocking nothing"}

    if age_hours < timeout:
        return {"state": "waiting", "kind": kind, "age_hours": age_hours,
                "timeout_hours": timeout, "why": "within its timeout"}

    if kind in RESERVES_JUDGMENT or not line.get("default"):
        if age_hours >= timeout * ALARM_MULTIPLE:
            return {"state": "alarm", "kind": kind, "age_hours": age_hours,
                    "timeout_hours": timeout,
                    "why": "past twice its timeout with no default to lapse into"}
        return {"state": "late", "kind": kind, "age_hours": age_hours,
                "timeout_hours": timeout,
                "why": "past its timeout; judgment is reserved so it cannot lapse"}

    return {"state": "lapsed", "kind": kind, "age_hours": age_hours,
            "timeout_hours": timeout, "assumption": line["default"],
            "why": "past its timeout; the policy authorises this assumption"}


def sweep(
    entries: list[dict[str, Any]],
    *,
    now: _dt.datetime | None = None,
    policy: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assess every open entry. **Nothing may be absent from the result.**

    The drill in TASK-0331 is exactly this: construct each silent-wait
    candidate and show it lands in a visible state.
    """
    assessed = [
        {**entry, "escalation": assess(entry, now=now, policy=policy)}
        for entry in entries
    ]
    counts: dict[str, int] = {}
    for item in assessed:
        state = str(item["escalation"]["state"])
        counts[state] = counts.get(state, 0) + 1
    return {
        "entries": assessed,
        "counts": counts,
        "alarming": [i for i in assessed if i["escalation"]["state"] == "alarm"],
        "lapsed": [i for i in assessed if i["escalation"]["state"] == "lapsed"],
    }
