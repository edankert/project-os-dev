#!/usr/bin/env python3
"""Score a note ranker against what real sessions actually read.

The companion benchmark to `rank-bench.py`, and the one that matches what a
ranker is for. `rank-bench.py` labels each commit with the notes it *wrote*,
which is the wrong target: nobody wants a tool that predicts which notes a
commit will touch. This one asks the question the ranker exists to answer --
**at session start, would it have surfaced the notes this session went on to
read?**

  query   the session's opening prompt, as typed
  labels  the notes that session opened, anywhere in its transcript
  corpus  that repository's notes as of the commit the session started from
  budget  however many distinct notes the session actually read

So a score of 0.6 means: of the notes this session needed badly enough to open,
the ranker would have put six in ten in front of it before it started looking.

PRIVACY -- project-os-dev RISK-0004
-----------------------------------
Transcripts hold whatever was typed and read in past sessions. This program
prints counts, note IDs and recalls, and never transcript text: not the prompt
it scores on, not a file's contents, not a session's words. The prompt is read
into memory, tokenised and dropped. Keep it that way -- a benchmark that leaks
a credential into a committed report has done more harm than any ranking gains.

WHAT IT CANNOT SEE
------------------
Only sessions that opened at least two notes can be scored, and in a typical
project-os repo that is a minority -- 11 of 96 transcripts in project-os-dev.
The other 85 never touched a note: they were questions, shell work, or sessions
about code rather than records. That is not an extraction gap to be fixed. It
is what the sample is, and the run says so.

Reads are found by scanning each record for `docs/.../<ID>...md`, which catches
a note opened with `Read`, with `cat` or `sed` in a Bash command, by a
subagent, or named in a tool result. In these repos Bash outnumbers Read forty
to one, so a `file_path`-only scan finds a fraction of the truth.

Usage:
    rank-bench-sessions.py                       # sessions of the current repo
    rank-bench-sessions.py --repo-root ../your-trainer
    rank-bench-sessions.py --ranker path/to/other-ranker.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECTS = Path.home() / ".claude" / "projects"

# A note opened anywhere in a record: Read's file_path, a cat/sed/grep inside a
# Bash command, a subagent's prompt, a tool result listing a path.
NOTE_IN_RECORD = re.compile(
    r"docs/[^\s\"',:;)\]]*?([A-Z]{2,6}-\d{3,4})[^\s\"',:;)\]]*\.md")
ISO = re.compile(r'"timestamp":"([^"]+)"')

# Text that is not the user speaking: hook output, command caveats, the system
# reminders the harness injects. Scoring on these would measure the harness.
NOT_A_PROMPT = (
    "<local-command-caveat>", "<system-reminder>", "Caveat: The messages below",
    "[Request interrupted", "<command-name>", "<command-message>",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo,
                          capture_output=True, text=True).stdout


def project_dir_for(repo: Path) -> Path:
    """Claude Code stores a repo's transcripts under a slug of its path."""
    return PROJECTS / str(repo).replace("/", "-")


def parse_iso(text: str):
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_session(path: Path) -> tuple[str, set[str], object]:
    """(opening prompt, notes opened, start time) for one transcript.

    The prompt is returned for tokenising by the caller and is never printed.
    """
    prompt = ""
    opened: set[str] = set()
    start = None
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if "docs/" in line:
                opened |= set(NOTE_IN_RECORD.findall(line))
            stamp = ISO.search(line)
            if stamp and start is None:
                start = parse_iso(stamp.group(1))
            if prompt or '"user"' not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("type") != "user" or record.get("isSidechain"):
                continue
            content = (record.get("message") or {}).get("content")
            candidates = []
            if isinstance(content, str):
                candidates = [content]
            elif isinstance(content, list):
                candidates = [b.get("text", "") for b in content
                              if isinstance(b, dict) and b.get("type") == "text"]
            for text in candidates:
                text = text.strip()
                if len(text) < 25 or any(m in text for m in NOT_A_PROMPT):
                    continue
                prompt = text
                break
    return prompt, opened, start


def commit_before(repo: Path, when) -> str:
    """The commit the session started from. A session that began mid-afternoon
    saw the tree as of the last commit before it, not as of today."""
    if when is None:
        return "HEAD"
    stamp = when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    sha = git(repo, "rev-list", "-1", f"--before={stamp}", "HEAD").strip()
    return sha or "HEAD"


