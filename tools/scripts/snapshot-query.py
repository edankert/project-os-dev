#!/usr/bin/env python3
"""Look an item up in SNAPSHOT.yaml the same way in every repo (read-only).

project-os-dev TASK-0081. Agents looked items up with grep, and grep answers
differently by the snapshot's YAML style: in an inline flow map
(`    TASK-0001: { status: doing, ... }`) the matching line holds the status; in
a block item the next line is `file:` and the status is further down, so the
answer is silently missing. This reads either style with the parser the
session-start orientation uses (`snapshot-slice.py`), and falls back to the
note's own frontmatter when the snapshot does not carry the id -- a pruned
item is still a real one (ISS-0030).

Usage:
  snapshot-query.py ID [ID ...]            one line per item
  snapshot-query.py --status doing          filter; combine with --collection, --phase
  snapshot-query.py --in-flight             items at doing/review, open/triage or active, focus included
  snapshot-query.py --search TEXT           notes whose text contains TEXT (case-insensitive)
  snapshot-query.py --links-to ID           notes that link to ID
      both: live notes first, labelled with id and status; finished notes folded
      into a count unless --all; docs/archive/ read only with --all
  add --json for machine-readable output, --repo-root to point at another repo

JSON shape, version 1 (kept stable; a change bumps `version`):
  {"version": 1, "items": [{"id", "collection", "status", "file", "parent",
   "phase", "links": {field: [ids]}, "source": "snapshot" | "note"}],
   "missing": [ids not found anywhere]}

A change note's id carries its slug (CHG-20260925-Some-Title) and is kept
whole. A date alone (CHG-20260925) is answered when one change has it and
reported as ambiguous, naming the candidates, when several do.

Exit 0 when every id asked for was found (or a filter ran), 1 when one was
not or was ambiguous, 2 on a usage error (ids and a filter together).
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID = re.compile(r"([A-Z]+)-(\d+[A-Za-z]?)((?:-[A-Za-z0-9_.]+)*)")
LINK_FIELDS = ("tasks", "features", "requirements", "issues", "tests", "related",
               "depends", "blocks", "implements", "risks", "deferred")


def _module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(token):
    """An item id as the snapshot keys it: a change keeps its slug, others do not.

    `[[TASK-0081-Format-Independent-Query|TASK-0081]]` is TASK-0081;
    `CHG-20260925-Some-Title` stays whole (FEAT-0021 review, 2026-09-25).
    """
    m = ID.search(str(token or ""))
    if not m:
        return ""
    return m.group(0) if m.group(1) == "CHG" else "%s-%s" % (m.group(1), m.group(2))


def _ids(value):
    values = value if isinstance(value, list) else [value]
    out = []
    for v in values:
        for m in ID.finditer(str(v or "")):
            out.append(m.group(0) if m.group(1) == "CHG" else "%s-%s" % (m.group(1), m.group(2)))
    return out


def _one(value):
    found = _ids(value)
    return found[0] if found else ""


def record(item_id, collection, fields, source):
    return {
        "id": item_id,
        "collection": collection,
        "status": str(fields.get("status", "") or ""),
        "file": str(fields.get("file", "") or ""),
        "parent": _one(fields.get("parent")),
        "phase": _one(fields.get("phase")),
        "links": {k: _ids(fields.get(k)) for k in LINK_FIELDS if _ids(fields.get(k))},
        "source": source,
    }


def note_paths(root, item_id):
    """Notes whose file is this id: the exact name, or the id and a slug."""
    docs = root / "docs"
    exact = [p for p in docs.rglob(item_id + ".md") if p.is_file()]
    return exact or sorted(p for p in docs.rglob(item_id + "-*.md") if p.is_file())


_VD = None


def validator():
    global _VD
    if _VD is None:
        _VD = _module("validate_docs_for_query", "validate-docs.py")
    return _VD


def add_pointers(root, rec):
    """Say when the item's note has been replaced or amended (ISS-0096).

    derive-pointers.py stamps the old note, so the answer is on the note even
    when the snapshot entry is old or gone. An agent that looks an id up is told
    before it reads a rule that no longer holds.
    """
    path = root / rec["file"] if rec["file"] else None
    if path is None or not path.is_file():
        return rec
    try:
        fm = validator().parse_frontmatter(path) or {}
    except Exception:  # an unreadable note says nothing about pointers
        return rec
    by = _ids(fm.get("superseded_by")) or _ids(fm.get("superseded"))
    if by:
        rec["superseded_by"] = by
    amended = _ids(fm.get("amended_by"))
    if amended:
        rec["amended_by"] = amended
    return rec


def from_note(root, item_id, path):
    """The note's own frontmatter, for an id the snapshot does not carry."""
    try:
        fm = validator().parse_frontmatter(path)
    except Exception:  # an unreadable note is still found, with what can be told
        fm = {}
    fm = fm if isinstance(fm, dict) else {}
    fields = dict(fm, file=str(path.relative_to(root)))
    kind = str(fm.get("type", "")).strip("[]\"'")
    return record(item_id, kind + "s" if kind else "", fields, "note")


