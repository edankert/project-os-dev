#!/usr/bin/env python3
"""Rank the project's notes against a plain-language query.

Answers one question: *given what I am about to work on, which notes should I
read first?* It returns an ordered list of note IDs and nothing else -- no
prose, no summary, no judgement about what they say.

WHY THIS EXISTS AT ALL
----------------------
A session starting in a project-os repo is told to read `SNAPSHOT.yaml`, which
in project-os-dev is 26k tokens naming 168 items, and then to work out for
itself which notes matter. Nothing measured how well that works until
project-os-dev REQ-0032, which forbids any mechanism from claiming to know
which notes a session needs unless it states its recall beside the baseline it
replaces. `rank-bench.py` is that measurement; this file is the thing measured.

The scores it earns on project-os-dev are recorded in project-os-dev
FEAT-0038, not here, because they are properties of a corpus and a date rather
than of this code.

WHAT IT SCORES ON
-----------------
Okapi BM25 over each note's full text, then four adjustments in code:

  * `status`  -- a note in a live state is likelier to be what you want than a
                 finished one. A multiplier, not a filter: closed notes still
                 rank, because "why did we decide that" is a real query.
  * `updated` -- a small boost for notes touched in the last two months.
  * exact ID  -- a query naming `FEAT-0012` means that note, so it goes top.
                 `rank-bench.py` scores a second row with IDs stripped, because
                 this boost makes the benchmark trivially easy otherwise.
  * `title`   -- terms in the title count for more than terms in the body.

NO SECOND LENGTH PENALTY
------------------------
BM25's `b` term already normalises for document length. An earlier prototype
divided the score again by `1 + log(1 + len/avg)`, and the second penalty
buried exactly the notes a feature's own documentation produces: on
project-os-dev, ISS-0048 fell to rank 44 of 360 for a query matching its title
almost word for word, and FEAT-0038 to 8th on its own subject. Removing it
raised recall at every depth. Do not reintroduce it.

That defect also says something about how to test a change here: the aggregate
barely moved (0.53 to 0.55 on one benchmark) while a single note moved 41
places. Run `rank-bench.py`, then also run a real query and look at the answer.

THE INTERFACE `rank-bench.py` USES
----------------------------------
Any ranker this harness can score exposes one function:

    build_index(notes: dict[str, Note]) -> object with .rank(query: str, k: int)

`notes` maps a note ID to a `Note`. `.rank` returns at most `k` note IDs, best
first. That is the whole contract: a different ranker is a different file with
the same two names, scored with `rank-bench.py --ranker path/to/it.py`.

Usage:
    rank-notes.py "the review keeps running past its budget"
    rank-notes.py "phase cannot close" -k 10 --json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# BM25 parameters. Defaults from the literature; project-os-dev TASK-0154
# sweeps them against the benchmark rather than leaving them at taste.
K1 = 1.5
B = 0.75

TITLE_WEIGHT = 2.0      # a term in the title counts double
STATUS_BOOST = 0.15     # a live note scores 15% higher than a finished one
RECENT_BOOST = 0.10     # touched within RECENT_DAYS
RECENT_DAYS = 60
ID_BOOST = 5.0          # a query naming an ID means that note

# Statuses that mean "this is live work". Everything else still ranks.
LIVE = frozenset({
    "doing", "open", "backlog", "active", "draft", "planned",
    "review", "triage", "proposed", "ready", "failing",
})

STOPWORDS = frozenset("""
a an and are as at be been but by can did do does for from had has have how
if in into is it its not of on or should that the their then there these this
to was were what when where which who why will with would you your
""".split())

ID_RE = re.compile(r"\b([A-Z]{2,6}-\d{3,4})\b")
WORD_RE = re.compile(r"[a-z0-9]+")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
H1_RE = re.compile(r"^#\s+(.+)$", re.M)


@dataclass
class Note:
    """One note, as the ranker needs it. Built by `load_worktree` or by the
    harness reading a past commit -- the ranker never touches the filesystem
    itself, so it can be scored against a corpus that no longer exists."""

    id: str
    path: str = ""
    body: str = ""
    title: str = ""
    status: str = ""
    updated: str = ""
    type: str = ""


def tokenize(text: str) -> list[str]:
    return [w for w in WORD_RE.findall(text.lower())
            if len(w) > 2 and w not in STOPWORDS]


def _frontmatter_value(front: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+)$", front, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'").strip()


def parse_note(note_id: str, text: str, path: str = "") -> Note:
    """Build a Note from a file's raw text. Tolerant by design: a note with no
    frontmatter, or unparseable frontmatter, still ranks on its body rather
    than vanishing from the corpus."""
    fm = FRONTMATTER_RE.match(text)
    front = fm.group(1) if fm else ""
    title = _frontmatter_value(front, "title")
    if not title:
        h1 = H1_RE.search(text)
        title = h1.group(1).strip() if h1 else note_id
    return Note(
        id=note_id,
        path=path,
        body=text,
        title=title,
        status=_frontmatter_value(front, "status"),
        updated=_frontmatter_value(front, "updated"),
        type=_frontmatter_value(front, "type").strip("[]"),
    )


def note_id_from_filename(name: str) -> str | None:
    """`FEAT-0038-Note-Relevance-Harness.md` -> `FEAT-0038`. A file whose name
    carries no ID is not a note and is skipped -- README.md, INDEX.md and the
    templates all land here."""
    m = re.match(r"([A-Z]{2,6}-\d{3,4})", os.path.basename(name))
    return m.group(1) if m else None


def load_worktree(repo_root: str | os.PathLike, docs_dir: str = "docs") -> dict[str, Note]:
    """Every note under `docs/` in the working tree, keyed by ID.

    Templates are excluded: they are shapes, not records, and their placeholder
    prose matches far too many queries.
    """
    notes: dict[str, Note] = {}
    root = Path(repo_root) / docs_dir
    for path in sorted(root.rglob("*.md")):
        if "__templates__" in path.parts:
            continue
        note_id = note_id_from_filename(path.name)
        if not note_id or note_id in notes:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        notes[note_id] = parse_note(note_id, text, str(path))
    return notes


@dataclass
class Index:
    """A scored corpus. Build once, query many times: building is the
    expensive half and a query is about a millisecond."""

    notes: dict[str, Note]
    _tf: dict[str, Counter] = field(default_factory=dict, repr=False)
    _title_tf: dict[str, Counter] = field(default_factory=dict, repr=False)
    _idf: dict[str, float] = field(default_factory=dict, repr=False)
    _length: dict[str, int] = field(default_factory=dict, repr=False)
    _avg_length: float = 0.0

    def __post_init__(self) -> None:
        df: Counter = Counter()
        for note_id, note in self.notes.items():
            terms = tokenize(note.body)
            self._tf[note_id] = Counter(terms)
            self._title_tf[note_id] = Counter(tokenize(note.title))
            self._length[note_id] = len(terms)
            df.update(set(terms))
        n = len(self.notes) or 1
        self._avg_length = (sum(self._length.values()) / n) or 1.0
        # BM25 probabilistic idf, +1 inside the log so a term in every document
        # scores 0 rather than going negative.
        self._idf = {
            term: math.log(1 + (n - count + 0.5) / (count + 0.5))
            for term, count in df.items()
        }

    def _recent(self, updated: str) -> bool:
        if not re.match(r"\d{4}-\d{2}-\d{2}", updated):
            return False
        try:
            import datetime as dt
            seen = dt.date.fromisoformat(updated[:10])
        except ValueError:
            return False
        return (dt.date.today() - seen).days <= RECENT_DAYS

    def score(self, query: str) -> list[tuple[float, str]]:
        """Every note scored against the query, best first."""
        terms = tokenize(query)
        wanted_ids = {m for m in ID_RE.findall(query.upper())}
        scored: list[tuple[float, str]] = []
        for note_id, note in self.notes.items():
            length = self._length[note_id]
            tf = self._tf[note_id]
            title_tf = self._title_tf[note_id]
            total = 0.0
            for term in terms:
                idf = self._idf.get(term)
                if idf is None:
                    continue
                freq = tf.get(term, 0) + TITLE_WEIGHT * title_tf.get(term, 0)
                if not freq:
                    continue
                denominator = freq + K1 * (1 - B + B * length / self._avg_length)
                total += idf * freq * (K1 + 1) / denominator
            # No second length penalty here. See the module docstring.
            if note.status in LIVE:
                total *= 1 + STATUS_BOOST
            if self._recent(note.updated):
                total *= 1 + RECENT_BOOST
            if note_id in wanted_ids:
                total += ID_BOOST
            scored.append((total, note_id))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return scored

    def rank(self, query: str, k: int = 24) -> list[str]:
        """The interface `rank-bench.py` calls. At most `k` IDs, best first.

        Notes scoring zero are dropped rather than padded: returning arbitrary
        IDs to fill a budget would inflate recall at large k and tell the
        reader nothing.
        """
        return [note_id for score, note_id in self.score(query)[:k] if score > 0]


def build_index(notes: dict[str, Note]) -> Index:
    """The other half of the ranker interface. See the module docstring."""
    return Index(notes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rank this project's notes against a query.")
    parser.add_argument("query", help="plain language; naming an ID pins that note")
    parser.add_argument("-k", type=int, default=24, help="how many to return (default 24)")
    parser.add_argument("--repo-root", default=".", help="repository root (default .)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--scores", action="store_true", help="show the score beside each note")
    args = parser.parse_args(argv)

    notes = load_worktree(args.repo_root)
    if not notes:
        print(f"rank-notes: no notes under {args.repo_root}/docs", file=sys.stderr)
        return 1
    index = build_index(notes)
    ranked = index.score(args.query)[:args.k]
    ranked = [(s, n) for s, n in ranked if s > 0]

    if args.json:
        print(json.dumps({
            "query": args.query,
            "corpus": len(notes),
            "results": [
                {"id": n, "score": round(s, 4), "status": notes[n].status,
                 "title": notes[n].title, "file": notes[n].path}
                for s, n in ranked
            ],
        }, indent=2))
        return 0

    if not ranked:
        print(f"no note matched (corpus {len(notes)} notes)")
        return 0
    width = max(len(n) for _, n in ranked)
    for position, (score, note_id) in enumerate(ranked, 1):
        note = notes[note_id]
        prefix = f"{score:7.2f}  " if args.scores else ""
        print(f"{position:3}. {prefix}{note_id:<{width}}  {note.status:<11} {note.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
