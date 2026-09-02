"""The returning human's watermark (FEAT-0071 / TASK-0312).

`DES-0008`: *"one human per cockpit, and server-side survives the renderer's
storage being cleared."*

**Moved only by an explicit `Caught up`, never by opening the app.** Presence is
not attention. A watermark that moves itself turns the digest into a slot
machine — you look, it empties, and you learn nothing about what you missed.

**A missing watermark reads as the epoch**, so the first digest shows
everything. Defaulting to *now* would be the same lie in a different shape: a
fresh install would report a quiet project because it had no memory, not
because nothing happened.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

#: What an unset watermark means. Deliberately not `now`.
EPOCH = "1970-01-01T00:00:00Z"


class Watermark:
    """File-backed last-seen marker for one workspace.

    Thread-safe (the HTTP server is threaded) and crash-tolerant, matching
    `ReviewStore`: writes go through a temp file + replace, and a corrupt store
    degrades to *unset* rather than taking the sidecar down — and unset means
    "show everything", which is the safe direction to fail in.
    """

    def __init__(self, project_root: Path) -> None:
        self._path = project_root / ".cockpit" / "last-seen.json"
        self._lock = threading.Lock()
        self._seen_at: str | None = None
        self._caught_up_count = 0
        self._load()

    def _load(self) -> None:
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError:
            return
        try:
            data = json.loads(raw)
        except ValueError:
            return
        if not isinstance(data, dict):
            return
        seen = data.get("seen_at")
        if isinstance(seen, str) and seen.strip():
            self._seen_at = seen.strip()
        count = data.get("caught_up_count")
        if isinstance(count, int) and count >= 0:
            self._caught_up_count = count

    def _persist_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seen_at": self._seen_at,
            "caught_up_count": self._caught_up_count,
        }
        fd, tmp = tempfile.mkstemp(dir=str(self._path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
                fh.write("\n")
            os.replace(tmp, self._path)
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    # ---- reading -------------------------------------------------------

    @property
    def seen_at(self) -> str:
        """The watermark, or the epoch when unset.

        Never `None` to a caller: an unset watermark is a real answer — *you
        have seen nothing* — and returning `None` invites every consumer to
        invent its own default.
        """
        with self._lock:
            return self._seen_at or EPOCH

    @property
    def is_set(self) -> bool:
        with self._lock:
            return self._seen_at is not None

    def payload(self) -> dict[str, Any]:
        with self._lock:
            return {
                "seen_at": self._seen_at or EPOCH,
                "is_set": self._seen_at is not None,
                "caught_up_count": self._caught_up_count,
            }

    # ---- the one thing that moves it -----------------------------------

    def catch_up(self, at: str | None = None) -> dict[str, Any]:
        """Record that the human read to the bottom.

        The **only** mover. `at` exists so the caller can pass the timestamp
        the digest was computed from rather than the moment the button was
        clicked — otherwise anything that landed while they were reading is
        silently marked seen.
        """
        stamp = (at or "").strip() or _dt.datetime.now(_dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        with self._lock:
            self._seen_at = stamp
            self._caught_up_count += 1
            self._persist_locked()
            return {
                "seen_at": self._seen_at,
                "is_set": True,
                "caught_up_count": self._caught_up_count,
            }
