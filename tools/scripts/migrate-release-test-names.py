#!/usr/bin/env python3
"""Move a repo's own files from the walk's names to the release test's names.

project-os-dev ADR-0050 renamed the walk to the release test, internal names
included, in one template release. The template's own files arrive with a sync.
The files this repo authored do not, and this script moves them once:

  docs/tests/acceptance/WALK.md      -> docs/tests/acceptance/RELEASE-TEST.md
  docs/tests/acceptance/walk/        -> docs/tests/acceptance/release-test/
  `sitting:` in a procedure          -> `section:`
  `walk_readiness_for:` on a check   -> `readiness_for:`
  CLAUDE.md's skill line             -> tools/skills/release-test-procedure/SKILL.md
  `"mark":` in an unsealed ledger    -> `"result":`

A file moves with `git mv` when git tracks it, so its history follows it.

**A sealed ledger is never rewritten.** It is a record, and a release note
vouches for its bytes. Every reader accepts `mark` for good, so a sealed
ledger stays valid as it is. Only an open ledger, one with no `sealed:` value,
is rewritten, because the tool that writes to it next writes `result`.

**Nothing is overwritten.** Where both the old and the new name exist, the
item is reported as a conflict and left alone, and the exit status is 2.

Running it a second time changes nothing. After it, `validate-docs.sh` reports
any old name it finds as an error that names the new one (OLD-NAME).

Stdlib only. Usage:
    migrate-release-test-names.py [--repo-root .]          # dry run: what would change
    migrate-release-test-names.py --apply                  # make the changes
    migrate-release-test-names.py --check                  # exit 1 if anything would change
Exit codes: 0 = done or nothing to do, 1 = --check found work, 2 = a conflict.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ORDER_OLD = "docs/tests/acceptance/WALK.md"
ORDER_NEW = "docs/tests/acceptance/RELEASE-TEST.md"
FOLDER_OLD = "docs/tests/acceptance/walk"
FOLDER_NEW = "docs/tests/acceptance/release-test"
LEDGERS = "docs/releases/ledgers"
SKILL_OLD = "tools/skills/walk-procedure/"
SKILL_NEW = "tools/skills/release-test-procedure/"
#: The skill line the template's CLAUDE.md carried before the rename.
SKILL_LINE_RE = re.compile(r"^(\s*-\s*)Walk procedure:(\s*)tools/skills/walk-procedure/SKILL\.md\s*$", re.M)
#: A top-level frontmatter key, at the start of its line.
KEY_RE = "^%s:(?=\\s|$)"
#: `"mark":` as a JSON key. Inside a JSON string every quote is escaped, so
#: the pattern cannot match string content; the edit is re-parsed anyway.
MARK_KEY_RE = re.compile(r'"mark"(\s*):')


class Plan:
    def __init__(self) -> None:
        self.moves: list[tuple[str, str]] = []
        self.edits: dict[str, str] = {}      # path -> new text
        self.notes: list[str] = []           # one line per change, for the report
        self.conflicts: list[str] = []

    @property
    def empty(self) -> bool:
        return not self.moves and not self.edits


def frontmatter_span(text: str) -> tuple[int, int]:
    """(start, end) of the frontmatter's body in ``text``, or (0, 0) if none."""
    if not text.startswith("---"):
        return 0, 0
    first = text.find("\n")
    end = text.find("\n---", first)
    if first == -1 or end == -1:
        return 0, 0
    return first + 1, end + 1


def rename_key(text: str, old: str, new: str) -> tuple[str, str]:
    """(new text, problem) with frontmatter key ``old`` renamed to ``new``."""
    start, end = frontmatter_span(text)
    if not end:
        return text, ""
    front = text[start:end]
    if not re.search(KEY_RE % re.escape(old), front, re.M):
        return text, ""
    if re.search(KEY_RE % re.escape(new), front, re.M):
        return text, "has both `%s:` and `%s:`; keep one by hand" % (old, new)
    front = re.sub(KEY_RE % re.escape(old), new + ":", front, count=1, flags=re.M)
    return text[:start] + front + text[end:], ""


def new_path(rel: str) -> str:
    """Where a file under the old procedure folder goes."""
    if rel == ORDER_OLD:
        return ORDER_NEW
    if rel.startswith(FOLDER_OLD + "/"):
        return FOLDER_NEW + rel[len(FOLDER_OLD):]
    return rel


def migrate_ledger(text: str) -> tuple[str, str]:
    """(new text, problem) for one open ledger: every entry's `mark` becomes `result`.

    The text is edited in place, so a ledger written one entry per line stays
    that way. The edit is then read back and compared with the same change made
    to the parsed JSON; if they differ, the file is written from that JSON.
    """
    try:
        data = json.loads(text)
    except ValueError as exc:
        return text, "is not readable as JSON (%s)" % exc
    if not isinstance(data, dict) or str(data.get("sealed") or "").strip():
        return text, ""
    entries = data.get("entries") or []
    if not any(isinstance(e, dict) and "mark" in e for e in entries):
        return text, ""
    want = json.loads(text)
    for entry in want.get("entries") or []:
        if not isinstance(entry, dict) or "mark" not in entry:
            continue
        if "result" in entry:
            if entry["result"] != entry["mark"]:
                return text, ("has an entry for %s with result %r and mark %r; keep one by hand"
                              % (entry.get("check"), entry["result"], entry["mark"]))
            del entry["mark"]
            continue
        entry["result"] = entry.pop("mark")
    out = MARK_KEY_RE.sub(r'"result"\1:', text)
    try:
        if json.loads(out) == want:
            return out, ""
    except ValueError:
        pass
    #: The text edit could not be matched to the JSON change -- an entry with
    #: both keys, or `"mark"` used as a key outside an entry. Rewrite it whole.
    return json.dumps(want, indent=2, ensure_ascii=False) + "\n", ""


