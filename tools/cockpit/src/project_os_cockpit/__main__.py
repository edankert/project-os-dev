"""CLI entry point for project-os-cockpit.

Real argument parsing arrives with TASK-0002 (this file). The bootstrap
(TASK-0001) shipped a ``--help``-only stub; this expands it to the actual
``<docs-root>`` + ``--bind`` / ``--port`` surface and starts the HTTP
server. Wikilink resolution (TASK-0003), live reload (FEAT-0002), and the
cockpit shell (FEAT-0006) layer on top in later tasks.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .server import DocsServer

log = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-os-cockpit",
        description=(
            "On-the-fly Markdown render server for project-os repos. "
            "Renders any .md note as a linked HTML page at request time — "
            "no build step."
        ),
    )
    parser.add_argument(
        "docs_root",
        nargs="?",
        type=Path,
        help="Path to the docs/ directory to serve (e.g. ./docs).",
    )
    parser.add_argument(
        "--bind",
        default="127.0.0.1",
        help="Address to bind the render endpoint to (default: 127.0.0.1; "
        "use 0.0.0.0 to expose it on your LAN).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the render endpoint (default: 8765).",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Suppress any browser auto-launch. Used by the Electron "
        "desktop shell, which loads the server URL itself. Currently a "
        "no-op (the server does not auto-launch a browser) but reserved "
        "for forward compatibility.",
    )
    parser.add_argument(
        "--shell-assets",
        type=Path,
        default=None,
        help="Directory holding the desktop shell's built renderer assets "
        "(desktop/dist/renderer). Passed by the Electron shell so design "
        "artifacts can link the stylesheet that styles the app's own "
        "widgets. Omitted when running standalone, where the route simply "
        "404s.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(list(argv))

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.docs_root is None:
        parser.error("docs_root is required (positional argument).")

    docs_root: Path = args.docs_root
    if not docs_root.exists():
        parser.error(f"docs root does not exist: {docs_root}")
    if not docs_root.is_dir():
        parser.error(f"docs root is not a directory: {docs_root}")

    shell_assets = args.shell_assets
    if shell_assets is not None and not shell_assets.is_dir():
        # A bad path is worth saying out loud rather than silently 404ing
        # every asset later — but not worth refusing to start over, since
        # the capability is optional.
        log.warning("shell assets dir does not exist, ignoring: %s", shell_assets)
        shell_assets = None

    server = DocsServer(
        docs_root=docs_root,
        bind=args.bind,
        port=args.port,
        shell_assets=shell_assets,
    )
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
