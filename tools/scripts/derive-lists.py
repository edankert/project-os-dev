#!/usr/bin/env python3
"""Generate every reverse list from the child's own field (ADR-0048, ISS-0095).

Adding a task to a feature in a phase used to write one fact six times: the
task's `parent:` and `phase:`, the feature's `tasks:`, the phase note's
`tasks:`, and three lists in SNAPSHOT.yaml. PARENT-BACKLINK and
SNAPSHOT-MEMBERSHIP existed only to catch the copies drifting. Now the child is
the one place the fact is written, and this script writes the rest:

  a feature's or an issue's `tasks:`      from each task's `parent:`
  a phase note's `tasks:`, `features:`,   from each child's `phase:`
    `issues:` and `requirements:`
  the same lists on SNAPSHOT.yaml entries
  an `items.tasks` entry for a live task  (backlog or doing) whose parent or
    phase is a live snapshot entry

A list keeps its written style: inline or block, and each entry's own form
(`"[[TASK-0001-Slug]]"`, `"[[TASK-0001]]"` or a bare id). Entries of other id
types, entries naming no note, and text are left where they are. New entries
copy the form of the list's existing ones and are appended in id order.

A fact written only in a parent's list is first MOVED onto the child: a task
listed by one feature, whose `parent:` is empty, gets that feature as its
parent. A child listed by two parents, or naming a different parent than the
list that holds it, is a CONFLICT: the child's own field wins and the conflict
is reported, so a person can check it.

Nothing here runs unless the repo opts in with `retention.derive_lists: true`
in SNAPSHOT.yaml; until then `sync-snapshot.py` only reports what it would
change, as it did for `derive_fields` (TASK-0085).

Usage:
    derive-lists.py [--repo-root .]            # dry run: what would change
    derive-lists.py --apply                    # write it
    derive-lists.py --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

#: (parent prefix, list field, child prefix, the child's field that names the parent)
RULES = (
    ("FEAT", "tasks", "TASK", "parent"),
    ("ISS", "tasks", "TASK", "parent"),
    ("PHASE", "tasks", "TASK", "phase"),
    ("PHASE", "features", "FEAT", "phase"),
    ("PHASE", "issues", "ISS", "phase"),
    ("PHASE", "requirements", "REQ", "phase"),
)
#: A parent of these kinds gets a `tasks:` field when it has children and none;
#: a phase note gets only the lists it already has.
ADD_FIELD = {"FEAT", "ISS"}
LIVE_TASK = {"backlog", "doing"}
SETTLED = {"done", "cancelled", "superseded", "fixed", "declined", "deferred", "implemented", "retired"}
COLLECTION = {"FEAT": "features", "ISS": "issues", "PHASE": "phases", "TASK": "tasks", "REQ": "requirements"}


def _load_validator():
    spec = importlib.util.spec_from_file_location("_vd_derive", HERE / "validate-docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: The validator module, loaded on first use. `sync-snapshot.py` hands over the
#: one it already loaded, so both read the note cache once.
_vd = None


def validator():
    global _vd
    if _vd is None:
        _vd = _load_validator()
    return _vd


def extract_ids(value):
    return validator().extract_ids(value)


def prefix(the_id):
    return the_id.split("-", 1)[0]


# ------------------------------------------------------------ list text


def split_flow(inner):
    """The raw items of a flow list's inside, split at top-level commas."""
    items, cur, depth, quote, i = [], "", 0, None, 0
    while i < len(inner):
        ch = inner[i]
        if quote:
            cur += ch
            if ch == "\\" and quote == '"' and i + 1 < len(inner):
                cur += inner[i + 1]
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch in "[{":
            depth += 1
            cur += ch
        elif ch in "]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    if cur.strip():
        items.append(cur.strip())
    return items


def item_id(raw, want_prefix):
    """The id an entry names, when it is of the managed prefix; else None."""
    found = [i for i in extract_ids(raw) if prefix(i) == want_prefix]
    return found[0] if found else None


def entry_form(raws, want_prefix, the_id, stem, default=None):
    """Write `the_id` the way the list's existing entries are written."""
    for raw in raws:
        if item_id(raw, want_prefix) is None:
            continue
        quote = raw[0] if raw[:1] in "\"'" else ""
        body = raw.strip("\"'")
        if body.startswith("[["):
            inner = body[2:].split("]]", 1)[0].split("|", 1)[0]
            target = stem if re.match(r"^[A-Z]+-\d+[A-Za-z]?-", inner) and stem else the_id
            return '%s[[%s]]%s' % (quote, target, quote)
        return "%s%s%s" % (quote, the_id, quote)
    return default % the_id if default else '"[[%s]]"' % the_id