def plan(root: Path) -> Plan:
    p = Plan()
    docs = root / "docs"

    # 1. The section order file.
    if (root / ORDER_OLD).is_file():
        if (root / ORDER_NEW).exists():
            p.conflicts.append("%s and %s both exist; merge them by hand" % (ORDER_OLD, ORDER_NEW))
        else:
            p.moves.append((ORDER_OLD, ORDER_NEW))

    # 2. The procedure folder, file by file, so a partly moved folder finishes.
    old_dir = root / FOLDER_OLD
    procedures: list[str] = []
    if old_dir.is_dir():
        for path in sorted(q for q in old_dir.rglob("*") if q.is_file()):
            rel = path.relative_to(root).as_posix()
            target = new_path(rel)
            if (root / target).exists():
                p.conflicts.append("%s and %s both exist; merge them by hand" % (rel, target))
                continue
            p.moves.append((rel, target))
            if rel.endswith(".md"):
                procedures.append(rel)
    new_dir = root / FOLDER_NEW
    if new_dir.is_dir():
        procedures += sorted(q.relative_to(root).as_posix() for q in new_dir.rglob("*.md"))

    # 3. `sitting:` -> `section:` in every procedure, wherever it now lives.
    for rel in procedures:
        text = (root / rel).read_text(encoding="utf-8")
        out, problem = rename_key(text, "sitting", "section")
        if problem:
            p.conflicts.append("%s %s" % (rel, problem))
        elif out != text:
            p.edits[new_path(rel)] = out
            p.notes.append("%s: `sitting:` -> `section:`" % new_path(rel))

    # 4. `walk_readiness_for:` -> `readiness_for:` on any note. The template's
    #    own folders are the sync's to update, not this script's.
    moved = {old for old, _new in p.moves}
    if docs.is_dir():
        for path in sorted(docs.rglob("*.md")):
            if "__templates__" in path.parts or "__bases__" in path.parts:
                continue
            rel = path.relative_to(root).as_posix()
            key = new_path(rel) if rel in moved else rel
            text = p.edits.get(key) or path.read_text(encoding="utf-8")
            if "walk_readiness_for" not in text:
                continue
            out, problem = rename_key(text, "walk_readiness_for", "readiness_for")
            if problem:
                p.conflicts.append("%s %s" % (rel, problem))
            elif out != text:
                p.edits[key] = out
                p.notes.append("%s: `walk_readiness_for:` -> `readiness_for:`" % key)

    # 5. CLAUDE.md's skill list.
    claude = root / "CLAUDE.md"
    if claude.is_file():
        text = claude.read_text(encoding="utf-8")
        out = SKILL_LINE_RE.sub(r"\1Release test procedure:\2" + SKILL_NEW + "SKILL.md", text)
        out = out.replace(SKILL_OLD, SKILL_NEW)
        if out != text:
            p.edits["CLAUDE.md"] = out
            p.notes.append("CLAUDE.md: the skill line names %sSKILL.md" % SKILL_NEW)

    # 6. Open ledgers: `mark` -> `result`.
    ledgers = root / LEDGERS
    if ledgers.is_dir():
        for path in sorted(ledgers.glob("*.json")):
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            out, problem = migrate_ledger(text)
            if problem:
                p.conflicts.append("%s %s" % (rel, problem))
            elif out != text:
                p.edits[rel] = out
                p.notes.append("%s: each entry's `mark` -> `result`" % rel)
    return p


def tracked(root: Path, rel: str) -> bool:
    try:
        done = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", rel],
                              capture_output=True, text=True)
    except OSError:
        return False
    return done.returncode == 0


def apply(root: Path, p: Plan) -> None:
    for old, new in p.moves:
        (root / new).parent.mkdir(parents=True, exist_ok=True)
        if tracked(root, old):
            subprocess.run(["git", "-C", str(root), "mv", "--", old, new], check=True,
                           capture_output=True)
        else:
            (root / old).rename(root / new)
    for rel, text in p.edits.items():
        (root / rel).write_text(text, encoding="utf-8")
    old_dir = root / FOLDER_OLD
    if old_dir.is_dir():
        for folder in sorted((q for q in old_dir.rglob("*") if q.is_dir()), reverse=True):
            if not any(folder.iterdir()):
                folder.rmdir()
        if not any(old_dir.iterdir()):
            old_dir.rmdir()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true", help="make the changes")
    ap.add_argument("--check", action="store_true",
                    help="change nothing; exit 1 if anything would change")
    args = ap.parse_args(argv)
    root = Path(args.repo_root).resolve()
    p = plan(root)
    verb = "moved" if args.apply else "would move"
    if p.empty and not p.conflicts:
        print("migrate-release-test-names: nothing to do; this repo uses the release test names")
        return 0
    print("migrate-release-test-names: %s %d file(s) and %s %d"
          % (verb, len(p.moves), "edited" if args.apply else "would edit", len(p.edits)))
    for old, new in p.moves:
        print("   move  %s -> %s" % (old, new))
    for line in p.notes:
        print("   edit  %s" % line)
    for line in p.conflicts:
        print("   CONFLICT  %s" % line)
    if args.check:
        return 2 if p.conflicts else (1 if not p.empty else 0)
    if args.apply:
        apply(root, p)
        print("migrate-release-test-names: done. Run `bash tools/scripts/validate-docs.sh`; "
              "it reports any old name left as OLD-NAME.")
    else:
        print("migrate-release-test-names: dry run; add --apply to make these changes.")
    return 2 if p.conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
