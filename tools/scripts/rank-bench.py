#!/usr/bin/env python3
"""Score a note ranker against ground truth this repository already contains.

project-os-dev REQ-0032: nothing may tell a session *these are the notes you
need* without saying how often it is right, measured at the budget it proposes,
beside the baseline it would replace. This is the measurement. `rank-notes.py`
is the thing measured, and `--ranker` scores a different one.

WHAT IT MEASURES AGAINST
------------------------
Commits. For each commit that touched between 2 and 12 notes, the commit
message is the query and the notes that commit touched are the labels. The repo
supplies both for free and neither was written to be a benchmark, which is most
of why they are worth using.

Two rows score the ranker and two score the alternatives:

  * the commit message as written,
  * the same message with item IDs stripped -- **the honest row**, because a
    query naming `FEAT-0034` hands the answer to the ranker's exact-ID boost
    and measures nothing,
  * the cold start: what a session holds after reading `SNAPSHOT.yaml`, which
    is what the ranker would replace,
  * a floor: the most recently updated notes, which is what "look at what
    changed lately" gets you without any ranking at all.

THE CAVEAT IS PART OF THE OUTPUT
--------------------------------
These labels are the notes each commit **wrote**, not the notes its author
read. Close-out mechanically touches the task note and the snapshot, so part of
every label set is output rather than input. The bias falls on every row
equally, so comparing rows is sound; reading one row as "N% of what you needed"
is not. That sentence prints with the table and is not optional: a reader who
sees 0.77 without it has been misled by this program.

EVERY COMMIT IS SCORED AGAINST ITS OWN CORPUS
---------------------------------------------
The notes are read at each commit's parent, never from the working tree. This
is not fussiness. An earlier prototype indexed the working tree while scoring
labels from the past, and writing the eleven planning notes for this very
feature moved the floor row from 0.219 to 0.161 within hours -- eleven notes
dated today took eleven of the twenty-four floor slots, where they can never
match a commit made before they existed. Documenting the work silently degraded
the benchmark measuring it. Reading each commit's own corpus removes that, and
makes a re-run at the same commit reproducible.

Usage:
    rank-bench.py                        # default run, no arguments needed
    rank-bench.py --commits 200 --quick
    rank-bench.py --ranker path/to/other-ranker.py
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUDGETS = (5, 10, 24, 50)

CAVEAT = (
    "Labels are the notes each commit WROTE, not the notes its author read.\n"
    "  Close-out mechanically touches the task note and the snapshot, so part of every\n"
    "  label set is output rather than input. The bias falls on every row equally:\n"
    "  compare rows, and do not read a row as \"N% of what you needed to read\"."
)

ID_IN_TEXT = re.compile(r"\b[A-Z]{2,6}-\d{3,4}\b")


# ---------------------------------------------------------------- git plumbing

def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True)
    return result.stdout


def commit_cases(repo: Path, depth: int, lo: int, hi: int,
                 ranker_mod) -> list[tuple[str, str, set[str]]]:
    """[(sha, subject, {note ids touched})] for commits touching lo..hi notes.

    The window matters. A commit touching one note is usually a typo fix with
    nothing to rank; one touching forty is a bulk migration whose "query" is a
    sentence about none of them.
    """
    log = git(repo, "log", f"-{depth}", "--pretty=format:@@@%H|%s",
              "--name-only", "--", "docs")
    cases: list[tuple[str, str, set[str]]] = []
    sha = subject = None
    touched: set[str] = set()
    for line in log.splitlines():
        if line.startswith("@@@"):
            if sha and touched:
                cases.append((sha, subject, set(touched)))
            sha, subject = line[3:].split("|", 1)
            touched = set()
        elif line.strip().endswith(".md") and sha:
            note_id = ranker_mod.note_id_from_filename(line.rsplit("/", 1)[-1])
            if note_id:
                touched.add(note_id)
    if sha and touched:
        cases.append((sha, subject, set(touched)))
    return [c for c in cases if lo <= len(c[2]) <= hi]


def corpus_at(repo: Path, rev: str, ranker_mod) -> dict:
    """Every note under `docs/` as it stood at `rev`, keyed by ID.

    Two subprocesses per commit rather than one per file: `ls-tree` for the
    blob ids, then a single `cat-file --batch` streaming all of them. Reading
    350 notes one `git show` at a time would be 30,000 processes over a full
    run.
    """
    listing = git(repo, "ls-tree", "-r", rev, "--", "docs")
    wanted: list[tuple[str, str, str]] = []   # (blob, path, note id)
    for line in listing.splitlines():
        if not line.endswith(".md") or "__templates__" in line:
            continue
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) < 3:
            continue
        note_id = ranker_mod.note_id_from_filename(path.rsplit("/", 1)[-1])
        if note_id:
            wanted.append((parts[2], path, note_id))
    if not wanted:
        return {}

    # Bytes, not text. `cat-file --batch` sizes its records in bytes, and these
    # notes are full of em-dashes: decoding the whole stream first makes every
    # size wrong by however many multi-byte characters preceded it, and the
    # cursor walks off into the middle of a blob.
    proc = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=repo,
        input=("\n".join(blob for blob, _, _ in wanted) + "\n").encode(),
        capture_output=True)
    out = proc.stdout

    notes: dict = {}
    cursor = 0
    for _blob, path, note_id in wanted:
        header_end = out.find(b"\n", cursor)
        if header_end == -1:
            break
        header = out[cursor:header_end].split()
        if len(header) < 3:                      # "<sha> missing"
            cursor = header_end + 1
            continue
        size = int(header[2])
        body = out[header_end + 1:header_end + 1 + size]
        cursor = header_end + 1 + size + 1       # trailing newline
        if note_id not in notes:
            notes[note_id] = ranker_mod.parse_note(
                note_id, body.decode("utf-8", errors="replace"), path)
    return notes


# ------------------------------------------------------------------ baselines

def snapshot_at(repo: Path, rev: str) -> tuple[set[str], list[str], int]:
    """What a cold session holds after reading `SNAPSHOT.yaml` at `rev`: the IDs
    in its focus block, every item it lists in file order, and the file's size.

    A commit whose parent has no snapshot returns a size of 0. The caller
    counts those and reports them rather than dropping them quietly -- early
    history predates the file, and a baseline silently computed over fewer
    commits than the ranker is not a baseline.
    """
    text = git(repo, "show", f"{rev}:SNAPSHOT.yaml")
    if not text:
        return set(), [], 0
    focus_block = re.search(r"^focus:\n((?:[ \t]+.*\n)+)", text, re.M)
    focus = set(ID_IN_TEXT.findall(focus_block.group(1))) if focus_block else set()
    items: list[str] = []
    for m in re.finditer(r"^\s{4}([A-Z]{2,6}-\d{3,4}):\s*$", text, re.M):
        if m.group(1) not in items:
            items.append(m.group(1))
    return focus, items, len(text.encode())


def most_recent(notes: dict, k: int) -> list[str]:
    return [n for n, _ in sorted(
        notes.items(), key=lambda kv: (kv[1].updated or "", kv[0]), reverse=True)][:k]


def strip_ids(text: str) -> str:
    return ID_IN_TEXT.sub("", text)


def recall(got, gold) -> float:
    return len(set(got) & gold) / len(gold) if gold else 0.0


# ----------------------------------------------------------------------- main

def load_ranker(path: Path):
    spec = importlib.util.spec_from_file_location("ranker_under_test", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"rank-bench: cannot load ranker at {path}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves annotations through
    # sys.modules[cls.__module__], which on 3.9 raises AttributeError for a
    # module that was never registered.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for name in ("build_index", "parse_note", "note_id_from_filename"):
        if not hasattr(module, name):
            raise SystemExit(
                f"rank-bench: {path} has no {name}(); see rank-notes.py "
                f"'THE INTERFACE rank-bench.py USES'")
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score a note ranker against this repo's own history.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--ranker", default=str(HERE / "rank-notes.py"))
    parser.add_argument("--commits", type=int, default=300,
                        help="how far back to look for labelled commits")
    parser.add_argument("--min-notes", type=int, default=2)
    parser.add_argument("--max-notes", type=int, default=12)
    parser.add_argument("--quick", action="store_true",
                        help="score the 25 most recent qualifying commits only")
    parser.add_argument("--no-sessions", action="store_true",
                        help="skip the session benchmark (rank-bench-sessions.py), "
                             "which is otherwise run after the commit one so a "
                             "single command reports both")
    parser.add_argument("--worktree", action="store_true",
                        help="DIAGNOSTIC: index the working tree instead of each "
                             "commit's own corpus. This leaks the future into the "
                             "index -- a note's present text was written partly BY "
                             "the commit being scored -- and inflates every ranker "
                             "row. Here to measure that inflation, never to report.")
    args = parser.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    if not (repo / ".git").exists():
        print(f"rank-bench: {repo} is not a git repository", file=sys.stderr)
        return 2

    ranker = load_ranker(Path(args.ranker))
    cases = commit_cases(repo, args.commits, args.min_notes, args.max_notes, ranker)
    if args.quick:
        cases = cases[:25]
    if not cases:
        print("rank-bench: no commit touched between "
              f"{args.min_notes} and {args.max_notes} notes in the last "
              f"{args.commits} commits -- nothing to score", file=sys.stderr)
        return 1

    head = git(repo, "rev-parse", "--short", "HEAD").strip()
    worktree_notes = ranker.load_worktree(repo) if args.worktree else None
    rows = {key: {k: [] for k in BUDGETS}
            for key in ("as_written", "stripped", "snapshot_all",
                        "snapshot_order", "focus", "floor")}
    corpus_sizes = []
    snapshot_sizes: list[int] = []
    snapshot_items: list[int] = []
    no_snapshot = 0
    started = time.perf_counter()

    for done, (sha, subject, gold) in enumerate(cases, 1):
        parent = f"{sha}^"
        notes = worktree_notes if args.worktree else corpus_at(repo, parent, ranker)
        if not notes:
            continue
        corpus_sizes.append(len(notes))
        index = ranker.build_index(notes)
        focus, items, snap_bytes = snapshot_at(repo, parent)
        if snap_bytes:
            snapshot_sizes.append(snap_bytes)
            snapshot_items.append(len(items))
        else:
            no_snapshot += 1
        as_written = index.score(subject)
        stripped = index.score(strip_ids(subject))
        for k in BUDGETS:
            rows["as_written"][k].append(
                recall([n for s, n in as_written[:k] if s > 0], gold))
            rows["stripped"][k].append(
                recall([n for s, n in stripped[:k] if s > 0], gold))
            rows["snapshot_order"][k].append(recall(items[:k], gold))
            rows["snapshot_all"][k].append(recall(items, gold))
            rows["focus"][k].append(recall(focus, gold))
            rows["floor"][k].append(recall(most_recent(notes, k), gold))
        if done % 20 == 0:
            print(f"  ... {done}/{len(cases)} commits", file=sys.stderr)

    elapsed = time.perf_counter() - started
    scored = len(rows["stripped"][BUDGETS[0]])
    if not scored:
        print("rank-bench: every commit's parent was unreadable", file=sys.stderr)
        return 1

    def mean(key: str, k: int) -> float:
        return statistics.mean(rows[key][k])

    print()
    print("RANK-BENCH -- recall against this repository's own commits")
    print("=" * 78)
    print(f"  ranker        {Path(args.ranker).name}")
    provenance = ("WORKING TREE -- DIAGNOSTIC, leaks the future, do not report"
                  if args.worktree else "each commit scored against its own parent's corpus")
    print(f"  repo          {repo.name} at {head} ({provenance})")
    print(f"  labelled set  {scored} commits touching {args.min_notes}-"
          f"{args.max_notes} notes, from the last {args.commits}")
    print(f"  corpus        {min(corpus_sizes)}-{max(corpus_sizes)} notes "
          f"depending on the commit")
    if snapshot_sizes:
        print(f"  baseline read SNAPSHOT.yaml at each parent: median "
              f"{statistics.median(snapshot_sizes):,.0f} bytes listing "
              f"{statistics.median(snapshot_items):.0f} items")
    if no_snapshot:
        print(f"  NOTE          {no_snapshot} of {scored} commits have no "
              f"SNAPSHOT.yaml at their parent (history predates the file); they "
              f"score 0 on both snapshot rows rather than being dropped")
    print(f"  run           {elapsed:.1f}s")
    print()
    print("  CAVEAT: " + CAVEAT)
    print("=" * 78)
    print()
    header = "  " + "recall at".ljust(46) + "".join(f"{k:>8}" for k in BUDGETS)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for key, label in (
        ("as_written", "ranker, commit message as written"),
        ("stripped", "ranker, IDs stripped from query  [HONEST ROW]"),
        ("snapshot_order", "baseline: first N items SNAPSHOT.yaml lists"),
        ("focus", "baseline: the snapshot's focus block alone"),
        ("floor", "floor: the N most recently updated notes"),
    ):
        print("  " + label.ljust(46) + "".join(f"{mean(key, k):8.3f}" for k in BUDGETS))
    print()
    print(f"  baseline: EVERY item the snapshot lists"
          f"{mean('snapshot_all', BUDGETS[0]):>32.3f}   (not budgeted -- "
          f"a whole-snapshot read)")
    print()
    print("  Every row above carries the caveat printed in the header.")

    if args.no_sessions or args.worktree:
        return 0

    # The second benchmark, so one command reports both. It labels sessions with
    # the notes they READ, which is the task a ranker is for; this file labels
    # commits with the notes they WROTE. Agreement between two label sources
    # built from different evidence is worth more than either alone.
    sessions = HERE / "rank-bench-sessions.py"
    if not sessions.exists():
        print(f"\n  (session benchmark not found at {sessions})")
        return 0
    print()
    result = subprocess.run(
        [sys.executable, str(sessions), "--repo-root", str(repo),
         "--ranker", args.ranker])
    if result.returncode not in (0, 1):
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
