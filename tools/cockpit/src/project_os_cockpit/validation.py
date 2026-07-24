"""Validation health runner (FEAT-0018 / TASK-0111).

Runs the project-os docs validator (``tools/scripts/validate-docs.py``)
against the browsed repo, caches the parsed report, and re-runs it on
watcher events with a short debounce. The validator stays the single
source of validation logic — this module only locates it, invokes it as
a subprocess, and parses its report lines. No check is reimplemented
here.

Locate order:

1. ``<project-root>/tools/scripts/validate-docs.py`` — the browsed
   repo's own copy (guaranteed after a project-os template sync, and
   authoritative because it honours that repo's ``STATUSES.md``).
2. The cockpit's bundled copy (``validate_docs_bundled.py``, a verbatim
   copy of the canonical script shipped inside this package) — so repos
   that predate the validator still get a health signal.

Result states:

- ``ok`` — validator exit 0 (may still carry warnings).
- ``failing`` — validator exit 1: one or more ``ERROR [CODE]`` lines.
- ``unavailable`` — validator exit 2 (missing SNAPSHOT.yaml / usage or
  internal error), no locatable script, missing interpreter, or a hung
  run. Distinct from both healthy and failing so the UI can grey out
  instead of lying in either direction.

Change fan-out: when the observable state changes (ok↔failing↔
unavailable, or the error set differs), the fresh payload is published
as a ``cockpit:validation`` :class:`~project_os_cockpit.events.ControlEvent`
on the shared bus, and the SSE channel forwards it to connected clients
(same pipeline as ``cockpit:agent-state``).

The main filesystem watcher only covers the docs root, so this runner
owns a second, non-recursive watchdog observer on the project root to
catch ``SNAPSHOT.yaml`` edits (started via :meth:`ValidationRunner.start`).
"""

from __future__ import annotations

import datetime as _dt
import logging
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .events import ControlEvent, Event, EventBus, FileEvent

log = logging.getLogger("project_os_cockpit.validation")

# Debounce window for watcher-triggered re-runs: a bulk save touching
# many notes (or an agent's close-out pass) coalesces into one run.
DEBOUNCE_SECONDS: float = 1.0

# Subprocess guard — the validator is a single stdlib pass over docs/,
# well under a second on real corpora; anything past this is a hang.
_RUN_TIMEOUT_SECONDS: float = 30.0

# ``ERROR [CODE] message`` / ``WARN  [CODE] message`` — the validator's
# report line shape (see the Report class in validate-docs.py).
_REPORT_LINE_RE = re.compile(r"^(ERROR|WARN)\s+\[([A-Z0-9-]+)\]\s+(.*)$")

# Same project-os ID pattern the index uses (index.PROJECT_OS_ID_RE) —
# the first match in a message is the subject item.
_ID_RE = re.compile(
    r"\b(?:FEAT|TASK|REQ|ISS|CHG|ADR|RISK|TST|REL|PHASE|WF|PLAN)-[\w-]+"
)

# Repo-relative note path embedded in a report message, e.g.
# ``... (docs/features/x/FEAT-0001-X.md)`` or ``file does not exist: docs/...``.
_REL_PATH_RE = re.compile(r"\b((?:docs|tools)/[^\s:)]+\.md)\b")

# Verbatim copy of tools/scripts/validate-docs.py shipped in the package.
BUNDLED_VALIDATOR: Path = Path(__file__).resolve().parent / "validate_docs_bundled.py"

# SSE / ControlEvent name for validation-state changes.
SSE_EVENT: str = "cockpit:validation"


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")