def new_list(raws, want_prefix, wanted, stems, drop, default=None):
    """(new raw entries, added ids, removed ids) for one list."""
    out, seen, removed = [], set(), []
    for raw in raws:
        the_id = item_id(raw, want_prefix)
        if the_id is None:
            out.append(raw)
            continue
        if the_id in seen:
            removed.append(the_id)
            continue
        if the_id in drop:
            removed.append(the_id)
            continue
        seen.add(the_id)
        out.append(raw)
    added = [i for i in sorted(wanted) if i not in seen]
    for the_id in added:
        out.append(entry_form(raws, want_prefix, the_id, stems.get(the_id, ""), default))
    return out, added, removed


# ------------------------------------------------ one field in YAML lines


def find_field(lines, start, end, field, indent):
    """(first, last, style, raws) for `field` at `indent` within lines[start:end].

    `style` is "inline" (`field: [a, b]`, possibly over several lines),
    "block" (`field:` then `- item` lines) or "scalar" (anything else, which
    this script leaves alone). None when the field is absent.
    """
    key = re.compile(r"^%s%s:(.*)$" % (re.escape(" " * indent), re.escape(field)))
    for i in range(start, end):
        m = key.match(lines[i].rstrip("\n"))
        if not m:
            continue
        rest = m.group(1).strip()
        if rest.startswith("["):
            text, j = rest, i
            while text.count("[") > text.count("]") and j + 1 < end:
                j += 1
                text += " " + lines[j].strip()
            inner = text[1:text.rfind("]")] if "]" in text else text[1:]
            return i, j, "inline", split_flow(inner)
        if rest == "" or rest.startswith("#"):
            raws, j = [], i
            while j + 1 < end:
                nxt = lines[j + 1].rstrip("\n")
                s = nxt.lstrip()
                if s.startswith("- ") or s == "-":
                    if len(nxt) - len(s) < indent:
                        break
                    raws.append(s[1:].strip())
                    j += 1
                elif s == "" or s.startswith("#"):
                    break
                else:
                    break
            return i, j, "block", raws
        return i, i, "scalar", []
    return None


def render(field, indent, style, raws, item_indent=None):
    pad = " " * indent
    if style == "block" and raws:
        ipad = " " * (indent if item_indent is None else item_indent)
        return ["%s%s:\n" % (pad, field)] + ["%s- %s\n" % (ipad, r) for r in raws]
    return ["%s%s: [%s]\n" % (pad, field, ", ".join(raws))]


def block_item_indent(lines, first, last):
    for k in range(first + 1, last + 1):
        s = lines[k].lstrip()
        if s.startswith("-"):
            return len(lines[k]) - len(s)
    return None


# ------------------------------------------------------------ the notes


def frontmatter_bounds(lines):
    if not lines or not lines[0].startswith("---"):
        return None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\n") == "---":
            return 1, i
    return None


def set_scalar(lines, field, value):
    """Set a top-level frontmatter scalar, inserting it before the close if absent."""
    b = frontmatter_bounds(lines)
    if b is None:
        return False
    start, end = b
    key = re.compile(r"^%s:(.*)$" % re.escape(field))
    for i in range(start, end):
        if key.match(lines[i]):
            lines[i] = '%s: %s\n' % (field, value)
            return True
    lines.insert(end, '%s: %s\n' % (field, value))
    return True


def notes_of(root):
    """{id: (path, fm)} for notes that alone claim their id."""
    index, claimants = validator().build_note_index(root / "docs")
    return {i: (p, fm or {}) for i, (p, fm) in index.items()
            if claimants.get(i) == [p] and "__templates__" not in p.parts}


