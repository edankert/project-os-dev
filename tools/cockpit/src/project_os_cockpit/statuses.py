"""Canonical project-os status vocabulary and its palette bands.

Before this module the vocabulary was restated in six places — two Python
tables, one JS table, two CSS rule blocks, and the collapse set — and they
drifted (ISS-0023): ``implemented`` was coloured and ranked with the done
family but absent from the Hide-completed set and from the tasks-pane
ordering, so a corpus like ``../your-sudoku`` (97 requirements at
``implemented``) looked finished yet never cleared out of the navigator.

The bands here are the single source of truth for *membership* — which
statuses exist and which bucket each belongs to. Two concerns deliberately
stay separate, because they answer different questions:

* ``cockpit.TASK_STATUS_ORDER`` — attention priority in the tasks pane.
* ``templates.STATUS_RANK`` — reading order on index pages.

Both are checked against this vocabulary by ``tests/test_status_vocabulary.py``,
which also parses ``static/cockpit.js`` and the two stylesheets so a surface
cannot silently fall behind again.

Band semantics (REQ-0012, as amended 2026-07-24):

``active``      work in flight
``pending``     not started, or awaiting a decision
``delivered``   built and shipped, **not yet signed off** — non-terminal
``done``        terminal, successful
``archived``    terminal, without success
``blocked``     stalled or failing
``reference``   not lifecycle state at all, or parked out of scope

``delivered`` is the band ISS-0023 added for work that is shipped but not
signed off. ``implemented`` was its founding member; ADR-0007 subsequently
retired the requirement ``verified`` status and made ``implemented``
terminal, so it now sits in ``done`` and the band keeps ``staged`` and
``monitoring`` — a release that is ready but not live, and a risk that is
mitigated but still watched. Both are still genuinely non-terminal, so the
band and its exclusion from Hide-completed remain correct.
"""

from __future__ import annotations

# Band -> members. Order within a band is not significant here; see the
# module docstring for where ordering lives.
BANDS: dict[str, tuple[str, ...]] = {
    "active": (
        "active", "approved", "accepted", "ready",
        "doing", "in-progress", "in-review", "next",
        "mitigating",
    ),
    "pending": (
        "planned", "backlog", "todo", "open", "pending",
        "draft", "proposed", "triage",
    ),
    # Non-terminal: delivered, awaiting verification / sign-off.
    "delivered": (
        "staged",        # release: verified and ready, not yet live
        "monitoring",    # risk: mitigated, still under watch
    ),
    "done": (
        "done", "merged", "fixed", "resolved",
        "fulfilled", "met", "complete",
        "implemented",   # requirement: terminal since ADR-0007
        "verified", "passing", "published", "released", "closed",
    ),
    "archived": (
        "obsolete", "retired", "cancelled", "superseded",
        "wont-fix", "reverted", "rolled-back", "deprecated",
    ),
    "blocked": ("blocked", "failing", "reopened"),
    "reference": ("reference", "deferred"),
}

# CSS custom property backing each band (base.css :root / [data-theme]).
BAND_TOKEN: dict[str, str] = {
    "active": "--status-active",
    "pending": "--status-pending",
    "delivered": "--status-delivered",
    "done": "--status-done",
    "archived": "--status-archived",
    "blocked": "--status-blocked",
    "reference": "--status-reference",
}

STATUS_BAND: dict[str, str] = {
    status: band for band, members in BANDS.items() for status in members
}

VOCABULARY: frozenset[str] = frozenset(STATUS_BAND)

#: Terminal statuses — what "Hide completed" removes, and what collapses by
#: default on index pages. Both done-positive and done-negative; ``delivered``
#: is deliberately excluded (see module docstring).
COMPLETED_STATUSES: frozenset[str] = frozenset(BANDS["done"]) | frozenset(BANDS["archived"])

#: Shipped but unverified. Kept visible under Hide-completed on purpose.
DELIVERED_STATUSES: frozenset[str] = frozenset(BANDS["delivered"])


def band_of(status: str | None) -> str | None:
    """Return the palette band for ``status``, or ``None`` if unmapped."""
    if not status:
        return None
    return STATUS_BAND.get(status.strip().lower())


def is_completed(status: str | None) -> bool:
    """True for terminal statuses only — ``implemented`` is not one."""
    if not status:
        return False
    return status.strip().lower() in COMPLETED_STATUSES
