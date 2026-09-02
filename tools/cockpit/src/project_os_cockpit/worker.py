"""The standing worker's brakes, and its lease (FEAT-0074).

[[REQ-0031]]'s fourth criterion is the order this module was built in:

    *"Every halt path exercised by drill before any repo runs unattended —
    brakes are tested before the hill."*

So the stop conditions and the lease exist before the loop that would need
them, and `tests/test_worker.py` drills every halt path.

**Nothing here starts a loop.** `can_start` is a predicate, and its first
question is whether an approved delegation policy exists — which by
`delegation.load`'s default it does not, until a principal approves one
([[ADR-0009]] §4). A worker with no policy is not a worker.

The stop conditions, from REQ-0031:

* budgets bound every loop — sessions per day, wall-clock per session;
* failure compounds toward **stopping**, never toward retrying: two failed
  close-outs park an item, three parked items halt the worker;
* the human's stop switch halts from the landing, without shell access;
* a halt **files what and why** — a halted worker is an obligation on the desk,
  not an absence.

That last one is the difference between a system that stopped and a system that
merely went quiet, and quiet is indistinguishable from broken.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any

from . import delegation

LEASE_REL = Path(".cockpit") / "lease.json"
STOP_REL = Path(".cockpit") / "worker-stop"

#: Defaults, stated here because the number IS the decision.
MAX_SESSIONS_PER_DAY = 12
MAX_SESSION_MINUTES = 30
#: Two failed close-outs park an item; three parked items halt the worker.
FAILURES_TO_PARK = 2
PARKED_TO_HALT = 3
#: A lease whose heartbeat is older than this is expired — as an escalation
#: event, never a silent takeover.
LEASE_STALE_MINUTES = 10


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _iso(value: _dt.datetime) -> str:
    return value.isoformat(timespec="seconds")


# ---- the lease ------------------------------------------------------------


def read_lease(root: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads((root / LEASE_REL).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


def lease_state(root: Path, *, now: _dt.datetime | None = None) -> dict[str, Any]:
    """Live, expired, or absent — and an expired lease is an **event**.

    A worker that silently took over an expired lease would make two workers on
    one repo indistinguishable from one worker with a slow heartbeat.
    """
    now = now or _now()
    lease = read_lease(root)
    if not lease:
        return {"state": "absent"}
    beat = lease.get("heartbeat") or lease.get("acquired") or ""
    try:
        last = _dt.datetime.fromisoformat(str(beat).replace("Z", "+00:00"))
    except ValueError:
        return {"state": "expired", "lease": lease, "why": "unreadable heartbeat"}
    if last.tzinfo is None:
        last = last.replace(tzinfo=_dt.timezone.utc)
    age_minutes = (now - last).total_seconds() / 60.0
    if age_minutes > LEASE_STALE_MINUTES:
        return {"state": "expired", "lease": lease, "age_minutes": age_minutes,
                "why": f"heartbeat {age_minutes:.0f}m old (limit {LEASE_STALE_MINUTES}m)"}
    return {"state": "live", "lease": lease, "age_minutes": age_minutes}


def acquire(root: Path, *, worker_id: str, item: str = "",
            now: _dt.datetime | None = None) -> dict[str, Any]:
    """Claim the repo, or refuse **naming the holder**.

    "Refused" with no name is a dead end; with a name it is a question somebody
    can answer.
    """
    now = now or _now()
    state = lease_state(root, now=now)
    if state["state"] == "live":
        holder = state["lease"].get("worker_id", "unknown")
        return {"ok": False, "error": f"a live lease is held by {holder!r}",
                "holder": holder}
    if state["state"] == "expired":
        # Not taken silently: expiry is surfaced, and taking over is a separate
        # decision the caller makes with the reason in hand.
        return {"ok": False, "error": f"lease expired ({state.get('why')}) — "
                "expiry is an escalation, not an opening", "expired": state}
    lease = {"worker_id": worker_id, "item": item,
             "acquired": _iso(now), "heartbeat": _iso(now)}
    path = root / LEASE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lease, indent=2), encoding="utf-8")
    return {"ok": True, "lease": lease}


def release(root: Path) -> bool:
    try:
        (root / LEASE_REL).unlink()
        return True
    except OSError:
        return False


# ---- the brakes -----------------------------------------------------------


def stop_requested(root: Path) -> bool:
    """The human's stop switch, from the landing — no shell access needed."""
    return (root / STOP_REL).exists()


def request_stop(root: Path, *, reason: str = "", actor: str = "") -> dict[str, Any]:
    path = root / STOP_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"reason": reason, "actor": actor, "at": _iso(_now())}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def clear_stop(root: Path) -> bool:
    try:
        (root / STOP_REL).unlink()
        return True
    except OSError:
        return False


