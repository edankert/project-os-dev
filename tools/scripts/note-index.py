#!/usr/bin/env python3
"""The note index: one record per note, built from the cached parse (ISS-0093).

project-os-dev ISS-0093, ADR-0048. Every note under `docs/` gets a record:

  id, path, type, status, phase, parent   from the frontmatter
  links      ids the note links to: its frontmatter link fields, and every
             [[ID...]] or bare ID in its body
  headings   its `#` headings, backticks and emphasis removed
  archived   True when the note sits under docs/archive/ (ISS-0091)
  superseded_by, amended_by   the back-pointers derive-pointers.py stamps (ISS-0096)
  frozen     filled by the tool that owns it (ISS-0097)

`backlinks(index)` inverts `links`. Records are built through
validate-docs.py's `parse_frontmatter` and `cached_note_value`, so a note is
read once and a later run re-reads only what changed. Nothing here is
authored: the notes are the source, and the index is rebuilt from them.

Usage: note-index.py [--repo-root .] [ID ...] [--links-to ID] [--json]
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINK_FIELDS = ("parent", "phase", "tasks", "features", "requirements", "issues", "tests",
               "related", "depends", "blocks", "implements", "supersedes", "superseded",
               "superseded_by", "amends", "amended_by", "risks", "deferred", "origin", "covers", "fixes")


def _module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_VD = None


def validator():
    global _VD
    if _VD is None:
        _VD = _module("validate_docs_for_index", "validate-docs.py")
    return _VD


ID = re.compile(r"\b([A-Z]{2,6})-(\d{2,}[A-Za-z]?)((?:-[A-Za-z0-9_.]+)*)")
HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.M)


def canonical(match):
    prefix, number, slug = match.group(1), match.group(2), match.group(3)
    return prefix + "-" + number + slug if prefix == "CHG" else prefix + "-" + number


def ids_in(value):
    values = value if isinstance(value, list) else [value]
    return [canonical(m) for v in values for m in ID.finditer(str(v or ""))]


def _body_facts(path):
    """(ids linked in the body, headings) for one note; cached with the parse."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"links": [], "headings": []}
    body = text.split("\n---", 1)[1] if text.startswith("---") and "\n---" in text[3:] else text
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    headings = [re.sub(r"[`*]", "", h).strip() for h in HEADING.findall(body)]
    return {"links": sorted(set(ids_in(body))), "headings": headings}


def note_id(path, fm):
    raw = str(fm.get("id", "") or "").strip()
    if raw:
        found = ids_in(raw)
        if found:
            return found[0]
    found = ids_in(path.stem)
    return found[0] if found else ""


def build(root):
    """{id: record} for every note under docs/ that has an id."""
    vd = validator()
    root = Path(root).resolve()
    docs = root / "docs"
    out = {}
    if not docs.is_dir():
        return out
    for path in sorted(docs.rglob("*.md")):
        if "__templates__" in path.parts or "__bases__" in path.parts:
            continue
        fm = vd.parse_frontmatter(path)
        fm = fm if isinstance(fm, dict) else {}
        nid = note_id(path, fm)
        if not nid or nid in out:
            continue
        facts = vd.cached_note_value(path, "body-facts", _body_facts)
        links = set(facts["links"])
        for field in LINK_FIELDS:
            links.update(ids_in(fm.get(field)))
        links.discard(nid)
        rel = path.relative_to(root)
        out[nid] = {
            "id": nid,
            "path": str(rel),
            "type": str(fm.get("type", "") or "").strip("[]\"' "),
            "status": str(fm.get("status", "") or ""),
            "phase": (ids_in(fm.get("phase")) or [""])[0],
            "parent": (ids_in(fm.get("parent")) or [""])[0],
            "links": sorted(links),
            "headings": facts["headings"],
            "archived": rel.parts[:2] == ("docs", "archive"),
            "superseded_by": sorted(set(ids_in(fm.get("superseded_by")) or ids_in(fm.get("superseded")))),
            "amended_by": sorted(set(ids_in(fm.get("amended_by")))),
            "frozen": False,
        }
    return out


def backlinks(index):
    """{id: [ids of notes that link to it]}."""
    back = {}
    for nid, rec in index.items():
        for target in rec["links"]:
            back.setdefault(target, []).append(nid)
    return {k: sorted(v) for k, v in back.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--links-to", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    index = build(args.repo_root)
    if args.links_to:
        found = backlinks(index).get(args.links_to, [])
        print(json.dumps(found) if args.json else "\n".join(found))
        return 0
    chosen = {i: index[i] for i in args.ids if i in index} if args.ids else index
    if args.json:
        print(json.dumps(chosen, indent=2))
    else:
        for rec in chosen.values():
            print("%s %s %s" % (rec["id"], rec["status"] or "?", rec["path"]))
    return 0 if not args.ids or len(chosen) == len(args.ids) else 1


if __name__ == "__main__":
    sys.exit(main())