def corpus_at(repo: Path, rev: str, ranker):
    """Shared with rank-bench.py by intent, duplicated by necessity: that file
    is a script, not an importable module. If a third benchmark needs this,
    lift both copies into one place rather than adding a third."""
    listing = git(repo, "ls-tree", "-r", rev, "--", "docs")
    wanted = []
    for line in listing.splitlines():
        if not line.endswith(".md") or "__templates__" in line:
            continue
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) < 3:
            continue
        note_id = ranker.note_id_from_filename(path.rsplit("/", 1)[-1])
        if note_id:
            wanted.append((parts[2], path, note_id))
    if not wanted:
        return {}
    proc = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=repo,
        input=("\n".join(b for b, _, _ in wanted) + "\n").encode(),
        capture_output=True)
    out, notes, cursor = proc.stdout, {}, 0
    for _blob, path, note_id in wanted:
        end = out.find(b"\n", cursor)
        if end == -1:
            break
        header = out[cursor:end].split()
        if len(header) < 3:
            cursor = end + 1
            continue
        size = int(header[2])
        body = out[end + 1:end + 1 + size]
        cursor = end + 1 + size + 1
        notes.setdefault(note_id, ranker.parse_note(
            note_id, body.decode("utf-8", errors="replace"), path))
    return notes


def load_ranker(path: Path):
    spec = importlib.util.spec_from_file_location("ranker_under_test", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"rank-bench-sessions: cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module          # @dataclass needs this on 3.9
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score a ranker against what real sessions read.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--ranker", default=str(HERE / "rank-notes.py"))
    parser.add_argument("--min-notes", type=int, default=2,
                        help="skip sessions that opened fewer notes than this")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    transcripts = project_dir_for(repo)
    if not transcripts.is_dir():
        print(f"rank-bench-sessions: no transcripts for {repo} "
              f"(looked in {transcripts})", file=sys.stderr)
        return 1

    ranker = load_ranker(Path(args.ranker))
    files = sorted(transcripts.glob("*.jsonl"))
    rows = []
    skipped_few = skipped_noprompt = 0

    for path in files:
        prompt, opened, start = read_session(path)
        if len(opened) < args.min_notes:
            skipped_few += 1
            continue
        if not prompt:
            skipped_noprompt += 1
            continue
        rev = commit_before(repo, start)
        notes = corpus_at(repo, rev, ranker)
        if not notes:
            continue
        gold = {n for n in opened if n in notes}     # notes that existed then
        if len(gold) < args.min_notes:
            skipped_few += 1
            continue
        index = ranker.build_index(notes)
        budget = len(gold)
        ranked = index.rank(prompt, budget)
        recent = [n for n, _ in sorted(
            notes.items(), key=lambda kv: (kv[1].updated or "", kv[0]),
            reverse=True)][:budget]
        rows.append({
            "session": path.stem[:8],
            "corpus": len(notes),
            "opened": len(opened),
            "scorable": budget,
            "ranker": len(set(ranked) & gold) / budget,
            "floor": len(set(recent) & gold) / budget,
        })

    if not rows:
        print(f"rank-bench-sessions: none of {len(files)} transcripts opened "
              f"{args.min_notes}+ notes that still existed", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"repo": repo.name, "sessions": rows}, indent=2))
        return 0

    ranker_mean = statistics.mean(r["ranker"] for r in rows)
    floor_mean = statistics.mean(r["floor"] for r in rows)
    print()
    print("RANK-BENCH-SESSIONS -- would the ranker have surfaced what the session read?")
    print("=" * 78)
    print(f"  ranker        {Path(args.ranker).name}")
    print(f"  repo          {repo.name}")
    print(f"  transcripts   {len(files)} found, {len(rows)} scored")
    print(f"                {skipped_few} opened fewer than {args.min_notes} notes, "
          f"{skipped_noprompt} had no usable opening prompt")
    print(f"  query         each session's opening prompt (read, never printed "
          f"-- RISK-0004)")
    print(f"  labels        the notes that session opened, corpus pinned to the "
          f"commit it started from")
    print(f"  budget        each session scored at the number of notes it "
          f"actually read")
    print("=" * 78)
    print()
    print(f"  {'session':<10}{'corpus':>8}{'read':>6}{'scored':>8}{'ranker':>9}{'floor':>8}")
    for r in sorted(rows, key=lambda r: -r["scorable"]):
        print(f"  {r['session']:<10}{r['corpus']:>8}{r['opened']:>6}"
              f"{r['scorable']:>8}{r['ranker']:>9.2f}{r['floor']:>8.2f}")
    print(f"  {'MEAN':<10}{'':>8}{'':>6}{'':>8}{ranker_mean:>9.2f}{floor_mean:>8.2f}")
    print()
    verdict = ("the ranker beats recency" if ranker_mean > floor_mean
               else "recency beats the ranker" if floor_mean > ranker_mean
               else "the ranker ties recency")
    print(f"  On {len(rows)} sessions, {verdict}: "
          f"{ranker_mean:.3f} against {floor_mean:.3f}.")
    print(f"  n={len(rows)} is small. Run this in every project-os repo before "
          f"concluding anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
