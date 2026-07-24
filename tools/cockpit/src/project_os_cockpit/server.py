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
import json
import re
import logging
import mimetypes
import os
import queue
import threading
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable

from . import cockpit, renderer, templates, terminal_proxy
from .agent_actions import load_actions
from .agent_hooks import AgentSessionTracker
from .status_diff import StatusTracker
from .agent_hooks import MAX_BODY_BYTES as _AGENT_HOOK_MAX_BYTES
from .events import ControlEvent, EventBus, FileEvent
from .index import Index
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

    def __init__(self, *, docs_root: Path, bind: str, port: int) -> None:
        self.docs_root = docs_root.resolve(strict=True)
        if not self.docs_root.is_dir():
            raise NotADirectoryError(f"docs root is not a directory: {self.docs_root}")
        self.bind = bind
        self.port = port
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
) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class with the per-server collaborators baked in."""
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

            if path == "/api/cockpit/transitions":
                self._respond_json({
                    "transitions": status_diff.transitions() if status_diff else [],
                })
                return

            if path == "/api/cockpit/stats":
                self._serve_cockpit_stats(parsed.query)
                return

            if path == "/api/cockpit/sessions":
                self._serve_cockpit_sessions()
                return

            if path == "/api/cockpit/actions":
                self._serve_cockpit_actions()
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

        def _serve_cockpit_sessions(self) -> None:
            """``GET /api/cockpit/sessions`` — newest-first session
            index for the history browser (FEAT-0022 / TASK-0123)."""
            self._respond_json({
                "schema_version": cockpit.SCHEMA_VERSION,
                "sessions": tracker.sessions_payload(),
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
            if rel_path.startswith("docs/"):
                rel_path = rel_path[len("docs/"):]
            if not rel_path or any(part == ".." for part in rel_path.split("/")):
                self._respond_json(
                    {"ok": False, "error": "path traversal blocked"},
                    status=HTTPStatus.FORBIDDEN,
                )
                return
            target = (docs_root / rel_path).resolve()
            if not _is_under(target, docs_root):
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
