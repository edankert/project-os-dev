"""Agent verb registry (FEAT-0024 / TASK-0131).

Project-os notes are the nouns; the skills playbooks under
``tools/skills/`` are the verbs. This module maps note types to the
actions an agent can be dispatched with — each action carries a prompt
template (``{id}`` / ``{rel}`` slots) that points the agent at the note
first and at the relevant SKILL.md when one applies.

Downstream workspaces can override or extend per type via
``tools/adapters/cockpit/actions.yaml``::

    task:
      - key: implement
        label: Implement
        default: true
        prompt: "Work on {id}. …"

A type present in the YAML replaces that type's built-in list wholesale
(simple, predictable); absent types keep the defaults. Malformed files
are ignored — the built-ins always work.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("project_os_cockpit.agent_actions")

ACTIONS_REL_PATH = Path("tools") / "adapters" / "cockpit" / "actions.yaml"

_LIFECYCLE = "follow the project-os lifecycle (preflight, implement, close-out)"

DEFAULT_ACTIONS: dict[str, list[dict[str, Any]]] = {
    "task": [
        {
            "key": "implement", "label": "Implement", "default": True,
            "when": ["backlog", "next", "doing", "blocked"],
            "prompt": (
                "Work on {id}. Read docs/{rel} first — the note is the "
                f"spec — and {_LIFECYCLE}."
            ),
        },
        {
            "key": "refine", "label": "Refine",
            "when": ["backlog", "next", "doing", "blocked", "deferred"],
            "prompt": (
                "Refine {id}: read docs/{rel} and tighten its Definition "
                "of Done and Steps so an agent could implement it without "
                "guessing, per tools/skills/task-breakdown/SKILL.md. Do "
                "not start implementation."
            ),
        },
        {
            "key": "review", "label": "Review",
            "when": ["doing", "done"],
            "prompt": (
                "Review the implementation of {id} against its Definition "
                "of Done in docs/{rel}. Report gaps and risks; do not fix "
                "anything without confirming with me first."
            ),
        },
        {
            "key": "close-out", "label": "Close out",
            "when": ["doing", "done"],
            "prompt": (
                "Close out {id} per tools/skills/close-out/SKILL.md: "
                "verify the Definition of Done in docs/{rel}, then update "
                "statuses, SNAPSHOT.yaml, and the change note."
            ),
        },
    ],
    "issue": [
        {
            "key": "fix", "label": "Fix", "default": True,
            "when": ["triage", "open", "backlog", "next", "doing"],
            "prompt": (
                "Fix {id}. Read docs/{rel} first, reproduce the problem "
                f"if possible, then {_LIFECYCLE}."
            ),
        },
        {
            "key": "triage", "label": "Triage / refine",
            "when": ["triage", "open", "backlog"],
            "prompt": (
                "Triage {id}: read docs/{rel} and refine its severity, "
                "component, and reproduction steps per "
                "tools/skills/issue-intake/SKILL.md. Do not fix yet."
            ),
        },
        {
            "key": "reproduce", "label": "Reproduce",
            "when": ["triage", "open", "backlog", "doing"],
            "prompt": (
                "Reproduce {id} as described in docs/{rel}. Confirm or "
                "correct the reproduction steps in the note and report "
                "what you find. Do not fix yet."
            ),
        },
    ],
    "feature": [
        {
            "key": "break-down", "label": "Break down", "default": True,
            "when": ["backlog", "planned", "in-progress"],
            "prompt": (
                "Break down {id} into tasks per "
                "tools/skills/task-breakdown/SKILL.md. Read docs/{rel} "
                "first; create the TASK notes and SNAPSHOT entries. Do "
                "not implement anything yet."
            ),
        },
        {
            "key": "implement-next", "label": "Implement next task",
            "when": ["planned", "in-progress", "in-review"],
            "prompt": (
                "Advance {id}: read docs/{rel}, pick the highest-priority "
                f"open task under it, and {_LIFECYCLE}."
            ),
        },
        {
            "key": "refine", "label": "Refine scope",
            "when": ["backlog", "planned", "in-progress"],
            "prompt": (
                "Refine the scope of {id} in docs/{rel}: sharpen the "
                "goal, scope boundaries, and acceptance criteria. Do not "
                "implement."
            ),
        },
        {
            "key": "close-out", "label": "Close out",
            "when": ["in-progress", "in-review"],
            "prompt": (
                "Close out {id} per tools/skills/close-out/SKILL.md: "
                "check every task and linked test of docs/{rel}, then "
                "update statuses, SNAPSHOT.yaml, and the change note."
            ),
        },
    ],
    "requirement": [
        {
            "key": "implement", "label": "Implement", "default": True,
            "prompt": (
                "Implement {id}: read docs/{rel} — the acceptance "
                f"criteria are the contract — and {_LIFECYCLE}."
            ),
        },
        {
            "key": "refine", "label": "Refine acceptance",
            "prompt": (
                "Refine {id}: read docs/{rel} and sharpen its acceptance "
                "criteria until they are individually testable. Run "
                "tools/skills/impact-analysis/SKILL.md against related "
                "requirements. Do not implement."
            ),
        },
        {
            "key": "verify", "label": "Verify",
            "prompt": (
                "Verify {id}: read docs/{rel}, ensure TST notes exist "
                "covering each acceptance criterion, run them, and "
                "update the requirement's status accordingly."
            ),
        },
    ],
    "phase": [
        {
            "key": "groom", "label": "Groom backlog", "default": True,
            "when": ["planned", "active"],
            "prompt": (
                "Groom the backlog of {id} per "
                "tools/skills/backlog-grooming/SKILL.md, scoped to the "
                "items of docs/{rel}. Propose priority order and flag "
                "stale or under-specified items. Do not implement."
            ),
        },
        {
            "key": "status-sweep", "label": "Status sweep",
            "prompt": (
                "Run a status sweep over {id}: compare every item linked "
                "from docs/{rel} against reality (code, tests, SNAPSHOT) "
                "per tools/skills/status-transition/SKILL.md and fix "
                "drift."
            ),
        },
        {
            "key": "close-out", "label": "Close out phase",
            "when": ["active"],
            "prompt": (
                "Close out {id} per tools/skills/close-out/SKILL.md: "
                "verify the exit criteria in docs/{rel}, close remaining "
                "items or move them out, and update SNAPSHOT.yaml."
            ),
        },
    ],
    "risk": [
        {
            "key": "mitigate", "label": "Plan mitigation", "default": True,
            "when": ["open", "doing"],
            "prompt": (
                "Plan mitigation for {id} per "
                "tools/skills/risk-mitigation-planning/SKILL.md: read "
                "docs/{rel}, turn mitigations into concrete tasks, and "
                "link them."
            ),
        },
        {
            "key": "reassess", "label": "Re-assess",
            "prompt": (
                "Re-assess {id}: read docs/{rel} and check whether the "
                "hazard, likelihood, and severity still hold. Update the "
                "note and report what changed."
            ),
        },
    ],
}


def _valid_action(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    key = raw.get("key")
    label = raw.get("label")
    prompt = raw.get("prompt")
    if not (isinstance(key, str) and key and isinstance(label, str) and label
            and isinstance(prompt, str) and prompt):
        return None
    out: dict[str, Any] = {"key": key, "label": label, "prompt": prompt}
    if raw.get("default"):
        out["default"] = True
    when = raw.get("when")
    if isinstance(when, list):
        statuses = [str(s).lower() for s in when if isinstance(s, (str, int))]
        if statuses:
            out["when"] = statuses
    return out


def load_actions(project_root: Path) -> dict[str, list[dict[str, Any]]]:
    """Built-ins, with per-type wholesale override from the workspace's
    ``tools/adapters/cockpit/actions.yaml`` when present and valid."""
    actions = {k: [dict(a) for a in v] for k, v in DEFAULT_ACTIONS.items()}
    override_path = project_root / ACTIONS_REL_PATH
    if not override_path.is_file():
        return actions
    try:
        import yaml
        raw = yaml.safe_load(override_path.read_text(encoding="utf-8"))
    except Exception as exc:  # malformed YAML must never break the API
        log.warning("actions.yaml ignored (%s): %s", override_path, exc)
        return actions
    if not isinstance(raw, dict):
        return actions
    for note_type, entries in raw.items():
        if not isinstance(entries, list):
            continue
        cleaned = [a for a in (_valid_action(e) for e in entries) if a]
        if cleaned:
            actions[str(note_type)] = cleaned
    return actions