def plan(root):
    """Everything the generator would change, without writing."""
    notes = notes_of(root)
    names = {}                       # (child id, child field) -> every id the field names
    wanted = {}                      # (parent id, list field) -> {child ids}
    for cid, (_p, fm) in notes.items():
        for pp, field, cp, cf in RULES:
            if prefix(cid) != cp:
                continue
            named = extract_ids(fm.get(cf))
            names[(cid, cf)] = named
            for pid in named:
                if prefix(pid) == pp:
                    wanted.setdefault((pid, field), set()).add(cid)

    # A fact written only in a parent's list is moved onto the child when the
    # child's field is empty and exactly one list holds it.
    holders = {}                     # (child id, child field) -> {parent ids}
    for pid, (_p, fm) in notes.items():
        for pp, field, cp, cf in RULES:
            if prefix(pid) != pp:
                continue
            for cid in extract_ids(fm.get(field)):
                if prefix(cid) == cp and cid in notes:
                    holders.setdefault((cid, cf), set()).add(pid)
    moves, conflicts, moved = [], [], {}
    for (cid, cf), pids in sorted(holders.items()):
        named = names.get((cid, cf), [])
        if named:
            for pid in sorted(pids):
                if stale(pid, cid, cf, names):
                    conflicts.append({"child": cid, "field": cf, "names": named, "listed_by": pid})
        elif len(pids) == 1:
            pid = next(iter(pids))
            moves.append({"child": cid, "field": cf, "parent": pid})
            moved[(cid, cf)] = pid
            for pp, field, cp, rcf in RULES:
                if pp == prefix(pid) and cp == prefix(cid) and rcf == cf:
                    wanted.setdefault((pid, field), set()).add(cid)
        else:
            conflicts.append({"child": cid, "field": cf, "names": [], "listed_by": ", ".join(sorted(pids))})

    stems = {i: pth.stem for i, (pth, _fm) in notes.items()}
    edits = []
    for pid, (path, fm) in sorted(notes.items()):
        for pp, field, cp, cf in RULES:
            if prefix(pid) != pp:
                continue
            want = wanted.get((pid, field), set())
            if field not in fm and not (want and pp in ADD_FIELD):
                continue
            edits.append({"id": pid, "path": path, "field": field, "prefix": cp, "cf": cf, "want": want})
    return {"notes": notes, "moves": moves, "conflicts": conflicts, "edits": edits,
            "wanted": wanted, "stems": stems, "moved": moved, "names": names}


def stale(owner, cid, cf, names):
    """True when the child names a different parent of the owner's own kind.

    Only then is the list's entry a stale copy: the task moved to another
    feature, the issue to another phase. A child that names a parent of
    another kind stays listed: in your-trainer an issue's `tasks:` holds the
    task that fixes it, while that task's `parent:` is a feature, and both are
    true.
    """
    same = [i for i in names.get((cid, cf), []) if prefix(i) == prefix(owner)]
    return bool(same) and owner not in same


def drops(owner, raws, cp, cf, names, notes):
    """The listed children whose entry is a stale copy (see `stale`)."""
    out = set()
    for raw in raws:
        cid = item_id(raw, cp)
        if cid and cid in notes and stale(owner, cid, cf, names):
            out.add(cid)
    return out


def apply_note_edits(root, p, write):
    """Rewrite each parent list and each moved child field. Returns changes."""
    changes = []
    by_path = {}
    for mv in p["moves"]:
        path = p["notes"][mv["child"]][0]
        by_path.setdefault(path, []).append(("move", mv))
    for ed in p["edits"]:
        by_path.setdefault(ed["path"], []).append(("list", ed))
    for path, work in sorted(by_path.items()):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        for kind, w in work:
            if kind == "move":
                set_scalar(lines, w["field"], '"[[%s]]"' % w["parent"])
                changes.append({"path": str(path.relative_to(root)), "id": w["child"],
                                "field": w["field"], "added": [w["parent"]], "removed": [], "kind": "move"})
                continue
            b = frontmatter_bounds(lines)
            if b is None:
                continue
            found = find_field(lines, b[0], b[1], w["field"], 0)
            if found is None:
                raws, style, first, last = [], "inline", None, None
            else:
                first, last, style, raws = found
                if style == "scalar":
                    if not str(lines[first]).split(":", 1)[1].strip() in ("", '""', "''", "~", "null"):
                        continue
                    style, raws = "inline", []
            out, added, removed = new_list(raws, w["prefix"], w["want"], p["stems"],
                                           drops(w["id"], raws, w["prefix"], w["cf"], p["names"], p["notes"]))
            if not added and not removed:
                continue
            item_indent = block_item_indent(lines, first, last) if style == "block" else None
            new = render(w["field"], 0, style, out, item_indent)
            if first is None:
                lines[b[1]:b[1]] = new
            else:
                lines[first:last + 1] = new
            changes.append({"path": str(path.relative_to(root)), "id": w["id"], "field": w["field"],
                            "added": added, "removed": removed, "kind": "list"})
        new_text = "".join(lines)
        if write and new_text != text:
            path.write_text(new_text, encoding="utf-8")
    if write and changes:
        validator().invalidate_note_index()
    return changes


