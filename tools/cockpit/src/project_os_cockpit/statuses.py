"""Canonical project-os status vocabulary and its palette bands.

Before this module the vocabulary was restated in eight places — three Python
tables, one JS table, two CSS rule blocks, the Electron renderer, and the
collapse set — and they drifted (ISS-0023): ``implemented`` was coloured and ranked with the done
family but absent from the Hide-completed set and from the tasks-pane
ordering, so a corpus like ``../your-sudoku`` (97 requirements at
``implemented``) looked finished yet never cleared out of the navigator.

The bands here are the single source of truth for *membership* — which
statuses exist and which bucket each belongs to. Two concerns deliberately
stay separate, because they answer different questions:

* ``cockpit.TASK_STATUS_ORDER`` — attention priority in the tasks pane.
* ``templates.STATUS_RANK`` — reading order on index pages.

Both are checked against this vocabulary by ``tests/test_status_vocabulary.py``,
which also parses ``static/cockpit.js``, the two stylesheets and the Electron
renderer so a surface cannot silently fall behind again.

Band semantics (REQ-0012, as amended 2026-07-24):

``active``      work in flight
``pending``     not started, or awaiting a decision
``done``        terminal, successful
``archived``    terminal, without success
``blocked``     stalled or failing
``reference``   not lifecycle state at all, or parked out of scope

The ``delivered`` band is **retired** (ADR-0006, 2026-07-25). ISS-0023 added it
for work shipped but not signed off, with ``implemented`` as its founding
member; ADR-0007 made ``implemented`` terminal and moved it to ``done``, leaving
only ``staged`` and ``monitoring``. Upstream ADR-0008 then deleted both, having
measured zero writes of either across 5,890 fleet status writes — so the band
was left with no members at all rather than merely few. The distinction it drew
was real but nobody ever expressed it; recording that is more honest than
keeping a coloured band no status can enter.

Legacy vocabulary (``todo``, ``pending``, ``fulfilled``, ``met``, ``verified``,
``closed`` …) is retained in ``BANDS`` **deliberately**, so a repo whose history
predates a migration still renders. Upstream ADR-0008 collapsed the authored
taxonomy to 53 values; this module stays a superset of it on purpose, and that
tolerance is a decision rather than an oversight.

Values retired by upstream ADR-0012 (``in-progress``, ``in-review``,
``rolled-back``, ``wont-fix``) are handled differently, per ADR-0008 here: they
live in :data:`LEGACY_STATUS_BAND` rather than in ``BANDS``, so they still
*render* in their historical colour while remaining illegal for validation,
Hide-completed and the parity suite. Rendering tolerance is not permission.
"""

from __future__ import annotations

# Band -> members. Order within a band is not significant here; see the
# module docstring for where ordering lives.
BANDS: dict[str, tuple[str, ...]] = {
    "active": (
        "active", "approved", "accepted",
        "doing", "review", "next",
        "mitigating",
    ),
    "pending": (
        "planned", "backlog", "todo", "open", "pending",
        "draft", "proposed", "triage",
        "ready",         # test: defined, not yet executed (ADR-0008/ADR-0010)
    ),
    "done": (
        "done", "merged", "fixed", "resolved",
        "fulfilled", "met", "complete",
        "implemented",   # requirement: terminal since ADR-0007
        "verified", "passing", "published", "released", "closed",
    ),
    "archived": (
        "obsolete", "retired", "cancelled", "superseded",
        "declined", "reverted", "deprecated",
        # ISS-0141: an acceptance-suite check settled by a decision instead of
        # by being walked (`- [~]`) — terminal, and terminal *without* the
        # thing having been done, which is what the archived band means. Not a
        # note status: `validate-docs.py`'s per-type tables still refuse it
        # everywhere, so membership here buys colour, ordering and
        # Hide-completed, not permission to write it into frontmatter.
        "reconciled",
    ),
    "blocked": ("blocked", "failing", "reopened"),
    "reference": ("reference", "deferred"),
}

# CSS custom property backing each band (base.css :root / [data-theme]).
BAND_TOKEN: dict[str, str] = {
    "active": "--status-active",
    "pending": "--status-pending",
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

#: Retired by ADR-0006 (2026-07-25). ADR-0008 upstream deleted `staged` and
#: `monitoring` — the band's only two members after `implemented` moved to `done`
#: — because neither was written once in 5,890 fleet status writes. Kept as an
#: empty frozenset so callers need not branch on its absence; delete once no
#: surface references it.
DELIVERED_STATUSES: frozenset[str] = frozenset()


#: Values retired by upstream ADR-0012, mapped to the band they used to
#: occupy. This is a *rendering* fallback, not membership: the cockpit shows
#: ten corpora that migrate on their own schedule, and during that window a
#: live note may still carry a retired value. Colouring it grey would tell
#: the reader something false about a state the system understands perfectly
#: well under its old name (ADR-0008).
#:
#: Deliberately NOT part of `BANDS`, so retired values stay illegal for
#: `VOCABULARY`, `COMPLETED_STATUSES`, the validator and the parity suite —
#: rendering tolerance must not become permission. Expected to shrink to
#: empty as the fleet migrates; deleting the last entry is the signal that
#: it has.
LEGACY_STATUS_BAND: dict[str, str] = {
    "in-progress": "active",     # -> doing
    "in-review": "active",       # -> review
    "wont-fix": "archived",      # -> declined
    "rolled-back": "archived",   # -> reverted
}


def band_of(status: str | None) -> str | None:
    """Return the palette band for ``status``, or ``None`` if unmapped.

    Falls back to :data:`LEGACY_STATUS_BAND` so an unmigrated corpus still
    renders in its historical colours (ADR-0008). Callers that need to know
    whether a status is *legal* must test `VOCABULARY`, not this.
    """
    if not status:
        return None
    key = status.strip().lower()
    return STATUS_BAND.get(key) or LEGACY_STATUS_BAND.get(key)


def is_completed(status: str | None) -> bool:
    """True for terminal statuses only. ``implemented`` IS one since ADR-0007;
    the ``delivered`` band was retired by ADR-0006 once ADR-0008 deleted its
    last two members."""
    if not status:
        return False
    return status.strip().lower() in COMPLETED_STATUSES