def assess_halt(
    root: Path,
    *,
    sessions_today: int = 0,
    session_minutes: float = 0.0,
    parked_items: int = 0,
    validator_failing: bool = False,
    now: _dt.datetime | None = None,
) -> dict[str, Any]:
    """Should the worker stop, and **why**?

    Returns the first reason found, in the order a person would want them: an
    explicit human stop before any computed one, because "somebody said stop"
    outranks every budget.

    Every branch names its reason. A halt with no reason is the quiet this
    module exists to prevent.
    """
    if stop_requested(root):
        return {"halt": True, "reason": "stop-switch",
                "detail": "a human asked the worker to stop"}
    policy = delegation.load(root)
    if not policy.get("approved"):
        return {"halt": True, "reason": "no-delegation",
                "detail": "no approved delegation policy — no policy, no worker"}
    if validator_failing:
        return {"halt": True, "reason": "validator-red",
                "detail": "the record does not validate; working on a broken record compounds it"}
    if parked_items >= PARKED_TO_HALT:
        return {"halt": True, "reason": "parked-items",
                "detail": f"{parked_items} items parked (limit {PARKED_TO_HALT}) — "
                          "failure is compounding, not clearing"}
    if sessions_today >= MAX_SESSIONS_PER_DAY:
        return {"halt": True, "reason": "session-budget",
                "detail": f"{sessions_today} sessions today (limit {MAX_SESSIONS_PER_DAY})"}
    if session_minutes >= MAX_SESSION_MINUTES:
        return {"halt": True, "reason": "wall-clock",
                "detail": f"{session_minutes:.0f}m in this session (limit {MAX_SESSION_MINUTES}m)"}
    return {"halt": False, "reason": "", "detail": "within every bound"}


def should_park(failures: int) -> bool:
    """Failure compounds toward stopping, never toward retrying."""
    return failures >= FAILURES_TO_PARK


def can_start(root: Path, *, worker_id: str = "", now: _dt.datetime | None = None) -> dict[str, Any]:
    """Everything that must be true before a loop may begin.

    Deliberately a predicate and not a launcher: **this module starts nothing.**
    The order is the safety order — policy first, because without a delegation
    there is no worker to have budgets.
    """
    halt = assess_halt(root, now=now)
    if halt["halt"]:
        return {"ok": False, "why": halt["reason"], "detail": halt["detail"]}
    state = lease_state(root, now=now)
    if state["state"] == "live" and state["lease"].get("worker_id") != worker_id:
        return {"ok": False, "why": "lease-held",
                "detail": f"held by {state['lease'].get('worker_id')!r}"}
    return {"ok": True, "why": "", "detail": "policy approved, no halt, lease free"}


# ---- selection ------------------------------------------------------------

#: Statuses a worker may pick up. Deliberately narrow — `review` and `blocked`
#: are states where somebody else is mid-thought, and picking one up is taking
#: work off a person rather than off a queue.
WORKABLE: frozenset[str] = frozenset({"backlog", "next", "doing", "triage", "open"})

#: Severity order for issues, worst first.
_SEVERITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def select(
    candidates: list[dict[str, Any]],
    *,
    focus: str = "",
    parked: set[str] | None = None,
) -> dict[str, Any]:
    """Pick the next item, **and say why** (TASK-0322, LIFECYCLE step 2).

    Order: the focus item when workable, else by phase order, then severity,
    then id. Items parked by failure backoff are skipped.

    **Every selection explains itself, including what it passed over.** An
    unattended system's first duty is to be explainable afterwards: "why is it
    working on that?" asked three hours later must have an answer that does not
    require re-deriving the state the picker saw.

    An empty workable backlog returns `idle` — which is a **stop condition**,
    not a busy-wait. A loop that spins looking for work it will not find burns
    budget to discover nothing, repeatedly.
    """
    parked = parked or set()
    considered: list[dict[str, str]] = []
    workable: list[dict[str, Any]] = []

    for item in candidates:
        item_id = str(item.get("id") or "")
        status = str(item.get("status") or "").strip().lower()
        if item_id in parked:
            considered.append({"id": item_id, "passed": "parked by failure backoff"})
            continue
        if status not in WORKABLE:
            considered.append({"id": item_id, "passed": f"status {status or 'unset'} is not workable"})
            continue
        blockers = [b for b in (item.get("depends") or []) if b not in (item.get("resolved") or [])]
        if blockers:
            considered.append({"id": item_id, "passed": f"blocked on {', '.join(blockers)}"})
            continue
        workable.append(item)

    if not workable:
        return {
            "state": "idle",
            "chosen": None,
            "why": "no workable item — idle is a stop condition, not a busy-wait",
            "considered": considered,
        }

    focused = next((i for i in workable if str(i.get("id")) == focus), None)
    if focused is not None:
        chosen, why = focused, f"the focus item {focus} is workable"
    else:
        def key(item: dict[str, Any]) -> tuple[Any, ...]:
            return (
                _coerce_phase(item.get("phase")),
                _SEVERITY.get(str(item.get("severity") or "").lower(), 9),
                str(item.get("id") or ""),
            )
        workable.sort(key=key)
        chosen = workable[0]
        why = (
            f"focus {focus!r} not workable; " if focus else ""
        ) + "first by phase order, then severity, then id"

    for item in workable:
        if item is not chosen:
            considered.append({"id": str(item.get("id") or ""), "passed": "ranked below the choice"})

    return {"state": "selected", "chosen": chosen, "why": why, "considered": considered}


