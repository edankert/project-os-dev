"""Permission prompts as durable state, not a colour (ISS-0094).

`agent_hooks.py` maps `PermissionRequest → needs-input` and the landing shows an
amber card. That is **detection**. Answering still means finding the terminal
and typing into it, and nothing survives a restart.

**Why this is a hole and not a wish.** [[FEAT-0076]] establishes that *nothing
in the system can wait silently without bound* — timeouts per kind,
proceed-on-assumption, the stall alarm. Every one of those mechanisms watches
**the review queue**.

A tool-permission prompt is not a queue entry. So the most likely way an
unattended worker stops — an agent asking *"may I run this command?"* — is
precisely the way the alarm cannot see it. The worker is not idle, not failed,
not budget-exhausted; it is blocked, and the loop's own supervision is blind.

This module gives a prompt an id, a status and a clock, so it can be answered
from the cockpit and **counted by the same sweep as everything else**.
"""

from __future__ import annotations

import datetime as _dt
import json
import threading
import uuid
from pathlib import Path
from typing import Any

#: Where they live. Runtime state beside the review ledger, not in `docs/` —
#: an approval is a fact about a session, not a record of the project.
STORE_REL = Path(".cockpit") / "approvals.json"

#: The escalation kind these register under, so `escalation.assess` can see
#: them without learning a second vocabulary.
KIND = "permission"

#: **No default, deliberately.** A permission prompt is a request to take an
#: action with effects outside the record — running a command, writing a file
#: somewhere the cockpit does not guard. Lapsing one into "yes" would be the
#: system granting itself authority nobody delegated; lapsing into "no" would
#: silently change what the agent did. So it has a timeout that makes it
#: **alarm**, and never an assumption.
POLICY: dict[str, Any] = {"timeout_hours": 1, "default": None}

_STATUSES = ("open", "granted", "denied", "expired")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class ApprovalStore:
    """Permission prompts, persisted so they survive a restart."""

    def __init__(self, project_root: Path) -> None:
        self._path = project_root / STORE_REL
        self._lock = threading.Lock()
        self._items: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, list):
            self._items = [i for i in raw if isinstance(i, dict)]

    def _persist_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._items, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def record(
        self, *, session_id: str, tool: str = "", prompt: str = "",
        agent: str = "", options: list[str] | None = None,
    ) -> dict[str, Any]:
        """A prompt arrived. Idempotent per (session, tool, prompt) while open.

        Repeated hook deliveries are normal — a retried request must not become
        two obligations, which is the same lesson the review store learned when
        16 concurrent offers produced 9 indistinguishable rows.
        """
        with self._lock:
            for item in self._items:
                if (item.get("status") == "open"
                        and item.get("session_id") == session_id
                        and item.get("tool") == tool
                        and item.get("prompt") == prompt):
                    return dict(item)
            entry = {
                "approval_id": uuid.uuid4().hex[:12],
                "session_id": str(session_id),
                "agent": str(agent),
                "tool": str(tool),
                "prompt": str(prompt)[:1000],
                "options": [str(o) for o in (options or [])],
                "status": "open",
                "ts": _now(),
                "kind": KIND,
            }
            self._items.append(entry)
            self._persist_locked()
            return dict(entry)

    def answer(
        self, approval_id: str, *, decision: str, actor: str = "",
    ) -> dict[str, Any] | None:
        """Grant or deny. **An agent may not answer its own prompt.**

        The whole point of a permission prompt is that a different party
        decides; an agent answering its own would be the loop granting itself
        authority, which is exactly what the prompt exists to prevent.
        """
        if decision not in ("granted", "denied"):
            raise ValueError(f"decision must be granted or denied, not {decision!r}")
        who = (actor or "").strip()
        if not who:
            raise ValueError("an answer needs an actor; a permission decision is somebody's")
        low = who.lower()
        if low.startswith("agent:") and low != "agent:principal":
            raise ValueError(
                f"{actor!r} may not answer a permission prompt — the prompt exists "
                "because a different party decides (ADR-0009)"
            )
        with self._lock:
            for item in self._items:
                if item.get("approval_id") != approval_id:
                    continue
                if item.get("status") != "open":
                    return dict(item)
                item["status"] = decision
                item["decided_by"] = who
                item["decided_at"] = _now()
                self._persist_locked()
                return dict(item)
        return None

    def open_prompts(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(i) for i in self._items if i.get("status") == "open"]

    def all_prompts(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(i) for i in self._items]
