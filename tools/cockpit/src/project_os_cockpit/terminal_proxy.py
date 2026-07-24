"""Reverse-proxy ttyd through the cockpit server (TASK-0047).

ttyd runs on a free local port; the cockpit forwards every request
under ``/_terminal/*`` (HTTP + WebSocket) so the browser sees the
terminal iframe as same-origin with the rest of the cockpit. That
unlocks:

* injecting custom CSS into ttyd's index HTML (muted scrollbar styling
  for the embedded xterm.js viewport),
* injecting a small JS bridge so xterm.js events can postMessage the
  parent cockpit page (future TASK-0048),
* avoiding cross-origin permission prompts in the browser.

Implementation is stdlib-only — http.client for HTTP forwarding, a
hand-rolled WebSocket upgrade for the ``/_terminal/ws`` channel with
two daemon threads shuttling bytes between the client socket and the
ttyd socket. No external proxy dependency.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import logging
import os
import socket
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Optional

log = logging.getLogger(__name__)

# RFC 6455 magic GUID used to compute the WebSocket accept value.
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Best-effort CSS injection inside the iframe to hide the scrollbar.
# Chrome aggressively memoises the iframe load even with
# Cache-Control: no-store, so this often doesn't land on return visits.
# The real defence is the iframe-overshoot trick in cockpit.css
# (.cockpit-bottom-body { overflow: hidden } + iframe
# width: calc(100% + 16px)). This block stays as belt-and-suspenders
# for Firefox / fresh sessions where the injection does reach.
_SCROLLBAR_CSS = b"""
<style>
html, body, .xterm, .xterm-viewport, * {
  scrollbar-width: none !important;
  scrollbar-color: transparent transparent !important;
}
*::-webkit-scrollbar,
*::-webkit-scrollbar-track,
*::-webkit-scrollbar-thumb,
*::-webkit-scrollbar-corner,
*::-webkit-scrollbar-button {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  -webkit-appearance: none !important;
  appearance: none !important;
  background: transparent !important;
}
</style>
"""


def ws_accept(key: str) -> str:
    """Compute the Sec-WebSocket-Accept value for a given client key."""
    digest = hashlib.sha1((key + _WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def inject_html_extras(body: bytes) -> bytes:
    """Inject the scrollbar CSS into ttyd's index HTML.

    Inserts the ``<style>`` block right before ``</head>``. If the body
    isn't HTML (or doesn't contain ``</head>``) it's passed through
    unchanged — non-HTML responses (the JS bundle, fonts, etc.) skip
    this path entirely.
    """
    needle = b"</head>"
    idx = body.lower().find(needle)
    if idx == -1:
        return body
    return body[:idx] + _SCROLLBAR_CSS + body[idx:]


def proxy_http(
    handler: BaseHTTPRequestHandler,
    ttyd_port: int,
    upstream_path: str,
) -> None:
    """Forward an HTTP request to ttyd, with optional response munging.

    ``upstream_path`` is the path ttyd should receive (including any
    base-path prefix ttyd was started with — ttyd's ``-b /_terminal/``
    means ttyd expects paths starting with ``/_terminal/``).
    """
    headers = {}
    for key, value in handler.headers.items():
        # Strip hop-by-hop headers + Host (we set our own).
        if key.lower() in ("host", "connection", "keep-alive", "te",
                           "trailers", "transfer-encoding", "upgrade",
                           "proxy-authorization", "proxy-authenticate"):
            continue
        headers[key] = value
    try:
        conn = http.client.HTTPConnection("127.0.0.1", ttyd_port, timeout=15)
        conn.request("GET", upstream_path, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
    except (ConnectionError, OSError, http.client.HTTPException) as exc:
        log.warning("terminal proxy: upstream HTTP failed: %s", exc)
        handler.send_response(HTTPStatus.BAD_GATEWAY)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return
    finally:
        try:
            conn.close()
        except Exception:
            pass

    content_type = (resp.getheader("Content-Type") or "").lower()
    is_html = "html" in content_type
    if is_html:
        body = inject_html_extras(body)

    handler.send_response(resp.status)
    skip_lower = {
        "transfer-encoding", "connection", "content-length", "keep-alive",
    }
    # Force no-store on the injected HTML so the browser always re-fetches
    # — otherwise CSS / JS injection changes get masked by Chrome's
    # heuristic iframe cache.
    if is_html:
        skip_lower.update({"cache-control", "etag", "last-modified"})
    for header, value in resp.getheaders():
        if header.lower() in skip_lower:
            continue
        handler.send_header(header, value)
    if is_html:
        handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        handler.send_header("Pragma", "no-cache")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def proxy_websocket(
    handler: BaseHTTPRequestHandler,
    ttyd_port: int,
    upstream_path: str,
) -> None:
    """Handle a WebSocket upgrade by reverse-proxying to ttyd.

    The handshake is performed in two halves:

    1. **Cockpit ↔ ttyd**: we open a raw socket to ttyd, send our own
       WebSocket upgrade request (with a freshly-generated key), and
       expect a 101 response.
    2. **Browser ↔ cockpit**: we then send a 101 response to the
       browser, computing the accept value from the browser's original
       Sec-WebSocket-Key.

    After both upgrades succeed, two daemon threads shuttle bytes
    bidirectionally until either side closes. WebSocket framing isn't
    parsed — we forward bytes verbatim.
    """
    client_key = handler.headers.get("Sec-WebSocket-Key")
    if not client_key:
        handler.send_response(HTTPStatus.BAD_REQUEST)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    # Connect to ttyd and request a WS upgrade ourselves.
    try:
        ttyd_sock = socket.create_connection(("127.0.0.1", ttyd_port), timeout=5)
    except OSError as exc:
        log.warning("terminal proxy: ttyd unreachable: %s", exc)
        handler.send_response(HTTPStatus.BAD_GATEWAY)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    upstream_key = base64.b64encode(os.urandom(16)).decode("ascii")
    request_lines = [
        f"GET {upstream_path} HTTP/1.1",
        f"Host: 127.0.0.1:{ttyd_port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {upstream_key}",
        "Sec-WebSocket-Version: 13",
    ]
    sub_proto = handler.headers.get("Sec-WebSocket-Protocol")
    if sub_proto:
        request_lines.append(f"Sec-WebSocket-Protocol: {sub_proto}")
    sub_ext = handler.headers.get("Sec-WebSocket-Extensions")
    if sub_ext:
        request_lines.append(f"Sec-WebSocket-Extensions: {sub_ext}")
    # Forward Origin (ttyd may want it; we run with origin-check off).
    if handler.headers.get("Origin"):
        request_lines.append(f"Origin: {handler.headers['Origin']}")
    request_lines.extend(["", ""])
    try:
        ttyd_sock.sendall("\r\n".join(request_lines).encode("ascii"))
    except OSError as exc:
        log.warning("terminal proxy: upstream send failed: %s", exc)
        ttyd_sock.close()
        handler.send_response(HTTPStatus.BAD_GATEWAY)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    # Read ttyd's upgrade response (headers up to the blank line). Any
    # trailing bytes after the blank line are early WS frames from
    # ttyd — forward them to the client after we send our 101.
    ttyd_sock.settimeout(5)
    resp_buf = b""
    try:
        while b"\r\n\r\n" not in resp_buf and len(resp_buf) < 65536:
            chunk = ttyd_sock.recv(4096)
            if not chunk:
                break
            resp_buf += chunk
    except socket.timeout:
        log.warning("terminal proxy: upstream upgrade timeout")
        ttyd_sock.close()
        handler.send_response(HTTPStatus.GATEWAY_TIMEOUT)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return
    ttyd_sock.settimeout(None)

    head, sep, leftover = resp_buf.partition(b"\r\n\r\n")
    if not sep or not head.startswith(b"HTTP/1.1 101"):
        log.warning("terminal proxy: upstream did not upgrade (%r)", head[:80])
        ttyd_sock.close()
        handler.send_response(HTTPStatus.BAD_GATEWAY)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    upstream_resp_headers: dict[str, str] = {}
    for line in head.decode("latin-1", errors="replace").split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            upstream_resp_headers[k.strip().lower()] = v.strip()

    # Send 101 to the browser. Bypass the helpers to avoid extra
    # buffering — we want the response on the wire before the bytes
    # start flying.
    resp_lines = [
        "HTTP/1.1 101 Switching Protocols",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Accept: {ws_accept(client_key)}",
    ]
    if "sec-websocket-protocol" in upstream_resp_headers:
        resp_lines.append(
            f"Sec-WebSocket-Protocol: "
            f"{upstream_resp_headers['sec-websocket-protocol']}"
        )
    resp_lines.extend(["", ""])
    try:
        handler.wfile.write("\r\n".join(resp_lines).encode("ascii"))
        handler.wfile.flush()
        if leftover:
            handler.wfile.write(leftover)
            handler.wfile.flush()
    except OSError as exc:
        log.warning("terminal proxy: client upgrade write failed: %s", exc)
        ttyd_sock.close()
        return

    # Both halves upgraded. Forward bytes bidirectionally. The
    # client→ttyd thread reads via handler.rfile (which may have
    # buffered bytes from the upgrade phase); the ttyd→client thread
    # writes via handler.wfile.
    _bidirectional_forward(handler, ttyd_sock)


def _bidirectional_forward(
    handler: BaseHTTPRequestHandler, ttyd_sock: socket.socket
) -> None:
    """Shuttle bytes between the browser socket and the ttyd socket
    until either direction closes; then tear both down."""
    stop = threading.Event()

    def c2s() -> None:
        try:
            while not stop.is_set():
                # read1 returns whatever is currently buffered (or
                # blocks for the next chunk); 0 = EOF.
                data = handler.rfile.read1(8192)
                if not data:
                    break
                ttyd_sock.sendall(data)
        except (OSError, ValueError):
            pass
        finally:
            stop.set()
            try:
                ttyd_sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def s2c() -> None:
        try:
            while not stop.is_set():
                data = ttyd_sock.recv(8192)
                if not data:
                    break
                handler.wfile.write(data)
                handler.wfile.flush()
        except (OSError, ValueError):
            pass
        finally:
            stop.set()
            try:
                handler.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    forward_thread = threading.Thread(target=c2s, daemon=True)
    forward_thread.start()
    try:
        s2c()
    finally:
        forward_thread.join(timeout=2)
        try:
            ttyd_sock.close()
        except OSError:
            pass
