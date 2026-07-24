"""Tiny ``cockpit`` CLI for in-terminal agents (TASK-0049).

Designed to be called from the LLM CLI session running inside the
cockpit's embedded terminal. Discovers the cockpit's HTTP base URL via
the ``COCKPIT_URL`` env var (set by ``terminal.py`` when spawning
ttyd's shell). Commands POST to the cockpit server which then
broadcasts an SSE event to every open browser tab.

Example::

    cockpit focus FEAT-0006
    cockpit focus docs/features/cockpit/FEAT-0006-Cockpit-Layout.md
    cockpit focus /docs/changes/CHG-20260522-Foo.md

Subcommands are intentionally minimal in v1 (``focus`` only); ``pin``,
``toggle``, ``query`` etc. are reserved for follow-ups.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _walk_up_for_discovery(start: Path) -> str:
    """Walk up from ``start`` looking for ``.cockpit/url`` — the file the
    cockpit server writes on startup so any-terminal CLIs can find it.

    Returns the URL string (without trailing slash) or ``""`` if no
    discovery file is found before reaching the filesystem root.
    """
    here = start.resolve()
    while True:
        candidate = here / ".cockpit" / "url"
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8").strip().rstrip("/")
            except OSError:
                return ""
        parent = here.parent
        if parent == here:
            return ""
        here = parent


def _default_base_url() -> str:
    """Cockpit URL, discovered in priority order:

    1. ``COCKPIT_URL`` env (set automatically when the embedded ttyd
       spawns its shell).
    2. ``<ancestor>/.cockpit/url`` walking up from CWD (lets an LLM in
       any terminal under the project tree drive a running cockpit).
    """
    env = os.environ.get("COCKPIT_URL", "").strip().rstrip("/")
    if env:
        return env
    return _walk_up_for_discovery(Path.cwd())


_NO_COCKPIT_MSG = (
    "cockpit: no running cockpit found. Either:\n"
    "  - run this from inside a directory served by a cockpit "
    "(it writes .cockpit/url at startup), or\n"
    "  - set COCKPIT_URL=http://host:port explicitly."
)


def _post_json(base: str, path: str, body: dict) -> tuple[int, dict]:
    """POST JSON to the cockpit; return (status, parsed-body)."""
    if not base:
        print(_NO_COCKPIT_MSG, file=sys.stderr)
        return 0, {}
    url = base + path
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
        except Exception:
            raw = ""
        status = exc.code
    except urllib.error.URLError as exc:
        print(f"cockpit: cannot reach {url}: {exc.reason}", file=sys.stderr)
        return 0, {}
    try:
        parsed = json.loads(raw) if raw else {}
    except ValueError:
        parsed = {"raw": raw}
    return status, parsed


def _get_json(base: str, path: str) -> tuple[int, dict]:
    """GET JSON from the cockpit; return (status, parsed-body)."""
    if not base:
        print(_NO_COCKPIT_MSG, file=sys.stderr)
        return 0, {}
    url = base + path
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
        except Exception:
            raw = ""
        status = exc.code
    except urllib.error.URLError as exc:
        print(f"cockpit: cannot reach {url}: {exc.reason}", file=sys.stderr)
        return 0, {}
    try:
        parsed = json.loads(raw) if raw else {}
    except ValueError:
        parsed = {"raw": raw}
    return status, parsed


def cmd_focus(args: argparse.Namespace) -> int:
    base = args.cockpit_url or _default_base_url()
    status, body = _post_json(base, "/api/cockpit/focus", {"target": args.target})
    if status == 0:
        return 1
    if status >= 400 or not body.get("ok"):
        msg = body.get("error") or f"HTTP {status}"
        print(f"cockpit focus: {msg}", file=sys.stderr)
        return 1
    print(f"cockpit -> {body.get('url')}")
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    base = args.cockpit_url or _default_base_url()
    status, body = _get_json(base, "/api/cockpit/state")
    if status == 0:
        return 1
    if status >= 400:
        print(f"cockpit state: HTTP {status}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0
    _print_state_pretty(body)
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    base = args.cockpit_url or _default_base_url()
    status, body = _get_json(base, "/api/cockpit/state")
    if status == 0:
        return 1
    if status >= 400:
        print(f"cockpit history: HTTP {status}", file=sys.stderr)
        return 1
    events = body.get("history") or []
    if args.limit and args.limit > 0:
        events = events[: args.limit]
    if args.json:
        print(json.dumps(events, ensure_ascii=False, indent=2))
        return 0
    if not events:
        print("(no recent navigation)")
        return 0
    for ev in events:
        src = ev.get("source", "?")
        ts = ev.get("ts", "")
        url = ev.get("url", "")
        tail = ""
        if src == "agent" and ev.get("target"):
            tail = f"  [{ev['target']}]"
        elif src == "user" and ev.get("tab_id"):
            tail = f"  [tab {ev['tab_id'][:8]}]"
        print(f"{ts}  {src:5s}  {url}{tail}")
    return 0


def _print_state_pretty(body: dict) -> None:
    agent = body.get("agent_focus")
    user = body.get("user_view")
    tabs = body.get("tabs") or []
    history = body.get("history") or []
    if agent:
        print(
            f"agent focus : {agent.get('target', '?')}  ({agent.get('url', '')})  "
            f"@ {agent.get('ts', '')}"
        )
    else:
        print("agent focus : (none yet)")
    if user:
        print(f"user view   : {user.get('url', '')}  @ {user.get('ts', '')}")
    else:
        print("user view   : (no live tabs)")
    if tabs:
        print(f"tabs        : {len(tabs)} live")
        for t in tabs:
            follow = "follow" if t.get("following") else "manual"
            print(
                f"  - {t.get('tab_id', '')[:8]}  {follow:6s}  {t.get('url', '')}  "
                f"@ {t.get('last_seen', '')}"
            )
    else:
        print("tabs        : 0 live (no open cockpit tabs)")
    if history:
        recent = history[:5]
        print(f"history     : {len(history)} events (showing {len(recent)})")
        for ev in recent:
            src = ev.get("source", "?")
            tail = ""
            if src == "agent" and ev.get("target"):
                tail = f"  [{ev['target']}]"
            print(f"  - {src:5s}  {ev.get('url', '')}{tail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cockpit",
        description="Drive the project-os-cockpit window from inside the embedded terminal.",
    )
    parser.add_argument(
        "--cockpit-url",
        default=None,
        help="Override COCKPIT_URL env var (e.g. http://127.0.0.1:8770).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_focus = sub.add_parser(
        "focus",
        help="Navigate every open cockpit tab to a note (by ID, path, or URL).",
    )
    p_focus.add_argument(
        "target",
        help="Note ID (FEAT-0006), docs-rel path, or full URL (/docs/...).",
    )
    p_focus.set_defaults(func=cmd_focus)

    p_state = sub.add_parser(
        "state",
        help="Show current cockpit state (agent focus, user view, live tabs).",
    )
    p_state.add_argument(
        "--json", action="store_true",
        help="Emit the raw JSON snapshot instead of the human-readable form.",
    )
    p_state.set_defaults(func=cmd_state)

    p_history = sub.add_parser(
        "history",
        help="Show recent navigation events (both agent focuses and user nav).",
    )
    p_history.add_argument(
        "--limit", type=int, default=10,
        help="Maximum events to show (default: 10).",
    )
    p_history.add_argument(
        "--json", action="store_true",
        help="Emit the raw JSON list instead of the human-readable form.",
    )
    p_history.set_defaults(func=cmd_history)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
