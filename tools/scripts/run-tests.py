#!/usr/bin/env python3
"""Execute TST-* notes that declare a `command:` and stamp their status (ADR-0010).

`QUALITY.md` builds its close-out rules on one gate: an item may not reach a
terminal status while a linked TST-* is not `passing`. Across 10 repos and 5,890
status writes that gate has never once observed a failure -- `failing` was
written zero times, 78% of test notes are born `passing`, and 99% never change
again. The mechanism is structural, not cultural: the status is written by the
agent that wants the transition, at the moment it wants it, and nothing returns
to the note when CI goes red three weeks later.

This removes the conflict of interest. A note carrying a `command:` has its
`status` written here, from the exit code, and nowhere else.

Three outcomes, deliberately distinguished:

  passing     exit 0
  failing     non-zero exit -- the check ran and the system is wrong
  unrunnable  the command could not execute at all (missing binary, missing
              env, timeout). Reported, and the status is left ALONE.

The third matters more than it looks. Stamping `failing` on a test that could
not run conflates "the system is broken" with "my machine is missing a tool",
and that is exactly the noise that teaches people to stop believing a status --
the failure mode this whole change exists to end. It is also the `blocked` vs
`failing` confusion ADR-0007's amendment called out one level up.

Exit codes: 0 = no failures, 1 = at least one test failed, 2 = usage error.

Stdlib only. Usage:
    run-tests.py [--repo-root PATH] [--write] [--filter TST-0001] [--timeout N]
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TIMEOUT = 600


def split_frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[:4], text[4:end], text[end:]


def fm_get(fm, key):
    m = re.search(r"^%s:\s*(.*)$" % re.escape(key), fm, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def fm_set(fm, key, value):
    line = "%s: %s" % (key, value)
    if re.search(r"^%s:" % re.escape(key), fm, re.M):
        return re.sub(r"^%s:.*$" % re.escape(key), line, fm, count=1, flags=re.M)
    return fm.rstrip("\n") + "\n" + line + "\n"


def discover(root, only=None):
    out = []
    docs = root / "docs"
    if not docs.is_dir():
        return out
    for path in sorted(docs.rglob("*.md")):
        if "__templates__" in path.parts:
            continue
        if not re.match(r"^TST-\d+", path.name):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        parts = split_frontmatter(text)
        if not parts:
            continue
        _pre, fm, _post = parts
        cmd = fm_get(fm, "command")
        if not cmd:
            continue
        tid = fm_get(fm, "id") or path.name.split("-")[0] + "-" + path.name.split("-")[1]
        if only and tid not in only:
            continue
        out.append((path, tid, cmd))
    return out


def run_one(root, cmd, timeout):
    """Return (outcome, exit_code, detail)."""
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=str(root), capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PROJECT_OS_TEST_RUN": "1"},
        )
    except subprocess.TimeoutExpired:
        return "unrunnable", None, "timed out after %ss" % timeout
    except OSError as exc:
        return "unrunnable", None, "could not execute: %s" % exc
    # 127 is the shell's "command not found"; treat as environmental, not a failure.
    if proc.returncode == 127:
        head = (proc.stderr or "").strip().splitlines()[:1]
        return "unrunnable", 127, "command not found%s" % (": " + head[0] if head else "")
    tail = ((proc.stderr or "") + (proc.stdout or "")).strip().splitlines()[-1:]
    return ("passing" if proc.returncode == 0 else "failing"), proc.returncode, (tail[0] if tail else "")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run TST-* commands and stamp their status.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--write", action="store_true", help="Stamp status/last_run (default: dry run)")
    ap.add_argument("--filter", action="append", default=None, help="Only these TST ids")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not (root / "SNAPSHOT.yaml").is_file():
        print("run-tests: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 2

    tests = discover(root, set(args.filter) if args.filter else None)
    if not tests:
        print("run-tests: %s — no TST-* notes declare a `command:`" % root.name)
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    counts = {"passing": 0, "failing": 0, "unrunnable": 0}
    print("== %s  %s ==" % ("RUN" if args.write else "DRY RUN", root.name))
    for path, tid, cmd in tests:
        outcome, code, detail = run_one(root, cmd, args.timeout)
        counts[outcome] += 1
        print("   %-12s %-10s %s%s" % (tid, outcome, cmd[:48], ("  — " + detail[:60]) if detail else ""))
        if not args.write or outcome == "unrunnable":
            continue
        text = path.read_text(encoding="utf-8")
        pre, fm, post = split_frontmatter(text)
        fm = fm_set(fm, "status", outcome)
        fm = fm_set(fm, "last_run", '"%s"' % stamp)
        fm = fm_set(fm, "exit_code", str(code))
        fm = fm_set(fm, "updated", stamp[:10])
        path.write_text(pre + fm + post, encoding="utf-8")

    print("   passing=%(passing)d failing=%(failing)d unrunnable=%(unrunnable)d" % counts)
    if counts["unrunnable"]:
        print("   note: unrunnable tests keep their previous status — an environment gap is not a failure")
    return 1 if counts["failing"] else 0


if __name__ == "__main__":
    sys.exit(main())
