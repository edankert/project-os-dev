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


class AgentSpec(TypedDict):
    """One dispatchable agent."""

    id: str
    label: str
    command: str
    #: Whether the cockpit can inject hooks to instrument this agent's sessions
    #: (FEAT-0019). An uninstrumented agent still dispatches; its sessions are
    #: simply not tracked, which is a degradation rather than a failure.
    instrumented: bool


#: Dispatchable agents, in menu order. ``id`` is the wire value used by the
#: dispatch ledger, the queue, IPC and localStorage — one spelling everywhere.
AGENTS: tuple[AgentSpec, ...] = (
    {"id": "claude", "label": "Claude Code", "command": "claude", "instrumented": True},
    {"id": "codex", "label": "Codex", "command": "codex", "instrumented": True},
)

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