def parse_report_lines(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse validator stdout into ``(errors, warnings)`` entry lists.

    Each entry is ``{code, message, id, rel}`` — ``id``/``rel`` are
    ``None`` when the message carries neither a project-os ID nor a
    repo-relative note path. Non-report lines (the trailing ``FAIL``/
    ``OK`` summary) are ignored.
    """
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        m = _REPORT_LINE_RE.match(line.strip())
        if not m:
            continue
        level, code, message = m.group(1), m.group(2), m.group(3).strip()
        id_match = _ID_RE.search(message)
        rel_match = _REL_PATH_RE.search(message)
        entry: dict[str, Any] = {
            "code": code,
            "message": message,
            "id": id_match.group(0) if id_match else None,
            "rel": rel_match.group(1) if rel_match else None,
        }
        (errors if level == "ERROR" else warnings).append(entry)
    return errors, warnings


class _SnapshotHandler(FileSystemEventHandler):
    """Non-recursive project-root watcher — SNAPSHOT.yaml edits only."""

    def __init__(self, on_change: Callable[[], None]) -> None:
        self._on_change = on_change

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        for raw in (event.src_path, getattr(event, "dest_path", None)):
            if raw and Path(str(raw)).name == "SNAPSHOT.yaml":
                self._on_change()
                return


class ValidationRunner:
    """Locates, runs, caches, and fans out the docs validator.

    Collaborators mirror the existing server wiring: the shared
    :class:`EventBus` for both input (docs file events via
    :meth:`on_event`) and output (``cockpit:validation`` publishes),
    and the index's ``resolve`` callable for deep-linking violations
    to their notes.
    """

    def __init__(
        self,
        project_root: Path,
        bus: EventBus | None = None,
        *,
        resolver: Callable[[str], str | None] | None = None,
        debounce_seconds: float = DEBOUNCE_SECONDS,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self._bus = bus
        self._resolver = resolver
        self._debounce = debounce_seconds
        self._lock = threading.Lock()          # cache + timer state
        self._run_lock = threading.Lock()      # serialises validator runs
        self._timer: threading.Timer | None = None
        self._cached: dict[str, Any] | None = None
        self._observer: Observer | None = None

    # ---- lifecycle ----

    def start(self) -> None:
        """Start the project-root SNAPSHOT.yaml observer (idempotent).

        Docs-tree events arrive via the main watcher through
        :meth:`on_event`; SNAPSHOT.yaml lives *above* the docs root so
        it needs this dedicated non-recursive observer.
        """
        if self._observer is not None:
            return
        observer = Observer()
        observer.schedule(
            _SnapshotHandler(self.schedule),
            str(self.project_root),
            recursive=False,
        )
        observer.daemon = True
        observer.start()
        self._observer = observer
        log.info("validation: watching %s/SNAPSHOT.yaml", self.project_root)

    def stop(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None

    # ---- event intake ----

    def on_event(self, event: Event) -> None:
        """Bus subscriber — any docs-tree file event schedules a re-run.

        The main watcher only emits :class:`FileEvent` for paths under
        the docs root (dotfiles already filtered), so every file event
        is validation-relevant. Control events are ignored.
        """
        if isinstance(event, FileEvent):
            self.schedule()

    def schedule(self) -> None:
        """Schedule a debounced re-run (~1 s), coalescing bursts."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            timer = threading.Timer(self._debounce, self._scheduled_refresh)
            timer.daemon = True
            timer.name = "cockpit-validation-debounce"
            self._timer = timer
            timer.start()

    def _scheduled_refresh(self) -> None:
        with self._lock:
            self._timer = None
        try:
            self.refresh()
        except Exception:
            log.exception("validation: scheduled refresh failed")

    # ---- report access ----

    def current(self) -> dict[str, Any]:
        """Cached report; runs the validator synchronously when cold."""
        with self._lock:
            cached = self._cached
        if cached is not None:
            return cached
        return self.refresh()

    def refresh(self) -> dict[str, Any]:
        """Run the validator now, cache the report, fan out changes."""
        with self._run_lock:
            payload = self._run_validator()
            with self._lock:
                previous = self._cached
                self._cached = payload
            if self._bus is not None and self._observable_changed(previous, payload):
                self._bus.publish(ControlEvent(SSE_EVENT, payload))
            return payload

    # ---- internals ----

    def locate_validator(self) -> Path | None:
        """The browsed repo's validator, else the bundled copy."""
        repo_copy = self.project_root / "tools" / "scripts" / "validate-docs.py"
        if repo_copy.is_file():
            return repo_copy
        if BUNDLED_VALIDATOR.is_file():
            return BUNDLED_VALIDATOR
        return None

    @staticmethod
    def _observable_changed(
        previous: dict[str, Any] | None, current: dict[str, Any]
    ) -> bool:
        """ok↔failing↔unavailable flips or an error-set delta.

        Warnings-only drift does not fan out — the badge and drift
        panel key off state + errors, and warning churn (e.g. the
        PATH-ALIAS count) would be SSE noise.
        """
        if previous is None:
            return True

        def _key(p: dict[str, Any]) -> tuple:
            return (
                p.get("state"),
                tuple((e.get("code"), e.get("message")) for e in p.get("errors") or []),
            )

        return _key(previous) != _key(current)

    def _deep_link(self, entry: dict[str, Any]) -> str | None:
        """Resolve an entry to a cockpit URL via the existing resolver."""
        if self._resolver is not None and entry.get("id"):
            url = self._resolver(entry["id"])
            if url:
                return url
        rel = entry.get("rel")
        if rel and rel.startswith("docs/"):
            return "/" + rel
        return None

    def _payload(
        self,
        state: str,
        errors: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, Any]] | None = None,
        detail: str | None = None,
    ) -> dict[str, Any]:
        errors = errors or []
        for entry in errors:
            entry["url"] = self._deep_link(entry)
        payload: dict[str, Any] = {
            "ok": state == "ok",
            "state": state,
            "errors": errors,
            "warnings": warnings or [],
            "checked_at": _utc_now_iso(),
        }
        if detail:
            payload["detail"] = detail
        return payload

    def _run_validator(self) -> dict[str, Any]:
        script = self.locate_validator()
        if script is None:
            return self._payload(
                "unavailable", detail="no validate-docs.py found (repo or bundled)"
            )
        cmd = [
            sys.executable,
            str(script),
            "--repo-root",
            str(self.project_root),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_RUN_TIMEOUT_SECONDS,
                cwd=str(self.project_root),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            log.warning("validation: validator run failed: %s", exc)
            return self._payload(
                "unavailable", detail=f"validator run failed: {exc}"
            )
        errors, warnings = parse_report_lines(proc.stdout)
        if proc.returncode == 0:
            return self._payload("ok", errors=[], warnings=warnings)
        if proc.returncode == 1:
            return self._payload("failing", errors=errors, warnings=warnings)
        # Exit 2 — usage / setup / internal error (e.g. no SNAPSHOT.yaml).
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return self._payload(
            "unavailable",
            detail=detail[-1] if detail else f"validator exit {proc.returncode}",
        )
