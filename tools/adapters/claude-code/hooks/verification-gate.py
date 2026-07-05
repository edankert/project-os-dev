#!/usr/bin/env python3
"""HC-003: Verification Gate (blocking).

Claude Code PreToolUse hook for Write|Edit. Denies an edit that transitions an
item to a terminal status (task done, issue closed/fixed->closed, requirement
verified, feature done) while any linked TST-* note is not `status: passing`.

Escape hatches (both are recorded artifacts, not silence):
  - the new content or the existing note carries `verification_waiver: <reason>`
  - no tests are linked at all -> "ask" (surface the decision to the human
    instead of hard-denying; QUALITY.md requires verification but the gate
    cannot tell an implementation task from a docs-only chore)

Fail-open on parse errors (a broken gate must not brick every edit), fail-closed
on confirmed violations. Prints hookSpecificOutput JSON per Claude Code hooks.
"""

import json
import re
import sys
from pathlib import Path

TERMINAL_RE = re.compile(r"status:\s*[\"']?(done|closed|verified)[\"']?\b")
ID_RE = re.compile(r"\b((?:TASK|ISS|REQ|FEAT))-(\d{2,})\b")
TST_RE = re.compile(r"\bTST-\d{2,}\b")
WAIVER_RE = re.compile(r"verification_waiver:\s*\S")


def emit(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))


def frontmatter_text(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[4:end] if end != -1 else ""


def note_index(project_dir):
    """Map ID -> note path for docs/ notes (filename or frontmatter id)."""
    index = {}
    docs = project_dir / "docs"
    if not docs.is_dir():
        return index
    for p in docs.rglob("*.md"):
        if "__templates__" in p.parts or "__bases__" in p.parts:
            continue
        m = re.match(r"((?:TASK|ISS|REQ|FEAT|TST|PHASE|RISK|WF|ADR|REL)-\d{2,})", p.name)
        if m:
            index.setdefault(m.group(1), p)
    return index


def tst_status(tst_id, project_dir, index):
    path = index.get(tst_id)
    if path is None:
        return None
    m = re.search(r"^status:\s*[\"']?([\w-]+)", frontmatter_text(path), re.MULTILINE)
    return m.group(1) if m else None


def linked_tests(item_id, project_dir, index, new_content):
    """Collect TST ids linked to the item from its note, the snapshot, and the pending edit."""
    tests = set(TST_RE.findall(new_content))
    note = index.get(item_id)
    if note is not None:
        tests.update(TST_RE.findall(frontmatter_text(note)))
    snap = project_dir / "SNAPSHOT.yaml"
    if snap.is_file():
        try:
            lines = snap.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        in_item = False
        item_indent = 0
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip(" "))
            if re.match(r"^%s\s*:" % re.escape(item_id), stripped):
                in_item, item_indent = True, indent
                continue
            if in_item:
                if stripped and indent <= item_indent:
                    in_item = False
                    continue
                tests.update(TST_RE.findall(line))
    return tests


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0  # fail open: unparseable hook input
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    new_content = tool_input.get("new_string") or tool_input.get("content") or ""
    if not file_path or not new_content:
        return 0
    if not (file_path.endswith("SNAPSHOT.yaml") or ("/docs/" in file_path and file_path.endswith(".md"))):
        return 0
    if not TERMINAL_RE.search(new_content):
        return 0

    project_dir = Path(payload.get("cwd") or ".").resolve()
    if not (project_dir / "SNAPSHOT.yaml").is_file():
        import os
        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
    if not (project_dir / "SNAPSHOT.yaml").is_file():
        return 0  # not a project-os repo

    # Which items is this edit touching? Note edits: the note's own ID. Snapshot edits: IDs present in the new content.
    ids = set("%s-%s" % m for m in ID_RE.findall(new_content))
    note_match = re.match(r"((?:TASK|ISS|REQ|FEAT)-\d{2,})", Path(file_path).name)
    if note_match:
        ids = {note_match.group(1)}
    if not ids:
        return 0

    if WAIVER_RE.search(new_content):
        return 0  # waiver recorded in this very edit; validator will log it as a warning

    index = note_index(project_dir)
    blocked, untested = [], []
    for item_id in sorted(ids):
        note = index.get(item_id)
        if note is not None and WAIVER_RE.search(frontmatter_text(note)):
            continue
        tests = linked_tests(item_id, project_dir, index, new_content)
        if not tests:
            untested.append(item_id)
            continue
        for tst in sorted(tests):
            status = tst_status(tst, project_dir, index)
            if status != "passing":
                blocked.append("%s -> %s is '%s'" % (item_id, tst, status or "missing"))

    if blocked:
        emit("deny", "Verification gate (HC-003): terminal status set while linked tests are not passing: %s. Make the tests pass first, or record an explicit `verification_waiver: <reason>` in the note frontmatter." % "; ".join(blocked))
        return 0
    if untested:
        emit("ask", "Verification gate (HC-003): %s transitioning to a terminal status with no linked TST-* found. QUALITY.md requires a verifying test for implementation work; approve only if this is a docs-only/chore item, otherwise link a test or record a `verification_waiver`." % ", ".join(untested))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
