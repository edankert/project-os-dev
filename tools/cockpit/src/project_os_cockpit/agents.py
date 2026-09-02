"""Canonical agent registry — which agents the cockpit can dispatch to.

Before this module the set ``claude | codex`` was restated across nine sites
that did not agree on being a set (ISS-0032), and the disagreement was not
cosmetic:

* ``ipc/dispatch-queue.ts`` validated persisted queue items against the two
  literals, so a third agent's queued work **failed validation and was
  discarded without a message** on the next restart. FEAT-0025's whole promise
  is that the queue survives a restart.
* ``renderer.ts`` (``agent-set``) and ``main.ts`` (``currentAgent``) coerced an
  unrecognised value to ``claude`` rather than rejecting it, so a third agent
  could neither be selected nor stay selected.
* Four independent closed type unions and two hardcoded surfaces restated the
  membership again.

Meanwhile the *ingestion* side was already open: ``cli.py`` documents the
``signal`` agent as "Agent name (e.g. claude, codex, aider). Freeform.", and
``agent_hooks.py`` / ``server.py`` preserve whatever string they are handed. So
the repo simultaneously accepted a signal from any agent and refused to
dispatch to any but two, with nothing reconciling the halves.

This module is the single source of truth for **membership**, in the same shape
and for the same reason as ``statuses.py`` — which exists because the status
vocabulary drifted across eight surfaces (ISS-0023).
``tests/test_agent_vocabulary.py`` parses the TypeScript surfaces so one cannot
fall behind again, exactly as ``tests/test_status_vocabulary.py`` does.

Two concerns stay deliberately separate:

* **Dispatchable** — an agent the cockpit can start and send prompts to. Closed
  set; needs a launch command and, to be instrumented, a hook strategy.
* **Recordable** — an agent that may appear in a session record or a signal.
  **Open**: any string. A record of an agent the cockpit cannot launch is
  legitimate (someone ran it in an external terminal), and rejecting it would
  discard real history.

Adding a dispatchable agent is one entry here plus its launch wiring in
``desktop/src/ipc/agent-instrument.ts``. Deliberately not one entry in nine
places.
"""

from __future__ import annotations

from typing import TypedDict


class AgentSpec(TypedDict, total=False):
    """One dispatchable agent.

    A **declared entry**, not a branch (ISS-0095). Adding a third agent is one
    row here and nothing else — `is_dispatchable`, the ledger's wire values and
    the dispatch menu all read this table already.

    That matters more after [[ADR-0009]]: the principal is a role, and so is
    the *worker*. A standing worker that can only ever be one vendor is a loop
    with a single point of vendor failure, and it forecloses the cheapest
    quality mechanism there is — a second opinion from a different model on the
    same item, which ADR-0013 already blesses for review.
    """

    id: str
    label: str
    command: str
    #: Whether the cockpit can inject hooks to instrument this agent's sessions
    #: (FEAT-0019). An uninstrumented agent still dispatches; its sessions are
    #: simply not tracked, which is a degradation rather than a failure.
    instrumented: bool
    #: Optional. Extra argv the launcher passes before the prompt — a driver
    #: hint rather than a command line, so a vendor's flags live with the
    #: vendor's row instead of in the launcher's branches.
    args: tuple[str, ...]
    #: Optional. What this agent is *for*, when a repo runs more than one.
    #: Free text, shown in the dispatch menu; no behaviour keys off it.
    role: str


#: Dispatchable agents, in menu order. ``id`` is the wire value used by the
#: dispatch ledger, the queue, IPC and localStorage — one spelling everywhere.
AGENTS: tuple[AgentSpec, ...] = (
    {"id": "claude", "label": "Claude Code", "command": "claude", "instrumented": True},
    {"id": "codex", "label": "Codex", "command": "codex", "instrumented": True},
)


def extend(entries: list[dict[str, object]]) -> tuple[AgentSpec, ...]:
    """A repo's own agents, merged over the built-in table (ISS-0095).

    Entries are validated rather than trusted: an entry missing `id`,
    `label` or `command` is **dropped**, because a half-declared agent in the
    menu is a dispatch that fails after the human has already committed to it.

    A repo entry with an existing `id` replaces that row — so a project can
    change how `claude` is launched without forking the table.
    """
    merged: dict[str, AgentSpec] = {a["id"]: a for a in AGENTS}
    for raw in entries or []:
        if not isinstance(raw, dict):
            continue
        agent_id = str(raw.get("id") or "").strip()
        label = str(raw.get("label") or "").strip()
        command = str(raw.get("command") or "").strip()
        if not (agent_id and label and command):
            continue
        spec: AgentSpec = {
            "id": agent_id, "label": label, "command": command,
            "instrumented": bool(raw.get("instrumented", False)),
        }
        args = raw.get("args")
        if isinstance(args, (list, tuple)):
            spec["args"] = tuple(str(a) for a in args)
        role = str(raw.get("role") or "").strip()
        if role:
            spec["role"] = role
        merged[agent_id] = spec
    return tuple(merged.values())

#: Used when no preference is stored and none is supplied.
DEFAULT_AGENT: str = "claude"

AGENT_IDS: tuple[str, ...] = tuple(a["id"] for a in AGENTS)


def is_dispatchable(agent: str | None) -> bool:
    """True if the cockpit can launch this agent.

    Deliberately narrow: answers "can we start it", not "is this a legal value".
    Gate a dispatch with it; never validate a record with it.
    """
    return bool(agent) and agent in AGENT_IDS


def resolve_dispatch_agent(agent: str | None) -> str | None:
    """Normalise a dispatch target, or None if it is not dispatchable.

    Returns None rather than falling back to ``DEFAULT_AGENT``, which is the
    whole point of ISS-0032: silently substituting ``claude`` for the agent the
    caller actually asked for produces a wrong record and no error. A caller
    that wants the default should ask for the default.
    """
    if agent is None:
        return None
    normalised = agent.strip().lower()
    return normalised if normalised in AGENT_IDS else None


def label_for(agent: str | None) -> str:
    """Display label. An unknown agent renders as itself, never as a sibling.

    An agent the cockpit cannot dispatch to can still appear in a record, and
    showing it under another agent's name would be a lie about who did the work.
    """
    if not agent:
        return "unknown"
    for spec in AGENTS:
        if spec["id"] == agent:
            return spec["label"]
    return agent


def agents_payload() -> dict:
    """The registry as the renderer consumes it.

    Served rather than restated, so the TypeScript surfaces carry no membership
    of their own — the ISS-0023 remedy applied to the same class of problem.
    """
    return {
        "agents": [dict(a) for a in AGENTS],
        "default": DEFAULT_AGENT,
    }
