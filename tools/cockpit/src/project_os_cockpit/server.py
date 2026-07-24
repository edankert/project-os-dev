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

import json
import logging
import mimetypes
import queue
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable

from . import cockpit, renderer, templates
from .events import EventBus
from .index import Index
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
        # Header home-link label = repo name (parent of docs/), so users
        # always see which project they're browsing.
        templates.set_project_name(
            self.docs_root.parent.name or self.docs_root.name or "docs"
        )

    def run(self) -> None:
        handler_cls = _make_handler(self.docs_root, self.index, self.bus)
        self.watcher.start()
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
    docs_root: Path, index: Index, bus: EventBus
) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class with the per-server collaborators baked in."""
    project_root = docs_root.parent.resolve()

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
                    payload = (
                        f"event: file-changed\n"
                        f"data: {ev.rel_path}\n\n"
                    ).encode("utf-8")
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
