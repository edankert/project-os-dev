#!/usr/bin/env python3
"""Strip `id:`/`aliases:` from typed plan notes, and re-point inbound links.

Plans deliberately carry no ID. `PLAN-FEAT-0012` contains `FEAT-0012`, so
`extract_ids` reads the feature's ID out of the plan's own, letting the plan
claim its feature's entry in the note index and answer lookups meant for the
feature. The PLAN-ID check enforces this; see tools/instructions/STATUSES.md,
`[[plan]]`.

Repos written before that check exists carry the pattern the old template
taught. This migrates them:

  1. Removes `id:` and `aliases:` from any note with `type: "[[plan]]"`.
  2. Rewrites inbound `[[PLAN-FEAT-0012]]` wiki-links to a relative path link,
     because an ID-less note cannot be reached by ID. Dropping the link text
     entirely would lose a real pointer a reader follows.

Only touches notes whose `type:` is `[[plan]]` -- a `PLAN-*` filename is not
enough, since an untyped PLAN.md is prose and carries no contract.

Usage:  python3 migrate-plan-ids.py --dry-run <repo>...
        python3 migrate-plan-ids.py <repo>...
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

PLAN_TYPE_RE = re.compile(r'^type:\s*"?\[\[plan\]\]"?\s*$', re.MULTILINE)
ID_LINE_RE = re.compile(r'^id:\s*(?P<id>PLAN-[A-Z]+-\d+)\s*$', re.MULTILINE)
ALIASES_LINE_RE = re.compile(r'^aliases:\s*\[[^\]]*\]\s*$', re.MULTILINE)


def is_plan_note(text: str) -> bool:
    """True only for notes whose frontmatter declares the plan type."""
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    return bool(PLAN_TYPE_RE.search(text[:end]))


def strip_plan_id(text: str) -> tuple[str, str | None]:
    """Remove `id:`/`aliases:` from a plan's frontmatter. Returns the ID found."""
    end = text.find("\n---", 3)
    if end == -1:
        return text, None
    head, tail = text[: end + 1], text[end + 1 :]

    m = ID_LINE_RE.search(head)
    if not m:
        return text, None
    plan_id = m.group("id")

    head = ID_LINE_RE.sub("", head, count=1)
    # Only drop an aliases line that is about this plan. A plan aliasing
    # something else is not this migration's business.
    def drop_alias(match: re.Match) -> str:
        return "" if plan_id in match.group(0) else match.group(0)

    head = ALIASES_LINE_RE.sub(drop_alias, head, count=1)
    head = re.sub(r"\n{3,}", "\n\n", head)
    return head + tail, plan_id


def repoint_links(text: str, targets: dict[str, str], from_path: pathlib.Path,
                  docs_root: pathlib.Path) -> tuple[str, int]:
    """Rewrite `[[PLAN-FEAT-0012]]` to a relative Markdown link to the file."""
    hits = 0

    def sub(m: re.Match) -> str:
        nonlocal hits
        plan_id = m.group("id")
        rel_target = targets.get(plan_id)
        if not rel_target:
            return m.group(0)
        label = m.group("label") or "the delivery plan"
        try:
            href = pathlib.posixpath.relpath(
                rel_target, pathlib.PurePosixPath(
                    from_path.relative_to(docs_root).as_posix()).parent.as_posix()
            )
        except ValueError:
            return m.group(0)
        hits += 1
        return f"[{label}]({href})"

    pattern = re.compile(
        r"\[\[(?P<id>PLAN-[A-Z]+-\d+)(?:\|(?P<label>[^\]]+))?\]\]"
    )
    return pattern.sub(sub, text), hits


def run(root: pathlib.Path, dry: bool) -> dict[str, int]:
    stats = {"plans": 0, "links": 0, "files_relinked": 0}
    docs = root / "docs"
    if not docs.is_dir():
        return stats

    notes = [p for p in docs.rglob("*.md") if "__templates__" not in p.parts]

    # Pass 1 -- strip IDs, and record where each stripped plan lives so pass 2
    # can point at it. Both passes are needed before any write in dry-run mode,
    # which is why the edits are staged rather than written as they are found.
    staged: dict[pathlib.Path, str] = {}
    targets: dict[str, str] = {}
    for path in notes:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not is_plan_note(text):
            continue
        new, plan_id = strip_plan_id(text)
        if plan_id:
            stats["plans"] += 1
            staged[path] = new
            targets[plan_id] = path.relative_to(docs).as_posix()

    # Pass 2 -- re-point inbound links, including links inside plans themselves.
    for path in notes:
        try:
            text = staged.get(path) or path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new, hits = repoint_links(text, targets, path, docs)
        if hits:
            stats["links"] += hits
            stats["files_relinked"] += 1
            staged[path] = new

    if not dry:
        for path, text in staged.items():
            path.write_text(text, encoding="utf-8")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for r in args.repos:
        root = pathlib.Path(r).expanduser()
        if not (root / "SNAPSHOT.yaml").is_file():
            print(f"  {root.name:<26} SKIP (not a project-os repo)")
            continue
        s = run(root, args.dry_run)
        print(f"  {root.name:<26} {s['plans']:>3} plan(s) de-ID'd"
              f" | {s['links']:>3} link(s) re-pointed in {s['files_relinked']} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