# ------------------------------------------------------------ the snapshot

_ITEM = re.compile(r"^(\s+)([A-Z]+-[\w-]+):\s*(\{.*\})?\s*$")


def snapshot_entries(lines):
    """[(id, collection, first line, last line, indent, inline)] under `items:`."""
    out, coll, in_items, cur = [], None, False, None
    for i, line in enumerate(lines):
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            in_items = False
        if not in_items:
            continue
        m = re.match(r"^  ([a-z_]+):\s*$", line)
        if m:
            coll = m.group(1)
            cur = None
            continue
        m = _ITEM.match(line)
        if m and len(m.group(1)) == 4:
            cur = [m.group(2), coll, i, i, 4, bool(m.group(3))]
            out.append(cur)
            continue
        if cur is not None and (line.startswith(" " * 6) or not line.strip()):
            if line.strip():
                cur[3] = i
    return [tuple(e) for e in out]


def sync_snapshot_lists(lines, p):
    """Derive the snapshot's own copies of the lists. Returns changes; edits `lines`.

    A new entry in the snapshot is a bare id unless the list already writes
    its entries another way.
    """
    changes = []
    for the_id, coll, first, last, indent, inline in reversed(snapshot_entries(lines)):
        for pp, field, cp, cf in RULES:
            if pp != prefix(the_id):
                continue
            want = p["wanted"].get((the_id, field), set())
            if inline:
                line = lines[first]
                span = _flow_field(line, field)
                if span is None:
                    continue
                raws = split_flow(line[span[0] + 1:span[1] - 1])
                out, added, removed = new_list(raws, cp, want, {}, drops(the_id, raws, cp, cf, p["names"], p["notes"]), "%s")
                if added or removed:
                    lines[first] = line[:span[0]] + "[" + ", ".join(out) + "]" + line[span[1]:]
                    changes.append({"id": the_id, "field": field, "added": added, "removed": removed})
                continue
            found = find_field(lines, first + 1, last + 1, field, indent + 2)
            if found is None or found[2] == "scalar":
                continue
            f0, f1, style, raws = found
            out, added, removed = new_list(raws, cp, want, {}, drops(the_id, raws, cp, cf, p["names"], p["notes"]), "%s")
            if not added and not removed:
                continue
            item_indent = block_item_indent(lines, f0, f1) if style == "block" else None
            lines[f0:f1 + 1] = render(field, indent + 2, style, out, item_indent)
            changes.append({"id": the_id, "field": field, "added": added, "removed": removed})
    return changes


def _flow_field(line, field):
    """(start, end) of `field: [ ... ]`'s brackets inside an inline flow map."""
    m = re.search(r"[{,]\s*%s:\s*\[" % re.escape(field), line)
    if not m:
        return None
    start = m.end() - 1
    depth, quote = 0, None
    for j in range(start, len(line)):
        ch = line[j]
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return start, j + 1
    return None


def sync_membership(lines, p, snap):
    """Add an `items.tasks` entry for each live task under a live snapshot entry."""
    items = (snap or {}).get("items") or {}
    have = set()
    for coll in items.values():
        if isinstance(coll, dict):
            have.update(coll)
    live_parents = set()
    for coll in ("features", "issues", "phases"):
        for pid, entry in (items.get(coll) or {}).items():
            if isinstance(entry, dict) and str(entry.get("status", "")) not in SETTLED:
                live_parents.add(pid)
    add = []
    for tid, (path, fm) in sorted(p["notes"].items()):
        if prefix(tid) != "TASK" or tid in have or str(fm.get("status", "")) not in LIVE_TASK:
            continue
        parent = p["moved"].get((tid, "parent"))
        parents = [parent] if parent else extract_ids(fm.get("parent"))
        phases = extract_ids(fm.get("phase"))
        if not any(x in live_parents for x in parents + phases):
            continue
        add.append((tid, path, fm, parents, phases))
    if not add:
        return []
    header, in_items = None, False
    for i, line in enumerate(lines):
        if re.match(r"^items:\s*$", line):
            in_items = True
        elif in_items and re.match(r"^\S", line):
            break
        elif in_items and re.match(r"^  tasks:\s*(\{\s*\})?\s*$", line):
            header = i
            break
    if header is None:
        return []
    if lines[header].strip() != "tasks:":
        lines[header] = "  tasks:\n"
    nxt = lines[header + 1] if header + 1 < len(lines) else ""
    m = _ITEM.match(nxt)
    inline = bool(m and m.group(3))
    new = []
    for tid, path, fm, parents, phases in add:
        fields = [("file", '"%s"' % path.relative_to(p["root"]) if inline else str(path.relative_to(p["root"]))),
                  ("status", str(fm.get("status")))]
        if parents:
            fields.append(("parent", parents[0]))
        if phases:
            fields.append(("phase", '"[[%s]]"' % phases[0]))
        if inline:
            new.append("    %s: { %s }\n" % (tid, ", ".join("%s: %s" % kv for kv in fields)))
        else:
            new.append("    %s:\n" % tid)
            new.extend("      %s: %s\n" % kv for kv in fields)
    lines[header + 1:header + 1] = new
    return [t[0] for t in add]


