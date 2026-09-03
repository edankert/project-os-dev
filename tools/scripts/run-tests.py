#!/usr/bin/env python3
"""Run every TST-* note's `command:` and report the outcome.

A test that carries a `command:` records no verdict on its note (project-os-dev
ADR-0025; STATUSES.md [[test]]): this script runs it, prints passing / failing /
unrunnable per test, and exits 1 on any failure. In CI that exit code is the
verdict. It never writes to a note. An unrunnable command (exit 127, a missing
tool, a timeout) is an environment gap locally, reported and not counted as a
failure; in CI (the `CI` variable set) it fails the run, because a test CI
cannot run has no verdict, unless PROJECT_OS_ALLOW_UNRUNNABLE=1 accepts that.

Usage: run-tests.py [--repo-root DIR] [--filter TST-0001 ...] [--timeout SECONDS]
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
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
    ap = argparse.ArgumentParser(description="Run every TST-* command: and report; CI is the verdict (ADR-0025).")
    ap.add_argument("--repo-root", default=".")
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

    # ADR-0025 (project-os-dev): the runner never writes to a note. A test
    # with a command: records no verdict; this exit code, in CI, is the verdict.
    counts = {"passing": 0, "failing": 0, "unrunnable": 0}
    print("== RUN  %s ==" % root.name)
    for _path, tid, cmd in tests:
        outcome, _code, detail = run_one(root, cmd, args.timeout)
        counts[outcome] += 1
        print("   %-12s %-10s %s%s" % (tid, outcome, cmd[:48], ("  — " + detail[:60]) if detail else ""))

    print("   passing=%(passing)d failing=%(failing)d unrunnable=%(unrunnable)d" % counts)
    # Locally an unrunnable command (a missing sibling checkout, a missing
    # tool, a timeout) is an environment gap and not a failure. In CI it is a
    # red build, because CI is the verdict and a test CI cannot run has none;
    # set PROJECT_OS_ALLOW_UNRUNNABLE=1 to accept the gap deliberately.
    ci_value = (os.environ.get("CI") or "").strip().lower()
    in_ci = ci_value not in ("", "0", "false", "no") and not os.environ.get("PROJECT_OS_ALLOW_UNRUNNABLE")
    if counts["unrunnable"]:
        if in_ci:
            print("   CI cannot run these tests, so they have no verdict; check out what they need "
                  "(a sibling ../project-os for cross-repo commands) or set PROJECT_OS_ALLOW_UNRUNNABLE=1")
        else:
            print("   note: an unrunnable test is an environment gap, not a failure")
    return 1 if counts["failing"] or (in_ci and counts["unrunnable"]) else 0


if __name__ == "__main__":
    sys.exit(main())
