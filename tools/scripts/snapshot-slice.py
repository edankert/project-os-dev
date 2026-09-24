#!/usr/bin/env python3
"""Print the part of SNAPSHOT.yaml a session needs at its start (HC-002).

project-os-dev TASK-0080. The SessionStart hooks and tools/agents/bootstrap.sh
print this instead of telling the agent to read the whole snapshot: measured
uptake of that instruction was 5 of 260 sessions (ISS-0031), and the file runs
to 400 KB in some repos.

What it prints: the focus items with their statuses and note paths, the focus
note cut to FOCUS_NOTE_CHARS, one line of counts, and every in-flight item
(a task or feature at `doing`/`review`, an issue at `open`/`triage`, a phase at
`active`) as ID, status and note path. Titles are left out on purpose: the note
path carries the slug, and titles are what made one repo's slice 11,573 tokens.
The whole output is capped at MAX_CHARS (about 1,500 tokens); items past the cap
are counted, not listed.

Reads both snapshot styles in the fleet: block items (`    TASK-0001:` then
`      status: doing`) and inline flow maps (`    TASK-0001: { status: doing }`).
Standard library only. Exits 1 without output when the snapshot is missing or
yields nothing, so callers can fall back to their old reminder.
"""

import re
import sys
from pathlib import Path

MAX_CHARS = 6000
FOCUS_NOTE_CHARS = 400
IN_FLIGHT = {
    "tasks": ("doing", "review"),
    "features": ("doing", "review"),
    "issues": ("open", "triage"),
    "phases": ("active",),
}
CONTRACT_FILES = ("AGENTS.md", "CONTEXT.md", "docs/INDEX.md")
ID = re.compile(r"[A-Z]+-\d+")


def scalar(raw):
    """A YAML scalar as text: comment dropped, quotes removed."""
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        quote = raw[0]
        end = raw.find(quote, 1)
        while quote == '"' and end > 0 and raw[end - 1] == "\\":
            end = raw.find(quote, end + 1)
        return raw[1:end] if end > 0 else raw[1:]
    return raw.split(" #", 1)[0].strip()


def flow_map(text):
    """The top-level key: value pairs of an inline `{ ... }` map."""
    body = text.strip()
    if body.startswith("{"):
        body = body[1:]
    if body.endswith("}"):
        body = body[:-1]
    pairs, depth, quote, start = {}, 0, "", 0
    parts = []
    for i, ch in enumerate(body):
        if quote:
            if ch == quote and body[i - 1] != "\\":
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(body[start:i])
            start = i + 1
    parts.append(body[start:])
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            pairs[key.strip()] = scalar(value)
    return pairs


def parse(text):
    """updated, focus, metrics.counts and items.<collection>.<id> (status, file)."""
    updated, focus, counts, items = "", {}, {}, {}
    section = sub = current = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            section, sub, current = stripped.split(":", 1)[0], None, None
            if section == "updated":
                updated = scalar(stripped.split(":", 1)[1])
            continue
        key, _, value = stripped.partition(":")
        if section == "focus" and indent == 2:
            focus[key] = scalar(value)
        elif section == "metrics" and indent == 2:
            sub = key
        elif section == "metrics" and sub == "counts" and indent == 4:
            counts[key] = scalar(value)
        elif section == "items" and indent == 2:
            sub, current = key, None
            items.setdefault(sub, {})
        elif section == "items" and sub and indent == 4 and ID.fullmatch(key):
            current = key
            value = value.strip()
            items[sub][key] = flow_map(value) if value.startswith("{") else {}
        elif section == "items" and current and indent == 6 and key in ("status", "file"):
            items[sub][current][key] = scalar(value)
    return updated, focus, counts, items


def bare_id(value):
    match = ID.search(value or "")
    return match.group(0) if match else ""


def render(root):
    snapshot = root / "SNAPSHOT.yaml"
    try:
        text = snapshot.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    if re.search(r"^\s*replace_me:\s*true", text, re.M):
        return ""
    updated, focus, counts, items = parse(text)
    index = {i: (col, fields) for col, members in items.items() for i, fields in members.items()}
    if not focus and not index:
        return ""

    def describe(item_id):
        _, fields = index.get(item_id, ("", {}))
        status = fields.get("status", "?")
        path = fields.get("file", "")
        return "%s (%s)%s" % (item_id, status, " " + path if path else "")

    lines = ["project-os orientation from SNAPSHOT.yaml (updated %s). This is the part of the snapshot a session needs; do not read the whole file." % (updated or "unknown")]
    missing = [f for f in CONTRACT_FILES if not (root / f).exists()]
    if missing:
        lines.append("MISSING contract files: %s. Restore them before implementation (HC-002)." % ", ".join(missing))
    focused = []
    for key in ("phase", "feature", "task", "issue"):
        item_id = bare_id(focus.get(key, ""))
        if item_id:
            focused.append(item_id)
            lines.append("focus.%s: %s" % (key, describe(item_id)))
    if not focused:
        lines.append("focus: nothing set")
    note = focus.get("note") or focus.get("notes") or ""
    if note:
        cut = note if len(note) <= FOCUS_NOTE_CHARS else note[:FOCUS_NOTE_CHARS].rsplit(" ", 1)[0] + " [...]"
        lines.append("focus.note: " + cut)
    if counts:
        lines.append("counts: " + ", ".join("%s %s" % (k, v) for k, v in counts.items()))

    flight = [i for col, statuses in IN_FLIGHT.items() for i, f in items.get(col, {}).items()
              if f.get("status") in statuses and i not in focused]
    lines.append("in flight (%d, besides focus):" % len(flight))
    closing = ("Before changing anything, open the note of the item you are working on and the notes it links, "
               "including ones the request does not name. For any other item, find its `file:` under its ID in SNAPSHOT.yaml and open the note.")
    budget = MAX_CHARS - len(closing) - 60
    used = sum(len(l) + 1 for l in lines)
    shown = 0
    for item_id in flight:
        entry = "  " + describe(item_id)
        if used + len(entry) + 1 > budget:
            break
        lines.append(entry)
        used += len(entry) + 1
        shown += 1
    if shown < len(flight):
        lines.append("  ... and %d more, not listed to keep this short" % (len(flight) - shown))
    lines.append(closing)
    return "\n".join(lines)


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    out = render(root)
    if not out:
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception:  # fail open: callers fall back to their reminder
        sys.exit(1)
