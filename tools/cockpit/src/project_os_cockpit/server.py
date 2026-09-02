"""HTTP server for project-os-cockpit.

A small ``ThreadingHTTPServer`` with a custom request handler that:

- serves static assets (CSS, JS) from the packaged ``static/`` directory at
  ``/_static/<file>``,
- renders Markdown notes under the configured docs root at ``/docs/<rel-path>``,
- emits directory listings when the path resolves to a directory,
- enforces a strict path-traversal guard (no ``..``, no symlink escapes).

Live reload (FEAT-0002), wikilink resolution (TASK-0003), and the cockpit
shell (FEAT-0006) layer on top of this in later tasks.
"""

from __future__ import annotations

import atexit
import collections
import datetime as _dt
import base64
import binascii
import json
import re
import logging
import mimetypes
import os
import queue
import subprocess
import threading
import time as _time
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable

from . import decisions
from . import (
    acceptance, agents, cockpit, criteria, note_writes, renderer, templates,
    terminal_proxy,
)
from .agent_actions import load_actions
from .agent_hooks import AgentSessionTracker
from .status_diff import StatusTracker
from .agent_hooks import MAX_BODY_BYTES as _AGENT_HOOK_MAX_BYTES
from .events import ControlEvent, EventBus, FileEvent
from .index import Index
from . import inbox as inbox_mod
from .watermark import Watermark
from . import obligations as _obligations
from . import review
from .approvals import ApprovalStore
from . import escalation
from .review import ReviewStore
from .terminal import TERMINAL_BASE_PATH, TerminalProcess
from .validation import ValidationRunner
from .watcher import Watcher


def _desktop_mode() -> bool:
    """True when the server is running as a sidecar of the Electron shell.

    The Electron shell (FEAT-0007) sets ``COCKPIT_DESKTOP=1`` in the
    spawned sidecar's environment. In that mode:

    * the ``.cockpit/url`` discovery file is NOT written (the shell
      drives focus over IPC, not via the on-disk hint), and
    * the ``/api/terminal`` + ``/_terminal/*`` endpoints short-circuit
      (the shell mounts a native ``node-pty``-backed pane in the same
      bottom-panel slot the browser uses for the ttyd iframe).

    Defaults — and therefore mode 1 (per-project browser use) — are
    unchanged.
    """
    return os.environ.get("COCKPIT_DESKTOP") == "1"

# URL plural → frontmatter type singular. Project-os IDs and template names
# disagree in one place: ``/index/decisions`` indexes ``type: [[adr]]``.
INDEX_TYPE_PLURALS: dict[str, str] = {
    "features": "feature",
    "tasks": "task",
    "requirements": "requirement",
    "issues": "issue",
    "risks": "risk",
    "decisions": "adr",
    "changes": "change",
    "releases": "release",
    "workflows": "workflow",
    "tests": "test",
    "phases": "phase",
    "references": "reference",
}

log = logging.getLogger("project_os_cockpit.server")

STATIC_DIR: Path = Path(__file__).resolve().parent / "static"

#: Files the shell-assets route will serve (TASK-0227). An allow-list rather
#: than a directory share: the design surface needs the stylesheet, and
#: nothing about that is a reason to expose the bundle or its source maps.
SHELL_ASSET_FILES: frozenset[str] = frozenset({"renderer.css"})

# Tabs whose last_seen heartbeat is older than this are pruned from the
# state snapshot. The cockpit JS sends a heartbeat every 15 s
# (TASK-0055); 45 s allows two missed pings before we declare the tab
# gone.
_TAB_STALE_SECONDS: int = 45
_HISTORY_MAX: int = 50

# How long a stored `busy` / `waiting` agent state stays "current"
# before the snapshot reports it as decayed-to-idle (FEAT-0013 /
# TASK-0076). Env-overridable so tests can shrink the window without
# patching internals.
_AGENT_STATE_DECAY_SECONDS: int = int(
    os.environ.get("COCKPIT_AGENT_STATE_DECAY_SECONDS", "600")
)

# Allowed agent-state values. Mirrored by the validator in
# `_serve_agent_state` (TASK-0077) and the `cockpit signal` CLI
# subcommand (TASK-0078). `needs-input` (FEAT-0019 / TASK-0114) is
# hook-fed: the agent is blocked on a human (permission prompt,
# elicitation, idle prompt).
_AGENT_STATES: frozenset[str] = frozenset(
    {"busy", "waiting", "needs-input", "done", "error", "idle"}
)
# Only `busy` decays: a working agent that goes silent is a dead worker,
# so idling its rail dot is correct. Attention states (`waiting`,
# `needs-input`) must NOT decay — REQ-0018 requires they persist until the
# user acts or dismisses, since a blocked agent sends no further events
# and would otherwise vanish from the inbox while still needing you
# (TASK-0175). The ack/read-state (static-once-seen) handles staleness.
_AGENT_DECAYABLE_STATES: frozenset[str] = frozenset({"busy"})


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")


def _parse_iso(ts: str) -> float:
    try:
        return _dt.datetime.fromisoformat(ts).timestamp()
    except (ValueError, TypeError):
        return 0.0


