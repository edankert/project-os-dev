#!/usr/bin/env python3
"""Move finished tickets whose release is out to docs/archive/ (ISS-0091, ADR-0048).

"The notes are the archive" kept every finished note beside the live ones for
good. In your-trainer 832 of 974 tasks and 436 of 515 issues were finished, and
a search for one rule returned 57 notes, 27 of them finished tickets that each
had to be opened and judged as history. This moves them out of the way:

  moved       a task, issue or change note that was finished when the last
              release went out and is still finished, and an acceptance check
              that was retired by then
  where       docs/archive/<the same path under docs/>, with `git mv` so its
              history follows it. Nothing is ever deleted.
  snapshot    its SNAPSHOT.yaml entry is dropped; the note is the record
  kept        features, phases, ADRs, requirements, risks, releases, live
              checks, and any ticket finished after the release

"Finished at the release" uses the same boundary as FROZEN-EDIT: the newest
`released` REL note's `tag:`, else the newest git tag. A ticket closed after it
is still in play, as the your-trainer session found when it had to change an
issue and a task closed the day before.

Links still resolve: the validator's note index reads docs/archive/ too, and an
Obsidian link names the note, not its folder. A repo `.ignore` keeps ripgrep and
agent search out of the archive unless asked (`rg --no-ignore`).

Usage:
    archive-notes.py [--repo-root .]     # dry run: what would move, and why
    archive-notes.py --apply
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = "archive"
#: Retired acceptance checks are archived too; their status vocabulary is the test's.
RETIRED = {"retired"}


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.returncode, r.stdout


def finished(vd):
    return {"task": vd.PHASE_RESOLVED["task"], "issue": vd.PHASE_RESOLVED["issue"],
            "change": vd.ALLOWED_STATUS["change"], "test": RETIRED}


def at_revision(root: Path, rev: str, paths: list[str]) -> dict[str, str]:
    """{path: text at rev} for the paths that exist there, read in one git call."""
    if not paths:
        return {}
    raw = subprocess.run(["git", "cat-file", "--batch"], cwd=root, capture_output=True,
                         input="".join("%s:%s\n" % (rev, p) for p in paths).encode()).stdout
    out, pos = {}, 0
    for path in paths:
        end = raw.index(b"\n", pos)
        header = raw[pos:end].decode(errors="replace").split()
        pos = end + 1
        if len(header) < 3 or header[1] == "missing":
            continue
        size = int(header[2])
        out[path] = raw[pos:pos + size].decode(errors="replace")
        pos += size + 1
    return out


def plan(root: Path):
    """(tag, [(id, relative path, why)], reason nothing moves)."""
    vd = _load("_vd_archive", "validate-docs.py")
    code, _ = git(root, "rev-parse", "--git-dir")
    if code != 0:
        return "", [], "this is not a git checkout, so nothing says what the last release contained"
    tag = vd.release_boundary(root)
    if not tag:
        return "", [], "no release is out yet: no released REL note with a tag, and no git tag"
    done = finished(vd)
    docs = root / "docs"
    candidates = []
    for path in sorted(docs.rglob("*.md")):
        rel = path.relative_to(root)
        if rel.parts[1:2] == (ARCHIVE,) or "__templates__" in rel.parts or "__bases__" in rel.parts:
            continue
        fm = vd.parse_frontmatter(path)
        fm = fm if isinstance(fm, dict) else {}
        ntype = vd.note_type(fm)
        if ntype not in done or str(fm.get("status", "")).strip() not in done[ntype]:
            continue
        nid = str(fm.get("id", "") or "").strip() or path.stem
        candidates.append((nid, rel, ntype))
    #: Every candidate's text at the tag, in one `git cat-file --batch` call.
    then = at_revision(root, tag, [rel.as_posix() for _nid, rel, _t in candidates])
    out = []
    for nid, rel, ntype in candidates:
        old = then.get(rel.as_posix())
        if old is None:
            continue                                   # not in the release: still in play
        status = str(vd._split_note(old)[0].get("status", "")).strip()
        if status not in done[ntype]:
            continue                                   # finished after the release
        out.append((nid, rel, "%s %s at %s" % (ntype, status, tag)))
    return tag, out, ""


def apply(root: Path, moves) -> list[str]:
    sync = _load("_sync_archive", "sync-snapshot.py")
    snap = root / "SNAPSHOT.yaml"
    moved = []
    for nid, rel, _why in moves:
        dest = Path("docs") / ARCHIVE / Path(*rel.parts[1:])
        (root / dest).parent.mkdir(parents=True, exist_ok=True)
        code, _ = git(root, "mv", rel.as_posix(), dest.as_posix())
        if code != 0:
            os.replace(root / rel, root / dest)
        moved.append(nid)
    if snap.is_file() and moved:
        text = snap.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        sync.prune_entries(lines, [(None, nid) for nid in moved])
        if "".join(lines) != text:
            sync.write_if_unchanged(snap, text, "".join(lines))
    return moved


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.repo_root).resolve()
    tag, moves, why_not = plan(root)
    if why_not:
        print("archive-notes: nothing to move; %s" % why_not)
        return 0
    by = {}
    for _nid, rel, why in moves:
        by[why.split(" ")[0]] = by.get(why.split(" ")[0], 0) + 1
    print("archive-notes: %s %d note(s) finished at %s to docs/%s/ (%s)"
          % ("moved" if args.apply else "would move", len(moves), tag, ARCHIVE,
             ", ".join("%s %d" % kv for kv in sorted(by.items())) or "none"))
    if args.apply:
        apply(root, moves)
        print("archive-notes: run sync-snapshot.py and validate-docs.sh, then commit the move")
    else:
        for nid, rel, why in moves[:20]:
            print("   %s  %s (%s)" % (nid, rel, why))
        if len(moves) > 20:
            print("   ... and %d more" % (len(moves) - 20))
    return 0


if __name__ == "__main__":
    sys.exit(main())