#: Statuses that finish a note: a hit on one is history, not the answer.
FINISHED = {"done", "fixed", "cancelled", "superseded", "declined", "merged", "reverted",
            "implemented", "retired", "released", "closed", "deferred"}


def _search_paths(root, text, include_archive):
    """Notes under docs/ whose text contains `text`, case-insensitive.

    ripgrep when it is installed, which honours `.gitignore` and `.ignore`
    (project-os-dev ISS-0102); otherwise a plain scan that skips the same
    `docs/archive/` the repo's `.ignore` names, so a machine without rg gets
    the same answer, if slower.
    """
    import shutil
    import subprocess
    docs = root / "docs"
    rg = shutil.which("rg")
    if rg:
        cmd = [rg, "-l", "-i", "-F", "--glob", "*.md"]
        if include_archive:
            cmd.append("--no-ignore")
        r = subprocess.run(cmd + ["--", text, str(docs)], capture_output=True, text=True)
        found = [Path(line) for line in r.stdout.splitlines() if line.strip()]
    else:
        needle = text.lower()
        found = []
        for path in docs.rglob("*.md"):
            rel = path.relative_to(root).as_posix()
            if not include_archive and rel.startswith("docs/archive/"):
                continue
            try:
                if needle in path.read_text(encoding="utf-8", errors="replace").lower():
                    found.append(path)
            except OSError:
                continue
    return sorted(p for p in found if "__templates__" not in p.parts and "__bases__" not in p.parts)


def _label(root, paths):
    """[(id, status, path, finished)] for note paths."""
    vd = validator()
    out = []
    for path in paths:
        path = path if path.is_absolute() else root / path
        fm = vd.parse_frontmatter(path) or {}
        fm = fm if isinstance(fm, dict) else {}
        the_id = canonical(fm.get("id")) or canonical(path.stem) or path.stem
        status = str(fm.get("status", "") or "").strip()
        rel = path.relative_to(root).as_posix()
        out.append((the_id, status, rel, status in FINISHED or rel.startswith("docs/archive/")))
    return out


