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
#: An item key: a change note's id carries its slug (CHG-20260925-Some-Title),
#: so a key is matched whole, not cut at the number (FEAT-0021 review).
ITEM_KEY = re.compile(r"[A-Z]+-\d+[A-Za-z]?(?:-[A-Za-z0-9_.]+)*")  # CHG-20260531e-...: a letter orders one day's changes


def split_top(body):
    """Split a flow body at its top-level commas, quotes and brackets respected."""
    parts, depth, quote, start = [], 0, "", 0
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
    return [part for part in parts if part.strip()]


def flow_list(text):
    """`[a, "b, c"]` as a list of scalars."""
    body = text.strip()
    body = body[1:-1] if body.startswith("[") and body.endswith("]") else body
    return [scalar(part) for part in split_top(body)]


def scalar(raw):
    """A YAML scalar as text: comment dropped, quotes removed, escapes read.

    In a double-quoted string, `\\"` is a quote, `\\\\` a backslash, `\\n` and
    `\\t` a newline and a tab, `\\u2019` and its `\\x`/`\\U` kin the character; in a single-quoted one, `''` is a quote. The
    FEAT-0021 round-two review found `\\"` kept as written in about 30 prose
    fields across the fleet.
    """
    raw = raw.strip()
    if raw[:1] == '"':
        out, i = [], 1
        while i < len(raw):
            ch = raw[i]
            if ch == "\\" and i + 1 < len(raw):
                code = raw[i + 1]
                width = {"x": 2, "u": 4, "U": 8}.get(code, 0)
                digits = raw[i + 2:i + 2 + width]
                if width and len(digits) == width and all(c in "0123456789abcdefABCDEF" for c in digits):
                    out.append(chr(int(digits, 16)))
                    i += 2 + width
                    continue
                out.append({"n": "\n", "t": "\t"}.get(code, code))
                i += 2
                continue
            if ch == '"':
                break
            out.append(ch)
            i += 1
        return "".join(out)
    if raw[:1] == "'":
        out, i = [], 1
        while i < len(raw):
            if raw[i] == "'":
                if raw[i + 1:i + 2] == "'":
                    out.append("'")
                    i += 2
                    continue
                break
            out.append(raw[i])
            i += 1
        return "".join(out)
    return raw.split(" #", 1)[0].strip()


def flow_map(text):
    """The top-level key: value pairs of an inline `{ ... }` map; lists as lists."""
    body = text.strip()
    if body.startswith("{"):
        body = body[1:]
    if body.endswith("}"):
        body = body[:-1]
    pairs = {}
    for part in split_top(body):
        if ":" in part:
            key, value = part.split(":", 1)
            value = value.strip()
            pairs[key.strip()] = flow_list(value) if value.startswith("[") else scalar(value)
    return pairs


def parse(text):
    """updated, focus, metrics.counts and items.<collection>.<id> -> every field.

    Also the parser behind `snapshot-query.py` (project-os-dev TASK-0081), so
    the orientation and the lookup read the snapshot the same way. A block
    item's fields are its 6-space keys: a scalar, an inline list, or a block
    list of `- value` lines beneath the key.
    """
    updated, focus, counts, items = "", {}, {}, {}
    section = sub = current = None
    listing = None
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
        if section == "items" and current and listing and indent >= 6 and stripped.startswith("- "):
            #: A block list, indented under its key or at the key's own indent
            #: (PyYAML's default dump style; FEAT-0021 review).
            if items[sub][current][listing] == "":
                items[sub][current][listing] = []
            items[sub][current][listing].append(scalar(stripped[2:]))
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
        elif section == "items" and sub and indent == 4 and ITEM_KEY.fullmatch(key):
            current, listing = key, None
            value = value.strip()
            items[sub][key] = flow_map(value) if value.startswith("{") else {}
        elif section == "items" and current and indent == 6:
            value = value.strip()
            listing = None
            if value.startswith("["):
                items[sub][current][key] = flow_list(value)
            elif value:
                items[sub][current][key] = scalar(value)
            else:
                #: Empty until a `- ` line makes it a list.
                items[sub][current][key] = ""
                listing = key
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
    closing = "Before changing anything, open the note of the item you are working on and the notes it links, including ones the request does not name."
    if (root / "tools" / "scripts" / "snapshot-query.py").is_file():
        closing += (" Look up any other item with `python3 tools/scripts/snapshot-query.py <ID>`;"
                    " `--search TEXT` and `--links-to <ID>` find notes, live ones first, finished ones folded.")
    else:
        closing += " For any other item, find its `file:` under its ID in SNAPSHOT.yaml and open the note."
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
