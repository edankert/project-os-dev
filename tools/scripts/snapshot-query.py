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


def from_note(root, item_id, path):
    """The note's own frontmatter, for an id the snapshot does not carry."""
    try:
        fm = _module("validate_docs_for_query", "validate-docs.py").parse_frontmatter(path)
    except Exception:  # an unreadable note is still found, with what can be told
        fm = {}
    fm = fm if isinstance(fm, dict) else {}
    fields = dict(fm, file=str(path.relative_to(root)))
    kind = str(fm.get("type", "")).strip("[]\"'")
    return record(item_id, kind + "s" if kind else "", fields, "note")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="*", help="item ids, such as TASK-0081")
    ap.add_argument("--status", default="")
    ap.add_argument("--collection", default="", help="tasks, features, issues, ...")
    ap.add_argument("--phase", default="")
    ap.add_argument("--in-flight", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
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

    if args.json:
        print(json.dumps({"version": 1, "items": found, "missing": missing}, indent=2))
        for line in notes:
            print(line, file=sys.stderr)
    else:
        for rec in found:
            extra = "".join(" %s=%s" % (k, rec[k]) for k in ("parent", "phase") if rec[k])
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