def list_view(root, labelled, show_all, as_json, what):
    live = [x for x in labelled if not x[3]]
    done = [x for x in labelled if x[3]]
    if as_json:
        print(json.dumps({"version": 1, "query": what, "live": [
            {"id": i, "status": s, "file": f} for i, s, f, _ in live],
            "finished": [{"id": i, "status": s, "file": f} for i, s, f, _ in done] if show_all else [],
            "finished_count": len(done)}, indent=2))
        return 0
    for i, s, f, _ in live:
        print("%s %s %s" % (i, s or "?", f))
    if show_all:
        for i, s, f, _ in done:
            print("%s %s %s (finished)" % (i, s or "?", f))
    elif done:
        print("... and %d finished note(s) that also match, not listed: %s%s; --all lists them"
              % (len(done), ", ".join(i for i, _s, _f, _ in done[:8]), ", ..." if len(done) > 8 else ""))
    if not labelled:
        print("no note matches %s" % what)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="*", help="item ids, such as TASK-0081")
    ap.add_argument("--status", default="")
    ap.add_argument("--collection", default="", help="tasks, features, issues, ...")
    ap.add_argument("--phase", default="")
    ap.add_argument("--in-flight", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--search", default="", metavar="TEXT")
    ap.add_argument("--links-to", default="", metavar="ID")
    ap.add_argument("--all", action="store_true", help="with --search or --links-to: list finished and archived notes too")
    args = ap.parse_args(argv)
    if args.search or args.links_to:
        #: project-os-dev ISS-0101: a search put finished notes in front of the
        #: agent mixed in with live ones, and each had to be opened to find out.
        root = Path(args.repo_root).resolve()
        if args.search:
            paths = _search_paths(root, args.search, args.all)
            what = "%r" % args.search
        else:
            ni = _module("note_index_for_query", "note-index.py")
            ni._VD = validator()
            index = ni.build(root)
            target = canonical(args.links_to)
            paths = [root / index[i]["path"] for i in ni.backlinks(index).get(target, [])
                     if args.all or not index[i]["archived"]]
            what = "a link to %s" % target
        return list_view(root, _label(root, paths), args.all, args.json, what)
    filters = args.status or args.collection or args.phase or args.in_flight
    if not (args.ids or filters) or (args.ids and filters):
        ap.print_usage(sys.stderr)
        if args.ids and filters:
            print("snapshot-query: give ids or a filter, not both", file=sys.stderr)
        return 2

    root = Path(args.repo_root).resolve()
    snapshot = root / "SNAPSHOT.yaml"
    slice_mod = _module("snapshot_slice_for_query", "snapshot-slice.py")
    text = snapshot.read_text(encoding="utf-8") if snapshot.is_file() else ""
    _, _, _, items = slice_mod.parse(text)
    index = {i: (col, f) for col, members in items.items() for i, f in members.items()}

    found, missing, notes = [], [], []
    if args.ids:
        for raw in args.ids:
            item_id = canonical(raw)
            if item_id in index:
                col, fields = index[item_id]
                found.append(record(item_id, col, fields, "snapshot"))
                continue
            #: A change asked for by its date alone: several may share it.
            keyed = sorted(k for k in index if item_id and k.startswith(item_id + "-")) if item_id.startswith("CHG-") else []
            paths = note_paths(root, item_id) if item_id else []
            candidates = sorted(set(keyed) | {p.stem for p in paths}) if keyed or len(paths) > 1 else []
            if len(candidates) > 1:
                missing.append(raw)
                notes.append("%s: ambiguous, %d items match: %s" % (raw, len(candidates), ", ".join(candidates)))
            elif keyed:
                col, fields = index[keyed[0]]
                found.append(record(keyed[0], col, fields, "snapshot"))
            elif paths:
                found.append(from_note(root, paths[0].stem if item_id.startswith("CHG-") else item_id, paths[0]))
            else:
                missing.append(raw)
                notes.append("%s: not in SNAPSHOT.yaml and no note named %s under docs/"
                             % (raw, (item_id + ".md or " + item_id + "-*.md") if item_id else raw))
    else:
        wanted = {col: states for col, states in slice_mod.IN_FLIGHT.items()} if args.in_flight else None
        for item_id, (col, fields) in index.items():
            rec = record(item_id, col, fields, "snapshot")
            if wanted is not None and rec["status"] not in wanted.get(col, ()):
                continue
            if args.status and rec["status"] != args.status:
                continue
            if args.collection and col != args.collection:
                continue
            if args.phase and rec["phase"] != _one(args.phase):
                continue
            found.append(rec)

    if args.ids:
        found = [add_pointers(root, rec) for rec in found]
    if args.json:
        print(json.dumps({"version": 1, "items": found, "missing": missing}, indent=2))
        for line in notes:
            print(line, file=sys.stderr)
    else:
        for rec in found:
            extra = "".join(" %s=%s" % (k, rec[k]) for k in ("parent", "phase") if rec[k])
            extra += "".join(" %s=%s" % (k.replace("_", "-"), ",".join(rec[k]))
                             for k in ("superseded_by", "amended_by") if rec.get(k))
            print("%s %s %s%s%s" % (rec["id"], rec["status"] or "?", rec["file"] or "(no file)", extra,
                                    " (from the note; not in SNAPSHOT.yaml)" if rec["source"] == "note" else ""))
            if len(args.ids) == 1:
                for field, ids in rec["links"].items():
                    print("  %s: %s" % (field, ", ".join(ids)))
        for line in notes:
            print(line, file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