def _coerce_phase(value: Any) -> int:
    """Phase order out of a `PHASE-0027` link, or last."""
    import re as _re
    m = _re.search(r"PHASE-(\d+)", str(value or ""))
    return int(m.group(1)) if m else 9999


def ledger_line(selection: dict[str, Any]) -> str:
    """One line recording a selection, for the worker's ledger.

    Carries the passed-over items as well as the choice, because *"why not that
    one?"* is the question a person actually asks when a worker's choice looks
    wrong, and it cannot be answered from the choice alone.
    """
    if selection.get("state") == "idle":
        return f"idle — {selection.get('why')}"
    chosen = selection.get("chosen") or {}
    passed = "; ".join(
        f"{c['id']}: {c['passed']}" for c in (selection.get("considered") or [])
    )
    line = f"chose {chosen.get('id')} — {selection.get('why')}"
    return f"{line} | passed over: {passed}" if passed else line


# ---- the session loop (TASK-0323) -----------------------------------------

#: Outcomes a session may end with. `stalled` is distinct from `failed`
#: deliberately: a session that stopped answering and one that finished badly
#: need different responses, and collapsing them loses the difference at
#: exactly the moment somebody is trying to work out what happened.
OUTCOMES: tuple[str, ...] = ("closed-out", "failed", "stalled", "halted")


def run_once(
    root: Path,
    *,
    worker_id: str,
    candidates: list[dict[str, Any]],
    dispatch: Any,
    focus: str = "",
    parked: set[str] | None = None,
    sessions_today: int = 0,
    now: _dt.datetime | None = None,
) -> dict[str, Any]:
    """One turn: check, claim, select, dispatch, record, release.

    **`dispatch` is injected, and that is the design rather than a testing
    convenience.** This module decides *whether* and *what*; something else
    decides *how to spawn*. Keeping the spawn out means the halt logic can be
    exercised — and has been, over every path — without a test ever starting a
    session, and it means this file cannot start one either.

    Returns what happened and why, always. A turn that produced nothing must
    still say which gate stopped it, because "the worker did nothing" and "the
    worker was stopped by its budget" look identical from outside and only one
    of them is a problem.

    **The lease is released on every path**, including failure. A worker that
    died holding its lease would block the next one until the heartbeat aged
    out, turning one bad turn into ten minutes of silence.
    """
    now = now or _now()

    gate = can_start(root, worker_id=worker_id, now=now)
    if not gate["ok"]:
        return {"ran": False, "outcome": "halted", "why": gate["why"],
                "detail": gate["detail"]}

    budget = assess_halt(root, sessions_today=sessions_today, now=now)
    if budget["halt"]:
        return {"ran": False, "outcome": "halted", "why": budget["reason"],
                "detail": budget["detail"]}

    picked = select(candidates, focus=focus, parked=parked)
    if picked["state"] == "idle":
        return {"ran": False, "outcome": "halted", "why": "idle",
                "detail": picked["why"], "ledger": ledger_line(picked)}

    item = picked["chosen"]
    item_id = str(item.get("id") or "")
    claim = acquire(root, worker_id=worker_id, item=item_id, now=now)
    if not claim["ok"]:
        return {"ran": False, "outcome": "halted", "why": "lease",
                "detail": claim["error"]}

    try:
        result = dispatch(item)
        outcome = str((result or {}).get("outcome") or "failed")
        if outcome not in OUTCOMES:
            # An unrecognised outcome is a failure, not a success. Reading an
            # unknown value optimistically is how a broken dispatcher would
            # look like a working one.
            outcome = "failed"
        detail = str((result or {}).get("detail") or "")
    except Exception as exc:                      # noqa: BLE001 — recorded, not swallowed
        # A raising dispatcher is a failed session, not a crashed worker. The
        # exception is recorded rather than propagated so the lease is released
        # and the failure counts toward parking, which is what makes failure
        # compound *toward stopping*.
        outcome, detail = "failed", f"dispatch raised: {exc}"
    finally:
        release(root)

    return {
        "ran": True,
        "item": item_id,
        "outcome": outcome,
        "detail": detail,
        "why": picked["why"],
        "ledger": ledger_line(picked),
    }
