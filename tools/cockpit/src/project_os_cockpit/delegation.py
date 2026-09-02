"""The delegation policy — its format and its enforcement (FEAT-0075).

[[ADR-0009]] §4 made a delegation *a per-repo recorded fact*. This is that
fact's format, and the two layers that make it real.

**The absence of a policy means what it should: no delegation, no worker.**
That is the single most important property here. A missing `DELEGATION.md` must
not read as "delegate everything" or even "delegate the safe things" — it reads
as *nobody has said yes to anything*, because a default that grants authority is
authority nobody granted.

**A draft policy is no policy.** The note passes through the gate it configures:
the principal approves it through the actuator row, and only an `approved`
policy is consulted. An agent that could write its own policy and have it obeyed
would be delegating to itself.

Two layers, which is REQ-0030's shape and REQ-0026's pattern:

1. **Not offered** — `legal_actions` for a delegate answers from the policy, so
   an out-of-policy action never appears.
2. **Not performable** — the write path checks again, because a display bug
   must not be able to widen authority.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: Where the policy lives. One name, not configurable — a policy the enforcer
#: cannot find is a policy that silently permits nothing (safe) or everything
#: (catastrophic), and neither should depend on a path.
POLICY_REL = "DELEGATION.md"

#: `- judgment: <kind> → <to whom> [threshold: <text>]`
_DELEGATE_RE = re.compile(
    r"^\s*[-*+]\s*judgment:\s*(?P<judgment>[^→>]+?)\s*(?:→|->)\s*(?P<to>[^\[]+?)"
    r"(?:\s*\[threshold:\s*(?P<threshold>[^\]]*)\])?\s*$",
    re.IGNORECASE,
)


def parse(text: str) -> dict[str, Any]:
    """Read a policy note into `{status, delegations}`.

    Deliberately tolerant of prose around the entries and **intolerant of a
    missing status**: a note whose status cannot be read is treated as
    unapproved, because guessing in the permissive direction is the one mistake
    this module cannot afford.
    """
    status = ""
    m = re.search(r'^status:\s*"?([A-Za-z-]+)"?\s*$', text, re.MULTILINE)
    if m:
        status = m.group(1).strip().lower()

    delegations: list[dict[str, str]] = []
    in_fence = False
    in_comment = False
    for line in text.splitlines():
        # **HTML comments count as "not a grant"**, and this is not a nicety:
        # the shipped template ships its examples inside `<!-- -->`, so a
        # parser that only understood code fences would delegate everything on
        # install. Caught by `test_the_shipped_template_delegates_nothing` the
        # first time it ran — which is the test existing to catch exactly the
        # permissive-default mistake this module is about.
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        found = _DELEGATE_RE.match(line)
        if found:
            delegations.append({
                "judgment": found.group("judgment").strip().lower(),
                "to": found.group("to").strip().lower(),
                "threshold": (found.group("threshold") or "").strip(),
            })
    return {"status": status, "delegations": delegations}


def load(project_root: Path) -> dict[str, Any]:
    """The repo's policy, or the empty one.

    An unreadable or absent policy returns `approved: False` with no
    delegations — the no-delegation-no-worker default, stated once here rather
    than at each call site where one of them would forget it.
    """
    path = project_root / POLICY_REL
    try:
        parsed = parse(path.read_text(encoding="utf-8"))
    except OSError:
        return {"present": False, "approved": False, "delegations": [], "status": ""}
    return {
        "present": True,
        # Only an approved policy is consulted. A draft policy is no policy.
        "approved": parsed["status"] == "approved",
        "status": parsed["status"],
        "delegations": parsed["delegations"] if parsed["status"] == "approved" else [],
    }


def permits(policy: dict[str, Any], judgment: str, actor: str) -> bool:
    """Does this policy let `actor` make this judgment?

    Every path returns False unless something explicitly says yes. There is no
    branch here that grants on absence, which is the property worth reading the
    function for.
    """
    if not policy.get("approved"):
        return False
    who = (actor or "").strip().lower()
    wanted = (judgment or "").strip().lower()
    if not who or not wanted:
        return False
    for entry in policy.get("delegations") or []:
        if entry.get("judgment") != wanted:
            continue
        to = entry.get("to", "")
        if to in (who, "any-delegate") or (to == "agent:principal" and who == "agent:principal"):
            return True
    return False


def stamp(policy_sha: str) -> str:
    """The attribution a delegate's write carries.

    *"Who, under what authority, as the policy stood when"* — the sha matters
    because a policy that changed after the write would otherwise make the
    audit unanswerable.
    """
    return f"(agent:principal, delegation: {POLICY_REL}@{policy_sha[:12]})"
