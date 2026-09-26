#!/usr/bin/env python3
"""Drop the verdict fields ADR-0037 moved into the ledger, where the ledger holds them.

project-os-dev ISS-0099 (TASK-0183). In a repo that keeps acceptance ledgers,
LEDGER-FIELD warns on every acceptance check still carrying a field ADR-0037
moved off the note: 654 warnings a run in your-trainer. The fix is the same for
every note, so it is one pass, not 654 edits. A field is dropped only when
dropping it loses nothing:

  empty                      "", [], {} or a `todo` mark: no fact to lose
  mark                       the ledger has an entry for the check with the
                             same verdict (done -> pass, incomplete -> partial,
                             canceled -> na, the backfill's mapping)
  verdict_date               the ledger has an entry for the check on that date
  verdict_reason             the ledger has an entry for the check whose reason
                             contains the note's text
  invalidated_by             every id it names invalidates the check in a ledger
  automation                 `manual` (the default), or the ledger holds an
                             automated verdict for the check
  evidence                   every item is in a ledger's evidence for the check
  section, ordinal,          dead provenance (ISS-0224, ISS-0233); git holds it
  migrated_from, merged_from,
  burden

Anything else stays, and the report says why: a `covered_by:` nobody has
turned into a test's `@Covers` yet, a verdict the ledger does not have. Those
are a person's to move.

Usage:
    migrate-ledger-fields.py [--repo-root .]     # dry run, with a report
    migrate-ledger-fields.py --apply
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKS = {"done": "pass", "incomplete": "partial", "canceled": "na", "todo": None, "": None}
PROVENANCE = {"section", "ordinal", "migrated_from", "merged_from", "burden"}


def validator():
    spec = importlib.util.spec_from_file_location("_vd_ledger_migrate", HERE / "validate-docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ids_in(value):
    text = json.dumps(value) if not isinstance(value, str) else value
    return set(re.findall(r"[A-Z]+-\d{2,}[A-Za-z]?(?:-[A-Za-z0-9-]+)?", text))


def read_ledgers(root, rel):
    """{check id: {"entries": [...], "evidence": [...]}} across every ledger."""
    out = collections.defaultdict(lambda: {"entries": [], "evidence": []})
    for path in sorted((root / "docs" / rel).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for entry in data.get("entries") or []:
            if isinstance(entry, dict) and entry.get("check"):
                out[str(entry["check"])]["entries"].append(entry)
        for item in data.get("evidence") or []:
            if isinstance(item, dict) and item.get("check"):
                out[str(item["check"])]["evidence"].append(item)
    return out


def empty(value):
    return value is None or value == "" or value == [] or value == {} or (isinstance(value, str) and not value.strip())


def verdict(field, value, held):
    """(drop?, reason kept) for one field of one note."""
    entries, evidence = held["entries"], held["evidence"]
    if field in PROVENANCE:
        return True, ""
    if field == "mark":
        text = str(value).strip()
        if text not in MARKS:
            return False, "mark `%s` has no ledger equivalent" % text
        want = MARKS[text]
        if want is None or any(e.get("mark") == want for e in entries):
            return True, ""
        return False, "the ledger has no `%s` for it" % want
    if empty(value):
        return True, ""
    if field == "verdict_date":
        if any(str(e.get("date", "")) == str(value) for e in entries):
            return True, ""
        return False, "no ledger entry is dated %s" % value
    if field == "verdict_reason":
        needle = " ".join(str(value).split())[:60]
        if any(needle and needle in " ".join(str(e.get("reason", "")).split()) for e in entries):
            return True, ""
        return False, "its verdict_reason is in no ledger entry"
    if field == "invalidated_by":
        named = ids_in(value)
        held_ids = set()
        for e in entries:
            if e.get("invalidated_by"):
                held_ids |= ids_in(e["invalidated_by"])
        if named and named <= held_ids:
            return True, ""
        return False, "its invalidated_by names %s, which no ledger records" % ", ".join(sorted(named - held_ids) or ["text"])
    if field == "automation":
        if str(value).strip() == "manual" or any(e.get("method") == "automated" for e in entries):
            return True, ""
        return False, "automation `%s` and no automated verdict in a ledger yet" % value
    if field == "evidence":
        items = value if isinstance(value, list) else [value]
        held_paths = json.dumps(evidence)
        if all(str(i) in held_paths for i in items):
            return True, ""
        return False, "its evidence is in no ledger"
    if field == "covered_by":
        return False, "covered_by names %s; move it to the test's @Covers first (ADR-0037 stage 2)" % ", ".join(map(str, value if isinstance(value, list) else [value]))
    return False, "no rule for `%s`" % field


def drop_fields(text, fields):
    """The note's text without the named top-level frontmatter fields."""
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        return text
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\n") == "---"), None)
    if end is None:
        return text
    out, skipping = [lines[0]], False
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z_][\w-]*):", line)
        if m:
            skipping = m.group(1) in fields
        elif not (line.startswith((" ", "\t", "-")) or not line.strip()):
            skipping = False
        if not skipping:
            out.append(line)
    return "".join(out + lines[end:])


def plan(root):
    vd = validator()
    rel = vd.LEDGERS_REL
    if not any((root / "docs" / rel).glob("*.json")):
        return None, "this repo keeps no ledgers, so LEDGER-FIELD does not apply"
    ledgers = read_ledgers(root, rel)
    notes = []
    for path in sorted((root / "docs").rglob("*.md")):
        if "__templates__" in path.parts:
            continue
        fm = vd.parse_frontmatter(path)
        if not isinstance(fm, dict) or str(fm.get("level", "") or "").strip().lower() != "acceptance":
            continue
        present = [f for f in vd.LEDGER_MOVED_FIELDS if f in fm]
        if not present:
            continue
        check = str(fm.get("id", "") or "").strip() or path.stem
        held = ledgers.get(check, {"entries": [], "evidence": []})
        drop, keep = [], []
        for field in present:
            ok, why = verdict(field, fm[field], held)
            (drop.append(field) if ok else keep.append((field, why)))
        notes.append({"id": check, "path": path, "drop": drop, "keep": keep})
    return notes, ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.repo_root).resolve()
    notes, why_not = plan(root)
    if notes is None:
        print("migrate-ledger-fields: nothing to do; %s" % why_not)
        return 0
    cleared = [n for n in notes if n["drop"] and not n["keep"]]
    partly = [n for n in notes if n["drop"] and n["keep"]]
    untouched = [n for n in notes if not n["drop"]]
    reasons = collections.Counter(re.sub(r"[A-Z]+-\d+[\w-]*", "X", why)
                                  for n in notes for _f, why in n["keep"])
    print("migrate-ledger-fields: %s %d of %d notes' LEDGER-FIELD findings; %d more lose some fields; %d keep all"
          % ("cleared" if args.apply else "would clear", len(cleared), len(notes), len(partly), len(untouched)))
    for why, n in reasons.most_common():
        print("   kept %4d  %s" % (n, why))
    if args.apply:
        for n in notes:
            if n["drop"]:
                text = n["path"].read_text(encoding="utf-8")
                n["path"].write_text(drop_fields(text, set(n["drop"])), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
