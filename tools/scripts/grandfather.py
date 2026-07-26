#!/usr/bin/env python3
"""Generate tools/GRANDFATHERED.yaml — the debt a gate carried when it was promoted.

ADR-0011 clause 3 says a check is promoted to error only once the fleet carries
zero findings for it, so promotion is a no-op on the day it lands. Where that is
not achievable in one pass (clearing REQ-BOXES means ~900 individual criterion
judgements about work that closed months ago), the honest alternative is an
explicit, auditable exemption list rather than a silent severity downgrade.

This replaces the previous date-based grandfathering (`FEATURE_REQ_GATE_FROM`
compared against each note's `updated:`), which had two defects:

  * it keyed on when a note was last *edited*, not when the item closed, so
    editing a grandfathered note for any reason re-armed the gate on it;
  * a stale or malformed `updated:` silently exempted an item forever.

The ledger names IDs. It only shrinks — delete an entry when the debt is paid —
and an entry for an item that no longer violates anything is inert.

Run with no ledger present (or `--refresh`, which ignores the existing one) so
the generator sees the true violation set.

Usage:
    grandfather.py [--repo-root PATH] [--write] [--refresh]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

#: Gates that support grandfathering. VERIFY joined the list when ADR-0008 made
#: issue `fixed` terminal, which newly gated every issue that had been sitting in
#: the old `fixed` limbo — debt that predates the promotion by months.
GATES = ("VERIFY", "REQ-BOXES", "FEATURE-REQ", "TEST-FIELDS", "WAIVER")

LEDGER_REL = "tools/GRANDFATHERED.yaml"
_ID_RE = re.compile(r"\b((?:ADR|FEAT|ISS|PHASE|REQ|RISK|REL|TASK|TST|WF)-\d{2,})\b")
_LINE_RE = re.compile(r"^(?:ERROR|WARN)\s+\[([A-Z-]+)\]\s+(.*)$")


def collect(root: Path, refresh: bool) -> dict[str, dict[str, str]]:
    """Run the validator with no ledger in force and bucket findings by gate."""
    ledger = root / LEDGER_REL
    stashed = None
    if refresh and ledger.is_file():
        fd, stashed = tempfile.mkstemp(prefix="grandfather-", suffix=".yaml")
        os.close(fd)
        ledger.replace(stashed)
    try:
        proc = subprocess.run(
            [sys.executable, str(root / "tools/scripts/validate-docs.py"), "--repo-root", str(root)],
            capture_output=True, text=True,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
    finally:
        if stashed:
            Path(stashed).replace(ledger)

    found: dict[str, dict[str, str]] = {g: {} for g in GATES}
    for line in out.splitlines():
        m = _LINE_RE.match(line.strip())
        if not m:
            continue
        gate, msg = m.group(1), m.group(2)
        if gate not in GATES:
            continue
        ids = _ID_RE.findall(msg)
        if ids:
            # The first ID in the message is the item being gated; the rest are
            # the things it is gated *on* (a linked test, an owned requirement).
            found[gate].setdefault(ids[0], msg.strip())
    return found


def render(found: dict[str, dict[str, str]], cutover: str) -> str:
    total = sum(len(v) for v in found.values())
    lines = [
        "# Grandfather ledger — debt each gate carried when it was promoted to error.",
        "#",
        "# Read by tools/scripts/validate-docs.py. An item listed here reports as a",
        "# WARNING for that gate; every other item is an ERROR. There is no date-based",
        "# exemption: editing a listed note does not re-arm the gate on it, and editing",
        "# an unlisted note does not exempt it.",
        "#",
        "# This file only shrinks. When an item's debt is paid, delete its line — a",
        "# stale entry is inert but misleading. Regenerate with:",
        "#     python3 tools/scripts/grandfather.py --write --refresh",
        "#",
        "# ADR-0011 clause 3 prefers clearing debt to listing it. Entries here are an",
        "# admission that the debt was not cleared, and each one is a small backlog item.",
        "version: 1",
        'cutover: "%s"' % cutover,
        "count: %d" % total,
        "gates:",
    ]
    for gate in GATES:
        entries = found.get(gate) or {}
        if not entries:
            lines.append("  %s: {}" % gate)
            continue
        lines.append("  %s:" % gate)
        for item_id in sorted(entries):
            reason = entries[item_id].replace('"', "'")
            if len(reason) > 150:
                reason = reason[:147] + "..."
            lines.append('    %s: "%s"' % (item_id, reason))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate the grandfather ledger.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--write", action="store_true", help="Write the ledger (default: print)")
    ap.add_argument("--refresh", action="store_true",
                    help="Ignore any existing ledger while collecting, so the true violation set is seen")
    ap.add_argument("--cutover", default="2026-07-25")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not (root / "SNAPSHOT.yaml").is_file():
        print("grandfather: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 2

    found = collect(root, args.refresh)
    text = render(found, args.cutover)
    total = sum(len(v) for v in found.values())
    if args.write:
        if total == 0:
            ledger = root / LEDGER_REL
            if ledger.is_file():
                ledger.unlink()
                print("grandfather: %s — no debt; ledger removed" % root.name)
            else:
                print("grandfather: %s — no debt; no ledger needed" % root.name)
            return 0
        (root / LEDGER_REL).write_text(text, encoding="utf-8")
        print("grandfather: %s — %d entr%s (%s)" % (
            root.name, total, "y" if total == 1 else "ies",
            ", ".join("%s=%d" % (g, len(found[g])) for g in GATES if found[g])))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
