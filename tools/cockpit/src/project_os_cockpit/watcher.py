"""Filesystem watcher.

Wraps a ``watchdog.Observer`` and converts its events into :class:`FileEvent`
publishes on a shared :class:`EventBus`. Subscribers (the index, the SSE
channel, the cockpit JS re-fetch) all read from the same bus.

Coalescing: a single editor save can trigger multiple watchdog events for
the same path (modify + close + sometimes a tmp-file rename dance). We
debounce by dropping repeated events for the same ``(path, kind)`` tuple
within a 100 ms window. That's enough for typical editor saves; legitimate
back-to-back saves >100 ms apart still both publish.

Filtering: directory events are ignored. Hidden paths (any segment starting
with ``.``) are ignored. Everything else is forwarded — consumers filter
on extension as needed.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .events import EventBus, FileEvent, relative_to_ci

log = logging.getLogger("project_os_cockpit.watcher")

# Coalesce repeats for the same (path, kind) within this window.
DEBOUNCE_S: float = 0.10


class Watcher:
    """Recursive watchdog observer pointed at the docs root."""

    def __init__(self, docs_root: Path, bus: EventBus) -> None:
        self.docs_root = docs_root.resolve(strict=True)
        if not self.docs_root.is_dir():
            raise NotADirectoryError(f"docs root is not a directory: {self.docs_root}")
        self.bus = bus
        self._observer: Observer | None = None
        self._handler = _Handler(self.docs_root, self.bus)

    def start(self) -> None:
        if self._observer is not None:
            return
        observer = Observer()
        observer.schedule(self._handler, str(self.docs_root), recursive=True)
        observer.daemon = True  # don't block process shutdown if stop() is missed
        observer.start()
        self._observer = observer
        log.info("watcher: watching %s", self.docs_root)

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=2.0)
        self._observer = None
        log.info("watcher: stopped")

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()


class _Handler(FileSystemEventHandler):
    """watchdog handler — emits :class:`FileEvent` onto the shared bus."""

    def __init__(self, docs_root: Path, bus: EventBus) -> None:
        self._root = docs_root
        self._bus = bus
        self._last_emit: dict[tuple[str, str], float] = defaultdict(float)
        self._lock = threading.Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._emit("created", Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._emit("modified", Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._emit("deleted", Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        # Atomic-rename writers (vim, etc.) surface as Moved; turn into a
        # delete/create pair so consumers don't need to handle Moved
        # separately and the index sees the new path indexed.
        self._emit("deleted", Path(event.src_path))
        if getattr(event, "dest_path", None):
            self._emit("created", Path(event.dest_path))

    def _emit(self, kind: str, abs_path: Path) -> None:
        # Case-insensitive relativisation — see ``events.relative_to_ci``
        # for the macOS-specific reason why ``Path.relative_to`` isn't
        # safe here.
        rel = relative_to_ci(abs_path, self._root)
        if rel is None:
            return
        # Skip dotfiles / dot-dirs (`.git`, `.obsidian`, `.DS_Store`, etc.)
        if any(part.startswith(".") for part in rel.split("/") if part):
            return
        key = (rel, kind)
        now = time.monotonic()
        with self._lock:
            if now - self._last_emit[key] < DEBOUNCE_S:
                return
            self._last_emit[key] = now
        log.debug("watcher: %s %s", kind, rel)
        self._bus.publish(FileEvent(kind=kind, rel_path=rel, abs_path=abs_path))