class CockpitState:
    """In-memory snapshot of cockpit activity for the bi-directional
    awareness API (TASK-0053).

    Tracks three things:

    * ``agent_focus`` — the most recent ``cockpit focus`` call.
    * ``tabs`` — currently-alive cockpit tabs, keyed by client-generated
      ``tab_id``, each carrying ``url``, ``following``, ``last_seen``.
    * ``history`` — a bounded deque of recent navigation events from
      both the agent (``cockpit focus``) and the user (manual nav in a
      tab), newest first.

    All mutation goes through a lock — the HTTP server is multi-threaded
    and the SSE thread, the focus POST handler, and the tab-state POST
    handler can all touch this concurrently.
    """

    def __init__(self, *, state_path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._agent_focus: dict[str, Any] | None = None
        self._agent_state: dict[str, Any] | None = None
        # Flag flipped to True after the decay thread (TASK-0077)
        # observes a stored busy/waiting that has aged out; ensures
        # we only fire ONE synthetic SSE per decay event.
        self._agent_state_decay_observed: bool = False
        # Persisted agent-state file path (FEAT-0010 / TASK-0081).
        # When set, every state transition (including decay) writes a
        # mirror copy here so the desktop shell's workspace rail
        # (TASK-0082) can poll per-workspace state without needing a
        # live sidecar / SSE subscription per workspace.
        self._state_path: Path | None = state_path
        if state_path is not None:
            self._seed_agent_state_from_file(state_path)
        self._tabs: dict[str, dict[str, Any]] = {}
        self._history: collections.deque[dict[str, Any]] = collections.deque(
            maxlen=_HISTORY_MAX
        )

    def _seed_agent_state_from_file(self, path: Path) -> None:
        """Load the on-disk agent-state into memory on startup so a
        cockpit restart doesn't reset the rail dot. Tolerates missing
        / malformed JSON — the file is best-effort, never required."""
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            return
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return
        if isinstance(data, dict) and isinstance(data.get("state"), str):
            self._agent_state = data

    def _persist_agent_state(self, payload: dict[str, Any] | None) -> None:
        """Mirror the in-memory state to disk for cross-workspace
        readers (TASK-0081). Called from the write paths under the
        instance lock; failures are logged, never raised."""
        if self._state_path is None:
            return
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            if payload is None:
                self._state_path.unlink(missing_ok=True)
                return
            self._state_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            log.warning(
                "agent-state file write failed for %s: %s",
                self._state_path, exc,
            )

    def record_agent_focus(self, target: str, url: str) -> None:
        ts = _utc_now_iso()
        with self._lock:
            self._agent_focus = {"target": target, "url": url, "ts": ts}
            self._history.appendleft(
                {"url": url, "ts": ts, "source": "agent", "target": target}
            )

    def record_agent_state(
        self,
        state: str,
        target: str | None = None,
        agent: str | None = None,
        message: str | None = None,
        source: str = "manual",
    ) -> dict[str, Any]:
        """Record an agent-state transition (FEAT-0013 / TASK-0076).

        Stores the latest declaration and pushes a history row so the
        agent's activity is observable alongside focus / user-nav. The
        returned dict is the canonical payload — callers fan it out as
        a ``cockpit:agent-state`` SSE event.
        """
        ts = _utc_now_iso()
        payload: dict[str, Any] = {"state": state, "ts": ts}
        if target:
            payload["target"] = target
        if agent:
            payload["agent"] = agent
        if message:
            payload["message"] = message
        if source != "manual":
            payload["source"] = source
        with self._lock:
            self._agent_state = payload
            # A fresh declaration clears the decay-observed flag so the
            # next decay event (if any) fires its own SSE.
            self._agent_state_decay_observed = False
            self._history.appendleft({
                "ts": ts, "source": "agent-state", **payload,
            })
            self._persist_agent_state(payload)
        return payload

    def _effective_agent_state(self, now: float) -> dict[str, Any] | None:
        """Apply lazy decay to the stored agent-state for read paths.

        Stored value is **not** mutated — decay is observation-only at
        this layer. Returns either the stored payload or, if it has
        aged out, a synthetic ``{state: "idle", decayed_from: ...,
        ts: <orig ts>}`` block. The decay-observed flag is what guards
        SSE re-emission; that's the decay thread's job (TASK-0077).
        """
        stored = self._agent_state
        if stored is None:
            return None
        if stored["state"] not in _AGENT_DECAYABLE_STATES:
            return stored
        age = now - _parse_iso(stored["ts"])
        if age <= _AGENT_STATE_DECAY_SECONDS:
            return stored
        return {
            "state": "idle",
            "decayed_from": stored["state"],
            "ts": stored["ts"],
        }

    def decay_tick(self, now: float | None = None) -> dict[str, Any] | None:
        """Called by the decay thread (TASK-0077). Returns the
        synthetic SSE payload exactly **once** per decay event;
        subsequent calls return None until the next fresh state.
        """
        if now is None:
            now = time.time()
        with self._lock:
            stored = self._agent_state
            if stored is None or stored["state"] not in _AGENT_DECAYABLE_STATES:
                return None
            age = now - _parse_iso(stored["ts"])
            if age <= _AGENT_STATE_DECAY_SECONDS:
                return None
            if self._agent_state_decay_observed:
                return None
            self._agent_state_decay_observed = True
            synthetic = {
                "state": "idle",
                "decayed_from": stored["state"],
                "ts": stored["ts"],
            }
            # Mirror the observable state to disk so the workspace
            # rail (TASK-0082) sees the same `idle` the SSE consumers
            # see, without needing to re-derive decay on the reader side.
            self._persist_agent_state(synthetic)
            return synthetic

    def update_tab(
        self, tab_id: str, url: str, following: bool
    ) -> None:
        ts = _utc_now_iso()
        with self._lock:
            prev = self._tabs.get(tab_id)
            self._tabs[tab_id] = {
                "url": url,
                "following": bool(following),
                "last_seen": ts,
            }
            # Only record into history when the URL actually changed —
            # heartbeats don't create history noise.
            if not prev or prev.get("url") != url:
                self._history.appendleft(
                    {"url": url, "ts": ts, "source": "user", "tab_id": tab_id}
                )

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            alive = {
                tid: info
                for tid, info in self._tabs.items()
                if now - _parse_iso(info["last_seen"]) <= _TAB_STALE_SECONDS
            }
            self._tabs = alive
            user_view: dict[str, Any] | None = None
            for info in alive.values():
                if user_view is None or info["last_seen"] > user_view["ts"]:
                    user_view = {"url": info["url"], "ts": info["last_seen"]}
            return {
                "agent_focus": self._agent_focus,
                "agent_state": self._effective_agent_state(now),
                "user_view": user_view,
                "tabs": [
                    {"tab_id": tid, **info} for tid, info in alive.items()
                ],
                "history": list(self._history),
            }

# Hidden from directory listings — VCS / editor / OS metadata.
HIDDEN_NAME_PREFIXES: tuple[str, ...] = (".",)
HIDDEN_NAMES: frozenset[str] = frozenset({"node_modules", "__pycache__"})


class _NoDNSThreadingHTTPServer(ThreadingHTTPServer):
    """Like ``ThreadingHTTPServer`` but skips the reverse-DNS lookup at bind.

    The stdlib ``HTTPServer.server_bind`` calls ``socket.getfqdn(host)`` to
    set ``server_name`` for logging. On constrained networks / sandboxes
    that lookup can take tens of seconds and contributes nothing useful for
    a local dev tool. We set ``server_name`` to the bind address verbatim.
    """

    def server_bind(self) -> None:  # type: ignore[override]
        # Skip socketserver.TCPServer's parent chain at the HTTPServer level
        # (which does the getfqdn) — call into TCPServer directly.
        import socketserver

        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host or "localhost"
        self.server_port = port


class DocsServer:
    """Wraps a ``ThreadingHTTPServer`` bound to a docs root."""

    def __init__(
        self, *, docs_root: Path, bind: str, port: int,
        shell_assets: Path | None = None,
    ) -> None:
        self.docs_root = docs_root.resolve(strict=True)
        if not self.docs_root.is_dir():
            raise NotADirectoryError(f"docs root is not a directory: {self.docs_root}")
        self.bind = bind
        self.port = port
        # Where the desktop shell's built stylesheet lives (TASK-0227).
        # `None` in mode-1, which has no Electron build at all — so this is
        # an optional capability, never a dependency.
        self.shell_assets = shell_assets.resolve() if shell_assets else None
        self.bus: EventBus = EventBus()
        self.index: Index = Index.build(self.docs_root)
        # Index subscribes for invalidation; the SSE channel (TASK-0006) and
        # the cockpit JS re-fetch (TASK-0011) attach later.
        self.index.subscribe_to(self.bus)
        self.watcher: Watcher = Watcher(self.docs_root, self.bus)
        # Agent-state mirror file lives next to .cockpit/url so the
        # desktop rail (TASK-0082) can poll all discovered workspaces
        # uniformly. Unlike the URL file, this IS written in desktop
        # mode — last-known-state is the contract, not "where is the
        # cockpit running."
        self.watermark = Watermark(self.docs_root.parent)
        state_path = self.docs_root.parent / ".cockpit" / "agent-state.json"
        self.cockpit_state: CockpitState = CockpitState(state_path=state_path)
        # Hook-fed session tracker (FEAT-0019 / TASK-0114). Persists the
        # session index next to the agent-state mirror; also watches
        # file events for CHG provenance correlation (TASK-0126).
        self.agent_tracker: AgentSessionTracker = AgentSessionTracker(
            docs_root=self.docs_root,
            sessions_path=self.docs_root.parent / ".cockpit" / "sessions.json",
        )

        def _tracker_file_event(ev) -> None:
            if isinstance(ev, FileEvent):
                self.agent_tracker.on_file_event(ev.kind, ev.rel_path)

        self.bus.subscribe(_tracker_file_event)
        # Docs-validator health runner (FEAT-0018 / TASK-0111). Subscribes
        # to the same bus the index/SSE use: docs-tree file events schedule
        # a debounced validator re-run; state changes fan back out as
        # ``cockpit:validation`` control events. The SNAPSHOT.yaml observer
        # (the file lives above the docs root, outside the main watcher)
        # starts in ``run`` and stops with the server.
        self.validation: ValidationRunner = ValidationRunner(
            self.docs_root.parent, self.bus, resolver=self.index.resolve,
        )
        self.bus.subscribe(self.validation.on_event)
        # Status-diff layer (FEAT-0036 / TASK-0162): note saves become
        # cockpit:status-change events feeding the live-work views.
        # Seeded from the current index so the first scan is silent.
        self.status_tracker: StatusTracker = StatusTracker(self.docs_root, self.bus)
        self.status_tracker.seed(self.index)
        self.bus.subscribe(self.status_tracker.on_event)

        # Correlate status changes to the live session (TASK-0194): the
        # watcher sees every note status change regardless of how the file
        # was written, so this captures shell-tool edits the PostToolUse
        # touch-tracker misses. Subscribed after the status tracker, which
        # publishes the cockpit:status-change events this consumes.
        def _tracker_status_event(ev) -> None:
            if isinstance(ev, ControlEvent) and ev.event_type == "cockpit:status-change":
                self.agent_tracker.record_status_change(ev.data)

        self.bus.subscribe(_tracker_status_event)
        # Decay thread shutdown flag — flipped in `run`'s `finally`.
        self._decay_stop: threading.Event = threading.Event()
        # Header home-link label = repo name (parent of docs/), so users
        # always see which project they're browsing.
        templates.set_project_name(
            self.docs_root.parent.name or self.docs_root.name or "docs"
        )

    def _cockpit_url(self) -> str:
        """Base URL ttyd's child shell uses for COCKPIT_URL.

        When the cockpit binds to 0.0.0.0 (LAN exposure), the terminal's
        child shell still talks to it via loopback — both run on the
        same host.
        """
        host = self.bind if self.bind not in ("0.0.0.0", "::") else "127.0.0.1"
        return f"http://{host}:{self.port}"

    def run(self) -> None:
        handler_cls = _make_handler(
            self.docs_root, self.index, self.bus,
            cockpit_url=self._cockpit_url(),
            cockpit_state=self.cockpit_state,
            agent_tracker=self.agent_tracker,
            validation_runner=self.validation,
            status_tracker=self.status_tracker,
            shell_assets=self.shell_assets,
            watermark=self.watermark,
        )
        self.watcher.start()
        # SNAPSHOT.yaml sits above the docs root — the validation runner
        # owns its own non-recursive observer for it (TASK-0111).
        self.validation.start()
        # Background decay thread for agent-state (FEAT-0013 / TASK-0077).
        # Wakes once a minute, asks the state for any aged-out
        # busy/waiting it should now consider idle, and publishes the
        # synthetic SSE event when it finds one. Daemon so it dies
        # with the process even if the explicit stop doesn't fire.
        self._decay_stop.clear()
        decay_thread = threading.Thread(
            target=self._agent_state_decay_loop,
            name="cockpit-agent-state-decay",
            daemon=True,
        )
        decay_thread.start()
        # Write the discovery file so the `cockpit` CLI (from any
        # terminal under the project tree) can auto-find this server.
        # Also written in desktop mode since FEAT-0027: it lets
        # external terminals reach the desktop sidecar (`cockpit
        # focus/dispatch`) and lets the external agent-state hook POST
        # to the full pipeline instead of file-writing. If a mode-1
        # server and the desktop sidecar run on the same repo the last
        # writer wins — both are valid targets.
        _write_discovery_file(
            self.docs_root.parent, self._cockpit_url(),
        )
        try:
            with _NoDNSThreadingHTTPServer(
                (self.bind, self.port), handler_cls
            ) as httpd:
                log.info(
                    "project-os-cockpit listening on http://%s:%d (docs root: %s)",
                    self.bind,
                    self.port,
                    self.docs_root,
                )
                print(
                    f"project-os-cockpit: http://{self.bind}:{self.port}/  "
                    f"(serving {self.docs_root})",
                    flush=True,
                )
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\nproject-os-cockpit: shutting down.", flush=True)
        finally:
            self._decay_stop.set()
            decay_thread.join(timeout=2)
            self.validation.stop()
            self.watcher.stop()

    def _agent_state_decay_loop(self) -> None:
        """Per-minute decay tick (FEAT-0013 / TASK-0077). On each
        wake-up, ask the state for any aged-out busy/waiting event;
        if one is observed, publish a synthetic
        ``cockpit:agent-state`` SSE so subscribers don't keep
        showing stale green/amber dots forever."""
        # Tick interval kept short relative to the decay window
        # so the synthetic event lands within ~1 min of expiry.
        # Configurable via env for tests that want sub-second.
        interval = float(os.environ.get(
            "COCKPIT_AGENT_STATE_DECAY_TICK_SECONDS", "60",
        ))
        while not self._decay_stop.is_set():
            payload = self.cockpit_state.decay_tick()
            if payload is not None:
                try:
                    self.bus.publish(
                        ControlEvent("cockpit:agent-state", payload),
                    )
                except Exception:
                    log.exception(
                        "agent-state decay publish failed",
                    )
            # Wait + return immediately on shutdown.
            if self._decay_stop.wait(timeout=interval):
                break


def _cwd_within_root(cwd: str, project_root: Path) -> bool:
    """True when ``cwd`` resolves inside ``project_root``.

    Identity guard for hook ingestion (ISS-0007 / TASK-0146): sidecar
    ports get reused across desktop-app restarts, so a stale
    ``.cockpit/url`` can route another repo's hook events here. Case
    is normalised on both sides — macOS paths arrive in mixed case
    (the ISS-0001 lesson).
    """
    try:
        cand = os.path.realpath(str(cwd))
        root = os.path.realpath(str(project_root))
    except (OSError, ValueError):
        return False
    # realpath does not canonicalise character case on macOS and
    # os.path.normcase is a no-op on POSIX, so fold explicitly — the
    # primary filesystem (APFS) is case-insensitive and mixed-case
    # paths for the same directory are routine. On a case-sensitive
    # filesystem this can over-accept a same-name-different-case
    # sibling; that trade is fine for a guard whose failure mode is
    # merely accepting a hook event.
    cand = cand.casefold()
    root = root.casefold()
    return cand == root or cand.startswith(root + os.sep)


def _make_handler(
    docs_root: Path, index: Index, bus: EventBus,
    *, cockpit_url: str = "",
    cockpit_state: CockpitState | None = None,
    agent_tracker: AgentSessionTracker | None = None,
    validation_runner: ValidationRunner | None = None,
    status_tracker: "StatusTracker | None" = None,
    shell_assets: Path | None = None,
    watermark: Watermark | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class with the per-server collaborators baked in."""
    marker = watermark or Watermark(docs_root.parent)
    project_root = docs_root.parent.resolve()
    state = cockpit_state or CockpitState()
    tracker = agent_tracker or AgentSessionTracker(docs_root=docs_root)
    status_diff = status_tracker
    validation = validation_runner
    if validation is None:
        # Standalone-handler path (tests spin handlers up without a
        # DocsServer): build a runner on the same bus so file events
        # still schedule debounced re-runs (TASK-0111).
        validation = ValidationRunner(
            project_root, bus, resolver=index.resolve,
        )
        bus.subscribe(validation.on_event)
    # Stats payload cache (TASK-0128): scope key → (index generation,
    # payload). Invalidation is generation comparison, nothing to evict.
    _stats_cache: dict[str, tuple[int, dict]] = {}
    # Commits payload cache (TASK-0199): single slot keyed on
    # (HEAD, index generation, limit) — a new commit or a note edit
    # invalidates it, so SSE refetches don't re-shell out to git.
    _commits_cache: dict[str, tuple[tuple[str, int, int], dict]] = {}
    # Contribution-grid cache (TASK-0258): keyed on HEAD only — a note
    # edit cannot change a past commit, so the index generation has no
    # business in this key.
    _activity_cache: dict[str, tuple[str, dict]] = {}
    # Review desk queue (FEAT-0041). Durable across sidecar restarts —
    # a proposal can wait days — and deliberately separate from note
    # state: pending-ness is runtime, verdicts live in the notes.
    review_store = ReviewStore(project_root)
    approval_store = ApprovalStore(project_root)
    # Lazy-instantiated; ttyd doesn't actually spawn until the first
    # /api/terminal request (the JS client only fetches when the user
    # opens the bottom panel). cockpit_url is propagated into the
    # shell's env as COCKPIT_URL for the `cockpit` CLI (TASK-0049).
    terminal = TerminalProcess(
        working_dir=project_root, cockpit_url=cockpit_url,
    )

    class Handler(BaseHTTPRequestHandler):
        server_version = "project-os-cockpit/0.1"
        # HTTP/1.1 lets the SSE channel stay open with chunked semantics; for
        # other endpoints we still send Content-Length so keep-alive works.
        protocol_version = "HTTP/1.1"

        # ---- routing ----

        def do_GET(self) -> None:  # noqa: N802 — http.server API
            try:
                self._route()
            except BrokenPipeError:
                # Client disconnected mid-response; nothing to do.
                pass

        def do_POST(self) -> None:  # noqa: N802 — http.server API
            try:
                self._route_post()
            except BrokenPipeError:
                pass

        def _route_post(self) -> None:
            parsed = urllib.parse.urlsplit(self.path)
            path = urllib.parse.unquote(parsed.path)
            if path == "/api/cockpit/focus":
                self._serve_cockpit_focus()
                return
            if path == "/api/cockpit/tab-state":
                self._serve_cockpit_tab_state()
                return
            if path == "/api/design/verdict":
                self._serve_design_verdict()
                return

            if path == "/api/inbox/store":
                self._serve_inbox_store()
                return

            if path == "/api/inbox/discard":
                self._serve_inbox_discard()
                return

            if path == "/api/design/offer-review":
                self._serve_design_offer_review()
                return

            if path == "/api/design/comment":
                self._serve_design_comment()
                return

            if path == "/api/design/capture":
                self._serve_design_capture()
                return

            if path == "/api/notes/check-toggle":
                self._serve_check_toggle()
                return
            if path == "/api/cockpit/agent-state":
                self._serve_cockpit_agent_state()
                return
            if path == "/api/agent-hook":
                self._serve_agent_hook(parsed.query)
                return
            if path == "/api/cockpit/dispatch":
                self._serve_cockpit_dispatch()
                return
            if path == "/api/cockpit/review-request":
                self._serve_review_request()
                return
            if path == "/api/cockpit/review-resolve":
                self._serve_review_resolve()
                return
            if path == "/api/notes/review":
                self._serve_note_review()
                return
            if path == "/api/notes/decide":
                self._serve_note_decide()
                return
            if path == "/api/cockpit/caught-up":
                self._serve_caught_up()
                return
            if path == "/api/notes/transition":
                self._serve_note_transition()
                return
            if path == "/api/notes/tick":
                self._serve_note_tick()
                return
            if path == "/api/notes/create":
                self._serve_note_create()
                return
            if path == "/api/cockpit/approve":
                self._serve_approve()
                return

            if path == "/api/notes/choose-variant":
                self._serve_choose_variant()
                return

            if path == "/api/notes/attach":
                self._serve_note_attach()
                return

            if path == "/api/notes/acceptance-run":
                self._serve_acceptance_run()
                return

            if path == "/api/notes/test-run":
                self._serve_test_run()
                return

            if path == "/api/notes/tick-owed":
                self._serve_tick_owed()
                return

            if path == "/api/notes/seal-ledger":
                self._serve_seal_ledger()
                return
            if path == "/api/notes/mark-check":
                self._serve_mark_check()
                return

            if path == "/api/notes/retire-check":
                self._serve_retire_check()
                return

                return

            if path == "/api/notes/release-mark-released":
                self._serve_mark_released()
                return

            if path == "/api/notes/release-contents":
                self._serve_release_contents()
                return

            if path == "/api/notes/release-verified":
                self._serve_release_verified()
                return

            if path == "/api/notes/release-prepare":
                self._serve_release_prepare()
                return
            # Unknown POST. Drain the request body before responding so
            # HTTP/1.1 keep-alive framing stays intact: an undrained body
            # bleeds into the next request line on the same TCP socket,
            # which the server then parses as a bogus method (the
            # symptom: ``501 Unsupported method`` for innocent
            # subsequent GETs of CSS/JS/favicon).
            self._drain_request_body()
            self._respond_status(HTTPStatus.NOT_FOUND)

        def _drain_request_body(self) -> None:
            """Read and discard ``Content-Length`` bytes from the socket."""
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return
            if length <= 0:
                return
            try:
                self.rfile.read(length)
            except (OSError, ValueError):
                pass

        def _route(self) -> None:
            parsed = urllib.parse.urlsplit(self.path)
            path = urllib.parse.unquote(parsed.path)

            if path == "/favicon.ico":
                self._respond_status(HTTPStatus.NO_CONTENT)
                return

            if path == "/healthz":
                self._serve_healthz()
                return

            if path == "/":
                self._serve_landing()
                return

            if path == "/_events":
                self._serve_sse()
                return

            if path == "/api/cockpit/nav":
                self._serve_cockpit_nav(parsed.query)
                return

            if path == "/api/cockpit/context":
                self._serve_cockpit_context(parsed.query)
                return

            if path == "/api/cockpit/state":
                self._serve_cockpit_state()
                return

            if path == "/api/cockpit/validation":
                self._serve_cockpit_validation()
                return


            if path == "/api/cockpit/identity":
                self._serve_cockpit_identity()
                return

            if path == "/api/cockpit/runtime":
                self._serve_cockpit_runtime()
                return

            if path == "/api/cockpit/obligations":
                self._respond_json(_obligations.badges_payload(index))
                return

            # What one view owes, with the rows (FEAT-0092 / TASK-0387). The
            # badge's own numbers, plus what they count — the pairing the
            # badge could not make on its own.
            if path == "/api/cockpit/landing":
                params = urllib.parse.parse_qs(parsed.query)
                view = (params.get("view") or [""])[0]
                self._respond_json(cockpit.landing_payload(index, view))
                return

            # Done-but-unshipped (FEAT-0072 / TASK-0315). Its own endpoint
            # rather than a field on the overview: the record column fetches
            # its cards independently, and a card that arrived only with the
            # overview could not refresh when a release shipped.
            if path == "/api/cockpit/unreleased":
                self._respond_json(cockpit.unreleased_payload(index))
                return

            if path == "/api/cockpit/digest":
                self._respond_json(cockpit.digest_payload(
                    project_root, index, marker.seen_at,
                ))
                return

            if path == "/api/cockpit/watermark":
                self._respond_json(marker.payload())
                return

            # Where a note id lives in THIS repo (FEAT-0093 / TASK-0392).
            # A cross-repo jump switches workspace first and then asks the
            # arriving sidecar; the shell holds the fleet map and each sidecar
            # holds its own corpus, and neither can answer the other's half.
            if path == "/api/cockpit/locate":
                params = urllib.parse.parse_qs(parsed.query)
                wanted = (params.get("id") or [""])[0].strip()
                found = index.by_id(wanted) if wanted else None
                record = index.get(found) if found else None
                self._respond_json({
                    "id": wanted,
                    "project": cockpit.project_id(docs_root),
                    "found": bool(record),
                    "rel": record.rel_path if record else "",
                    "title": (record.title if record else "") or "",
                })
                return

            if path == "/api/notes/actions":
                params = urllib.parse.parse_qs(parsed.query)
                note_id = (params.get("id") or [""])[0].strip()
                note_path = index.by_id(note_id) if note_id else None
                record = index.get(note_path) if note_path else None
                # A decision's options travel with its actions (FEAT-0097).
                # The surface never parses markdown: a renderer reading the
                # note itself would be a second parser to keep in step.
                opts: dict[str, Any] = {"options": [], "proposed": None}
                if record is not None and (record.note_type or "").lower() in (
                    "adr", "decision",
                ):
                    try:
                        opts = decisions.payload(
                            note_path.read_text(encoding="utf-8"),
                        )
                    except OSError:
                        pass
                self._respond_json({
                    "id": note_id,
                    "type": (record.note_type if record else "") or "",
                    "status": (record.status if record else "") or "",
                    "actions": note_writes.legal_actions(
                        record.note_type if record else None,
                        record.status if record else None,
                    ),
                    **opts,
                })
                return

            # The acceptance runner's input (TASK-0287). A GET: it reads the
            # criteria and their state and writes nothing — a run's writes go
            # through the guarded `note_writes` verbs, not through here.
            if path == "/api/notes/acceptance":
                params = urllib.parse.parse_qs(parsed.query)
                feature_id = (params.get("id") or [""])[0].strip()
                self._respond_json(criteria.payload(index, feature_id))
                return

            # Acceptance debt (FEAT-0065 / TASK-0294) — three numbers derived
            # from the same criteria parse the runner and REQ-BOXES share.
            # The shape of a change, keyed to a note (ISS-0096). Counts, not
            # contents — the cockpit is not an editor.
            if path == "/api/notes/shape":
                params = urllib.parse.parse_qs(parsed.query)
                self._respond_json(cockpit.change_shape_payload(
                    project_root, (params.get("id") or [""])[0].strip(),
                ))
                return

            # Permission prompts as durable state (ISS-0094) — so they can be
            # answered from here and counted by the same clock as the queue.
            if path == "/api/cockpit/approvals":
                open_prompts = approval_store.open_prompts()
                self._respond_json({
                    "approvals": open_prompts,
                    # The escalation state per prompt, so the surface shows the
                    # clock rather than only the amber.
                    "escalation": escalation.sweep(open_prompts)["counts"],
                })
                return

            if path == "/api/cockpit/acceptance-debt":
                self._respond_json(criteria.debt_payload(index))
                return

            if path == "/api/cockpit/transitions":
                self._respond_json({
                    "transitions": status_diff.transitions() if status_diff else [],
                })
                return

            if path == "/api/cockpit/stats":
                self._serve_cockpit_stats(parsed.query)
                return

            if path == "/api/cockpit/review-queue":
                self._respond_json(
                    cockpit.review_queue_payload(index, review_store)
                )
                return

            if path == "/api/cockpit/reviewed":
                # The reviewed register, re-homed to the record column
                # (TASK-0377). Its own endpoint rather than a slice of
                # `review-queue`: FEAT-0090 retires that surface, and a record
                # card sourced from a queue payload is exactly the harvest
                # ISS-0065 was — a card whose contents depend on a page that
                # is about to stop existing.
                self._respond_json({
                    "schema_version": cockpit.SCHEMA_VERSION,
                    "reviewed": cockpit._reviewed_register(index),
                })
                return

            if path == "/api/cockpit/release":
                params = urllib.parse.parse_qs(parsed.query)
                from . import publication as _pub
                self._respond_json({
                    "schema_version": cockpit.SCHEMA_VERSION,
                    **_pub.release_payload(
                        docs_root.parent, index,
                        (params.get("id") or ["next"])[0],
                    ),
                })
                return

            if path == "/api/cockpit/acceptance":
                # The suite and the release gate (TASK-0373), plus the walkable
                # view (TASK-0464). The index is passed now because a migrated
                # suite IS notes — the comment that used to sit here said the
                # suite was "a checklist, not a note the graph resolves", which
                # was true of the file shape and is the exact thing ADR-0030
                # changed.
                #
                # **`?platform=` names whose verdicts these are** ([[ADR-0037]]).
                # The nav filter's value, and `all` is not a platform: it means
                # the UNION, where every platform must clear a check for it to
                # read as cleared. That is how a release which has not said
                # what it ships fails closed rather than inheriting the
                # loosest platform's answer.
                _platform = (urllib.parse.parse_qs(parsed.query)
                             .get("platform", [""])[0]).strip().lower()
                if _platform == "all":
                    _platform = ""
                from . import ledger as _led
                self._respond_json({
                    "schema_version": cockpit.SCHEMA_VERSION,
                    **acceptance.payload(docs_root, index, platform=_platform),
                    "gate": acceptance.gate_payload(docs_root, index=index,
                                                    platform=_platform),
                    "view": acceptance.view_payload(docs_root, index,
                                                    platform=_platform),
                    #: **Which platforms this repo keeps a ledger for**
                    #: ([[ISS-0272]]). The renderer sends no platform when the
                    #: nav picker reads `All`, and once a ledger exists the
                    #: scalar write path is refused -- so a walker was met with
                    #: a 409 telling them to "use the ledger write path", which
                    #: is advice for whoever is calling the API rather than for
                    #: someone ticking a checklist. With this the client can
                    #: supply the platform itself when there is only one, and
                    #: the storage decision stops being the walker's problem.
                    "ledger_platforms": _led.platforms(docs_root),
                })
                return

            if path == "/api/cockpit/release-item":
                # `~release/<id>/<ITEM-ID>` — what this item is, in this
                # release (TASK-0472). Read-only.
                params = urllib.parse.parse_qs(parsed.query)
                from . import publication as _pub2
                self._respond_json({
                    "schema_version": cockpit.SCHEMA_VERSION,
                    **_pub2.release_item_payload(
                        index,
                        (params.get("release") or ["next"])[0],
                        (params.get("item") or [""])[0],
                    ),
                })
                return

            if path == "/api/cockpit/scope-tests":
                params = urllib.parse.parse_qs(parsed.query)
                self._respond_json(cockpit.scope_tests_payload(
                    index, (params.get("id") or [""])[0],
                ))
                return

            if path.startswith("/api/cockpit/review/"):
                self._serve_review_detail(path[len("/api/cockpit/review/"):])
                return

            if path == "/api/cockpit/commits":
                self._serve_cockpit_commits(parsed.query)
                return

            if path == "/api/cockpit/history":
                self._serve_cockpit_history(parsed.query)
                return

            if path == "/api/cockpit/activity":
                self._serve_cockpit_activity()
                return

            if path == "/api/cockpit/changes":
                params = urllib.parse.parse_qs(parsed.query)
                self._respond_json(cockpit.changes_payload(
                    index, (params.get("platform") or [None])[0],
                ))
                return

            if path == "/api/cockpit/decisions":
                params = urllib.parse.parse_qs(parsed.query)
                self._respond_json(cockpit.decisions_payload(
                    index, (params.get("platform") or [None])[0],
                ))
                return

            if path == "/api/cockpit/sessions":
                self._serve_cockpit_sessions()
                return

            if path == "/api/cockpit/session-cache":
                self._serve_cockpit_session_cache()
                return

            if path == "/api/cockpit/actions":
                self._serve_cockpit_actions()
                return

            if path == "/api/cockpit/agents":
                self._serve_cockpit_agents()
                return

            if path == "/api/cockpit/brief":
                self._respond_json(cockpit.brief_payload(docs_root.parent))
                return

            if path == "/api/cockpit/designs":
                self._serve_cockpit_designs()
                return

            if path.startswith("/api/cockpit/design-comments/"):
                self._respond_json(cockpit.design_comments_payload(
                    docs_root, index,
                    urllib.parse.unquote(path[len("/api/cockpit/design-comments/"):])))
                return

            if path.startswith("/api/cockpit/design-revisions/"):
                self._serve_design_revisions(
                    path[len("/api/cockpit/design-revisions/"):])
                return

            if path.startswith("/design-asset-at/"):
                self._serve_design_asset_at(path[len("/design-asset-at/"):])
                return

            if path.startswith("/design-asset/"):
                self._serve_design_asset(path[len("/design-asset/"):])
                return

            if path == "/api/cockpit/dispatch-requests":
                self._serve_dispatch_requests()
                return

            if path == "/api/render":
                self._serve_render(parsed.query)
                return

            if path == "/api/terminal":
                self._serve_terminal_info()
                return

            if path == TERMINAL_BASE_PATH.rstrip("/") or path.startswith(TERMINAL_BASE_PATH):
                self._proxy_terminal(path)
                return

            if path.startswith("/_static/"):
                self._serve_static(path[len("/_static/"):])
                return

            # The desktop shell's stylesheet, for design artifacts that want
            # to show real widgets (TASK-0227). Served from where the build
            # already puts it — never copied into the package, because a
            # second copy of a stylesheet is the ISS-0023 failure again.
            if path.startswith("/_shell/"):
                self._serve_shell_asset(path[len("/_shell/"):])
                return

            # A project's OWN stylesheets, for its design artifacts
            # (TASK-0230). The allow-list is whatever the design notes
            # declare — see `_serve_project_stylesheet`.
            #: **The inbox is loopback-only to READ, not just to write**
            #: (independent review, 2026-09-02). The store endpoint had
            #: `_require_loopback` from the start and these two never did, so
            #: with `--bind 0.0.0.0` anyone on the Wi-Fi could list the inbox
            #: and download any item in it.
            #:
            #: The bargain that bind makes is scoped to NOTES — a tablet on the
            #: same network reading the documentation. The inbox is not notes.
            #: It is unreviewed external material somebody dropped ten seconds
            #: ago, gitignored precisely because nobody has decided about it
            #: yet, and now holding any file type up to 250 MB.
            #:
            #: Nothing is lost: the tray lives in the Electron renderer, which
            #: reaches the sidecar over 127.0.0.1, and no web template renders
            #: an inbox surface.
            if path == "/api/inbox":
                if not self._require_loopback("inbox reads"):
                    return
                self._respond_json({
                    "schema_version": cockpit.SCHEMA_VERSION,
                    "items": inbox_mod.list_items(project_root),
                })
                return

            if path.startswith("/_inbox/"):
                if not self._require_loopback("inbox reads"):
                    return
                self._serve_inbox_item(
                    urllib.parse.unquote(path[len("/_inbox/"):]))
                return

            if path.startswith("/_project/"):
                self._serve_project_stylesheet(
                    urllib.parse.unquote(path[len("/_project/"):]))
                return

            if path == "/index" or path == "/index/":
                self._redirect("/")
                return

            if path.startswith("/index/"):
                self._serve_index(path[len("/index/"):].rstrip("/"))
                return

            if path == "/docs" or path == "/docs/":
                self._serve_docs_path("")
                return

            if path.startswith("/docs/"):
                self._serve_docs_path(path[len("/docs/"):])
                return

            support_rel = _project_support_rel(path)
            if support_rel is not None:
                self._serve_project_support_path(support_rel)
                return

            self._respond_not_found(path)

        # ---- landing + indexes ----

        def _serve_landing(self) -> None:
            counts = index.type_counts()
            snapshot = _read_snapshot(docs_root)
            readme_html = _render_readme_if_present(docs_root, index)
            phase_counts = _feature_count_by_phase(index)
            html = templates.home_page_html(
                snapshot=snapshot,
                type_counts=counts,
                plural_for={v: k for k, v in INDEX_TYPE_PLURALS.items()},
                docs_root_name=docs_root.name or "docs",
                feature_count_by_phase=phase_counts,
                readme_html=readme_html,
                resolver=index.resolve,
            )
            self._respond_html(HTTPStatus.OK, html)

        def _serve_index(self, plural: str) -> None:
            if not plural:
                self._redirect("/")
                return
            type_singular = INDEX_TYPE_PLURALS.get(plural.lower())
            if type_singular is None:
                self._respond_not_found(self.path)
                return
            notes = index.notes_by_type(type_singular)
            html = templates.index_page_html(
                type_label=plural.lower(),
                type_singular=type_singular,
                notes=notes,
                docs_root_name=docs_root.name or "docs",
            )
            self._respond_html(HTTPStatus.OK, html)

        # ---- Cockpit JSON API ----

        def _serve_cockpit_nav(self, query_string: str) -> None:
            params = urllib.parse.parse_qs(query_string)
            mode = (params.get("mode") or [None])[0]
            platform = (params.get("platform") or [None])[0]
            pinned_raw = (params.get("pinned") or [None])[0] or ""
            pinned = [p for p in pinned_raw.split(",") if p] if pinned_raw else []
            payload = cockpit.nav_payload(
                index,
                mode=mode,
                platform=platform,
                pinned=pinned,
                project_root=project_root,
            )
            self._respond_json(payload)

        def _serve_cockpit_stats(self, query_string: str = "") -> None:
            """``GET /api/cockpit/stats[?scope=PHASE-####]`` — dashboard
            payload, optionally scoped to one phase (FEAT-0023).

            Payloads are cached per scope and validated against
            ``index.generation``, so file-event refetches stop
            re-walking the corpus (TASK-0128).
            """
            params = urllib.parse.parse_qs(query_string)
            scope = (params.get("scope") or [None])[0]
            scope = scope.strip().upper() if scope else None
            cache_key = scope or ""
            generation = index.generation
            cached = _stats_cache.get(cache_key)
            if cached is not None and cached[0] == generation:
                self._respond_json(cached[1])
                return
            payload = cockpit.stats_payload(index, scope=scope)
            if payload is None:
                self._respond_json(
                    {"ok": False, "error": f"unknown scope: {scope}"},
                    status=HTTPStatus.NOT_FOUND,
                )
                return
            _stats_cache[cache_key] = (generation, payload)
            self._respond_json(payload)

        def _serve_cockpit_commits(self, query_string: str = "") -> None:
            """``GET /api/cockpit/commits[?limit=N]`` — recent commits with
            the doc items each one touched (TASK-0199).

            ``limit`` is the only caller-supplied value and is clamped to an
            int inside :func:`cockpit.commits_payload`; the git subprocess
            itself runs with a fixed argv. Cached on (HEAD, index
            generation, limit) so SSE-driven refetches don't re-shell.
            """
            params = urllib.parse.parse_qs(query_string)
            raw_limit = (params.get("limit") or [""])[0]
            try:
                limit = int(raw_limit)
            except (TypeError, ValueError):
                limit = cockpit.COMMITS_DEFAULT_LIMIT
            head = _git_head(project_root)
            cache_key = (head, index.generation, limit)
            cached = _commits_cache.get("k")
            if cached is not None and cached[0] == cache_key:
                self._respond_json(cached[1])
                return
            payload = cockpit.commits_payload(project_root, index, limit=limit)
            _commits_cache["k"] = (cache_key, payload)
            self._respond_json(payload)

        def _serve_cockpit_history(self, query_string: str = "") -> None:
            """``GET /api/cockpit/history[?limit=N][&fresh=1]`` — documentation
            history: status transitions grouped by commit, plus the
            uncommitted band (FEAT-0052 / TASK-0255).

            Deliberately **not** cached on HEAD alone the way
            ``/api/cockpit/commits`` is: the uncommitted band changes
            with every save, and a cache keyed on the commit would serve
            a stale "not saved yet" list — the one part of this payload
            whose whole value is being current. The git calls are
            measured at ~0.08 s for 40 commits, so there is nothing here
            a cache would rescue.

            ``fresh=1`` declines the *publication* cache specifically
            (ISS-0168). ``git_state.read()`` holds a reading for
            ``CACHE_SECONDS`` because the registry is walked on every nav
            change, and that is right — but **the push runs in the Electron
            main process**, so the server cannot know its answer just became
            false. Without this the surface that offered the push re-fetched
            and got the pre-push numbers back for up to ten seconds: correct
            on a slow click, wrong on a fast one.

            A GET declining a cache is an ordinary GET. Nothing is written and
            no write path widens — ``read_fresh`` re-stamps the same in-process
            cache, which is also why the badge refresh that follows a push is
            correct without a second probe.
            """
            params = urllib.parse.parse_qs(query_string)
            raw_limit = (params.get("limit") or [""])[0]
            try:
                limit = int(raw_limit)
            except (TypeError, ValueError):
                limit = cockpit.COMMITS_DEFAULT_LIMIT
            raw_until = (params.get("until") or [""])[0]
            until = raw_until if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_until) else None
            fresh = (params.get("fresh") or [""])[0] == "1"
            self._respond_json(
                cockpit.history_payload(
                    project_root, index, limit=limit, until=until, fresh=fresh)
            )

        def _serve_cockpit_activity(self) -> None:
            """``GET /api/cockpit/activity`` — per-day counts for the
            contribution grid (FEAT-0053 / TASK-0258).

            Cached on HEAD alone, which is the whole reason this is a
            separate endpoint from ``/api/cockpit/history``: that one
            must never be cached because its uncommitted band is the
            part whose value is being current, and this one is a
            whole-history pass (~0.7 s) whose answer changes only when a
            commit lands. The index generation is deliberately **not** in
            the key — editing a note changes no past commit.
            """
            head = _git_head(project_root)
            cached = _activity_cache.get("k")
            if cached is not None and cached[0] == head:
                self._respond_json(cached[1])
                return
            payload = cockpit.activity_payload(project_root, index)
            _activity_cache["k"] = (head, payload)
            self._respond_json(payload)

        def _serve_cockpit_context(self, query_string: str) -> None:
            params = urllib.parse.parse_qs(query_string)
            this_values = params.get("this", [])
            this_value = this_values[0] if this_values else None
            platform = (params.get("platform") or [None])[0]
            payload = cockpit.context_payload(
                index, this_value, platform=platform
            )
            if payload.get("active") is None and this_value:
                active = _project_support_active(project_root, this_value)
                if active is not None:
                    payload["active"] = active
            self._respond_json(payload)

        def _serve_terminal_info(self) -> None:
            """Return ttyd availability + URL for the embedded terminal.

            Lazy-spawns ttyd on first call (the JS client only fetches
            this when the user opens the bottom panel for the first
            time). Subsequent calls reuse the running process.

            In desktop mode (``COCKPIT_DESKTOP=1``) the Electron shell
            mounts a native node-pty pane instead, so this endpoint
            returns ``enabled: false`` with a clear reason — the JS
            client then leaves the bottom-panel slot empty for the
            shell to fill.
            """
            self._respond_json(terminal.info())

        def _serve_cockpit_agent_state(self) -> None:
            """``POST /api/cockpit/agent-state`` — agent declares its
            state (FEAT-0013 / TASK-0077).

            Body: ``{state, target?, agent?, message?}``. ``state`` must
            be one of ``busy``, ``waiting``, ``done``, ``error``,
            ``idle``. On success, records the transition on
            ``CockpitState`` and publishes a ``cockpit:agent-state``
            SSE event so connected clients (FEAT-0010 rail dots,
            future browser-side surfaces, OS notifications) update
            without polling.

            Auto-decay is handled by the background timer thread in
            ``DocsServer.run`` — when a busy/waiting state ages past
            ``COCKPIT_AGENT_STATE_DECAY_SECONDS`` (default 600), the
            thread emits a synthetic event flipping the observable
            state to ``idle``.
            """
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError):
                self._respond_json({"ok": False, "error": "invalid JSON"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            state_value = (body.get("state") or "").strip().lower()
            if not state_value:
                self._respond_json({"ok": False, "error": "missing 'state'"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            if state_value not in _AGENT_STATES:
                self._respond_json(
                    {
                        "ok": False,
                        "error": (
                            f"unknown state: {state_value!r} "
                            f"(allowed: {sorted(_AGENT_STATES)})"
                        ),
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            # Precedence (FEAT-0019 / TASK-0114): while an instrumented
            # session is live, hook-fed state is authoritative — a
            # voluntary `cockpit signal` would fight the push feed
            # (e.g. a remembered `signal done` racing the hooks' `Stop`).
            # Acknowledge without recording; manual signalling regains
            # authority the moment no live hook session exists.
            if tracker.has_live_session():
                self._respond_json({"ok": True, "superseded_by_hooks": True})
                return
            target = body.get("target")
            agent = body.get("agent")
            message = body.get("message")
            # Stringify optional fields if present so we don't bus
            # arbitrary types through the SSE payload.
            payload = state.record_agent_state(
                state_value,
                target=str(target) if target else None,
                agent=str(agent) if agent else None,
                message=str(message) if message else None,
            )
            bus.publish(ControlEvent("cockpit:agent-state", payload))
            self._respond_json({"ok": True})

        def _serve_cockpit_runtime(self) -> None:
            """``GET /api/cockpit/runtime`` — is what you are looking at built
            from the code that is on disk? (ISS-0140)

            **Two long-running processes, the same trap, twice in two days.**
            A sidecar is an editable install, so it needs no rebuild — but a
            running process never re-imports, and the SSE soft-reload
            refreshes documents, never modules. The renderer has the same
            shape for a different reason: `dist/renderer/*.js` is read once at
            window creation and nothing reloads it when a build rewrites the
            files underneath.

            Both cost the same thing when they go unnoticed, and it is not
            the stale code — it is hours spent investigating a defect that
            does not exist. On 2026-08-10 a stale sidecar produced two bug
            reports that were not bugs. On 2026-08-11 a shell running for
            **1 day 23 hours** produced a third, caught only because somebody
            checked the process table before writing it up.

            So the answer is computed rather than remembered: the newest
            mtime under the package (and under the shell's asset directory,
            when the shell passed one) against the moment this process
            started. A client compares the asset stamp to its own window
            start; the sidecar's own answer needs no client help.

            **Reporting, never reloading.** Reloading a window under someone
            mid-session is worse than telling them, and this is an obligation
            the reader discharges, not an action the tool takes.
            """
            def _newest(root: Path | None, suffixes: tuple[str, ...]) -> float:
                if not root or not root.exists():
                    return 0.0
                newest = 0.0
                for child in root.rglob("*"):
                    if child.suffix not in suffixes or not child.is_file():
                        continue
                    try:
                        newest = max(newest, child.stat().st_mtime)
                    except OSError:
                        continue
                return newest

            pkg = Path(__file__).resolve().parent
            source_newest = _newest(pkg, (".py",))
            assets_newest = _newest(shell_assets, (".js", ".css", ".html"))
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                "started_at": _PROCESS_STARTED_AT,
                "source_newest": source_newest,
                # The comparison, made here rather than left to each caller:
                # one definition of "behind" is the point of the endpoint.
                "sidecar_stale": source_newest > _PROCESS_STARTED_AT,
                "assets_newest": assets_newest,
                "assets_dir": str(shell_assets) if shell_assets else "",
            })

        def _serve_cockpit_identity(self) -> None:
            """``GET /api/cockpit/identity`` — who is this sidecar?

            Lets url-file consumers (desktop stale-url janitor, CLI)
            verify they reached the cockpit for the repo they think
            they did (ISS-0007 / TASK-0146).
            """
            self._respond_json({
                "root": str(docs_root.parent.resolve()),
                "docs_root": str(docs_root.resolve()),
                "pid": os.getpid(),
            })

        def _serve_agent_hook(self, query_string: str = "") -> None:
            """``POST /api/agent-hook`` — hook-fed agent lifecycle
            ingestion (FEAT-0019 / TASK-0114).

            Claude Code command-hooks (and the Codex notify/statusline
            forwarders) POST their JSON payloads here. The tracker maps
            them onto the agent-state machine and the activity feed;
            unknown events are accepted-and-ignored so CLI schema drift
            never breaks ingestion (RISK-0004). Payloads are untrusted
            local input: shape-validated, size-capped, clipped at
            storage, never rendered as HTML.

            Query params ``event`` and ``agent`` provide defaults for
            ``hook_event_name`` / ``agent`` so shell forwarders can
            pass a raw upstream blob without rewriting JSON (the
            statusline and Codex notify scripts use this).
            """
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length <= 0:
                self._respond_json(
                    {"ok": False, "error": "missing body"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if length > _AGENT_HOOK_MAX_BYTES:
                # Too big to drain politely — reject and drop the
                # connection so we don't read megabytes we won't use.
                self.close_connection = True
                self._respond_json(
                    {"ok": False, "error": "payload too large"},
                    status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                )
                return
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._respond_json(
                    {"ok": False, "error": "invalid JSON"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if not isinstance(body, dict):
                self._respond_json(
                    {"ok": False, "error": "body must be a JSON object"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            params = urllib.parse.parse_qs(query_string)
            for key, field in (("event", "hook_event_name"), ("agent", "agent")):
                default = (params.get(key) or [None])[0]
                if default and not body.get(field):
                    body[field] = default
            # Identity guard (ISS-0007 / TASK-0146): reject events from
            # sessions working in a different repo — a stale
            # `.cockpit/url` after port reuse would otherwise poison
            # this workspace's tracker, session index, and rail dot.
            # 409 makes the external hook's POST fail, and its existing
            # fallback writes agent-state into the *correct* repo.
            # Payloads without `cwd` stay accepted (statusline/forwarder
            # blobs don't always carry one).
            cwd = body.get("cwd")
            if isinstance(cwd, str) and cwd and not _cwd_within_root(
                cwd, docs_root.parent
            ):
                self._respond_json(
                    {
                        "ok": False,
                        "error": "wrong-cockpit",
                        "root": str(docs_root.parent),
                    },
                    status=HTTPStatus.CONFLICT,
                )
                return
            outcome = tracker.ingest(body)
            if not outcome.get("ok"):
                self._respond_json(
                    {"ok": False, "error": outcome.get("error", "rejected")},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            state_value = outcome.get("state")
            if state_value:
                agent_name = body.get("agent")
                payload = state.record_agent_state(
                    state_value,
                    agent=str(agent_name) if agent_name else "claude",
                    message=outcome.get("message"),
                    source="hook",
                )
                bus.publish(ControlEvent("cockpit:agent-state", payload))
            activity = outcome.get("activity")
            if activity:
                bus.publish(ControlEvent("cockpit:agent-activity", activity))
            resp: dict[str, Any] = {
                "ok": True, "ignored": bool(outcome.get("ignored")),
            }
            if outcome.get("duplicate"):
                resp["duplicate"] = True
            self._respond_json(resp)

        def _serve_cockpit_dispatch(self) -> None:
            """``POST /api/cockpit/dispatch`` — dispatch ledger entry
            (FEAT-0025 / TASK-0135). Body: ``{id, verb?, agent?,
            enqueue?}``. With ``enqueue`` the record is also stored as
            a queue-request for the desktop shell (the `cockpit
            dispatch` CLI path, TASK-0136) and announced over SSE."""
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError):
                self._respond_json({"ok": False, "error": "invalid JSON"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            note_id = body.get("id")
            if not isinstance(note_id, str) or not note_id.strip():
                self._respond_json({"ok": False, "error": "missing 'id'"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            verb = body.get("verb")
            agent = body.get("agent")
            enqueue = bool(body.get("enqueue"))
            rec = tracker.record_dispatch(
                note_id.strip().upper(),
                verb=str(verb) if verb else None,
                agent=str(agent) if agent else None,
                enqueue=enqueue,
            )
            if enqueue:
                bus.publish(ControlEvent("cockpit:dispatch-request", rec))
            self._respond_json({"ok": True, "recorded": rec})

        # ---- review desk (FEAT-0041) ----

        def _is_loopback(self) -> bool:
            """Mutation endpoints are Mac-local only.

            The render server binds 0.0.0.0 so a tablet on the Wi-Fi can
            *read* the notes; writing them is not part of that bargain.
            Same split the terminal endpoint draws (RISK-0001).
            """
            host = (self.client_address[0] if self.client_address else "") or ""
            return host in _LOOPBACK_HOSTS

        def _read_json_body(self, max_bytes: int | None = None) -> dict[str, Any] | None:
            """The request body as JSON, or ``None`` (already responded).

            ``max_bytes`` overrides the default 2 MB cap. The inbox needs it:
            a Retina screenshot is routinely over 2 MB and base64 inflates it by
            a third, so the shared cap would have refused ordinary items while
            `inbox.MAX_ITEM_BYTES` advertised a larger number it could never
            reach, which is worse than a small limit honestly stated.
            (That number was 25 MB when this was written and is 250 MB
            now; the figure lived in two places and only one moved.)
            """
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length > (max_bytes or _AGENT_HOOK_MAX_BYTES):
                self._respond_json({"ok": False, "error": "body too large"},
                                   status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return None
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError):
                self._respond_json({"ok": False, "error": "invalid JSON"},
                                   status=HTTPStatus.BAD_REQUEST)
                return None
            return body if isinstance(body, dict) else {}

        def _require_loopback(self, what: str = "mutations") -> bool:
            """Refuse anything that is not from this machine.

            ``what`` names the refused thing in the message. It defaults to
            ``mutations`` because that was the only caller until 2026-09-02,
            when the inbox READ paths joined — see `_serve_inbox_item`.
            """
            if self._is_loopback():
                return True
            self._respond_json(
                {"ok": False, "error": "%s are loopback-only" % what},
                status=HTTPStatus.FORBIDDEN,
            )
            return False

        def _serve_review_detail(self, request_id: str) -> None:
            """``GET /api/cockpit/review/<request-id|NOTE-ID>`` — one
            queue entry expanded: the proposal set with its items, or the
            note behind a decide/run row."""
            request_id = request_id.strip().strip("/")
            request = review_store.get(request_id)
            if request is not None:
                items = []
                for note_id in request.get("items") or []:
                    path = index.by_id(note_id)
                    record = index.get(path) if path else None
                    items.append(
                        cockpit._slim_note(record) if record else {"id": note_id}
                    )
                payload = {
                    "schema_version": cockpit.SCHEMA_VERSION,
                    "kind": request.get("kind"),
                    "request": request,
                    "items": items,
                }
                # Has the design moved since the reviewer was asked? Computed
                # on open rather than in the queue payload: it costs a git call
                # and only matters once you are looking at the thing (TASK-0229).
                subject = str(request.get("subject") or "").strip().upper()
                asked_at = str(request.get("at_revision") or "")
                if subject and index.by_id(subject) is None:
                    # The subject was deleted or renamed after being offered.
                    # The renderer reads this to offer the one action that can
                    # honestly be taken — clearing the request — instead of
                    # three buttons that all 404 (ISS-0056).
                    request = dict(request)
                    request["subject_missing"] = True
                    payload["request"] = request
                if subject:
                    # OUTSIDE the revision branch. Computing it only when a
                    # revision was captured meant a row with a subject and no
                    # `at_revision` — the shape every pre-fix offer wrote —
                    # still dispatched to the plan-verdict path, leaving
                    # ISS-0056 unfixed for exactly the rows finding 5 was
                    # about (round 2).
                    subject_path = index.by_id(subject)
                    subject_rec = index.get(subject_path) if subject_path else None
                    payload["subject_type"] = (
                        (subject_rec.note_type or "").lower() if subject_rec else "")
                if subject and asked_at:
                    revs = cockpit.design_revisions_payload(
                        docs_root.parent, index, subject)
                    head = ""
                    for rev in revs.get("revisions") or []:
                        head = str(rev.get("sha") or "")
                        break
                    payload["at_revision"] = asked_at
                    payload["head_revision"] = head
                    payload["revision_moved"] = bool(head and head != asked_at)
                    payload["dirty"] = bool(revs.get("dirty"))
                    # ISS-0057: the three signals above describe the ARTIFACT.
                    # A design's note carries half its substance — Problem,
                    # Approach, Regions, Tokens — and could be rewritten under a
                    # reviewer with all of them still reading current. Additive
                    # by design: `design_revision` keeps its meaning, so no
                    # existing verdict changes meaning.
                    subject_path = index.by_id(subject)
                    subject_rec = index.get(subject_path) if subject_path else None
                    if subject_rec is not None:
                        asked_digest = str(request.get("at_note_digest") or "")
                        now_digest = cockpit.design_note_digest(subject_rec)
                        payload["at_note_digest"] = asked_digest
                        payload["note_digest"] = now_digest
                        payload["note_moved"] = bool(
                            asked_digest and asked_digest != now_digest
                        )
                self._respond_json(payload)
                return
            # Fall back to a note id (a proposed ADR / ready test row).
            path = index.by_id(request_id)
            record = index.get(path) if path else None
            if record is None:
                self._respond_json({"ok": False, "error": "unknown review target"},
                                   status=HTTPStatus.NOT_FOUND)
                return
            payload: dict[str, Any] = {
                "schema_version": cockpit.SCHEMA_VERSION,
                "kind": "note",
                "note": cockpit._slim_note(record),
            }
            if (record.note_type or "").lower() == "test":
                payload["steps"] = cockpit.manual_test_steps(record.body)
                payload["mtime"] = record.path.stat().st_mtime
                fm = record.frontmatter
                payload["last_run"] = str(fm.get("last_run") or "")
                payload["verifies"] = [
                    str(v) for v in (fm.get("features") or fm.get("verifies") or [])
                ]
            self._respond_json(payload)

        def _serve_review_request(self) -> None:
            """``POST /api/cockpit/review-request`` — file a review or
            question request (the agent side of the desk).

            Loopback-only like the other mutations: it writes
            `.cockpit/review-requests.json`, records ledger entries and
            fires SSE, so a LAN reader on the 0.0.0.0 render port must
            not reach it (independent review, 2026-07-26).
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            # Read from the store's own vocabulary rather than a second list
            # here (FEAT-0069 added `annotation` and this literal would have
            # silently refused it — the two-lists failure ISS-0023 is about).
            kind = str(body.get("kind") or "review")
            if kind not in review.KINDS:
                self._respond_json({"ok": False, "error": f"unknown kind: {kind}"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            items = body.get("items")
            record = review_store.add(
                kind,
                items=[str(i) for i in items] if isinstance(items, list) else [],
                title=str(body.get("title") or ""),
                body=str(body.get("body") or ""),
                session_id=body.get("session_id"),
                prompt=body.get("prompt"),
                agent=body.get("agent"),
                subject=body.get("subject"),
                # Anchors are normalised by the store, so a coordinate cannot
                # be persisted whatever a caller sends (FEAT-0069).
                anchor=body.get("anchor"),
            )
            # Provenance: the ledger keeps the prompt→session→request
            # chain the proposal view shows (FEAT-0025 + FEAT-0019).
            for note_id in record.get("items") or []:
                tracker.record_dispatch(note_id, verb=f"review:{kind}")
            bus.publish(ControlEvent("cockpit:review-request", record))
            self._respond_json({"ok": True, "request": record})

        def _serve_review_resolve(self) -> None:
            """``POST /api/cockpit/review-resolve`` — close a queue entry
            with an outcome (recorded for ADR-0007's measurement)."""
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            request_id = str(body.get("request_id") or "")
            outcome = str(body.get("outcome") or "")
            try:
                resolved = review_store.resolve(
                    request_id, outcome, note=str(body.get("note") or ""),
                )
            except ValueError as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            if resolved is None:
                self._respond_json({"ok": False, "error": "unknown request"},
                                   status=HTTPStatus.NOT_FOUND)
                return
            bus.publish(ControlEvent("cockpit:review-request", resolved))
            self._respond_json({"ok": True, "request": resolved})

        def _serve_note_review(self) -> None:
            """``POST /api/notes/review`` — stamp the independent-review
            fields (and optionally a guarded status) on one note."""
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            # Field allow-list: the caller may not name any other key.
            extra = set(body) - note_writes.REVIEW_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False,
                     "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                result = note_writes.stamp_review(
                    index,
                    str(body.get("id") or ""),
                    reviewer=str(body.get("reviewer") or ""),
                    verdict=str(body.get("verdict") or ""),
                    status=(str(body["status"]) if body.get("status") else None),
                    mtime=(float(body["mtime"]) if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_note_decide(self) -> None:
            """``POST /api/notes/decide`` — advance or decline one queued
            note (a proposed ADR, a draft requirement).

            Separate from ``/api/notes/review`` because the two do
            different things: review records a verdict on a set and leaves
            the notes put; this performs the lifecycle move the note is
            queued for, guarded by that type's own vocabulary.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.DECIDE_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                result = note_writes.stamp_decision(
                    index,
                    str(body.get("id") or ""),
                    reviewer=str(body.get("reviewer") or ""),
                    accept=bool(body.get("accept")),
                    mtime=(float(body["mtime"]) if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_caught_up(self) -> None:
            """``POST /api/cockpit/caught-up`` — the only thing that moves the
            watermark (TASK-0312).

            Loopback-guarded even though it writes runtime state rather than
            `docs/`: it records *this human's* attention, and a LAN peer
            marking someone else caught up would silently empty their digest.

            `at` carries the timestamp the digest was computed from, so
            anything that landed while they were reading is not marked seen.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - {"at"}
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._respond_json({"ok": True, "result": marker.catch_up(
                str(body.get("at") or "") or None,
            )})

        def _serve_note_transition(self) -> None:
            """``POST /api/notes/transition`` — one human-owned transition.

            The table in ``note_writes.HUMAN_TRANSITIONS`` decides what is
            legal, keyed by the note's **current** status, so a stale renderer
            cannot replay an action that has since stopped being offered. An
            agent-owned transition is refused here with the ownership rule
            named (REQ-0026) — the refusal is the server's, so no display bug
            can widen it.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.TRANSITION_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                result = note_writes.stamp_transition(
                    index,
                    str(body.get("id") or ""),
                    to_status=str(body.get("to") or ""),
                    actor=str(body.get("actor") or ""),
                    severity=str(body.get("severity") or ""),
                    note=str(body.get("note") or ""),
                    option=str(body.get("option") or ""),
                    mtime=(float(body["mtime"]) if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_note_tick(self) -> None:
            """``POST /api/notes/tick`` — resolve one criterion.

            Writes the exact shapes REQ-BOXES / PHASE-BOXES parse. A tick the
            validator cannot read is worse than no tick: it looks resolved and
            does not count.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.TICK_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                result = note_writes.stamp_tick(
                    index,
                    str(body.get("id") or ""),
                    criterion=str(body.get("criterion") or ""),
                    evidence=str(body.get("evidence") or ""),
                    reason=str(body.get("reason") or ""),
                    actor=str(body.get("actor") or ""),
                    mtime=(float(body["mtime"]) if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_note_create(self) -> None:
            """``POST /api/notes/create`` — file an issue from the template.

            Only `type: issue`. Each further type earns its own review of what
            "next id" and "which template" mean (FEAT-0059's Out of Scope), so
            the allow-list is a constant rather than a parameter.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.CREATE_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            wanted_type = str(body.get("type") or "issue").strip().lower()
            if wanted_type not in note_writes.CREATABLE_TYPES:
                self._respond_json(
                    {"ok": False,
                     "error": f"the cockpit does not create {wanted_type} notes "
                              f"(creatable: {sorted(note_writes.CREATABLE_TYPES)})"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            related = body.get("related") or []
            if not isinstance(related, list):
                self._respond_json({"ok": False, "error": "related must be a list"},
                                   status=HTTPStatus.BAD_REQUEST)
                return

            if wanted_type == "release":
                # The done-but-unshipped set is computed HERE, from the same
                # function the card reads, so the note carries the number the
                # human saw (TASK-0316). Deriving it a second time inside
                # `create_release` is how the two would come to disagree.
                unreleased = cockpit.unreleased_payload(index)
                features = [str(r.get("id") or "") for r in unreleased["items"]]
                features = [f for f in features if f]
                since = unreleased.get("since") or {}
                try:
                    result = note_writes.create_release(
                        index,
                        docs_root,
                        title=str(body.get("title") or ""),
                        features=features,
                        previous_release=str(
                            body.get("previous_release") or since.get("id") or ""
                        ),
                        actor=str(body.get("actor") or ""),
                    )
                except note_writes.WriteError as exc:
                    self._respond_json({"ok": False, "error": exc.message},
                                       status=HTTPStatus(exc.status))
                    return
                except (TypeError, ValueError, OSError) as exc:
                    self._respond_json({"ok": False, "error": str(exc)},
                                       status=HTTPStatus.BAD_REQUEST)
                    return
                self._respond_json({"ok": True, "result": result})
                return

            try:
                result = note_writes.create_issue(
                    index,
                    docs_root,
                    title=str(body.get("title") or ""),
                    body=str(body.get("body") or ""),
                    severity=str(body.get("severity") or ""),
                    component=str(body.get("component") or ""),
                    phase=str(body.get("phase") or ""),
                    related=[str(r) for r in related],
                    actor=str(body.get("actor") or ""),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError, OSError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_approve(self) -> None:
            """``POST /api/cockpit/approve`` — answer a permission prompt.

            Loopback-guarded like every write path. It changes runtime state
            rather than `docs/`, but it authorises an agent to act, which is a
            larger thing than editing a note.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - {"approval_id", "decision", "actor"}
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                result = approval_store.answer(
                    str(body.get("approval_id") or ""),
                    decision=str(body.get("decision") or ""),
                    actor=str(body.get("actor") or ""),
                )
            except ValueError as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            if result is None:
                self._respond_json({"ok": False, "error": "no such approval"},
                                   status=HTTPStatus.NOT_FOUND)
                return
            bus.publish(ControlEvent("cockpit:approval", result))
            self._respond_json({"ok": True, "result": result})

        def _serve_choose_variant(self) -> None:
            """``POST /api/notes/choose-variant`` — record a chosen shape.

            It does NOT accept the design: choosing and accepting are two
            judgments, and a click on a thumbnail must not carry an
            acceptance nobody made (TASK-0302).
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.CHOOSE_VARIANT_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                result = note_writes.stamp_chosen_variant(
                    index, str(body.get("id") or ""),
                    variant=str(body.get("variant") or ""),
                    actor=str(body.get("actor") or ""),
                    mtime=body.get("mtime"),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError, OSError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_note_attach(self) -> None:
            """``POST /api/notes/attach`` — file a capture as evidence (TASK-0297).

            Loopback-guarded: it writes into `docs/`, which is the record.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.ATTACH_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            # The desktop capture bridge writes into `inbox/` and hands back a
            # name. `inbox/` is gitignored staging whose success condition is
            # being EMPTY (LIFECYCLE.md), so filing the capture as evidence
            # means moving it out — read it here, and remove it once it has a
            # home under `docs/attachments/`.
            png_b64 = str(body.get("png_base64") or "")
            inbox_name = str(body.get("inbox_name") or "").strip()
            staged: Path | None = None
            if inbox_name and not png_b64:
                import base64 as _b64
                # Basename only: a name arriving from a renderer must not be
                # able to read an arbitrary path.
                safe = Path(inbox_name).name
                staged = (project_root / "inbox" / safe).resolve()
                if not str(staged).startswith(str((project_root / "inbox").resolve())):
                    self._respond_json({"ok": False, "error": "refusing to read outside inbox/"},
                                       status=HTTPStatus.BAD_REQUEST)
                    return
                try:
                    png_b64 = _b64.b64encode(staged.read_bytes()).decode()
                except OSError as exc:
                    self._respond_json({"ok": False, "error": f"no staged capture: {exc}"},
                                       status=HTTPStatus.BAD_REQUEST)
                    return
            try:
                result = note_writes.attach_capture(
                    index, docs_root, str(body.get("id") or ""),
                    png_base64=png_b64,
                    caption=str(body.get("caption") or ""),
                    actor=str(body.get("actor") or ""),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError, OSError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            # Filed, so it leaves staging. Best-effort: the evidence is already
            # committed-able under docs/, and a capture left in inbox/ is a
            # tidiness problem rather than a lost one.
            if staged is not None:
                try:
                    staged.unlink()
                    result["staged_removed"] = True
                except OSError:
                    result["staged_removed"] = False
            self._respond_json({"ok": True, "result": result})

        def _serve_acceptance_run(self) -> None:
            """``POST /api/notes/acceptance-run`` — record a run (TASK-0289).

            Loopback-guarded like every write path. REQ-0028's *"an agent
            cannot be a witness"* rests on this guard plus REQ-0026's terms:
            the run is an actuator-row action, human-initiated, and the
            witness is whoever the guarded caller says it is.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.ACCEPTANCE_RUN_KEYS
            if extra:
                self._respond_json(
                    {"ok": False, "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            issues = body.get("issues") or []
            if not isinstance(issues, list):
                self._respond_json({"ok": False, "error": "issues must be a list"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            try:
                result = note_writes.stamp_acceptance_run(
                    index,
                    str(body.get("id") or ""),
                    passed=int(body.get("passed") or 0),
                    failed=int(body.get("failed") or 0),
                    skipped=int(body.get("skipped") or 0),
                    issues=[str(i) for i in issues],
                    complete=bool(body.get("complete", True)),
                    actor=str(body.get("actor") or ""),
                    mtime=body.get("mtime"),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError, OSError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, "result": result})

        def _serve_tick_owed(self) -> None:
            """``POST /api/notes/tick-owed`` — tick one post-release box
            (FEAT-0110 / TASK-0453).

            Reached only from a click. The verdict beside the box is computed
            and the write is a person's: a box disappearing without anyone
            asking destroys the only record the obligation existed.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                result = note_writes.tick_post_release_box(
                    index,
                    str(body.get("id") or ""),
                    line=int(body.get("line") or -1),
                    text=str(body.get("text") or ""),
                    mtime=(float(body["mtime"])
                           if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, **result})

        def _serve_seal_ledger(self) -> None:
            """``POST /api/notes/seal-ledger`` — close a cycle ([[TASK-0547]]).

            **The ledger had no lifecycle before this.** `ledger.seal()`
            existed and nothing but a script called it, so entries accumulated
            in `WORKING-<platform>.json` forever, no verdict was ever
            attributed to a release, and decision 7's expiry — the sharpest
            argument in [[ADR-0037]] — could not fire in normal use.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                result = note_writes.seal_ledger(
                    docs_root, index,
                    release_id=str(body.get("release") or ""),
                    platform=str(body.get("platform") or ""),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            self._respond_json({"ok": True, **result})

        def _reindex(self, *note_ids: str) -> None:
            """Make a write readable by the very next request ([[ISS-0264]]).

            **The index is refreshed by the WATCHER, which is asynchronous, and
            a write endpoint answers `ok` long before that lands.** Measured on
            a scratch repo: the `mark-check` POST returns in **1 ms**, a re-read
            issued the moment it resolves still reports the OLD mark, and the
            index catches up at roughly **50 ms**.

            The renderer repaints as soon as the POST resolves, so it always
            lost that race: the first tick appeared to do nothing and the
            second showed the first one's result. Edwin, walking v2.1.7's
            suite: *"I need to do the check twice before the feature/acceptance
            test disappears."*

            **A synchronous re-parse of one path**, not a rebuild — the write
            already knows which note it touched, and `Index.invalidate` is the
            same call the watcher subscriber makes when it arrives late.

            Answering `ok` for a write the next read cannot see is the API
            lying, so this belongs to the endpoint rather than to a delay in
            the client. A client-side retry would have to guess the watcher's
            latency, and every other consumer would still be told `ok` about
            something it could not read.
            """
            for note_id in note_ids:
                if not note_id:
                    continue
                path = index.by_id(note_id)
                if path is not None:
                    index.invalidate(path)

        def _serve_mark_check(self) -> None:
            """``POST /api/notes/mark-check`` — one acceptance check, one
            verdict, one justification (FEAT-0111 / TASK-0455).

            The mark and the reason arrive together and are written together:
            a `partial` or a `fail` with no reason is a 400, which is the
            whole difference between this and the `[!]` mark ISS-0177 records.

            **`id` addresses a `CHK-*` note** and nothing else (ADR-0030).
            The `number`+`name` form addressed a row in a document by its
            position and went with that document (ISS-0192).
            `verdict: "needs-re-run"` is the seventh action and is the only one
            that must name a `change`.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                mtime = (float(body["mtime"])
                         if body.get("mtime") is not None else None)
                verdict = str(body.get("verdict") or "")
                check_id = str(body.get("id") or "")
                platform = str(body.get("platform") or "")
                if platform:
                    #: **The ledger path** ([[ADR-0037]]). A verdict that names
                    #: its platform is an EVENT and never touches a note; the
                    #: branch below is the pre-ledger writer, kept for the nine
                    #: fleet repos that have not migrated.
                    #:
                    #: The discriminator is the payload rather than a config
                    #: flag on purpose: a repo mid-migration has both shapes
                    #: reachable for exactly as long as it takes, and a flag
                    #: would have to be flipped by somebody who remembered.
                    result = note_writes.record_verdict(
                        docs_root, index, check_id=check_id,
                        platform=platform, verdict=verdict,
                        reason=str(body.get("reason") or ""),
                        by=str(body.get("by") or ""),
                        method=str(body.get("method") or "manual"),
                        change=str(body.get("change") or ""),
                        evidence=body.get("evidence") or None,
                    )
                elif verdict == "needs-re-run":
                    # The seventh action (TASK-0466). Routed here rather than
                    # to its own endpoint because it IS a verdict write from
                    # the caller's side — one control, one refusal surface —
                    # and it is the only one that requires naming a change.
                    result = note_writes.invalidate_check(
                        index, check_id=check_id,
                        change=str(body.get("change") or ""),
                        reason=str(body.get("reason") or ""),
                        mtime=mtime,
                    )
                else:
                    result = note_writes.mark_check(
                        index,
                        check_id=check_id,
                        verdict=verdict,
                        reason=str(body.get("reason") or ""),
                        mtime=mtime,
                    )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            #: Before the response, never after: the caller repaints the moment
            #: this resolves ([[ISS-0264]]).
            self._reindex(check_id)
            self._respond_json({"ok": True, **result})

        def _serve_retire_check(self) -> None:
            """``POST /api/notes/retire-check`` — the front door
            [[note_writes.retire_check]] never had ([[ISS-0249]]).

            **A complete, tested write path that nothing could call.** Walking
            the POST dispatch answered [[TASK-0363]]'s question — 19 routes
            call `note_writes`, all 19 are loopback-guarded — and the same walk
            run in reverse answered one nobody had asked: *is every write
            routed?* It was not. `retire_check` performed TESTING.md's removal
            path and no route, no control and no CLI reached it, so the
            decision [[TASK-0518]] was asking for could only have been executed
            by hand-editing 83 notes, which is the failure [[ADR-0009]] exists
            to prevent.

            [[TASK-0518]]'s answer was *retire nothing today*. That is why the
            lever lands now rather than then: a decision that changes later
            must not find that there is no button to press.

            **It is not a verdict write.** [[ADR-0035]] is untouched: this
            changes a check's own lifecycle status, and it is reachable from
            the checks view, never from a release page.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                result = note_writes.retire_check(
                    index,
                    check_id=str(body.get("id") or ""),
                    reason=str(body.get("reason") or ""),
                    mtime=(float(body["mtime"])
                           if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            #: Same reason as `mark-check` ([[ISS-0264]]) — a retire that the
            #: next read cannot see reads to the walker as a dead button.
            self._reindex(str(body.get("id") or ""))
            self._respond_json({"ok": True, **result})

        def _serve_mark_released(self) -> None:
            """``POST /api/notes/release-mark-released`` — the missing end
            (FEAT-0116 / TASK-0469).

            Writes status, date, tag and the frozen feature list, behind two
            refusals that name their subjects. **Runs no git**: the tag and
            push commands come back as text for a person to run, because a
            commit is local and reversible while a pushed tag is published.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                result = note_writes.mark_released(
                    index,
                    str(body.get("id") or ""),
                    tag=str(body.get("tag") or ""),
                    actor=str(body.get("actor") or ""),
                    mtime=(float(body["mtime"])
                           if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, **result})

        def _serve_release_contents(self) -> None:
            """``POST /api/notes/release-contents`` — compose a release
            ([[TASK-0558]]).

            `{release, action: add|remove, id}`. A release note has carried
            `features:` since [[REL-0001]] and **nothing has ever written it**,
            so composing one meant editing frontmatter by hand — which is why
            *what is in this release* has always answered *when work finished*
            rather than what anybody chose ([[ADR-0040]]).

            Loopback-only like every other write path, and the refusals live in
            `note_writes` rather than here: a rule enforced at the transport is
            a rule the next caller does not get.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                result = note_writes.release_contents(
                    index,
                    str(body.get("release") or ""),
                    action=str(body.get("action") or ""),
                    feature_id=str(body.get("id") or ""),
                    # **A removal must say why** ([[TASK-0576]]). Refused in
                    # `note_writes`, not here — the other front door gets the
                    # same refusal for free.
                    reason=str(body.get("reason") or ""),
                    actor=str(body.get("actor") or ""),
                    mtime=(float(body["mtime"])
                           if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, **result})

        def _serve_release_verified(self) -> None:
            """``POST /api/notes/release-verified`` — record what a release was
            measured against (FEAT-0107 / TASK-0445).

            Writes only the answer it is given. It does not snapshot the
            suite: this project does not write files unasked, and ten of
            `your-trainer`'s twelve releases shipped with the field empty
            precisely because nobody was ever asked.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            raw = body.get("verified")
            try:
                result = note_writes.record_verification(
                    index,
                    str(body.get("id") or ""),
                    verified=[str(v) for v in raw] if isinstance(raw, list) else [],
                    actor=str(body.get("actor") or ""),
                    mtime=(float(body["mtime"])
                           if body.get("mtime") is not None else None),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, **result})

        def _serve_release_prepare(self) -> None:
            """``POST /api/notes/release-prepare`` — declare the release being
            prepared, as a ``REL-*`` at ``draft`` (FEAT-0103 / TASK-0431).

            Declaring is not shipping (ADR-0022): this writes one note and
            publishes nothing.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            try:
                version = str(body.get("version") or "").strip()
                result = note_writes.create_release(
                    index, docs_root,
                    version=version,
                    title=str(body.get("title") or "").strip() or f"v{version.lstrip('vV')}",
                    actor=str(body.get("actor") or ""),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            self._respond_json({"ok": True, **result})

        def _serve_test_run(self) -> None:
            """``POST /api/notes/test-run`` — record a manual test run."""
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            extra = set(body) - note_writes.TEST_RUN_REQUEST_KEYS
            if extra:
                self._respond_json(
                    {"ok": False,
                     "error": f"unsupported fields: {sorted(extra)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            steps = body.get("steps")
            try:
                result = note_writes.stamp_test_run(
                    index,
                    str(body.get("id") or ""),
                    outcome=str(body.get("outcome") or ""),
                    steps=[s for s in steps if isinstance(s, dict)]
                    if isinstance(steps, list) else [],
                    runner=str(body.get("runner") or ""),
                    mtime=(float(body["mtime"]) if body.get("mtime") is not None else None),
                    aborted=bool(body.get("aborted")),
                )
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": exc.message},
                                   status=HTTPStatus(exc.status))
                return
            except (TypeError, ValueError) as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            # The failing-step draft (TASK-0372). `note_writes.draft_issue_body`
            # was written for TASK-0209 and never wired to anything: TST-0021
            # records that a failing step "produces an issue draft — returned as
            # data for the user to confirm", and the runner told the user one
            # "will be offered", while the function's only caller in the tree
            # was its own unit test. Both statements were true of the function
            # and false of the system.
            #
            # Assembled HERE rather than inside `stamp_test_run`, deliberately:
            # TASK-0372's whole constraint is that the write path does not move
            # or change, and this writes nothing. It shapes a response. The
            # cockpit still never files the issue — allocating an id is a
            # documentation decision LIFECYCLE puts in preflight — so the draft
            # is offered, and a person presses Enter.
            first_fail = next(
                (s for s in (steps if isinstance(steps, list) else [])
                 if isinstance(s, dict)
                 and str(s.get("result") or "").strip().lower() == "fail"),
                None,
            )
            if first_fail is not None and not body.get("aborted"):
                note_path = index.by_id(str(body.get("id") or ""))
                record = index.get(note_path) if note_path else None
                result = {**result, "issue_draft": note_writes.draft_issue_body(
                    str(body.get("id") or ""),
                    (record.title if record else "") or str(body.get("id") or ""),
                    first_fail,
                )}
            self._respond_json({"ok": True, "result": result})

        def _serve_dispatch_requests(self) -> None:
            """``GET /api/cockpit/dispatch-requests`` — hand queued CLI
            requests to the desktop shell exactly once (TASK-0136)."""
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                "requests": tracker.take_dispatch_requests(),
            })

        def _serve_cockpit_actions(self) -> None:
            """``GET /api/cockpit/actions`` — the agent verb registry
            (FEAT-0024 / TASK-0131): per-note-type dispatch actions,
            with optional workspace override from
            ``tools/adapters/cockpit/actions.yaml``."""
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                "actions": load_actions(project_root),
            })

        def _serve_design_verdict(self) -> None:
            """``POST /api/design/verdict`` — record a design review verdict.

            **The revision is required.** A verdict given to v3 says nothing
            about v6, and a surface that lost that distinction would let an
            old approval launder a new design — the one way a design review is
            worse than no review at all. So the caller must name the revision
            it judged, and it must be one the artifact's history actually has.

            The machine records; it never decides. `accept` comes from the
            human, and an accepted design becomes `accepted`, not
            `implemented` — the latter is what the code shipping means and only
            the parity check can honestly claim it.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            design_id = str(body.get("id", "") or "").strip()
            verdict = str(body.get("verdict", "") or "").strip()
            revision = str(body.get("revision", "") or "").strip()
            reviewer = str(body.get("reviewer", "") or "").strip()
            accept = body.get("accept")
            if not (design_id and verdict and revision and reviewer):
                self._respond_json(
                    {"ok": False, "error": "id, verdict, revision and reviewer "
                                           "are all required — a verdict with no "
                                           "revision would launder a later design"},
                    status=HTTPStatus.BAD_REQUEST)
                return

            known = {r["sha"] for r in cockpit.design_revisions_payload(
                docs_root.parent, index, design_id)["revisions"]}
            if revision not in known:
                self._respond_json(
                    {"ok": False,
                     "error": "revision %r is not in this design's history; a "
                              "verdict must name a revision that exists" % revision,
                     "revisions": sorted(known)},
                    status=HTTPStatus.BAD_REQUEST)
                return
            try:
                result = note_writes.stamp_design_verdict(
                    index, design_id, reviewer=reviewer, verdict=verdict,
                    revision=revision,
                    accept=None if accept is None else bool(accept),
                    mtime=body.get("mtime"))
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=getattr(exc, "status", 409))
                return
            self._respond_json(result)

        def _serve_design_offer_review(self) -> None:
            """``POST /api/design/offer-review`` — put a design in front of a
            human without changing its status (TASK-0229).

            The desk had two entry paths and designs were wired to only one:
            status intake at `proposed`. No design in this repo has ever been
            `proposed` — DES-0001 was created at `implemented`, DES-0002 went
            `draft` → `implemented` — so the review path TASK-0218 built had
            never been entered by a real design, and the only way in was to
            change a status to something untrue.

            This is the ledger route FEAT/TASK sets already use (ADR-0007:
            pending-ness is runtime state, not note state). No new status, no
            frontmatter written here — the verdict still goes through
            `note_writes` when a human reaches one.

            **The current revision is recorded on the request.** A review is of
            a revision, not of "the design": TASK-0218 already requires
            `design_revision` on accept and validates it against real history.
            Without the same on the request, a reviewer can accept something
            other than what they were shown.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            design_id = str(body.get("id", "") or "").strip().upper()
            note = str(body.get("note", "") or "").strip()
            if not design_id:
                self._respond_json({"ok": False, "error": "id is required"},
                                   status=HTTPStatus.BAD_REQUEST)
                return

            record = next((d for d in cockpit.designs_payload(index)["designs"]
                           if d["id"].upper() == design_id), None)
            if record is None:
                self._respond_json({"ok": False, "error": "unknown design"},
                                   status=HTTPStatus.NOT_FOUND)
                return

            # Idempotent: a human asked to look at one thing should see one
            # row, however many times the button is pressed.
            existing = review_store.open_for_subject(design_id)
            if existing is not None:
                self._respond_json({"ok": True, "already_open": True,
                                    "request": existing})
                return

            revisions = cockpit.design_revisions_payload(
                docs_root.parent, index, design_id)
            head = ""
            for rev in revisions.get("revisions") or []:
                head = str(rev.get("sha") or "")
                break

            # Refused, not offered-without-one. A request with no revision
            # produces a 200 indistinguishable from a good one, and every
            # staleness field then silently disappears — which was DES-0002's
            # own situation until its `asset` was filled in (ISS-0056).
            # `/api/design/verdict` already refuses this case; so does this.
            if not head:
                self._respond_json(
                    {"ok": False,
                     "error": "%s has no committed revision to review — commit "
                              "the artifact first, or a reviewer would be "
                              "judging something with no name" % design_id},
                    status=HTTPStatus.CONFLICT)
                return

            # Both halves pinned: the artifact revision the reviewer was shown,
            # and a digest of the note's substance (ISS-0057). Either moving
            # afterwards means they reviewed something other than what stands.
            design_rec = index.get(index.by_id(design_id)) if index.by_id(design_id) else None
            request = review_store.add(
                "review",
                items=[design_id],
                subject=design_id,
                at_revision=head,
                at_note_digest=(cockpit.design_note_digest(design_rec)
                                if design_rec is not None else None),
                title="Design review: %s" % (record.get("title") or design_id),
                body=note,
            )
            # The surface renders the WORKING COPY, so a design offered dirty
            # was reviewed against something `at_revision` does not name.
            # Recorded at offer time because that is the moment it is true;
            # `dirty` computed at open is a different question.
            if revisions.get("dirty"):
                request = dict(request)
                request["dirty_at_offer"] = True
                review_store.annotate(request["request_id"], dirty_at_offer=True)
            self._respond_json({"ok": True, "request": request})

        def _serve_design_comment(self) -> None:
            """``POST /api/design/comment`` — one region-anchored comment.

            Written as Markdown into the design note's ``## Review`` section,
            never held as runtime state: REQ-0023's "readable without the tool"
            clause exists because a link to a hosted artifact already showed
            what the alternative costs.

            The region must be one the **artifact** declares, or empty for the
            document-level lane. Accepting an arbitrary string would let a
            comment anchor to nothing and silently never render.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            design_id = str(body.get("id", "") or "").strip()
            region = str(body.get("region", "") or "").strip()
            text = str(body.get("text", "") or "").strip()
            author = str(body.get("author", "") or "").strip()
            if not design_id or not text:
                self._respond_json({"ok": False, "error": "id and text are required"},
                                   status=HTTPStatus.BAD_REQUEST)
                return

            payload = cockpit.design_comments_payload(docs_root, index, design_id)
            if region and region not in payload["regions"]:
                self._respond_json(
                    {"ok": False,
                     "error": "unknown region %r — a comment anchored to a region "
                              "the artifact does not declare would never render"
                              % region,
                     "regions": payload["regions"]},
                    status=HTTPStatus.BAD_REQUEST)
                return

            record = next((d for d in cockpit.designs_payload(index)["designs"]
                           if d["id"] == design_id), None)
            if record is None:
                self._respond_json({"ok": False, "error": "unknown design"},
                                   status=HTTPStatus.NOT_FOUND)
                return
            note_abs = (docs_root.resolve() / record["rel"]).resolve()
            try:
                note_abs.relative_to(docs_root.resolve())
            except ValueError:
                self._respond_forbidden("note outside docs root")
                return
            try:
                fm_lines, body_md = note_writes._split_frontmatter(
                    note_abs.read_text(encoding="utf-8"))
                new_body = note_writes.append_design_comment(
                    body_md, region=region, date=_dt.date.today().isoformat(),
                    author=author, text=text)
                note_abs.write_text(
                    "---\n" + "\n".join(fm_lines) + "\n---\n" + new_body,
                    encoding="utf-8")
            except note_writes.WriteError as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.CONFLICT)
                return
            except OSError as exc:
                self._respond_json({"ok": False, "error": str(exc)},
                                   status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._respond_json({"ok": True, "id": design_id, "region": region})

        def _serve_design_capture(self) -> None:
            """``POST /api/design/capture`` — commit one artifact with a reason.

            The gap this closes is the whole point of PHASE-009. TASK-0216
            renders an artifact's git history; **nothing was depositing it**.
            An agent iterating against the live surface edits the working copy
            six times and commits once — which is exactly what happened to
            DES-0001, the loss this phase exists to prevent. Every exit
            criterion could have gone green while the next design session lost
            five revisions again.

            Three rules, each of which a naive version gets wrong:

            * **One artifact per commit.** Committing the asset alongside other
              files buries the reason in an unrelated message, and the message
              is the only readable record — two regenerated HTML files diff as
              a wall of noise.
            * **A reason is required.** A capture without one produces history
              that says a revision happened and not why, which is the state
              this feature exists to escape.
            * **The note's revision log is written in the same commit.** A log
              that can drift from git is worse than no log.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            design_id = str(body.get("id", "") or "").strip()
            reason = str(body.get("reason", "") or "").strip()
            if not design_id or not reason:
                self._respond_json(
                    {"ok": False, "error": "id and reason are both required; a "
                                           "revision without a reason is the state "
                                           "this exists to escape"},
                    status=HTTPStatus.BAD_REQUEST)
                return

            record = next(
                (d for d in cockpit.designs_payload(index)["designs"]
                 if d["id"] == design_id), None)
            if record is None or not record["asset"]:
                self._respond_json({"ok": False, "error": "unknown design or no asset"},
                                   status=HTTPStatus.NOT_FOUND)
                return

            root = docs_root.resolve()
            asset_abs = (root / record["asset"]).resolve()
            note_abs = (root / record["rel"]).resolve()
            for target in (asset_abs, note_abs):
                try:
                    target.relative_to(root)
                except ValueError:
                    self._respond_forbidden("design path outside docs root")
                    return
            if not asset_abs.is_file():
                self._respond_json({"ok": False, "error": "asset missing"},
                                   status=HTTPStatus.NOT_FOUND)
                return

            repo = root.parent
            try:
                dirty = subprocess.run(
                    ["git", "-C", str(repo), "status", "--porcelain", "--",
                     str(asset_abs)],
                    capture_output=True, text=True, timeout=10, check=True).stdout
            except (subprocess.SubprocessError, OSError) as exc:
                self._respond_json({"ok": False, "error": "git unavailable: %s" % exc},
                                   status=HTTPStatus.SERVICE_UNAVAILABLE)
                return
            if not dirty.strip():
                self._respond_json(
                    {"ok": False, "error": "no change to capture — the artifact "
                                           "matches its last committed revision"},
                    status=HTTPStatus.CONFLICT)
                return

            today = _dt.date.today().isoformat()
            try:
                text = note_abs.read_text(encoding="utf-8")
                fm_lines, body_md = note_writes._split_frontmatter(text)
                new_body = note_writes.append_revision_log(
                    body_md, date=today, reason=reason)
                note_abs.write_text(
                    "---\n" + "\n".join(fm_lines) + "\n---\n" + new_body,
                    encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(repo), "add", "--", str(asset_abs), str(note_abs)],
                    capture_output=True, text=True, timeout=10, check=True)
                subprocess.run(
                    ["git", "-C", str(repo), "commit", "-m",
                     "design(%s): %s" % (design_id, reason)],
                    capture_output=True, text=True, timeout=20, check=True)
                sha = subprocess.run(
                    ["git", "-C", str(repo), "rev-parse", "HEAD"],
                    capture_output=True, text=True, timeout=10, check=True).stdout.strip()
            except (subprocess.SubprocessError, OSError) as exc:
                self._respond_json({"ok": False, "error": "capture failed: %s" % exc},
                                   status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return

            self._respond_json({"ok": True, "id": design_id, "sha": sha[:7],
                                "date": today, "reason": reason})

        def _serve_cockpit_designs(self) -> None:
            """``GET /api/cockpit/designs`` — the design register
            (FEAT-0042 / TASK-0214). Membership by `type: "[[design]]"`,
            never by path."""
            self._respond_json(cockpit.designs_payload(index))

        def _serve_design_revisions(self, design_id: str) -> None:
            """``GET /api/cockpit/design-revisions/<DES-id>`` (TASK-0216)."""
            self._respond_json(cockpit.design_revisions_payload(
                docs_root.parent, index, urllib.parse.unquote(design_id)))

        def _serve_design_asset_at(self, rest: str) -> None:
            """``GET /design-asset-at/<DES-id>/<sha>`` — the artifact as it was.

            Same register gating as the live asset route: only a design the
            register knows, and only its own asset. `git show` rather than a
            checkout, so reading history never touches the working copy.
            """
            parts = urllib.parse.unquote(rest).strip("/").split("/")
            if len(parts) != 2:
                self._respond_not_found(rest)
                return
            design_id, sha = parts
            body = cockpit.design_asset_at(
                docs_root.parent, index, design_id, sha)
            if body is None:
                self._respond_not_found(rest)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _serve_design_asset(self, rel: str) -> None:
            """``GET /design-asset/<rel>`` — a design artifact, read-only.

            Deliberately separate from ``/api/render``: that endpoint renders
            Markdown to the cockpit's own HTML, while this serves an artifact
            *verbatim* for framing. Two rules, both load-bearing:

            * The path must resolve inside ``docs/`` and must be claimed by a
              design note's ``asset:``. Serving any file under docs/ by path
              would turn a render surface into a file browser.
            * Response carries no cookies and the endpoint is GET-only, so a
              script inside a framed artifact gains nothing by calling it.
            """
            rel = urllib.parse.unquote(rel).lstrip("/")
            claimed = {
                d["asset"] for d in cockpit.designs_payload(index)["designs"]
                if d["asset"]
            }
            if rel not in claimed:
                self._respond_not_found(rel)
                return
            root = docs_root.resolve()
            target = (root / rel).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                self._respond_forbidden("design asset outside docs root")
                return
            if not target.is_file():
                self._respond_not_found(rel)
                return
            ctype, _ = mimetypes.guess_type(str(target))
            # `guess_type` returns "text/html" with no charset, so a document
            # without its own <meta charset> was decoded as latin-1 and
            # rendered mojibake — while `_serve_design_asset_at` hard-codes
            # utf-8, so the SAME bytes rendered correctly from history and
            # incorrectly live. Revision-compare was comparing two encodings
            # (ISS-0050). Text is utf-8 here; binary assets are untouched.
            if ctype and ctype.startswith("text/"):
                ctype = ctype + "; charset=utf-8"
            body = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            # An artifact is authored content. Deny it a same-origin foothold.
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _serve_cockpit_agents(self) -> None:
            """``GET /api/cockpit/agents`` — the dispatchable-agent registry
            (ISS-0032). Served rather than restated: before this, the set
            ``claude | codex`` lived in nine places and a third agent's
            queued work was discarded on restart."""
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                **agents.agents_payload(),
            })

        def _serve_cockpit_sessions(self) -> None:
            """``GET /api/cockpit/sessions`` — newest-first session
            index for the history browser (FEAT-0022 / TASK-0123)."""
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                "sessions": tracker.sessions_payload(),
            })

        def _serve_cockpit_session_cache(self) -> None:
            """``GET /api/cockpit/session-cache`` — retrospective
            prompt-cache accounting for this workspace (FEAT-0081 /
            TASK-0345).

            What full-prefix re-writes have cost here, split by cause:
            TTL expiry, model switch (ISS-0104), and the honest ``other``
            bucket for entries evicted before their TTL. Costs are
            estimates derived from a per-family price table; the token
            counts beside them are exact.
            """
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                **tracker.cache_report(),
            })

        def _serve_check_toggle(self) -> None:
            """``POST /api/notes/check-toggle`` — toggle a task-list
            checkbox in the source ``.md`` (FEAT-0011 / TASK-0074).

            Body: ``{path, index, checked}``. ``index`` is the
            zero-based ordinal of the checkbox within the rendered
            HTML — the server walks the source file in the same
            order pymdownx.tasklist would render and toggles the
            Nth ``- [ ]`` / ``- [x]`` token.

            The per-file lock makes back-to-back toggles on the same
            file deterministic (the file watcher will re-emit a
            file-changed SSE for each successful write, so clients
            stay in sync).

            **Loopback-only since ISS-0129.** This endpoint predates
            `note_writes.py` (FEAT-0011) and so never inherited its
            discipline — it mutated a note in `docs/` for any peer that could
            reach the 0.0.0.0 render surface. REQ-0027 already said no write
            endpoint is reachable from a non-loopback peer; this is that
            requirement applied, not a new restriction.
            """
            if not self._require_loopback():
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError):
                self._respond_json({"ok": False, "error": "invalid JSON"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            rel = (body.get("path") or "").strip()
            try:
                idx = int(body.get("index"))
            except (TypeError, ValueError):
                self._respond_json({"ok": False, "error": "missing or non-int 'index'"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            if "checked" not in body:
                self._respond_json({"ok": False, "error": "missing 'checked'"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            checked = bool(body["checked"])
            if not rel:
                self._respond_json({"ok": False, "error": "missing 'path'"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            rel = rel.lstrip("/")
            if rel.startswith("docs/"):
                rel = rel[len("docs/"):]
            if any(part == ".." for part in rel.split("/")):
                self._respond_json({"ok": False, "error": "path traversal blocked"},
                                   status=HTTPStatus.FORBIDDEN)
                return
            target = (docs_root / rel).resolve()
            if not _is_under(target, docs_root) or not target.is_file() or target.suffix.lower() != ".md":
                self._respond_json({"ok": False, "error": f"not a markdown file: {rel}"},
                                   status=HTTPStatus.NOT_FOUND)
                return
            ok, error = _toggle_task_at(target, idx, checked)
            if not ok:
                self._respond_json({"ok": False, "error": error},
                                   status=HTTPStatus.NOT_FOUND)
                return
            self._respond_json({"ok": True})

        def _serve_render(self, query_string: str) -> None:
            """``GET /api/render?path=<rel-path>`` — rendered Markdown
            HTML fragment + metadata (FEAT-0008 / TASK-0067).

            Returns the body HTML the mode-1 page would have wrapped,
            plus the frontmatter dict, title, and the same
            ``linked`` / ``backlinks`` shape ``/api/cockpit/context``
            emits — so the FEAT-0011 native centre pane can fill the
            doc area and the right pane in one fetch.

            Path traversal is rejected; a leading ``docs/`` is
            tolerated and stripped (the cockpit URLs use ``/docs/``
            but our internal paths are docs-root-relative).
            """
            params = urllib.parse.parse_qs(query_string)
            raw_path = (params.get("path") or [None])[0]
            if not raw_path:
                self._respond_json(
                    {"ok": False, "error": "missing 'path' parameter"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            rel_path = raw_path.strip().lstrip("/")
            # Whether the caller SAID `docs/` is information, and the first
            # version of the root-file branch below threw it away before
            # testing the allowlist — so `docs/README.md`, an explicit and
            # unambiguous request for a real note, was answered with the
            # project-root README. Keep the disambiguator.
            explicit_docs = rel_path.startswith("docs/")
            # ...and the inverse, which ISS-0037 needed. `docs/` said "the
            # note"; nothing said "the project file", so `README.md` always
            # resolved to `docs/README.md` and the top-level README was
            # unreachable through this endpoint. The Library's rows for those
            # files were dead clicks not because the client dropped the rel,
            # but because there was no rel that could mean what they meant.
            explicit_root = rel_path.startswith("root/")
            if explicit_root:
                rel_path = rel_path[len("root/"):]
            if explicit_docs:
                rel_path = rel_path[len("docs/"):]
            if not rel_path or any(part == ".." for part in rel_path.split("/")):
                self._respond_json(
                    {"ok": False, "error": "path traversal blocked"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return
            # An allowlisted top-level project file (README, ROADMAP,
            # SECURITY, LLM_BRIEF) lives one level ABOVE docs_root, so the
            # docs resolution alone rejects it as escaping the root. The
            # Library has emitted `/<file>` urls for these since FEAT-0010
            # and this endpoint never served them — clicking one was a dead
            # click, and ISS-0033 is the identity band walking into the same
            # hole.
            #
            # **docs_root wins, and it is tried first.** The first version of
            # this tried the root allowlist first and shadowed the repo's own
            # `docs/README.md` (ISS-0036). Ordering it this way means the root
            # file is reachable only when docs has no file by that name, which
            # is the true state of affairs for `LLM_BRIEF.md` and is what makes
            # the branch safe rather than merely narrow.
            target = (docs_root / rel_path).resolve()
            if explicit_root:
                # An explicit root request never falls through to docs: that
                # fallthrough is what made the two indistinguishable.
                if (project_root is None
                        or rel_path not in cockpit.PROJECT_SUPPORT_ROOT_FILES):
                    self._respond_json(
                        {"ok": False, "error": f"not an allowlisted project file: {rel_path}"},
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                candidate = (project_root / rel_path).resolve()
                if not (_is_under(candidate, project_root) and candidate.is_file()):
                    self._respond_json(
                        {"ok": False, "error": f"no such project file: {rel_path}"},
                        status=HTTPStatus.NOT_FOUND,
                    )
                    return
                target = candidate
            elif not (_is_under(target, docs_root) and target.is_file()):
                root_file = None
                if (project_root is not None and not explicit_docs
                        and rel_path in cockpit.PROJECT_SUPPORT_ROOT_FILES):
                    candidate = (project_root / rel_path).resolve()
                    if _is_under(candidate, project_root) and candidate.is_file():
                        root_file = candidate
                if root_file is not None:
                    target = root_file
                elif not _is_under(target, docs_root):
                    self._respond_json(
                        {"ok": False, "error": "resolved path escapes docs root"},
                        status=HTTPStatus.FORBIDDEN,
                    )
                    return
            if not target.is_file() or target.suffix.lower() != ".md":
                self._respond_json(
                    {"ok": False, "error": f"not a markdown file: {rel_path}"},
                    status=HTTPStatus.NOT_FOUND,
                )
                return
            try:
                html = renderer.render_markdown_body(
                    target,
                    resolver=index.resolve,
                    asset_resolver=index.resolve_asset,
                )
            except Exception as exc:
                log.exception("render failure for %s", target)
                self._respond_json(
                    {
                        "ok": False,
                        "error": f"render failed: {type(exc).__name__}: {exc}",
                    },
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            record = index.get(target)
            raw_fm = dict(record.frontmatter) if record and record.frontmatter else {}
            fm = _jsonable(raw_fm)
            title = (
                (record.title if record else None)
                or (fm.get("title") if isinstance(fm.get("title"), str) else None)
                or target.stem
            )
            # Pre-resolve the frontmatter into the same HTML metadata
            # strip mode-1 emits, so the desktop renderer mounts a
            # fully-linked card (TASK-0075). Uses the raw (un-jsonable)
            # frontmatter so date / list / nested-dict values pass into
            # the renderer with their original Python types, matching
            # the contract `_metadata_strip_html` expects.
            metadata_html = templates._metadata_strip_html(
                raw_fm, resolver=index.resolve,
            )
            # Reuse the right-pane payload so the renderer can fill
            # the linked + backlinks columns in the same fetch. The
            # `active` block is implied by the response's own
            # rel_path/title/frontmatter, so we drop it.
            ctx = cockpit.context_payload(index, rel_path)
            payload = {
                "schema_version": cockpit.SCHEMA_VERSION,
                "rel_path": rel_path,
                "title": title,
                "frontmatter": fm,
                "metadata_html": metadata_html,
                "html": html,
                "linked": ctx.get("linked") or [],
                "backlinks": ctx.get("backlinks") or [],
            }
            # CHG provenance (FEAT-0022 / TASK-0126): when this note is
            # a change note the tracker knows about, say which agent
            # session produced it — enrichment only, the file is never
            # touched.
            # The acceptance suite, and only it, carries the map from a
            # rendered checkbox to the check it is (FEAT-0104 / TASK-0434).
            # Deliberately not a general markdown feature: this is one
            # document with an address scheme, and computing it for every note
            # would make the renderer know about the suite.
            if rel_path == acceptance.SUITE_REL:
                try:
                    payload["checks"] = acceptance.check_map(
                        target.read_text(encoding="utf-8"),
                    )
                except OSError:  # pragma: no cover — read succeeded above
                    pass
                payload["gate"] = acceptance.gate_payload(docs_root)
            if target.stem.upper().startswith("CHG-"):
                prov = tracker.chg_provenance(target.stem)
                if prov is not None:
                    payload["produced_by"] = prov
            # Dispatch provenance (FEAT-0025 / TASK-0135).
            id_match = re.match(
                r"^((?:TASK|ISS|FEAT|REQ|PHASE|RISK)-\d+)",
                target.stem, re.IGNORECASE,
            )
            if id_match:
                history = tracker.dispatch_history(id_match.group(1).upper())
                if history:
                    payload["dispatch_history"] = history
            self._respond_json(payload)

        def _serve_healthz(self) -> None:
            """Liveness + identity probe used by the Electron shell's
            sidecar lifecycle (FEAT-0007 / TASK-0061).

            Returns ``200`` once the HTTP server is accepting requests
            (the index is built eagerly in ``DocsServer.__init__``, so
            by the time this endpoint is reachable it is also ready).
            The body identifies the service so the shell can refuse to
            attach to a random unrelated process bound to the same
            port.
            """
            self._respond_json({
                "ok": True,
                "service": "project-os-cockpit",
                "schema": cockpit.SCHEMA_VERSION,
                "docs_root": str(docs_root),
                "desktop_mode": _desktop_mode(),
            })

        def _serve_cockpit_focus(self) -> None:
            """``POST /api/cockpit/focus`` — agent-driven cockpit navigation.

            Body: ``{"target": "<note-id | docs-rel-path | cockpit-url>"}``.
            Resolves the target to a cockpit URL, broadcasts a
            ``cockpit:focus`` SSE event, returns ``{ok, url}``. All open
            cockpit tabs that have "follow agent" enabled jump to the
            resolved URL. TASK-0048.
            """
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError):
                self._respond_json({"ok": False, "error": "invalid JSON"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            target = (body.get("target") or "").strip()
            if not target:
                self._respond_json({"ok": False, "error": "missing 'target'"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            url = _resolve_focus_target(target, index)
            if url is None:
                self._respond_json(
                    {"ok": False, "error": f"could not resolve target: {target!r}"},
                    status=HTTPStatus.NOT_FOUND,
                )
                return
            state.record_agent_focus(target, url)
            bus.publish(ControlEvent("cockpit:focus", {"url": url, "target": target}))
            self._respond_json({"ok": True, "url": url})

        def _serve_cockpit_tab_state(self) -> None:
            """``POST /api/cockpit/tab-state`` — per-tab heartbeat (TASK-0053).

            Body: ``{"tab_id": "<uuid>", "url": "/docs/...", "following": true}``.
            Updates the in-memory tabs table; the snapshot
            (``GET /api/cockpit/state``) prunes tabs that haven't
            pinged in ``_TAB_STALE_SECONDS``.
            """
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError):
                self._respond_json({"ok": False, "error": "invalid JSON"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            tab_id = (body.get("tab_id") or "").strip()
            url = (body.get("url") or "").strip()
            following = bool(body.get("following", True))
            if not tab_id or not url:
                self._respond_json(
                    {"ok": False, "error": "missing 'tab_id' or 'url'"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            state.update_tab(tab_id, url, following)
            self._respond_json({"ok": True})

        def _serve_cockpit_state(self) -> None:
            """``GET /api/cockpit/state`` — read-only snapshot (TASK-0053).

            Returns ``{agent_focus, user_view, tabs, history}``. The
            agent uses this to know where the user is currently
            looking before / after work, complementing the
            agent-drives-cockpit direction.

            FEAT-0019 adds the hook-fed ``activity`` (last activity
            event) and ``session`` (slim live-session record incl.
            cost snapshot + undocumented flag) blocks.
            """
            snap = state.snapshot()
            snap.update(tracker.snapshot())
            # Enrich the live / last session into prompt-scoped work items —
            # the declared SNAPSHOT focus unioned with notes touched this
            # prompt, with real title/status/done from the index (TASK-0191 /
            # TASK-0193). Runs even with no touched notes, so the focus set
            # still shows.
            for key in ("session", "last_session"):
                sess = snap.get(key)
                if isinstance(sess, dict):
                    sess["work_items"] = cockpit.work_items_for_session(index, sess)
            self._respond_json(snap)

        def _serve_cockpit_validation(self) -> None:
            """``GET /api/cockpit/validation`` — docs-validator health
            report (FEAT-0018 / TASK-0111).

            Returns the cached ``{ok, state, errors, warnings,
            checked_at}`` report; the first request after startup runs
            the validator synchronously. ``state`` distinguishes
            ``ok`` / ``failing`` / ``unavailable`` (validator exit 2 —
            e.g. no SNAPSHOT.yaml). Each error carries ``code`` /
            ``message`` plus, when parseable, the offending ``id``,
            repo-relative ``rel`` path, and a resolved ``url`` deep
            link for the drift panel (TASK-0112). Re-runs are watcher-
            driven (debounced) — clients listen for the
            ``cockpit:validation`` SSE event instead of polling.
            """
            payload = dict(validation.current())
            payload["schema_version"] = cockpit.SCHEMA_VERSION
            self._respond_json(payload)

        def _proxy_terminal(self, path: str) -> None:
            """Reverse-proxy a request to ttyd (TASK-0047).

            Lazy-starts ttyd if needed (mirrors /api/terminal); HTTP +
            WebSocket forwarding lives in :mod:`terminal_proxy`. Same-
            origin proxying lets us inject custom CSS into ttyd's
            index HTML and (later) a JS bridge for terminal ↔ cockpit
            communication.
            """
            if not TerminalProcess.is_available():
                self._respond_status(HTTPStatus.SERVICE_UNAVAILABLE)
                return
            try:
                terminal.start()
            except Exception:
                log.exception("terminal proxy: lazy start failed")
                self._respond_status(HTTPStatus.SERVICE_UNAVAILABLE)
                return
            port = terminal.port
            if port is None:
                self._respond_status(HTTPStatus.SERVICE_UNAVAILABLE)
                return
            # Normalise: an iframe with src="/_terminal/" hits us at
            # "/_terminal/" (with trailing slash); ttyd's -b expects
            # the prefix verbatim.
            upstream = path if path.startswith(TERMINAL_BASE_PATH) else TERMINAL_BASE_PATH
            if self.headers.get("Upgrade", "").lower() == "websocket":
                terminal_proxy.proxy_websocket(self, port, upstream)
            else:
                terminal_proxy.proxy_http(self, port, upstream)

        # ---- SSE channel ----

        def _serve_sse(self) -> None:
            """Long-lived ``text/event-stream`` for live-reload events.

            Each connection gets its own ``queue.Queue`` and a subscriber on
            the shared bus; events fan out to all queues, the handler thread
            drains its queue into the response. Heartbeats every 15 s keep
            proxies/loadbalancers from idling the connection.
            """
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")  # nginx, just in case
            self.end_headers()

            q: queue.Queue = queue.Queue()
            unsubscribe = bus.subscribe(lambda ev: q.put(ev))

            def _send(chunk: bytes) -> None:
                self.wfile.write(chunk)
                self.wfile.flush()

            try:
                _send(b": connected\n\n")
                while True:
                    try:
                        ev = q.get(timeout=15.0)
                    except queue.Empty:
                        _send(b": heartbeat\n\n")
                        continue
                    if isinstance(ev, FileEvent):
                        payload = (
                            f"event: file-changed\n"
                            f"data: {ev.rel_path}\n\n"
                        ).encode("utf-8")
                    elif isinstance(ev, ControlEvent):
                        payload = (
                            f"event: {ev.event_type}\n"
                            f"data: {json.dumps(ev.data, ensure_ascii=False)}\n\n"
                        ).encode("utf-8")
                    else:
                        continue
                    _send(payload)
            except (BrokenPipeError, ConnectionResetError, OSError):
                # Client disconnected — normal.
                pass
            finally:
                unsubscribe()

        # ---- static assets ----

        def _serve_static(self, rel: str) -> None:
            if not rel or ".." in rel.split("/"):
                self._respond_forbidden("static path traversal blocked")
                return
            target = (STATIC_DIR / rel).resolve()
            try:
                target.relative_to(STATIC_DIR.resolve())
            except ValueError:
                self._respond_forbidden("static path escapes static dir")
                return
            if not target.is_file():
                self._respond_not_found(self.path)
                return

            ctype, _ = mimetypes.guess_type(target.name)
            ctype = ctype or "application/octet-stream"
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            _send_stylesheet_cors(self, target.name)
            self.end_headers()
            self.wfile.write(data)

        def _serve_inbox_store(self) -> None:
            """``POST /api/inbox/store`` — stage one dropped or pasted item.

            **The first endpoint here that writes a file the caller supplies.**
            Everything else writes notes through `note_writes`, which is a
            field allow-list on files that already exist; a binary write to a
            new path is a different risk, so the guards come first and are
            tested to ISS-0056's three clauses.

            The caller's filename is treated as hostile — it arrives from a
            drag-and-drop or a clipboard paste. `inbox.safe_name` rewrites the
            stem **and the suffix**, and containment is re-checked at the write
            rather than trusted from the filter.

            *(This said "an allow-listed suffix" until 2026-09-02, fifteen
            lines above the code that had removed the allow-list in the same
            commit. Found by independent review. There is no suffix list on
            this path any more — `_serve_inbox_item` decides what a type
            means, at the read.)*
            """
            if not self._require_loopback():
                return
            # Base64 inflates by ~4/3; the decoded size is checked below.
            body = self._read_json_body(
                max_bytes=inbox_mod.MAX_ITEM_BYTES * 4 // 3 + 4096)
            if body is None:
                return
            raw_name = str(body.get("name", "") or "")
            data_b64 = str(body.get("data", "") or "")
            if not data_b64:
                self._respond_json({"ok": False, "error": "data is required"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            name = inbox_mod.safe_name(raw_name)
            if name is None:
                # Any *type* is storable (ISS-0274). What is left to refuse is
                # a name with nothing in it — empty, `.`, or `..`.
                self._respond_json(
                    {"ok": False,
                     "error": "%r has no filename in it" % (raw_name[:80],)},
                    status=HTTPStatus.BAD_REQUEST)
                return
            try:
                data = base64.b64decode(data_b64, validate=True)
            except (ValueError, binascii.Error):
                self._respond_json({"ok": False, "error": "data is not base64"},
                                   status=HTTPStatus.BAD_REQUEST)
                return
            if len(data) > inbox_mod.MAX_ITEM_BYTES:
                self._respond_json(
                    {"ok": False, "error": "item is %d bytes; the limit is %d"
                                           % (len(data), inbox_mod.MAX_ITEM_BYTES)},
                    status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return

            directory = inbox_mod.inbox_dir(project_root)
            directory.mkdir(parents=True, exist_ok=True)
            target = inbox_mod.unique_path(directory, name)
            # Belt to the filter's braces: a resolved path that is not inside
            # the inbox never gets written, whatever the name did.
            try:
                target.resolve().relative_to(directory.resolve())
            except ValueError:
                self._respond_forbidden("inbox path escapes the inbox")
                return
            target.write_bytes(data)
            self._respond_json({
                "ok": True, "name": target.name, "bytes": len(data),
                "rel": "inbox/%s" % target.name,
            })

        def _serve_inbox_discard(self) -> None:
            """``POST /api/inbox/discard`` — remove one item.

            Discarding is a *good* outcome: an inbox whose items can only
            accumulate is an archive, which is the thing the triage skill
            exists to prevent.
            """
            if not self._require_loopback():
                return
            body = self._read_json_body()
            if body is None:
                return
            target = inbox_mod.resolve_item(project_root, str(body.get("name", "") or ""))
            if target is None:
                self._respond_json({"ok": False, "error": "unknown inbox item"},
                                   status=HTTPStatus.NOT_FOUND)
                return
            target.unlink()
            self._respond_json({"ok": True,
                                "remaining": len(inbox_mod.list_items(project_root))})

        def _serve_inbox_item(self, name: str) -> None:
            """``GET /_inbox/<name>`` — one item, for preview.

            Read-only and containment-checked. No CORS: nothing sandboxed
            reads this, and adding a header nothing needs is how a route
            widens by accident.

            **This is where the file's type is judged** (ISS-0274). The write
            path used to hold a suffix allow-list, which was the wrong end: it
            refused `.zip`, which this route would only ever hand back as
            bytes, while admitting `.svg`, which came back as `image/svg+xml`
            at the cockpit's own origin and can carry `<script>`.

            Two headers replace that list, and they hold for anything dropped:

            - A suffix outside `INLINE_SUFFIXES` is served as an **attachment**
              with `application/octet-stream`, so the browser saves it rather
              than interpreting it. That is the whole of what the allow-list
              was reaching for.
            - Every response carries `default-src 'none'; sandbox`, which
              neutralises a navigated-to SVG or HTML document. Thumbnails are
              unaffected: a CSP on an image response does not govern the page
              that put it in an `<img>`, and `<img>` never ran SVG script.
            """
            target = inbox_mod.resolve_item(project_root, name)
            if target is None:
                self._respond_not_found(self.path)
                return
            suffix = target.suffix.lower()
            inline = suffix in inbox_mod.INLINE_SUFFIXES
            ctype, _ = mimetypes.guess_type(target.name) if inline else (None, None)
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            #: `sandbox` only where something could execute. It is what makes
            #: Chrome download a PDF rather than render it, so applying it to
            #: every inline type would have quietly broken PDF preview to
            #: protect a file format that cannot script (independent review,
            #: 2026-09-02). `default-src 'none'` is on everything and is what
            #: blocks the inline `<script>` in a navigated-to SVG.
            policy = "default-src 'none'"
            if not inline or suffix in inbox_mod.SCRIPTABLE_SUFFIXES:
                policy += "; sandbox"
            self.send_header("Content-Security-Policy", policy)
            if not inline:
                # Sanitised again for the header, and NOT because `safe_name`
                # left something dangerous: it did not. Items also arrive by
                # `cp` straight into `inbox/` — the convention's own escape
                # hatch — and `resolve_item` admits those. What actually keeps
                # those inside the inbox is the `relative_to` containment
                # check; nothing there looks at a quote or a newline, and macOS
                # allows both in a filename. One of those in an unescaped
                # header value is header injection.
                #
                # This comment said `resolve_item` "rejects a separator and a
                # traversal" until 2026-09-02. The separator half is true. The
                # traversal half is `".." in name.split(".")`, which cannot be
                # true for any string — `split(".")` never yields an element
                # containing a dot. Independent review caught it, in a comment
                # written for a change whose whole subject was a guard that
                # read as one and was not.
                self.send_header(
                    "Content-Disposition",
                    'attachment; filename="%s"'
                    % inbox_mod.header_filename(target.name))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _serve_project_stylesheet(self, rel: str) -> None:
            """A stylesheet a design note declares, served from the project root.

            Every downstream project's CSS lives ABOVE the docs root —
            `public/css/style.css`, `obsidian-plugin/styles.css` — so a design
            artifact could not read its own project's tokens and a downstream
            design system could only ever be a hand-typed table. That table is
            what DES-0002 stopped claiming was checked.

            **The allow-list is the corpus.** `project_stylesheet_allowlist`
            gathers `stylesheets:` from every design note, so widening it means
            declaring a path in a note that a human reviews — not editing a
            constant here, which would drift from the notes it describes, and
            not sharing a directory, which would publish the project.

            Read-only and CSS-only. The render server binds 0.0.0.0; these are
            stylesheets the app already serves to anyone who loads it. The
            narrowing is what stops this becoming a general file read.
            """
            # A fast path, not the guard. Containment below refuses the same
            # inputs — mutating this check out leaves every test green because
            # `relative_to` catches them anyway. Kept because it makes the
            # refusal reason accurate, and said plainly because a check that
            # cannot fire, under a comment implying it protects something, is
            # the defect this codebase keeps finding (ISS-0024, ISS-0056).
            if not rel or ".." in rel.split("/"):
                self._respond_forbidden("project path traversal blocked")
                return
            synthesise = cockpit.token_sources.supports(rel)
            if not rel.lower().endswith(".css") and not synthesise:
                self._respond_not_found(self.path)
                return
            if rel not in cockpit.project_stylesheet_allowlist(index):
                # Undeclared. Not "missing" — a real stylesheet elsewhere in
                # the project reaches exactly this branch.
                self._respond_not_found(self.path)
                return
            target = (project_root / rel).resolve()
            try:
                target.relative_to(project_root)
            except ValueError:
                # Catches a declared path that symlinks out of the tree; the
                # allow-list check above cannot see through a link.
                self._respond_forbidden("project path escapes project root")
                return
            if not target.is_file():
                self._respond_not_found(self.path)
                return
            if synthesise:
                # Parsed on every request, so the answer cannot be older than
                # the file. Only extracted `--name: value` pairs are emitted —
                # the source itself never leaves the machine, which is why this
                # is safer than serving it (ISS-0059).
                data = cockpit.token_sources.synthesise_css(
                    target.read_text(encoding="utf-8", errors="replace"),
                    rel).encode("utf-8")
            else:
                data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            # A design frame is sandboxed with an OPAQUE origin, so it cannot
            # read `cssRules` from a linked sheet and must fetch the text and
            # re-inject it (ISS-0043). Without this header that fetch fails.
            #
            # Sent unconditionally, because THIS ROUTE ALWAYS EMITS CSS. The
            # shared helper keys off the filename, which is right for the
            # static routes and wrong here: a synthesised response is named
            # `Color.kt` and is `text/css`, so the helper stayed silent and the
            # frame's fetch failed with everything else working. Found by
            # rendering in the sandbox — curl could not see it, because curl
            # has an origin.
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def _serve_shell_asset(self, rel: str) -> None:
            """A file from the desktop shell's built renderer directory.

            Absent in mode-1 (no Electron build), so a 404 here is a normal
            state rather than a fault — and a page that depends on it must
            say so rather than render unstyled markup that reads as a design
            regression.

            The guards are `_serve_static`'s, deliberately reused rather than
            re-derived: this route must not become the one place traversal
            checking was rewritten slightly differently.
            """
            if shell_assets is None:
                self._respond_not_found(self.path)
                return
            if not rel or ".." in rel.split("/"):
                self._respond_forbidden("shell path traversal blocked")
                return
            # An allow-list, not a directory share. The design surface needs
            # the stylesheet; nothing about this route is a reason to expose
            # the bundle, the source maps, or anything else the build emits.
            if rel not in SHELL_ASSET_FILES:
                self._respond_not_found(self.path)
                return
            target = (shell_assets / rel).resolve()
            try:
                target.relative_to(shell_assets)
            except ValueError:
                self._respond_forbidden("shell path escapes assets dir")
                return
            if not target.is_file():
                self._respond_not_found(self.path)
                return
            data = target.read_bytes()
            ctype, _ = mimetypes.guess_type(target.name)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            _send_stylesheet_cors(self, target.name)
            self.end_headers()
            self.wfile.write(data)

        # ---- docs content ----

        def _serve_docs_path(self, rel: str) -> None:
            rel = urllib.parse.unquote(rel.lstrip("/"))
            # Trim trailing slash for resolution; remember it for dir handling.
            had_trailing_slash = rel.endswith("/") or rel == ""
            rel_clean = rel.rstrip("/")

            # Reject blatant traversal attempts before touching the filesystem.
            if any(part == ".." for part in rel_clean.split("/")):
                self._respond_forbidden("path traversal blocked")
                return

            target = (docs_root / rel_clean).resolve() if rel_clean else docs_root
            if not _is_under(target, docs_root):
                self._respond_forbidden("resolved path escapes docs root")
                return

            if not target.exists():
                self._respond_not_found(self.path)
                return

            if target.is_dir():
                # Render README.md if present, else a directory listing.
                readme = target / "README.md"
                if readme.is_file():
                    self._render_markdown(readme, rel_clean + "/" if rel_clean else "")
                    return
                if not had_trailing_slash and rel_clean:
                    # Canonicalise: dirs get a trailing slash so relative links work.
                    self._redirect(f"/docs/{rel_clean}/")
                    return
                self._render_directory(target, rel_clean, url_prefix="/docs")
                return

            if target.suffix.lower() == ".md":
                self._render_markdown(target, rel_clean)
                return

            # Non-markdown files are served as raw bytes (handy for images
            # and the .base files which are plain YAML).
            self._serve_raw_file(target)

        def _serve_project_support_path(self, rel: str) -> None:
            rel = urllib.parse.unquote(rel.lstrip("/"))
            had_trailing_slash = rel.endswith("/") or rel == ""
            rel_clean = rel.rstrip("/")

            if any(part == ".." for part in rel_clean.split("/")):
                self._respond_forbidden("path traversal blocked")
                return

            target = (project_root / rel_clean).resolve() if rel_clean else project_root
            if not _is_allowed_project_support_path(project_root, target):
                self._respond_forbidden("resolved path escapes project support roots")
                return

            if not target.exists():
                self._respond_not_found(self.path)
                return

            if target.is_dir():
                readme = target / "README.md"
                if readme.is_file():
                    readme_rel = readme.relative_to(project_root).as_posix()
                    self._redirect(f"/{readme_rel}")
                    return
                if not had_trailing_slash and rel_clean:
                    self._redirect(f"/{rel_clean}/")
                    return
                self._render_directory(target, rel_clean, url_prefix="")
                return

            if target.suffix.lower() == ".md":
                support_rel = target.relative_to(project_root).as_posix()
                self._render_markdown(
                    target,
                    support_rel,
                    url_prefix="",
                    reload_source="",
                )
                return

            self._serve_raw_file(target)

        def _render_markdown(
            self,
            source_path: Path,
            rel_path: str,
            *,
            url_prefix: str = "/docs",
            reload_source: str | None = None,
        ) -> None:
            try:
                html = renderer.render_markdown_file(
                    source_path,
                    rel_path=rel_path,
                    resolver=index.resolve,
                    asset_resolver=index.resolve_asset,
                    url_prefix=url_prefix,
                    reload_source=reload_source,
                )
            except Exception as exc:  # pragma: no cover - dev-only safety net
                log.exception("render failure for %s", source_path)
                self._respond_html(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    templates.notice_page(
                        title="Render error",
                        heading="Render error",
                        body_html=f"<p>Failed to render <code>{rel_path}</code>:</p>"
                        f"<pre>{type(exc).__name__}: {exc}</pre>",
                        error=True,
                    ),
                )
                return
            self._respond_html(HTTPStatus.OK, html)

        def _render_directory(
            self,
            target: Path,
            rel_path: str,
            *,
            url_prefix: str,
        ) -> None:
            entries = _directory_entries(target, rel_path, url_prefix=url_prefix)
            listing_html = templates.directory_listing_html(entries)
            title = rel_path or docs_root.name or "docs"
            body_html = (
                f"<h1>{_escape(title)}/</h1>\n"
                "<p class=\"meta\">"
                f"<code>{_escape(str(target))}</code>"
                "</p>\n"
                f"{listing_html}"
            )
            self._respond_html(
                HTTPStatus.OK,
                templates.page(
                    title=title,
                    body_html=body_html,
                    rel_path=rel_path,
                    metadata=None,
                    reload_source="*",
                ),
            )

        def _serve_raw_file(self, target: Path) -> None:
            ctype, _ = mimetypes.guess_type(target.name)
            ctype = ctype or "application/octet-stream"
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        # ---- response helpers ----

        def _respond_html(self, status: HTTPStatus, html: str) -> None:
            data = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        def _respond_json(
            self, payload: Any, status: HTTPStatus = HTTPStatus.OK
        ) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header(
                "X-Cockpit-Schema", str(cockpit.SCHEMA_VERSION)
            )
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        def _respond_status(self, status: HTTPStatus) -> None:
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _redirect(self, location: str) -> None:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _respond_forbidden(self, reason: str) -> None:
            log.warning("403 %s -> %s", self.path, reason)
            self._respond_html(
                HTTPStatus.FORBIDDEN,
                templates.notice_page(
                    title="Forbidden",
                    heading="403 Forbidden",
                    body_html=f"<p>{_escape(reason)}.</p>",
                    error=True,
                ),
            )

        def _respond_not_found(self, path: str) -> None:
            self._respond_html(
                HTTPStatus.NOT_FOUND,
                templates.notice_page(
                    title="Not found",
                    heading="404 Not found",
                    body_html=f"<p>No content at <code>{_escape(path)}</code>.</p>",
                    error=False,
                ),
            )

        # ---- logging ----

        def log_message(self, format: str, *args) -> None:  # noqa: A002, N802
            log.info("%s - %s", self.address_string(), format % args)

    return Handler


def _send_stylesheet_cors(handler: BaseHTTPRequestHandler, filename: str) -> None:
    """Allow a stylesheet to be fetched from an opaque origin (ISS-0043).

    The design frame is sandboxed ``allow-scripts`` and deliberately NOT
    ``allow-same-origin`` — granting both would let the frame remove its own
    sandbox. The cost is that the frame has an *opaque* origin, so every
    stylesheet it loads from this very server is a cross-origin read: the CSSOM
    refuses ``cssRules``, and an artifact that enumerates design tokens sees
    nothing at all.

    Letting the artifact fetch the stylesheet TEXT and inject it as an inline
    sheet restores enumeration without weakening the sandbox — inline sheets
    belong to the frame's own document and carry no origin question.

    **CSS only.** These are the application's own stylesheets, already public to
    anyone who can reach the render port; nothing here reads user data. The
    narrowing to ``.css`` is so this does not quietly become blanket CORS on
    every static file the package ships.
    """
    if filename.lower().endswith(".css"):
        handler.send_header("Access-Control-Allow-Origin", "*")


def _is_under(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


import re as _re

# Per-file write locks for the checkbox-toggle endpoint (TASK-0074).
# A click can fire before the previous file-watcher event has propagated
# back to the renderer, so two toggles in quick succession can race on
# the same file. One lock per absolute path; lookups are themselves
# guarded by a module lock so the dict mutation is safe.
#: When this process began. Captured at import rather than asked for
#: later: the question ISS-0140 needs answered is "is the running code
#: older than the code on disk", and a value read at request time would
#: be the wrong end of that comparison.
_PROCESS_STARTED_AT = _time.time()

_TASK_TOGGLE_LOCKS_MUTEX = threading.Lock()
_TASK_TOGGLE_LOCKS: dict[str, threading.Lock] = {}

# Lines that pymdownx.tasklist renders as checkboxes. The leading
# whitespace is any indent (nested lists are valid); after the bullet
# (``-``, ``*``, ``+``) come `` [ ]`` / `` [x]`` / `` [X]``.
_TASK_LINE_RE = _re.compile(r"^(\s*[-*+]\s+)\[([ xX])\](\s)")


def _toggle_task_at(
    target: Path, index: int, checked: bool,
) -> tuple[bool, str]:
    """Toggle the ``index``-th task-list checkbox in ``target`` to
    ``checked``. Returns ``(ok, error_message)``.

    ``index`` is the zero-based ordinal as pymdownx.tasklist would
    render. The rendered DOM and the source are walked in the same
    document order, so the Nth rendered checkbox corresponds to the
    Nth matching source line.
    """
    key = str(target)
    with _TASK_TOGGLE_LOCKS_MUTEX:
        lock = _TASK_TOGGLE_LOCKS.setdefault(key, threading.Lock())
    with lock:
        try:
            text = target.read_text(encoding="utf-8")
        except OSError as exc:
            return False, f"read failed: {exc}"
        lines = text.splitlines(keepends=True)
        # Walk once to find the Nth task-list line.
        seen = -1
        hit: int | None = None
        for ln_idx, line in enumerate(lines):
            if _TASK_LINE_RE.match(line):
                seen += 1
                if seen == index:
                    hit = ln_idx
                    break
        if hit is None:
            return False, (
                f"checkbox index {index} not found "
                f"(only {seen + 1} checkbox(es) in file)"
            )
        replacement = "x" if checked else " "
        lines[hit] = _TASK_LINE_RE.sub(
            lambda m: f"{m.group(1)}[{replacement}]{m.group(3)}",
            lines[hit],
            count=1,
        )
        try:
            target.write_text("".join(lines), encoding="utf-8")
        except OSError as exc:
            return False, f"write failed: {exc}"
        return True, ""


def _jsonable(value: Any) -> Any:
    """Coerce frontmatter values into JSON-serialisable shapes.

    YAML-parsed frontmatter can include ``date`` / ``datetime``
    objects (the project's convention is `created: 2026-05-25`,
    which PyYAML parses as a ``datetime.date``). ``json.dumps``
    rejects those; stringify them, recurse into containers, and
    pass scalars through. Keys are always coerced to str so the
    output is shape-safe regardless of the original YAML.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return str(value)


# ---- Cockpit discovery file (TASK-0051) ----
# So that an LLM running in any terminal under the project tree (not just
# the cockpit's embedded ttyd) can find the running cockpit and drive it
# via the `cockpit` CLI, the server writes its URL to <project>/.cockpit/url
# on startup and removes the file on shutdown. The CLI walks up from cwd
# looking for that file.

def _write_discovery_file(project_root: Path, url: str) -> None:
    try:
        cockpit_dir = project_root / ".cockpit"
        cockpit_dir.mkdir(exist_ok=True)
        (cockpit_dir / "url").write_text(url + "\n", encoding="utf-8")
        atexit.register(_remove_discovery_file, project_root)
    except OSError as exc:
        log.warning("discovery file write failed for %s: %s", project_root, exc)


def _remove_discovery_file(project_root: Path) -> None:
    try:
        (project_root / ".cockpit" / "url").unlink(missing_ok=True)
    except OSError:
        pass


def _resolve_focus_target(target: str, index: Index) -> str | None:
    """Resolve a focus target to a cockpit URL.

    Accepted shapes (most-specific first):
      * a full cockpit URL like ``/docs/foo/bar.md`` or ``/``
      * a project-os note ID like ``FEAT-0006`` (resolved via index)
      * a docs-root-relative path like ``features/cockpit/foo.md``
      * a top-level support file like ``README.md`` / ``ROADMAP.md``

    Returns ``None`` when the target can't be mapped to anything the
    cockpit knows how to render.
    """
    t = target.strip()
    if not t:
        return None
    # Already an absolute path? Accept anything that looks like a cockpit
    # route — the cockpit deals with non-renderable URLs by falling back
    # to a full navigation if its in-pane swap doesn't find #cockpit-centre.
    if t.startswith("/"):
        return t
    # ID lookup via the index (handles FEAT-####, ADR-####, etc.).
    path = index.by_id(t)
    if path is not None:
        rel = index.get(path)
        if rel is not None:
            return f"/docs/{rel.rel_path}"
    # docs-root-relative path?
    rel_candidate = t
    if rel_candidate.startswith("docs/"):
        rel_candidate = rel_candidate[len("docs/"):]
    abs_candidate = (index.docs_root / rel_candidate).resolve()
    if _is_under(abs_candidate, index.docs_root) and abs_candidate.is_file():
        return f"/docs/{rel_candidate}"
    # Top-level project file (README.md, ROADMAP.md, SECURITY.md)?
    if t in cockpit.PROJECT_SUPPORT_ROOT_FILES:
        return f"/{t}"
    return None


def _project_support_rel(path: str) -> str | None:
    rel = path.lstrip("/")
    if not rel:
        return None
    if any(part == ".." for part in rel.split("/")):
        return rel
    if rel in cockpit.PROJECT_SUPPORT_ROOT_FILES:
        return rel
    for root_rel, _label, _max_depth in cockpit.PROJECT_SUPPORT_DIRS:
        if rel == root_rel or rel.startswith(root_rel + "/"):
            return rel
    return None


def _is_allowed_project_support_path(project_root: Path, target: Path) -> bool:
    if not _is_under(target, project_root):
        return False
    for root_file in cockpit.PROJECT_SUPPORT_ROOT_FILES:
        if target == (project_root / root_file).resolve():
            return True
    for root_rel, _label, max_depth in cockpit.PROJECT_SUPPORT_DIRS:
        support_root = (project_root / root_rel).resolve()
        if _is_under(target, support_root):
            try:
                rel_parts = target.relative_to(support_root).parts
            except ValueError:
                return False
            return len(rel_parts) <= max_depth
    return False


def _project_support_active(project_root: Path, this: str) -> dict[str, str | None] | None:
    rel = _project_support_rel("/" + this.lstrip("/"))
    if rel is None:
        return None
    target = (project_root / rel).resolve()
    if not target.is_file() or target.suffix.lower() != ".md":
        return None
    if not _is_allowed_project_support_path(project_root, target):
        return None
    return {
        "id": None,
        "title": _markdown_title(target),
        "url": f"/{rel}",
    }


def _markdown_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[:80]:
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
    except OSError:
        pass
    return path.stem


def _render_readme_if_present(docs_root: Path, idx) -> str | None:
    """Render the docs-root README.md body for the landing fallback.

    Used only when SNAPSHOT.yaml is absent — the synthetic snapshot home
    is the preferred landing.
    """
    readme = docs_root / "README.md"
    if not readme.is_file():
        return None
    try:
        from . import renderer as _renderer

        return _renderer.render_markdown_body(
            readme,
            resolver=idx.resolve,
            asset_resolver=idx.resolve_asset,
        )
    except Exception:
        return None


def _feature_count_by_phase(idx) -> dict[str, int]:
    """Count features per ``PHASE-NNN`` based on the index's frontmatter."""
    import re as _re

    counts: dict[str, int] = {}
    for record in idx.notes_by_type("feature"):
        raw = record.frontmatter.get("phase")
        if isinstance(raw, list):
            raw = raw[0] if raw else None
        if not isinstance(raw, str):
            continue
        m = _re.match(r"PHASE-\d+", raw.replace("[[", "").replace("]]", "").strip().upper())
        if m:
            counts[m.group(0)] = counts.get(m.group(0), 0) + 1
    return counts


#: Peer addresses treated as Mac-local for the desk's mutation endpoints.
#: Named so a test can assert the set rather than parse the predicate.
_LOOPBACK_HOSTS: frozenset[str] = frozenset({
    "127.0.0.1", "::1", "::ffff:127.0.0.1",
})


def _git_head(project_root: Path) -> str:
    """Current HEAD sha, read from the filesystem (no subprocess).

    Used only as a cache key for ``/api/cockpit/commits``; an unreadable or
    non-git workspace returns "" and simply caches on index generation.
    """
    git_dir = project_root / ".git"
    try:
        if git_dir.is_file():  # worktree: ".git" is a pointer file
            pointer = git_dir.read_text(encoding="utf-8").strip()
            if pointer.startswith("gitdir:"):
                git_dir = Path(pointer[len("gitdir:"):].strip())
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref = head[len("ref:"):].strip()
            return (git_dir / ref).read_text(encoding="utf-8").strip()
        return head
    except OSError:
        return ""


def _read_snapshot(docs_root: Path) -> dict | None:
    """Parse SNAPSHOT.yaml from the project root, or ``None`` if absent / broken."""
    snapshot_path = docs_root.parent / "SNAPSHOT.yaml"
    if not snapshot_path.is_file():
        return None
    try:
        import yaml

        data = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _read_focus(docs_root: Path) -> dict[str, str] | None:
    """Subset of :func:`_read_snapshot` returning just the ``focus.*`` block.

    Used by the legacy fallback landing render when no snapshot is available.
    """
    data = _read_snapshot(docs_root)
    if data is None:
        return None
    focus = data.get("focus") or {}
    if not isinstance(focus, dict):
        return None
    return {str(k): str(v) for k, v in focus.items() if v}


def _directory_entries(
    target: Path,
    rel_path: str,
    *,
    url_prefix: str,
) -> Iterable[tuple[str, str, bool]]:
    children = sorted(
        (p for p in target.iterdir() if not _is_hidden(p.name)),
        key=lambda p: (not p.is_dir(), p.name.lower()),
    )
    prefix = url_prefix.rstrip("/")
    base_url = f"{prefix}/{rel_path}/" if prefix else f"/{rel_path}/"
    if not rel_path:
        base_url = f"{prefix}/" if prefix else "/"
    if rel_path:
        parent_rel = "/".join(rel_path.split("/")[:-1])
        parent_url = f"{prefix}/{parent_rel}/" if prefix else f"/{parent_rel}/"
        parent_url = parent_url.replace("//", "/")
        root_url = f"{prefix}/" if prefix else "/"
        if parent_url == root_url:
            yield (root_url, "..", True)
        else:
            yield (parent_url, "..", True)
    for child in children:
        if child.is_dir():
            yield (f"{base_url}{child.name}/", child.name + "/", True)
        elif child.suffix.lower() == ".md":
            yield (f"{base_url}{child.name}", child.name, False)
        else:
            yield (f"{base_url}{child.name}", child.name, False)


def _is_hidden(name: str) -> bool:
    if name in HIDDEN_NAMES:
        return True
    return any(name.startswith(p) for p in HIDDEN_NAME_PREFIXES)


def _escape(text: str) -> str:
    from html import escape

    return escape(text)
