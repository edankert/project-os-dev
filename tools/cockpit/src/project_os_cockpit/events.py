"""Tiny in-process pub/sub for filesystem events.

Producer: :mod:`project_os_cockpit.watcher` (TASK-0005).
Consumers: :class:`project_os_cockpit.index.Index` (cache invalidation), the SSE
channel (TASK-0006, broadcasts to connected browsers), the cockpit's
JS-side re-fetch (TASK-0011 extends event payloads with ``kind`` info).

Thread safety:
- :meth:`EventBus.subscribe` / :meth:`unsubscribe` take a lock around the
  subscribers list.
- :meth:`publish` snapshots the subscribers under the lock, then dispatches
  outside the lock — long-running callbacks won't block other subscribers
  or new subscriptions.
- Each subscriber callback runs on the publisher's thread (typically the
  watchdog Observer thread). Callbacks should be fast or hand off to a
  worker.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Union

log = logging.getLogger("project_os_cockpit.events")

Subscriber = Callable[["Event"], None]


@dataclass(frozen=True)
class FileEvent:
    """A filesystem event emitted by the watcher.

    ``kind`` is the watchdog-aligned label (`created` / `modified` /
    `deleted` / `moved`). TASK-0011 will introduce a richer typed event
    layer (frontmatter vs body vs base) on top of this primitive feed.
    """

    kind: str
    rel_path: str  # POSIX, relative to docs_root
    abs_path: Path


@dataclass(frozen=True)
class ControlEvent:
    """Out-of-band cockpit-control event (TASK-0048).

    Published by API endpoints (e.g. ``/api/cockpit/focus``) and
    forwarded to every open cockpit tab via SSE. The JS-side handler
    branches on ``event_type`` and dispatches accordingly. ``data`` is
    JSON-serialised before transport.
    """

    event_type: str            # e.g. "cockpit:focus", "cockpit:pin"
    data: dict[str, Any] = field(default_factory=dict)


Event = Union[FileEvent, ControlEvent]


class EventBus:
    """Lock-protected fanout — one publisher, many subscribers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[Subscriber] = []

    def subscribe(self, callback: Subscriber) -> Callable[[], None]:
        """Register ``callback`` and return an unsubscribe handle."""
        with self._lock:
            self._subscribers.append(callback)

        def _unsubscribe() -> None:
            self.unsubscribe(callback)

        return _unsubscribe

    def unsubscribe(self, callback: Subscriber) -> None:
        with self._lock:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        with self._lock:
            subs = list(self._subscribers)
        for cb in subs:
            try:
                cb(event)
            except Exception:
                log.exception("subscriber failed for %s", event)

    def __len__(self) -> int:
        with self._lock:
            return len(self._subscribers)


def relative_to_ci(abs_path: Path, root: Path) -> str | None:
    """POSIX-style relative path, case-insensitive prefix match.

    Returns ``None`` when ``abs_path`` is not under ``root``.

    macOS volumes are case-preserving but case-insensitive: fsevents may
    report ``/Users/Edwin/...`` while ``root`` was constructed from
    ``$(pwd)`` and is ``/Users/edwin/...``. Python's ``Path.relative_to``
    is case-sensitive and would silently drop the path. This helper
    folds case before the prefix check.
    """
    abs_str = str(abs_path)
    root_str = str(root).rstrip("/")
    if abs_str.lower() == root_str.lower():
        return ""
    if not abs_str.lower().startswith(root_str.lower() + "/"):
        return None
    return abs_str[len(root_str) + 1:].replace("\\", "/")


def is_under_ci(abs_path: Path, root: Path) -> bool:
    """``True`` iff ``abs_path`` equals or descends from ``root`` (case-insensitive)."""
    return relative_to_ci(abs_path, root) is not None
