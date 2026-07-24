"""Status-diff layer (FEAT-0036 / TASK-0162).

Turns note saves into status-transition events. The docs-tree watcher
already publishes a ``FileEvent`` per save; this component parses the
saved note's frontmatter, compares its ``status`` against the last
known value, and — only on a real change — publishes a
``cockpit:status-change`` control event and records it in a capped
recent-transitions log served at ``GET /api/cockpit/transitions``.

Seeded from the index at startup so a cold scan (and a note's first
appearance) never fires a spurious transition.
"""

from __future__ import annotations

import datetime as _dt
import re
import threading
from collections import deque
from pathlib import Path
from typing import Any

import frontmatter

from .events import ControlEvent, FileEvent

_TRANSITIONS_MAX = 100


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")


def _norm_status(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    s = raw.strip().lower()
    return s or None


def _norm_type(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    m = re.search(r"[A-Za-z]+", raw)  # "[[task]]" -> "task"
    return m.group(0).lower() if m else None


class StatusTracker:
    """Emits ``cockpit:status-change`` on real frontmatter-status moves."""

    def __init__(self, docs_root: Path, bus) -> None:
        self._docs_root = docs_root
        self._bus = bus
        self._status: dict[str, str | None] = {}
        self._log: deque[dict[str, Any]] = deque(maxlen=_TRANSITIONS_MAX)
        self._lock = threading.Lock()

    def seed(self, index) -> None:
        """Prime the known-status map from the current index so the first
        real change emits (and the initial scan does not)."""
        with self._lock:
            for rec in index.iter_records():
                nid = getattr(rec, "note_id", None)
                if isinstance(nid, str) and nid:
                    self._status[nid] = _norm_status(rec.status)

    def on_event(self, event: object) -> None:
        if not isinstance(event, FileEvent):
            return
        if event.abs_path.suffix.lower() != ".md" or event.kind == "deleted":
            return
        try:
            post = frontmatter.load(str(event.abs_path))
        except Exception:
            return  # unreadable / mid-write — ignore, next event catches it
        fm = post.metadata or {}
        nid = fm.get("id")
        if not isinstance(nid, str) or not nid:
            return
        status = _norm_status(fm.get("status"))
        with self._lock:
            seen = nid in self._status
            old = self._status.get(nid)
            self._status[nid] = status
        # First appearance (seed/creation) or no change → not a transition.
        if not seen or old == status:
            return
        payload = {
            "id": nid,
            "rel": event.rel_path,
            "type": _norm_type(fm.get("type")),
            "title": fm.get("title") if isinstance(fm.get("title"), str) else None,
            "from": old,
            "to": status,
            "ts": _now_iso(),
        }
        with self._lock:
            self._log.append(payload)
        self._bus.publish(ControlEvent("cockpit:status-change", payload))

    def transitions(self) -> list[dict[str, Any]]:
        """Recent transitions, newest first."""
        with self._lock:
            return list(reversed(self._log))