# ------------------------------------------------------------ entry points


def derive(root, snap_lines=None, snap=None, write=False):
    """Run the whole generator. Notes are written when `write`; the snapshot
    lines, when given, are edited in place (the caller writes them)."""
    root = Path(root).resolve()
    p = plan(root)
    p["root"] = root
    note_changes = apply_note_edits(root, p, write)
    snap_changes, added = [], []
    if snap_lines is not None:
        snap_changes = sync_snapshot_lists(snap_lines, p)
        known = {(c["child"], c["listed_by"]) for c in p["conflicts"]}
        for c in snap_changes:
            for cid in c["removed"]:
                cf = next(r[3] for r in RULES if r[0] == prefix(c["id"]) and r[1] == c["field"])
                if (cid, c["id"]) not in known and stale(c["id"], cid, cf, p["names"]):
                    known.add((cid, c["id"]))
                    p["conflicts"].append({"child": cid, "field": cf, "names": p["names"].get((cid, cf), []),
                                           "listed_by": c["id"] + " (SNAPSHOT.yaml)"})
        added = sync_membership(snap_lines, p, snap)
    return {"notes": note_changes, "snapshot": snap_changes, "membership": added,
            "conflicts": p["conflicts"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true", help="write the notes and SNAPSHOT.yaml")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.repo_root).resolve()
    snap_path = root / "SNAPSHOT.yaml"
    text = snap_path.read_text(encoding="utf-8") if snap_path.is_file() else None
    lines = text.splitlines(keepends=True) if text is not None else None
    snap = validator().load_yaml(text) if text is not None else None
    result = derive(root, lines, snap, write=args.apply)
    if args.apply and lines is not None and "".join(lines) != text:
        tmp = snap_path.with_name(".%s.%d.tmp" % (snap_path.name, os.getpid()))
        tmp.write_text("".join(lines), encoding="utf-8")
        os.chmod(tmp, snap_path.stat().st_mode & 0o777)
        os.replace(tmp, snap_path)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0
    verb = "changed" if args.apply else "would change"
    moves = [c for c in result["notes"] if c["kind"] == "move"]
    lists = [c for c in result["notes"] if c["kind"] == "list"]
    print("derive-lists: %s: %s %d note list(s), moved %d fact(s) onto the child, "
          "%s %d snapshot list(s), %s %d snapshot entr(ies); %d conflict(s)"
          % (root.name, verb, len(lists), len(moves), verb, len(result["snapshot"]),
             "added" if args.apply else "would add", len(result["membership"]), len(result["conflicts"])))
    for c in moves:
        print("   move    %-10s %s: %s" % (c["id"], c["field"], c["added"][0]))
    for c in lists:
        print("   list    %-10s %s%s%s" % (c["id"], c["field"],
              " +" + ",".join(c["added"]) if c["added"] else "", " -" + ",".join(c["removed"]) if c["removed"] else ""))
    for c in result["snapshot"]:
        print("   snap    %-10s %s%s%s" % (c["id"], c["field"],
              " +" + ",".join(c["added"]) if c["added"] else "", " -" + ",".join(c["removed"]) if c["removed"] else ""))
    for tid in result["membership"]:
        print("   entry   %s" % tid)
    for c in result["conflicts"]:
        print("   CONFLICT %s %s names %s, but %s lists it; the child's field wins"
              % (c["child"], c["field"], ", ".join(c["names"]) or "nothing", c["listed_by"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
