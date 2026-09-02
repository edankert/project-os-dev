"""The intent charter — what a delegated principal reads first (FEAT-0077).

Acceptance asks *is this what I asked for?*, so a delegate needs **the asking
written down**. Without it, a delegated acceptance is a model guessing at taste
from a diff, which is the failure twelve PHASE-022 corrections already
demonstrated a human catching.

Three properties, and each is a way the charter could become decoration:

**Only an approved charter counts.** Same gate as the delegation policy, for
the same reason: an agent that could write the intent it is judged against is
judging itself. `draft` is no charter.

**Its sha is stamped on every judgment made under it.** *Who, under what
authority, against what statement of intent, as it stood when* — because a
charter amended after the fact makes the record unanswerable, which is exactly
what [[REQ-0029]] exists to prevent.

**Amendment re-enters approval.** A charter that could be edited in place while
approved would let the standard drift under judgments already made against it.

The content is **never invented**: a first draft is dispatched from the
corpus's own ADRs, phase close-outs and design-system notes ([[FEAT-0051]]'s
rule, applied to intent). This module reads and gates; it does not author.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

#: One name, like the delegation policy's.
CHARTER_REL = "INTENT.md"

#: The sections a charter must carry to be usable. A charter missing one is not
#: "partially useful" — a delegate reading it would judge against half a
#: standard and have no way to know which half.
REQUIRED_SECTIONS: tuple[str, ...] = ("What this is for", "What it must never become")


def _sections(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE)]


def parse(text: str) -> dict[str, Any]:
    """Status, sections, and the sha that pins this exact text."""
    status = ""
    m = re.search(r'^status:\s*"?([A-Za-z-]+)"?\s*$', text, re.MULTILINE)
    if m:
        status = m.group(1).strip().lower()
    found = _sections(text)
    missing = [s for s in REQUIRED_SECTIONS if not any(s.lower() in f.lower() for f in found)]
    return {
        "status": status,
        "sections": found,
        "missing": missing,
        # The sha is of the whole note, deliberately: a change anywhere in it
        # is a change to the standard, and pinning only the sections would let
        # the surrounding prose drift under a judgment.
        "sha": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def load(project_root: Path) -> dict[str, Any]:
    """The repo's charter, or the empty one.

    Absent, unreadable, unapproved or incomplete all yield `usable: False` —
    four different reasons, one safe outcome, and the reason is reported so the
    surface can say which.
    """
    path = project_root / CHARTER_REL
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"present": False, "usable": False, "sha": "",
                "why": f"no {CHARTER_REL} in this repo"}
    parsed = parse(text)
    if parsed["status"] != "approved":
        return {"present": True, "usable": False, "sha": parsed["sha"],
                "status": parsed["status"],
                "why": f"charter is {parsed['status'] or 'unset'}, not approved — "
                       "a draft charter is no charter"}
    if parsed["missing"]:
        return {"present": True, "usable": False, "sha": parsed["sha"],
                "status": parsed["status"], "missing": parsed["missing"],
                "why": "charter is missing " + ", ".join(f"'{s}'" for s in parsed["missing"])
                       + " — a delegate would judge against half a standard"}
    return {"present": True, "usable": True, "sha": parsed["sha"],
            "status": parsed["status"], "sections": parsed["sections"], "why": ""}


def witness(charter_sha: str, policy_sha: str) -> str:
    """The attribution a delegated judgment carries (REQ-0029).

    Names the delegate, the delegation and the charter — so `accepted_by`
    distinguishes a delegate from a human **at a glance**, which is the
    requirement's own test: *delegation without distinguishability is
    impersonation*.
    """
    return (
        f"agent:principal (delegation: DELEGATION.md@{policy_sha[:12]}, "
        f"charter: {CHARTER_REL}@{charter_sha[:12]})"
    )


def is_delegate_witness(value: str) -> bool:
    """True when this attribution was made under delegation rather than by a
    person. One reading, so no surface has to re-derive it."""
    return "agent:principal" in (value or "") and "charter:" in (value or "")
