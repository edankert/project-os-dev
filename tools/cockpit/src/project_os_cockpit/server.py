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
import logging
import mimetypes
import queue
import threading
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable

from . import cockpit, renderer, templates, terminal_proxy
from .events import ControlEvent, EventBus, FileEvent
from .index import Index
from .terminal import TERMINAL_BASE_PATH, TerminalProcess
from .watcher import Watcher

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

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._agent_focus: dict[str, Any] | None = None
        self._tabs: dict[str, dict[str, Any]] = {}
        self._history: collections.deque[dict[str, Any]] = collections.deque(
            maxlen=_HISTORY_MAX
        )

    def record_agent_focus(self, target: str, url: str) -> None:
        ts = _utc_now_iso()
        with self._lock:
            self._agent_focus = {"target": target, "url": url, "ts": ts}
            self._history.appendleft(
                {"url": url, "ts": ts, "source": "agent", "target": target}
            )

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
        self.cockpit_state: CockpitState = CockpitState()
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
        )
        self.watcher.start()
        # Write the discovery file so the `cockpit` CLI (from any
        # terminal under the project tree) can auto-find this server.
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
            self.watcher.stop()


def _make_handler(
    docs_root: Path, index: Index, bus: EventBus,
    *, cockpit_url: str = "",
    cockpit_state: CockpitState | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class with the per-server collaborators baked in."""
    project_root = docs_root.parent.resolve()
    state = cockpit_state or CockpitState()
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
            """
            self._respond_json(terminal.info())

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
            """
            self._respond_json(state.snapshot())

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
