"""A decision's options, as data the surface can offer (FEAT-0097 / TASK-0401).

A decision that lists three options and records only *accepted* has lost the
answer. Edwin, 2026-08-12, on [[ADR-0010]]: *"why do I not have a way to select
an option?"* — and the harder half: *"how can we make sure the LLM formats the
document correctly for me to be able to make these decisions?"*

A control is not the answer on its own. **The note has to declare its options
in a form the tool can read**, or the shape drifts per author and the control
silently stops appearing. Measured across this corpus on 2026-08-12: three
decisions carry an `## Options` section, in **two** different forms, because
nothing had ever said which was right.

Both parse. That is deliberate — a convention that invalidated notes already
written would be a migration wearing a convention's clothes, and both forms are
unambiguous:

    ## Options

    1. **Deprecate mode 1.** Honest about where the effort goes; loses…
    2. **Full parity.** Requires the desk and its write endpoints on a…

    ## Options

    ### 1. The human publishes, on cadence (status quo)

    The worker commits; a person pushes when they look…

What the validator enforces is not *which* form but that the section can be
read at all — see `validate-docs.py`'s `DECISION-OPTIONS`.
"""

from __future__ import annotations

import re
from typing import Any

#: The section. `Options` and nothing else: `Alternatives` is the ADR
#: template's frontmatter field for rejected paths and is a different thing —
#: a list of what was NOT chosen, written after the fact.
_SECTION_RE = re.compile(r"^##\s+Options\s*$", re.I)
_ANY_H2_RE = re.compile(r"^##\s+")

#: `1. **Label.** rationale…` — the form two of the three use.
_NUMBERED_RE = re.compile(r"^(?P<n>\d+)\.\s+\*\*(?P<label>.+?)\.?\*\*\s*(?P<body>.*)$")
#: `### 1. Label` — the form the third uses, with its body in the lines after.
_HEADING_RE = re.compile(r"^###\s+(?P<n>\d+)\.\s+(?P<label>.+?)\s*$")

#: A decision names the option it proposes in prose — "Option 3", "**Option
#: 3**", "Option 3." — and the surface defaults to it. Read rather than
#: guessed: proposing one and defaulting to another would be the surface
#: quietly disagreeing with the note.
_PROPOSED_RE = re.compile(r"\bOption\s+(\d+)\b", re.I)

_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _section_lines(body: str) -> list[str]:
    out: list[str] = []
    inside = False
    in_fence = False
    for line in body.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            if inside:
                out.append(line)
            continue
        if in_fence:
            if inside:
                out.append(line)
            continue
        if _SECTION_RE.match(line):
            inside = True
            continue
        if inside and _ANY_H2_RE.match(line):
            break
        if inside:
            out.append(line)
    return out


def parse_options(text: str) -> list[dict[str, Any]]:
    """`[{number, label, body}]` in document order, or `[]`.

    Tolerant on purpose, like every other parser here: an unrecognised line
    inside the section is prose belonging to the option above it, never an
    error. What cannot be read is reported by the validator, once, rather than
    by each surface inventing its own complaint.
    """
    lines = _section_lines(text)
    if not lines:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        m = _NUMBERED_RE.match(line.strip())
        if m:
            out.append({
                "number": int(m.group("n")),
                "label": m.group("label").strip(),
                "body": m.group("body").strip(),
            })
            continue
        m = _HEADING_RE.match(line.strip())
        if m:
            out.append({
                "number": int(m.group("n")),
                "label": m.group("label").strip(),
                "body": "",
            })
            continue
        if out and line.strip():
            # Continuation prose for the option above.
            out[-1]["body"] = (out[-1]["body"] + " " + line.strip()).strip()
    return out


def proposed_option(text: str, options: list[dict[str, Any]] | None = None) -> int | None:
    """The option the note proposes, if it names one **outside** the list.

    Read from the `## Decision` section rather than anywhere: every option in
    the list mentions itself by number, so scanning the whole note would return
    the first option every time.
    """
    opts = options if options is not None else parse_options(text)
    if not opts:
        return None
    numbers = {o["number"] for o in opts}
    in_decision = False
    for line in text.splitlines():
        if _ANY_H2_RE.match(line):
            in_decision = bool(re.match(r"^##\s+Decision\b", line, re.I))
            continue
        if not in_decision:
            continue
        m = _PROPOSED_RE.search(line)
        if m and int(m.group(1)) in numbers:
            return int(m.group(1))
    return None


def payload(text: str) -> dict[str, Any]:
    """What `/api/notes/actions` carries for a decision (TASK-0402).

    The surface never parses markdown: it receives the options and which one is
    proposed, and renders them. A renderer that read the note itself would be a
    second parser to keep in step with this one.
    """
    options = parse_options(text)
    return {
        "options": options,
        "proposed": proposed_option(text, options),
    }
