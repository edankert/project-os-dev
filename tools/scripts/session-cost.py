#!/usr/bin/env python3
"""How much of a session's note work went to notes that were already finished.

project-os-dev ISS-0100 (TASK-0168), the baseline PHASE-0009 is measured
against. For every Claude Code transcript of a repo it counts three kinds of
contact with a note, and how many of each were with a note that was already
finished when the session started:

  opened    a note named in a Read, or in a cat/sed/head/tail/less command
  edited    a note named in an Edit, Write or MultiEdit, or in a shell command
            that writes (sed -i, a redirect, tee, a Python write, mv, cp)
  surfaced  a note named in the result of a search (Grep, or grep/rg in Bash):
            put in front of the agent, which then had to judge it

"Finished" is the note's status at the last commit before the session began,
read from git, so a note closed during the session counts as live. Terminal
statuses are `TERMINAL` below.

PRIVACY -- project-os-dev RISK-0004: prints counts only, never transcript text
or note contents, as rank-bench-sessions.py does.

Usage:
    session-cost.py                          # this repo's sessions
    session-cost.py --repo-root ../your-trainer [--since 2026-09-01] [--json]
    session-cost.py --projects-dir DIR       # transcripts elsewhere (tests)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
NOTE = re.compile(r"(docs/[A-Za-z0-9_./-]*?([A-Z]{2,6}-\d{3,4}[a-z]?)[A-Za-z0-9_.-]*\.md)")
READ_CMD = re.compile(r"\b(cat|sed|head|tail|less|more|bat)\b")
SEARCH_CMD = re.compile(r"\b(grep|rg|ag|ack)\b")
#: A shell command that writes a file: agents here edit notes through Bash
#: (sed -i, a redirect, a Python write) far more often than with Edit.
WRITE_CMD = re.compile(r"sed\s+-i|>\s*\S*docs/|\btee\b|write_text\(|\.write\(|\bmv\b|\bcp\b")
TERMINAL = {"done", "fixed", "cancelled", "superseded", "declined", "merged",
            "implemented", "retired", "released", "closed"}
STATUS = re.compile(r"^status:\s*[\"']?([\w-]+)", re.M)


def git(repo, *args, stdin=None):
    return subprocess.run(["git", *args], cwd=repo, input=stdin, capture_output=True,
                          text=True).stdout


def project_dir(projects, repo):
    return projects / str(repo).replace("/", "-")


def parse_iso(text):
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def notes_in(text):
    """Note paths named in a string, as repo-relative paths."""
    out = set()
    for m in NOTE.finditer(text or ""):
        path = m.group(1)
        out.add(path[path.index("docs/"):])
    return out


def read_session(path):
    """(start time, opened, edited, surfaced) for one transcript."""
    start = None
    opened, edited, surfaced = set(), set(), set()
    search_ids = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if start is None:
                start = parse_iso(rec.get("timestamp", ""))
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name, args = block.get("name", ""), block.get("input") or {}
                    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                        edited |= notes_in(str(args.get("file_path", "")))
                    elif name == "Read":
                        opened |= notes_in(str(args.get("file_path", "")))
                    elif name == "Grep":
                        search_ids.add(block.get("id"))
                    elif name == "Bash":
                        cmd = str(args.get("command", ""))
                        if SEARCH_CMD.search(cmd):
                            search_ids.add(block.get("id"))
                        if WRITE_CMD.search(cmd):
                            edited |= notes_in(cmd)      # sed -i edits; it is not a read
                        elif READ_CMD.search(cmd):
                            opened |= notes_in(cmd)
                elif block.get("type") == "tool_result" and block.get("tool_use_id") in search_ids:
                    body = block.get("content")
                    text = body if isinstance(body, str) else json.dumps(body)
                    surfaced |= notes_in(text)
    return start, opened, edited, surfaced


def commit_before(repo, when):
    if when is None:
        return ""
    stamp = when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return git(repo, "rev-list", "-1", "--before=" + stamp, "HEAD").strip()


def statuses_at(repo, rev, paths):
    """{path: status} at a commit, read in one `git cat-file --batch` call."""
    if not rev or not paths:
        return {}
    paths = sorted(paths)
    raw = subprocess.run(["git", "cat-file", "--batch"], cwd=repo, capture_output=True,
                         input="".join("%s:%s\n" % (rev, p) for p in paths).encode()).stdout
    out, pos = {}, 0
    for path in paths:
        end = raw.index(b"\n", pos)
        header = raw[pos:end].decode(errors="replace").split()
        pos = end + 1
        if len(header) < 3 or header[1] == "missing":
            continue
        size = int(header[2])
        body = raw[pos:pos + size].decode(errors="replace")
        pos += size + 1
        m = STATUS.search(body.split("\n---", 1)[0])
        if m:
            out[path] = m.group(1)
    return out


def measure(repo, projects, since=None):
    sessions = []
    folder = project_dir(projects, repo)
    for path in sorted(folder.glob("*.jsonl")) if folder.is_dir() else []:
        start, opened, edited, surfaced = read_session(path)
        if since and start and start.date() < since:
            continue
        if not (opened or edited or surfaced):
            continue
        status = statuses_at(repo, commit_before(repo, start), opened | edited | surfaced)
        row = {"session": path.stem[:8], "start": start.isoformat() if start else ""}
        for kind, notes in (("opened", opened), ("edited", edited), ("surfaced", surfaced)):
            known = [n for n in notes if n in status]
            row[kind] = len(known)
            row[kind + "_finished"] = sum(1 for n in known if status[n] in TERMINAL)
        sessions.append(row)
    total = {k: sum(r[k] for r in sessions) for k in
             ("opened", "opened_finished", "edited", "edited_finished", "surfaced", "surfaced_finished")}
    return {"repo": repo.name, "sessions": len(sessions), "total": total, "per_session": sessions}


def share(done, whole):
    return "%d of %d (%s)" % (done, whole, "%d%%" % round(100 * done / whole) if whole else "n/a")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--projects-dir", default=str(PROJECTS))
    ap.add_argument("--since", default="", help="YYYY-MM-DD: only sessions starting on or after")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo_root).resolve()
    since = dt.date.fromisoformat(args.since) if args.since else None
    result = measure(repo, Path(args.projects_dir), since)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    t = result["total"]
    print("%s: %d sessions that touched a note" % (result["repo"], result["sessions"]))
    print("  opened:   %s finished" % share(t["opened_finished"], t["opened"]))
    print("  edited:   %s finished" % share(t["edited_finished"], t["edited"]))
    print("  surfaced: %s finished (notes a search put in front of the agent)" % share(t["surfaced_finished"], t["surfaced"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
