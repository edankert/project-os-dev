"""Embedded local-only terminal via ttyd (FEAT-0003).

Spawns ``ttyd`` as a child process bound to ``127.0.0.1`` (REQ-0005), on
a free local port, running the user's ``$SHELL`` by default. The
cockpit's JS client fetches ``/api/terminal`` to learn the URL and
renders an iframe in the bottom panel.

``ttyd`` is **not** a pip dependency — it's a separate binary the user
installs via their package manager (``brew install ttyd`` on macOS).
When the binary is missing, the endpoint returns ``enabled: false`` and
the JS shows a small install hint.
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# xterm.js theme tuned to sit quietly next to the cockpit's muted greyscale
# (REQ-0012). Dark surface; semantic ANSI colours pulled to the same
# saturation band as the cockpit type-colour palette. ttyd applies this
# at spawn time, so it doesn't follow the cockpit's light/dark toggle —
# treat the terminal as a fixed dark surface, like most editors.
_TERMINAL_THEME: dict[str, str] = {
    "background": "#1b1d1f",
    "foreground": "#d6d6d6",
    "cursor": "#7da6ff",
    "cursorAccent": "#1b1d1f",
    "selectionBackground": "#33373b",
    "selectionForeground": "#ffffff",
    "black":         "#1b1d1f",
    "red":           "#cc6f6f",
    "green":         "#8ab886",
    "yellow":        "#d5b878",
    "blue":          "#7da6ff",
    "magenta":       "#b48ead",
    "cyan":          "#86c1b9",
    "white":         "#c5c8c6",
    "brightBlack":   "#5c5f63",
    "brightRed":     "#d68a8a",
    "brightGreen":   "#a6c898",
    "brightYellow":  "#e0c895",
    "brightBlue":    "#9bb8ff",
    "brightMagenta": "#c8a4c6",
    "brightCyan":    "#a5d3cc",
    "brightWhite":   "#f0f0f0",
}
_TERMINAL_FONT_SIZE = 13
_TERMINAL_FONT_FAMILY = (
    'ui-monospace, "SF Mono", Menlo, Monaco, Consolas, '
    '"Liberation Mono", monospace'
)

# ttyd is reverse-proxied through the cockpit so the terminal iframe
# ends up same-origin with the cockpit page. ``-b /_terminal/`` makes
# ttyd's bundled JS construct URLs (including the WebSocket) relative
# to this prefix, so all client-side requests come back to the cockpit
# server at ``/_terminal/*`` and we forward them.
TERMINAL_BASE_PATH = "/_terminal/"


class TerminalProcess:
    """Manages a ttyd child process scoped to the cockpit's lifetime."""

    def __init__(
        self,
        working_dir: Path,
        command: Optional[list[str]] = None,
        cockpit_url: Optional[str] = None,
    ) -> None:
        self.working_dir: Path = Path(working_dir).resolve()
        # Default to the user's interactive shell. Project-os config may
        # override later (e.g. ["claude-code"] or ["codex"]).
        shell = os.environ.get("SHELL", "/bin/bash")
        self.command: list[str] = command or [shell]
        # The cockpit's own HTTP URL — passed into ttyd's child shell as
        # COCKPIT_URL so the `cockpit` CLI knows where to POST focus
        # commands. Set by the server at construction time.
        self.cockpit_url: Optional[str] = cockpit_url
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.port: Optional[int] = None
        self.url: Optional[str] = None

    @staticmethod
    def is_available() -> bool:
        """ttyd binary present on PATH? Always ``False`` in desktop mode.

        Desktop mode (``COCKPIT_DESKTOP=1``) means the Electron shell
        (FEAT-0007) is hosting this sidecar and mounts a native node-pty
        pane in the bottom-panel slot itself; spawning ttyd here would
        be wasted work and would cause two terminals to fight for the
        same space.
        """
        if os.environ.get("COCKPIT_DESKTOP") == "1":
            return False
        return shutil.which("ttyd") is not None

    @staticmethod
    def _free_port() -> int:
        """Ask the OS for an available loopback port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def start(self) -> None:
        """Spawn ttyd if not already running. Idempotent."""
        if self.process is not None and self.process.poll() is None:
            return
        if not self.is_available():
            raise RuntimeError("ttyd binary not found on PATH")
        port = self._free_port()
        # -p <port>: listen on the picked free port.
        # -i 127.0.0.1: bind to loopback only — enforces REQ-0005 even
        #   when the cockpit's render endpoint is on 0.0.0.0.
        # -W: writable terminal (default is read-only since ttyd 1.6).
        # xterm.js client options ttyd forwards via -t key=value. Theme
        # values must be a JSON string per ttyd's --client-option docs.
        argv = [
            "ttyd",
            "-p", str(port),
            "-i", "127.0.0.1",
            "-W",
            "-b", TERMINAL_BASE_PATH.rstrip("/"),
            "-t", f"fontSize={_TERMINAL_FONT_SIZE}",
            "-t", f"fontFamily={_TERMINAL_FONT_FAMILY}",
            "-t", f"theme={json.dumps(_TERMINAL_THEME, separators=(',', ':'))}",
            "-t", "cursorBlink=true",
            "-t", "scrollback=5000",
            "-t", "disableLeaveAlert=true",
            *self.command,
        ]
        log.info(
            "terminal: starting ttyd port=%d cwd=%s argv=%s",
            port, self.working_dir, argv,
        )
        env = os.environ.copy()
        if self.cockpit_url:
            # The `cockpit` CLI (TASK-0049) reads COCKPIT_URL to know
            # where to POST focus / pin / toggle commands.
            env["COCKPIT_URL"] = self.cockpit_url
        self.process = subprocess.Popen(
            argv,
            cwd=str(self.working_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        atexit.register(self.stop)

    def stop(self) -> None:
        """Terminate the ttyd subprocess. Idempotent."""
        if self.process is None:
            return
        if self.process.poll() is not None:
            self.process = None
            return
        log.info("terminal: stopping ttyd (pid %s)", self.process.pid)
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        except Exception:
            log.exception("terminal: stop failed")
        self.process = None
        self.port = None
        self.url = None

    def info(self) -> dict[str, object]:
        """Return the JSON payload for ``/api/terminal``."""
        if os.environ.get("COCKPIT_DESKTOP") == "1":
            return {
                "enabled": False,
                "reason": "desktop mode — terminal is provided by the Electron shell (FEAT-0007).",
            }
        if not self.is_available():
            return {
                "enabled": False,
                "reason": "ttyd binary not found. Install with `brew install ttyd` (macOS) or your package manager.",
            }
        # Lazy start on first info() call. If start fails, surface the
        # reason rather than crashing the endpoint.
        try:
            self.start()
        except Exception as exc:  # pragma: no cover — runtime failure
            log.exception("terminal: start failed")
            return {"enabled": False, "reason": f"ttyd start failed: {exc}"}
        return {
            "enabled": True,
            # Same-origin URL — the iframe loads through the cockpit's
            # /_terminal/* proxy (TASK-0047). The actual ttyd port lives
            # in self.port but isn't reachable directly from the browser.
            "url": TERMINAL_BASE_PATH,
            "command": self.command,
        }
