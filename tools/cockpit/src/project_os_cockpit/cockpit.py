"""Cockpit JSON API payload builders.

Pure functions that take an :class:`project_os_cockpit.index.Index` and return the
dicts that get serialised on the ``/api/cockpit/nav`` and
``/api/cockpit/context`` endpoints. Kept separate from the HTTP handler so
they're trivially testable: every assertion lives at the dict level, not
at HTTP-status level.

Schema is versioned via ``SCHEMA_VERSION`` and surfaced both inline in the
payload and in an ``X-Cockpit-Schema`` header so the JS client can detect
bumps and refuse to render an unknown shape.

The nav payload is mode-driven (``?mode=`` on the API). Every mode returns
the same outer envelope::

    {
        "schema_version": 2,
        "mode": "<mode-id>",
        "groups": [
            {"key", "label", "url" | None, "status" | None, "items": [...]},
            ...
        ]
    }

Each item carries the same shape regardless of mode::

    {"id", "title", "status", "url", "subtitle"}

so the JS renderer can be one function over four modes.
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any, Callable

from . import acceptance as _acceptance
from . import git_state as _git_state
from . import obligations as _obligations
from . import statuses
from . import token_sources
from . import command_targets
from .index import Index, NoteRecord

_CHG_DATE_RE = re.compile(r"^CHG-(\d{4})(\d{2})(\d{2})")
# Past months with fewer than this many CHGs render flat (items directly
# under the month label) — splitting into 1-item week sub-buckets is
# noise. Densely-populated months keep the weekly split (TASK-0041).
_CHG_PAST_MONTH_WEEK_SPLIT_MIN = 10
_MONTH_NAMES = (
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_MONTH_ABBR = (
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

_HEADING_RE = re.compile(r"^#{1,6}\s")
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_INLINE_FMT_RE = re.compile(r"(\*\*|__|\*|_|`)([^*_`\n]+?)\1")

# 4 (FEAT-0040 / TASK-0199): additive — stats gains `focus`, issue items
# gain `severity`, and `/api/cockpit/commits` joins the API surface.
SCHEMA_VERSION: int = 4

#: Manual-verification staleness threshold, in days. Mirrors
#: ``DEFAULT_STALENESS_DAYS`` in ``tools/scripts/validate-docs.py`` and is
#: overridden the same way, by ``SNAPSHOT.yaml`` ``verification.staleness_days``.
#:
#: Deliberately the validator's number and the validator's config key rather
#: than a second rule: a cockpit that called a test stale at 30 days while the
#: validator called it fresh at 89 would be a parallel vocabulary, which is the
#: defect ISS-0024 and ISS-0069 are both about. DES-0004's first draft cited "9
#: stale tests" on a 30-day threshold nobody had adopted; at 90 there are none.
DEFAULT_STALENESS_DAYS: int = 90

#: Mirror of ``PHASE_RESOLVED`` in ``tools/scripts/validate-docs.py``: per type,
#: the statuses that let a phase close over a note naming it in ``phase:``.
#:
#: Duplicated rather than imported because that validator is template-owned with
#: a byte-identical bundled copy (ISS-0026) and importing a hyphenated script is
#: awkward — so `test_unclosed_uses_the_validators_own_gate` asserts the two
#: tables are equal instead. **`risk` is in here.** Leaving it out is what made
#: the `unclosed` marker looser than the gate it is supposed to predict
#: (ISS-0071): the phase strip excludes risks by design, and computing the
#: marker from the strip inherited that exclusion.
PHASE_RESOLVED: dict[str, frozenset[str]] = {
    "task": frozenset({"done", "cancelled", "superseded"}),
    "issue": frozenset({"fixed", "declined"}),
    "requirement": frozenset({"implemented", "retired", "cancelled", "superseded"}),
    "feature": frozenset({"done", "cancelled", "superseded"}),
    "risk": frozenset({"closed"}),
}

#: Mirror of ``CLOSED_PHASE_STATUSES``. `superseded` closes a phase too, so a
#: superseded phase must not be offered for close-out.
CLOSED_PHASE_STATUSES: frozenset[str] = frozenset({"done", "superseded"})


def square_state_for(status: str, note_type: str = "task") -> str | None:
    """Module-level twin of `stats_payload`'s `_square_state`, for enumeration.

    The real one closes over the payload's `_is_done`; this takes the two inputs
    that actually matter so a test can sweep the whole status vocabulary. Kept
    beside it and asserted equivalent by `test_no_legal_status_falls_through_unmarked`
    — the alternative was a test that could only see the statuses the corpus
    happens to contain, which is how `failing` went unmarked (ISS-0071).
    """
    norm = (status or "").strip().lower()
    if norm == "deferred":
        return "deferred"
    if norm in statuses.BANDS["archived"]:
        return "dropped"
    if is_done_status(note_type, norm):
        return "delivered"
    if norm in {"doing", "active", "in_progress"}:
        return "doing"
    return None


def needs_human_for(status: str, note_type: str = "task") -> bool:
    """Module-level twin of `_needs_human`, minus the `depends:` lookup (which
    needs an index). Same purpose as `square_state_for`."""
    norm = (status or "").strip().lower()
    if norm in ("triage", "review"):
        return True
    if norm in statuses.BANDS["blocked"]:
        return True
    return note_type == "test" and norm == "ready"


def phase_close_blockers(index: Index, phase_id: str) -> list[str]:
    """Notes that would make PHASE-CHILDREN fire if ``phase_id`` closed.

    Computed over **every note naming the phase**, exactly as the validator
    does — not over the phase strip's items. The strip omits risks (none carry
    a phase, so DES-0004 scoped them out) and that omission is not the gate's.
    """
    out: list[str] = []
    for record in index.iter_records():
        raw = str((record.frontmatter or {}).get("phase") or "").strip()
        if not raw:
            continue
        named = _strip_wikilink(raw).strip()
        # `PHASE-011` and `PHASE-011-Unproven-Claims` both name PHASE-011; a
        # bare prefix match would also catch `PHASE-0110`, hence the boundary.
        if not (named == phase_id or named.startswith(phase_id + "-")):
            continue
        resolved = PHASE_RESOLVED.get((record.note_type or "").lower())
        if resolved is None:
            continue                    # not a type the gate polices
        if (record.status or "").strip().lower() not in resolved:
            out.append(record.note_id or record.rel_path)
    return sorted(out)



def project_id(docs_root: Path) -> str:
    """This repo's stable, writable identity (ADR-0024 / TASK-0390).

    `project.id` from `SNAPSHOT.yaml`, falling back to the repo's **directory
    name**. Neither of the two things that look like an id can be one:
    `project.name` is a display string — measured across the fleet on
    2026-08-12 it carries spaces and capitals (`Obsidian-Supernote Sync`,
    `Your Health`) and the template's still reads `REPLACE ME` — and the
    shell's workspace id is `sha1(absolute path)`, which is machine-local and
    can never appear in a committed note.

    The directory name is unique across all twelve repos and is what a person
    types when they mean that project. The explicit field exists for the case
    the default cannot survive: a repo renamed or cloned into a different
    folder changes identity silently, and every reference to it breaks with no
    error anywhere.
    """
    root = docs_root.parent
    try:
        text = (root / "SNAPSHOT.yaml").read_text(encoding="utf-8")
    except OSError:
        return root.name
    m = re.search(r"^project:\s*$", text, re.M)
    if m:
        for line in text[m.end():].splitlines():
            if line and not line[0].isspace():
                break
            got = re.match(r"^\s+id\s*:\s*(.+?)\s*$", line)
            if got:
                value = got.group(1).strip().strip('"').strip("'")
                if value:
                    return value
    return root.name


def _staleness_days(docs_root: Path) -> int:
    """The project's staleness threshold, from the snapshot or the default."""
    try:
        text = (docs_root.parent / "SNAPSHOT.yaml").read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_STALENESS_DAYS
    m = re.search(r"^verification:\s*$", text, re.M)
    if not m:
        return DEFAULT_STALENESS_DAYS
    tail = text[m.end():]
    for line in tail.splitlines():
        if line and not line[0].isspace():
            break
        got = re.match(r"^\s+staleness_days\s*:\s*(\d+)", line)
        if got:
            return int(got.group(1))
    return DEFAULT_STALENESS_DAYS


def _is_stale_verification(fm: dict[str, Any], days: int) -> bool:
    """True when ``last_verified`` is older than ``days``.

    Absent or unparseable dates are **not** stale here: the validator already
    errors on a manual test with no ``last_verified`` (``TEST-FIELDS``), and
    reporting the same corpus defect as staleness would say the wrong thing
    about it on a surface that cannot explain itself.
    """
    raw = str(fm.get("last_verified") or "").strip()
    if not raw:
        return False
    try:
        seen = _dt.date.fromisoformat(raw[:10])
    except ValueError:
        return False
    return (_dt.date.today() - seen).days > days


def _test_last_verified(fm: dict[str, Any]) -> str:
    """When a test was last seen to pass — from the field its kind makes authoritative.

    Both fields exist and they answer different questions. ``last_run`` is written
    by ``tools/scripts/run-tests.py`` from an exit code; ``last_verified`` is a date
    a person types after walking a procedure. So the order depends on which kind of
    test is asking:

    - **executable** (carries a ``command:``) — ``last_run`` first. The runner is
      the only hand permitted to write its status (ADR-0010), so the runner's date
      is the only one describing the status on the note.
    - **manual** — ``last_verified`` first. Nothing runs it; the typed date is the
      whole record, and ``TEST-FIELDS`` errors when it is absent.

    Either way the other field is the fallback, so a note carrying only one is
    never reported as unverified — a claim about the record rather than the test.

    **The order used to be unconditional**, ``last_verified`` then ``last_run``, and
    it was right when it was written: 22 of 23 notes were manual-shaped and only
    TST-0022 carried a run. ISS-0130 inverted that population in one afternoon —
    22 notes became executable and every one of them kept a ``last_verified`` from
    weeks earlier, so all 22 displayed a hand-typed date while a green run from
    minutes ago sat in the field beside it. None had crossed the 90-day threshold
    yet; the oldest was 39 days and climbing, on a test running green daily. A
    surface that calls a passing test stale is the parallel-vocabulary failure
    ISS-0024 and ISS-0069 are both about, arriving by data rather than by code.
    """
    keys = (
        ("last_run", "last_verified")
        if str(fm.get("command") or "").strip()
        else ("last_verified", "last_run")
    )
    for key in keys:
        value = str(fm.get(key) or "").strip()
        if value:
            return value
    return ""


def _test_is_stale(fm: dict[str, Any], days: int) -> bool:
    """Whether a test's verification no longer holds.

    **Two rules, chosen by execution rather than by level** (ADR-0034
    decision 2). A machine re-runs on every commit, so currency is free and the
    only question is whether the last run is old. A person does not, so the
    question is whether anything has CHANGED underneath the walk — which is
    what `invalidated_by:` records, and which no threshold can answer.

    *"This walk was true 89 days ago"* is not a question anybody asks; *"has
    something changed under it"* is. Time-based staleness was a proxy for change
    that a corpus carrying an invalidation field no longer needs — and the proxy
    is actively wrong in both directions: a walk untouched for a year is current
    if nothing it covers has moved, and one performed yesterday is stale if
    something has.
    """
    if not str(fm.get("command") or "").strip():
        invalidated = fm.get("invalidated_by") or {}
        if isinstance(invalidated, dict) and str(
                invalidated.get("change") or "").strip():
            verdict = str(fm.get("verdict_date") or fm.get("last_verified") or "").strip()
            when = str(invalidated.get("date") or "").strip()
            # Arithmetic where both dates are known: a walk recorded AFTER the
            # invalidating change answers it. Where either is missing the
            # invalidation stands, because not one of the fleet's annotations
            # carried a date when this was measured.
            return not (verdict and when and verdict >= when)
        return False
    return _test_is_stale_by_time(fm, days)


def _test_is_stale_by_time(fm: dict[str, Any], days: int) -> bool:
    """Whether an executable test's last verification is older than the threshold.

    Delegates to :func:`_is_stale_verification` — literally the same rule the
    validator and the overview's ``unproven`` marker use, reached through
    :func:`_staleness_days` and ``SNAPSHOT.yaml verification.staleness_days``.

    **There was a second rule, and it disagreed.** ``MANUAL_TEST_STALE_DAYS =
    60`` in the desktop renderer called a test stale at 60 days on ``last_run``
    and only if it was manual; the project calls it stale at 90 on
    ``last_verified``, whatever runs it. Measured 2026-08-10 across this
    corpus: 2 tests stale by the project's rule (TST-0001/TST-0002, 94 days),
    **0** by the renderer's, because both are automated. A surface that says
    "all fresh" while the validator says otherwise is the parallel vocabulary
    ISS-0024 and ISS-0069 are both about, so TASK-0371 removed the renderer's
    constant rather than adding a third.

    An absent date is **not** stale, per ``_is_stale_verification``: the
    validator already errors on a manual test with no ``last_verified``
    (``TEST-FIELDS``), and reporting that corpus defect as staleness would say
    the wrong thing about it here.
    """
    return _is_stale_verification({"last_verified": _test_last_verified(fm)}, days)


PROJECT_SUPPORT_ROOT_FILES: tuple[str, ...] = (
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
    # ISS-0033: the identity band offers "Open LLM_BRIEF.md" and the render
    # endpoint refused it, replacing the design surface with "No note here".
    # The brief is the one root file the cockpit actively sends people to,
    # so it belongs here more than the three above do.
    "LLM_BRIEF.md",
)

# Project mode indexes ``docs/``. The only non-docs Markdown surfaced by
# default is selected top-level human-facing project documentation; those
# files render at the root of the Docs tree group (TASK-0021), not as a
# separate "Top-level docs" group. The server still uses these constants
# to allowlist what may be served from outside ``docs/``.
PROJECT_SUPPORT_DIRS: tuple[tuple[str, str, int], ...] = ()

# Stable display order for type groups in the right pane (relationships).
# Order is derived from an aggregate analysis of a real project-os corpus
# (~1,175 notes in ../your-trainer): the most-frequently-linked types come
# first, so the typical reader sees the densest relationship sets at the
# top. Types absent from that corpus (risk, workflow, plan, reference) are
# slotted by schema affinity to their nearest neighbour.
TYPE_ORDER: tuple[str, ...] = (
    "task",
    "feature",
    "issue",
    "requirement",
    "change",
    "phase",
    "release",
    "adr",
    "risk",
    "test",
    "workflow",
    "plan",
    "reference",
)
_TYPE_RANK: dict[str, int] = {t: i for i, t in enumerate(TYPE_ORDER)}

# Order for the "tasks by status" left-pane mode. Items the user is
# actively touching first; archived states last. `deferred` sits in the
# parked band with blocked — it is descoped-but-still-wanted work, not
# archived history (project-os STATUSES.md, "Deferral and re-adoption").
#
# This is attention priority, which is finer-grained than the colour bands
# in `statuses.py` — hence an explicit tuple rather than a derivation. The
# two are kept in step by tests/test_status_vocabulary.py, which fails if
# any vocabulary status is missing here. `staged` / `monitoring` sit in
# their own delivered band just above the done family: shipped, but not
# signed off, so they outrank finished work. `implemented` joined the done
# family when ADR-0007 made it the terminal requirement status.
TASK_STATUS_ORDER: tuple[str, ...] = (
    "doing", "review", "next",
    "blocked", "failing", "reopened", "deferred",
    "ready", "active", "approved", "accepted", "mitigating",
    "planned", "triage",
    "todo", "open", "pending", "backlog",
    "draft", "proposed",
    "staged", "monitoring",
    "done", "merged", "fixed", "resolved", "fulfilled", "met", "complete",
    "implemented",
    "verified", "passing", "published", "released", "closed",
    "obsolete", "retired", "cancelled", "superseded", "declined", "reverted",
    "deprecated", "reconciled",
    "reference",
)
_TASK_STATUS_RANK: dict[str, int] = {s: i for i, s in enumerate(TASK_STATUS_ORDER)}

# Issue severity order. Severity vocabulary varies; project-os schema is
# critical / high / medium / low.
SEVERITY_ORDER: tuple[str, ...] = ("critical", "high", "medium", "low")
_SEVERITY_RANK: dict[str, int] = {s: i for i, s in enumerate(SEVERITY_ORDER)}

# Recent-mode time buckets (in render order).
_RECENT_BUCKETS = (
    ("today", "Today"),
    ("yesterday", "Yesterday"),
    ("week", "This week"),
    ("month", "This month"),
    ("earlier", "Earlier"),
)

NAV_MODES: tuple[str, ...] = (
    "intent", "features", "tasks", "issues", "tests", "publication",
    "active", "recent", "library",
)

#: Old mode ids that must keep answering (TASK-0385). `design` became
#: `intent` — the name Edwin agreed, which the obligation registry has used
#: since FEAT-0089 while the nav kept the inherited one.
#:
#: An alias rather than a removal, because an unknown mode falls back to
#: `DEFAULT_MODE` **silently**. On 2026-08-11 that exact behaviour made the
#: Tests view look broken for 33 hours: a stale client asked for `tests`,
#: got the features tree, and nothing anywhere said the mode was unknown.
#: A rename that drops the old id would do the same thing to every stored
#: preference and bookmark still saying `design`.
MODE_ALIASES: dict[str, str] = {"design": "intent"}

# Active mode (FEAT-0036 / TASK-0164) — in-flight items across all types.
_ACTIVE_DOING: frozenset[str] = frozenset({
    "doing", "in_progress", "review", "active",
    "mitigating", "reproducing", "reopened", "blocked", "failing",
})
_ACTIVE_NEXT: frozenset[str] = frozenset({
    # `accepted` is gone (ISS-0122). An accepted ADR or design is a decision
    # that HAS been made; listing it as upcoming work put 14 settled items in a
    # column of 45. The work an accepted decision implies is the feature or task
    # that implements it, and those carry their own status.
    "next", "ready", "planned", "approved", "triage",
})

#: Types whose `active` means something other than "somebody is working on it"
#: (ISS-0122). A **plan**'s status follows its parent feature by design
#: (STATUSES.md); a **reference** is `active` while it is current; a
#: **glossary** is `active` permanently. Reading any of them as work in flight
#: is a category error, and it is the same one that queued plans on the review
#: desk — reported 2026-07-26 and fixed there, not here.
#:
#: Measured before this exclusion: `Doing` held 27 items, of which 24 were
#: `reference` (14) and `plan` (10), against one feature, one task and one
#: phase anybody was actually working.
_ACTIVE_NON_WORK_TYPES: frozenset[str] = frozenset({
    "plan", "reference", "glossary",
})
_ACTIVE_DONE: frozenset[str] = frozenset(statuses.COMPLETED_STATUSES)
DEFAULT_MODE = "features"


def open_first_key(item: Any) -> tuple[int]:
    """Sort key placing open work above completed work (TASK-0267).

    Every navigator groups on a different axis — the tasks pane on
    status, issues on severity, features on phase order, the context pane
    on note *type* — and **state is orthogonal to all four**. No grouping
    axis can carry it, which is why a global Hide-completed switch got
    invented instead: it sidesteps the ordering problem rather than
    solving it. At 91% complete that switch removed 17 of 18 feature
    groups and every severity bucket. This is the thing it should have
    been.

    Returns a **1-tuple** on purpose. Python's sort is stable, so
    applying this to an already-ordered list moves completed items to the
    back and changes nothing else: the natural order (ID, severity, path)
    survives as the tiebreak for free, and no row shifts for a reason the
    reader cannot see.

    An unrecognised status ranks **open**. Sinking it would quietly bury
    a note whose status is a typo — hiding exactly the thing worth
    noticing.

    Not applied to the tasks pane, whose groups *are* statuses: ordering
    open-first inside a bucket labelled ``done`` means nothing. The
    comparator's job is to carry state where the axis cannot.
    """
    if isinstance(item, dict):
        status = item.get("status")
    else:
        status = getattr(item, "status", None)
    return (1 if statuses.is_completed(status) else 0,)

# Library mode discovery rules.
DOC_TREE_EXCLUDED_PREFIXES: tuple[str, ...] = ("__templates__/",)
DOC_TREE_EXCLUDED_ROOTS: tuple[str, ...] = (
    # Canonical project-os container dirs — each houses lifecycle-managed
    # notes that already have a dedicated nav surface (Features mode,
    # Tasks mode, the overview record column, the review desk). Hide them
    # from the Docs tree so the tree only carries non-project-os user
    # content. __templates__/ is separately blocked via
    # DOC_TREE_EXCLUDED_PREFIXES.
    #
    # `workflows` left this list in PHASE-010 (TASK-0244): a workflow is
    # prose with an `entrypoints:` list and no lifecycle to track, so the
    # tree is where it belongs — the same call references got in
    # TASK-0036.
    "changes",
    "decisions",
    "features",
    "issues",
    "phases",
    "plans",
    "releases",
    "requirements",
    "risks",
    "tasks",
    "tests",
)
# Note types that get their own by-type group in Library mode.
#
# Empty since PHASE-010 (TASK-0243/0245). Library accumulated eight groups
# by a process nobody chose: each time a type appeared with no obvious
# home it got a `rare:` group, and the result — measured against this
# repo's own corpus — was one duplicate of the Design mode, one duplicate
# of the overview record column, a Plans group rendering 14 of 33 files,
# and two types whose overview stat tiles navigated nowhere.
#
# Each type now has a purpose surface: plans nest under their feature
# (FEAT-0046), risks join the Issues mode (FEAT-0047), changes join the
# overview history band (FEAT-0048), tests and reviewed items join the
# review desk (FEAT-0049), decisions were already complete in the record
# column, designs in the Design mode, workflows in the Docs tree.
#
# Kept as a named empty tuple rather than deleted: it is the thing a
# future "where should this type live?" question should NOT answer by
# appending to.
LIBRARY_RARE_TYPES: tuple[str, ...] = ()
# Types that join the untyped Markdown tree in Library mode's Docs-tree group.
DOC_TREE_INLINE_TYPES: tuple[str, ...] = ("reference", "workflow")

# Types that already have their own UX surface elsewhere and therefore do
# NOT appear in the Library "By type" auto-discovery section. Without this
# skip-set, personal vaults with `task` notes would end up with a
# duplicate Tasks group in Library on top of the Tasks mode.
#
# Named explicitly rather than derived from LIBRARY_RARE_TYPES, which is
# now empty: deriving it would let every canonical type that clears
# _BY_TYPE_MIN_COUNT reappear here under a `by-type:` key, undoing the
# reduction through the back door. `release` is listed despite this
# corpus having zero REL notes — a release surface is not part of
# PHASE-010, and letting it fall through would hand a future release
# corpus a Library group by accident.
# `check` joined on 2026-08-17 with the first migration (ADR-0030), and the
# guard here fired the same hour: 34 acceptance checks appeared as a Library
# group the moment they became notes, and `../your-trainer` would have
# contributed 579. Its surface is the acceptance view (FEAT-0114) — exactly the
# condition this set exists to record, arriving for the first time on a type
# that was not hypothetical.
_BY_TYPE_SKIP_IN_LIBRARY: frozenset[str] = frozenset({
    "feature", "issue", "requirement", "phase", "task",
    "change", "adr", "decision", "release", "risk", "test", "workflow",
    "plan", "design", "check",
}) | frozenset(LIBRARY_RARE_TYPES) | frozenset(DOC_TREE_INLINE_TYPES)

# Minimum count for a discovered type to merit its own Library "By type"
# group. Below this, the notes still appear in the Docs tree (since the
# tree relaxation lands together with this work).
_BY_TYPE_MIN_COUNT: int = 5

# Curated parent-field names tried first when auto-detecting which
# frontmatter field carries the parent link for a given type. If a note
# of the type has any one of these fields with a non-empty value, that
# field wins regardless of whether the value resolves to an indexed note
# (so a ``project: [[Mother Interview]]`` field still groups the note
# under its project even when the project doesn't have its own ``.md``).
# Anything not on this list falls into the resolved-link fallback.
_PARENT_FIELD_CANDIDATES: tuple[str, ...] = (
    "parent", "part_of", "partof",
    "project", "projects",
    "world", "story", "series", "season", "episode",
    "chapter", "volume", "book",
    "page", "comic", "issue",
    "area", "topic", "domain",
)

# Frontmatter fields excluded from the resolved-link fallback. These
# tend to point at templates, assets, or timestamps — they may resolve
# to indexed notes (a template lives in the vault too) but they are not
# semantic parent relationships.
_NON_PARENT_FIELDS: frozenset[str] = frozenset({
    "template", "templates",
    "modified", "created", "updated", "date", "due",
    "image", "images", "cover", "icon", "banner", "thumbnail",
    "cssclass", "cssclasses",
    "source", "sources",
})

# Hard cap on items returned by the recent mode. Anything older falls off.
_RECENT_LIMIT = 60


# Per-type "done" vocabulary (TASK-0176 / TASK-0181), module-level so the
# stats payload AND the agent work-item enrichment (TASK-0191) share one
# definition. Terminal-resolved statuses (superseded/retired/cancelled)
# count done; `deferred` (parked, still intended) stays open work.
DONE_FEAT = {"done", "released", "merged", "verified", "complete", "superseded", "cancelled"}
# `implemented` is the terminal requirement status since ADR-0007; `verified` is
# kept only so repos that have not yet migrated still read correctly.
DONE_TASK = {"done", "merged", "verified", "closed", "fixed", "cancelled", "superseded"}
DONE_REQ  = {"implemented", "verified", "met", "fulfilled", "accepted", "retired", "superseded", "cancelled"}
DONE_ISS  = {"fixed", "closed", "declined", "resolved", "cancelled"}
PASSING   = {"passing"}
DONE_BY_TYPE: dict[str, set[str]] = {
    "feature": DONE_FEAT,
    "task": DONE_TASK,
    "requirement": DONE_REQ,
    "issue": DONE_ISS,
    #: **`retired` is terminal for a test** ([[ISS-0272]]). `PASSING` alone said
    #: a retired check was unfinished work, so retiring one left it sitting in
    #: the session work strip as something touched and never completed —
    #: reported by Edwin as *"Why is TST-75 still in the todo list?"* after
    #: every other surface had been cleaned.
    #:
    #: `statuses.is_completed("retired")` is already `True`: it sits in the
    #: `archived` band, whose own comment reads *"terminal, and terminal
    #: WITHOUT the thing having been done, which is what the archived band
    #: means."* That is exactly a retired check — kept as the record that a
    #: behaviour was once walked, owed by nobody. This table was the outlier.
    #:
    #: Scoped to `test` deliberately. The band predicate and the per-type
    #: tables disagree on `retired` for other types too, and `validate-docs.py`
    #: has a third opinion — see [[ISS-0269]], where a retired check keeps its
    #: coverage credit. Widening the fix here would paper over that rather than
    #: settle it.
    "test": PASSING | {"retired"},
    "risk": {"closed"},
    "change": {"merged"},
    "phase": {"done", "superseded"},
}
# Fallback for any other type: the union of every terminal vocabulary.
_DONE_ANY: set[str] = set().union(*DONE_BY_TYPE.values())


def is_done_status(note_type: object, status: object) -> bool:
    """One per-type done definition for boxes, counts, and work items."""
    nt = str(note_type or "").lower().strip()
    st = str(status or "").lower().strip()
    return st in DONE_BY_TYPE.get(nt, _DONE_ANY)


# Canonical short id (prefix + number), e.g. PHASE-0007 out of a bare id or
# a `[[PHASE-0007-Trends-V2]]` wikilink. The focus fields never hold CHG ids.
_FOCUS_ID_RE = re.compile(r"[A-Z]+-\d+")


def _focus_ids(docs_root: Path) -> list[str]:
    """Ids declared in the ``focus`` block of the workspace SNAPSHOT
    (TASK-0193) — the doc-first workflow's "what's being worked on now".

    Reads the top-level ``focus:`` mapping's ``task``/``issue``/
    ``feature``/``phase``/``requirement`` fields (values may be bare ids
    or ``[[wikilinks]]``); the free-text ``note`` field is ignored.
    """
    path = docs_root.parent / "SNAPSHOT.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    ids: list[str] = []
    in_focus = False
    for line in text.splitlines():
        if re.match(r"^focus:\s*(#.*)?$", line):
            in_focus = True
            continue
        if in_focus:
            # The block ends at the next non-indented, non-blank line.
            if line and not line[0].isspace():
                break
            m = re.match(r"^\s+(task|issue|feature|phase|requirement)\s*:\s*(.+)$", line)
            if m:
                hit = _FOCUS_ID_RE.search(m.group(2))
                if hit:
                    ids.append(hit.group(0))
    # De-dup, preserve declaration order.
    seen: set[str] = set()
    return [i for i in ids if not (i in seen or seen.add(i))]


_FOCUS_NOTE_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def focus_block(index: Index) -> dict[str, Any] | None:
    """The SNAPSHOT ``focus:`` block, resolved against the index (TASK-0199).

    Returns the declared slots (task / feature / phase / issue /
    requirement) enriched with title, status, type and rel_path, plus the
    free-text ``note`` and the leading ``YYYY-MM-DD`` date the convention
    puts at its head. The renderer labels staleness from that date: the
    focus block is always set but frequently outlives the work it
    describes, so its age is part of the reading.

    ``None`` when there is no snapshot or no focus block at all.
    """
    path = index.docs_root.parent / "SNAPSHOT.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    slots: dict[str, str] = {}
    note = ""
    in_focus = False
    for line in text.splitlines():
        if re.match(r"^focus:\s*(#.*)?$", line):
            in_focus = True
            continue
        if not in_focus:
            continue
        # The block ends at the next non-indented, non-blank line.
        if line and not line[0].isspace():
            break
        m = re.match(
            r"^\s+(task|issue|feature|phase|requirement)\s*:\s*(.+)$", line
        )
        if m:
            hit = _FOCUS_ID_RE.search(m.group(2))
            if hit:
                slots[m.group(1)] = hit.group(0)
            continue
        m = re.match(r"^\s+note\s*:\s*(.+)$", line)
        if m:
            note = m.group(1).strip().strip('"').strip("'")

    if not slots and not note:
        return None

    def _resolve(note_id: str) -> dict[str, Any]:
        item: dict[str, Any] = {"id": note_id}
        target = index.by_id(note_id)
        record = index.get(target) if target is not None else None
        if record is not None:
            item["title"] = record.title or note_id
            item["status"] = record.status or ""
            item["type"] = (record.note_type or "").lower()
            item["rel"] = record.rel_path
            item["done"] = is_done_status(record.note_type, record.status)
        return item

    note_date = ""
    hit = _FOCUS_NOTE_DATE_RE.search(note)
    if hit:
        note_date = hit.group(0)

    return {
        "items": {name: _resolve(note_id) for name, note_id in slots.items()},
        "note": note,
        "note_date": note_date,
    }


def work_items_for_session(index: Index, sess: dict[str, Any]) -> list[dict[str, Any]]:
    """Enrich a session's work into work items (TASK-0191 / TASK-0193).

    The in-flight set is the workspace's declared ``focus`` items UNIONED
    with the notes touched this prompt. Each item resolves id/title/current
    status/type from the live index and computes ``done`` with the same
    per-type sets as the overview boxes. ``current_prompt`` is true for a
    focus item (declared active work) or a note edited at/after the latest
    prompt boundary. Focus items lead (declared work first), then touched
    items by first-touch order. A seeded session with no prompt boundary
    counts any timestamped touch, so the set survives a sidecar reload.
    """
    work_ts = sess.get("work_ts") or {}
    status_touched = sess.get("status_touched") or {}
    prompt_started = sess.get("prompt_started")
    rels = [r for r in (sess.get("work_notes") or []) if isinstance(r, str)]

    # Resolve every rel we may need (touched + status-changed notes) up front.
    wanted_rels = set(rels) | set(status_touched)
    by_rel: dict[str, Any] = {}
    for rec in index.iter_records():
        if rec.rel_path in wanted_rels:
            by_rel[rec.rel_path] = rec

    def _item(nid: str, rec: Any, rel: str, ts: object, current: bool) -> dict[str, Any]:
        return {
            "id": nid,
            "rel": rel,
            "title": (rec.title if rec else None) or "",
            "status": (rec.status if rec else None) or "",
            "type": (rec.note_type if rec else None) or "",
            "done": is_done_status(rec.note_type, rec.status) if rec else False,
            "ts": ts,
            "current_prompt": current,
        }

    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []

    def _add(nid: str, rec: Any, rel: str, ts: object, current: bool) -> None:
        existing = by_id.get(nid)
        if existing is not None:  # de-dup across sources
            if ts and (not existing["ts"] or str(ts) > str(existing["ts"])):
                existing["ts"] = ts
            existing["current_prompt"] = existing["current_prompt"] or current
            if rec and not existing["rel"]:
                existing.update(_item(nid, rec, rel, existing["ts"], existing["current_prompt"]))
            return
        by_id[nid] = _item(nid, rec, rel, ts, current)
        order.append(nid)

    # 1) SNAPSHOT focus — the declared active work (always current).
    for fid in _focus_ids(index.docs_root):
        path = index.by_id(fid)
        rec = index.get(path) if path else None
        rel = (rec.rel_path if rec else "") or ""
        ts = work_ts.get(rel) or (status_touched.get(rel) or {}).get("ts")
        _add(fid, rec, rel, ts, True)

    # 2) Notes whose status changed this session — the implemented/moved work
    #    (captures shell-tool writes, survives a restart; always current).
    for rel, info in sorted(
        status_touched.items(), key=lambda kv: str(kv[1].get("ts") or "")
    ):
        rec = by_rel.get(rel)
        nid = (rec.note_id if rec else None) or info.get("id") \
            or rel.rsplit("/", 1)[-1].removesuffix(".md")
        _add(nid, rec, rel, info.get("ts"), True)

    # 3) Notes touched this prompt — current when at/after the boundary.
    for rel in rels:
        rec = by_rel.get(rel)
        nid = (rec.note_id if rec else None) or rel.rsplit("/", 1)[-1].removesuffix(".md")
        ts = work_ts.get(rel)
        current = bool(ts) and (
            not isinstance(prompt_started, str) or str(ts) >= prompt_started
        )
        _add(nid, rec, rel, ts, current)

    return [by_id[i] for i in order]


def _exit_criteria_from_body(body: str) -> list[dict[str, Any]]:
    """Parse ``- [ ] / - [x]`` checkbox lines from a phase note's
    "Exit Criteria" section (FEAT-0023). Tolerates heading level and
    case; stops at the next heading."""
    import re
    lines = (body or "").splitlines()
    out: list[dict[str, Any]] = []
    in_section = False
    heading = re.compile(r"^#{2,6}\s*exit\s+criteria\b", re.IGNORECASE)
    any_heading = re.compile(r"^#{1,6}\s")
    box = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s+(.*)$")
    for line in lines:
        if in_section and any_heading.match(line):
            break
        if heading.match(line):
            in_section = True
            continue
        if not in_section:
            continue
        m = box.match(line)
        if m:
            out.append({
                "text": m.group(2).strip(),
                "done": m.group(1).lower() == "x",
            })
    return out


_ANY_ID_RE = re.compile(r"\b((?:ADR|DES|FEAT|ISS|PHASE|REQ|RISK|REL|TASK|TST|WF)-\d{2,})\b")


def _design_link_ids(value: Any) -> list[str]:
    """IDs out of a scalar or list of wikilinks, order preserved, deduped."""
    out: list[str] = []
    for item in (value if isinstance(value, list) else [value] if value else []):
        for m in _ANY_ID_RE.finditer(str(item)):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


#: `## Variant <name>` followed (eventually) by a fenced ```html block.
_VARIANT_HEADING_RE = re.compile(r"^##\s+Variant\s+(.+?)\s*$", re.MULTILINE)
_HTML_FENCE_RE = re.compile(r"^```html\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def _read_note_body(record: NoteRecord) -> str:
    """A note's text, or empty when it cannot be read.

    Variants are parsed from the body rather than declared in frontmatter, so
    an unreadable note degrades to "no variants" instead of failing the whole
    design payload.
    """
    try:
        return record.path.read_text(encoding="utf-8")
    except OSError:
        return ""


def design_variants(text: str) -> list[dict[str, Any]]:
    """`## Variant <name>` sections carrying a fenced html block (TASK-0300).

    **Convention over machinery.** A variant is a markdown section, so an agent
    or a human authors one with what they already have — no new note type, no
    editor, no upload. The bench does the rest.

    Only the FIRST html fence in a section counts. A variant is one shape; a
    section with two fences is a section that has not decided, and rendering
    both side by side under one name would misreport which was chosen.
    """
    out: list[dict[str, Any]] = []
    matches = list(_VARIANT_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[m.end():end]
        # Stop at the next `##` of any kind, so prose after the variants does
        # not get swallowed into the last one.
        nxt = re.search(r"^##\s", section, re.MULTILINE)
        if nxt:
            section = section[:nxt.start()]
        fence = _HTML_FENCE_RE.search(section)
        if not fence:
            continue
        out.append({
            "name": m.group(1).strip(),
            "html": fence.group(1).strip("\n"),
        })
    return out


def _design_stylesheets(fm: dict) -> list[str]:
    """Project-relative stylesheet paths a design declares (TASK-0230).

    Normalised and filtered here rather than at the route, so the route has
    one question to ask ("is this in the set?") and the corpus has one place
    that decides what a declaration means. Anything that is not a plain
    relative ``.css`` path is dropped: a declaration the route would refuse
    anyway is a declaration that should never have counted.
    """
    raw = fm.get("stylesheets")
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        rel = str(item or "").strip().lstrip("/")
        # `.css`, or a source file whose colour declarations are synthesised
        # into CSS at read time (ISS-0059). Three fleet apps are native and
        # declare their palette in Kotlin or Swift; without this they have no
        # readable design system at all.
        if not rel or not (rel.lower().endswith(".css")
                           or token_sources.supports(rel)):
            continue
        if ".." in rel.split("/") or "\\" in rel:
            continue
        if rel not in out:
            out.append(rel)
    return out


def project_stylesheet_allowlist(index: Index) -> set[str]:
    """Every stylesheet path any design note declares.

    Derived from the corpus, never configured. A hardcoded list would drift
    from the notes it is meant to describe — the failure this project is
    named after (ISS-0023) — and a directory share would publish the project
    rather than the two or three files a style guide reads.
    """
    allowed: set[str] = set()
    for record in index.notes_by_type("design"):
        allowed.update(_design_stylesheets(record.frontmatter or {}))
    return allowed


def _design_rationale(index: Index, fm: dict) -> list[dict[str, str]]:
    """The ADRs a design LINKS — never every ADR in the project (TASK-0225).

    The filter is the whole point. ADR-0006 (retire the delivered band) is
    design rationale; ADR-0011 (dated promotion of review warnings) is process
    governance. A surface listing both drags governance into a product view and
    buries the two or three decisions that actually explain why something looks
    the way it does.

    Resolution is through the **link graph**, not a title heuristic. A
    title-substring match was tried once in the review desk and removed in
    independent review for exactly this reason: it guesses, and a guess that is
    usually right is worse than an explicit link, because nobody can tell when
    it is wrong.

    The one line is the ADR's own ``decision:`` frontmatter — the sentence its
    author wrote to be quoted. Falling back to the title when it is absent, and
    to nothing beyond that: an ADR with neither is listed by id rather than
    summarised by a machine, since a generated summary of a decision is exactly
    the kind of confident paraphrase that misleads.
    """
    seen: list[str] = []
    for field in ("implements", "related"):
        for note_id in _design_link_ids(fm.get(field)):
            if note_id.startswith("ADR-") and note_id not in seen:
                seen.append(note_id)

    out: list[dict[str, str]] = []
    for note_id in seen:
        path = index.by_id(note_id)
        record = index.get(path) if path is not None else None
        if record is None:
            # A link to an ADR that does not exist is REPORTED, not dropped.
            # Silently omitting it hides a typo in the note's own frontmatter,
            # and the whole reason this resolves by link is that links are
            # checkable in a way heuristics are not.
            out.append({"id": note_id, "title": "", "decision": "",
                        "url": "", "status": "", "missing": True})
            continue
        adr_fm = record.frontmatter or {}
        decision = adr_fm.get("decision")
        out.append({
            "id": note_id,
            "title": record.title or note_id,
            "decision": str(decision).strip() if isinstance(decision, str) else "",
            "url": index.url_for(record.path),
            "status": record.status or "",
            "missing": False,
        })
    return out


_BRIEF_PLACEHOLDER_RE = re.compile(r"REPLACE[ _-]?ME", re.IGNORECASE)
_BRIEF_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_BRIEF_FIELD_RE = re.compile(r"^-\s*([A-Za-z][A-Za-z ]*?):\s*(.+?)\s*$", re.MULTILINE)


def _brief_state(name: str, purpose: str, placeholders: int, sections: list) -> str:
    """``filled`` / ``unfilled`` for a brief that exists.

    Two ways to be filled, because there are two ways to write this file.

    1. The identity is **stated** — a real name and purpose. This is the
       template's shape and the common case.
    2. Nothing is left to fill: **no placeholders and real content**. A brief
       written as prose that never adopted the `- Name:` / `- Purpose:`
       bullets is a finished brief, and reporting `unfilled` over it would
       headline "This project has not said what it is" across a fully written
       file — the mirror of the bug this state field was reshaped to fix
       (ISS-0035), found by the same reviewer one round later.

    That second clause is what keeps the payload's promise of tolerant
    parsing. A brief is prose a human edits; the convention is a convenience
    for the parser, not a requirement the surface may hold the author to.
    """
    if name and purpose:
        return "filled"
    if placeholders == 0 and sections:
        return "filled"
    return "unfilled"


def _markdown_fragment(body: str, source_path: Path) -> str:
    """One brief section as HTML, through the pipeline every note uses.

    Failure is silent and falls back to the escaped source: the brief is
    hand-written prose whose whole surface is tolerant by design, and a
    section that will not parse must not take the identity band down with it.
    """
    if not body.strip():
        return ""
    try:
        from . import renderer as _renderer
        return _renderer.render_markdown_text(body, source_path=source_path)
    except Exception:                              # pragma: no cover
        from html import escape
        return f"<p>{escape(body)}</p>"


def brief_payload(project_root: Path) -> dict:
    """``LLM_BRIEF.md`` as the identity band consumes it (TASK-0223).

    **Three states, not two.** "No brief" and "a brief that says REPLACE ME"
    call for different things: one is a project that never adopted the
    convention, the other is a project that adopted it and stopped. Collapsing
    them would hide the second, which is the one worth acting on — measured at
    10 of 11 fleet repos on 2026-07-28.

    Parsing is **tolerant by design**. The brief is prose a human edits, not a
    data file: a missing section, a reordered one, an added heading are all
    normal, and none may break the surface. Read what is recognised, ignore
    the rest, and never fail closed on a file whose whole purpose is being
    hand-written.

    The placeholder text is deliberately **not** returned — **anywhere**,
    including inside ``sections[].body``. A surface that renders
    "Purpose: REPLACE ME" as the first thing an agent reads every session is
    worse than one that says the brief needs filling in. The first version of
    this scrubbed only ``name``/``purpose`` while the docstring and the test
    name both claimed "never returned"; independent review found the leak by
    going to the named evidence (ISS-0035).

    ``state`` describes the **identity**, not the file. A brief with a real
    name and purpose and one ``REPLACE ME`` left under a later heading is a
    project that HAS said what it is — reporting `unfilled` there made the
    band headline "This project has not said what it is" about a project that
    had. ``placeholders`` still counts every one, so the surface can say the
    rest needs work without denying what is already true.

    Note that the two are independent in both directions: a brief can be
    ``unfilled`` with **zero** placeholders, when someone deleted the template
    lines rather than filling them. The band's copy is built from what is
    actually true of the file rather than assuming one implies the other.
    """
    path = project_root / "LLM_BRIEF.md"
    empty = {
        "schema_version": SCHEMA_VERSION,
        "state": "absent",
        "name": "", "purpose": "", "sections": [], "placeholders": 0,
        "rel": "LLM_BRIEF.md",
    }
    if not path.is_file():
        return empty
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return empty

    placeholders = len(_BRIEF_PLACEHOLDER_RE.findall(text))
    fields = {k.strip().lower(): v.strip() for k, v in _BRIEF_FIELD_RE.findall(text)}
    name = fields.get("name", "")
    purpose = fields.get("purpose", "")
    # A placeholder value is not an answer. Blank it rather than pass it on.
    if _BRIEF_PLACEHOLDER_RE.search(name):
        name = ""
    if _BRIEF_PLACEHOLDER_RE.search(purpose):
        purpose = ""

    sections = []
    heads = list(_BRIEF_H2_RE.finditer(text))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        # The heading is a renderable field too. The first fix enumerated
        # name/purpose/body and stopped one field short of the contract its
        # own docstring stated — the same shape as the defect it closed.
        #
        # A placeholder HEADING drops the section, because a section nobody
        # named cannot be presented — but only when its body is placeholder
        # too. Dropping a real body because its heading was left unwritten
        # would contradict the per-line policy two lines below (round 3
        # independent review).
        body = text[m.end():end].strip()
        # Drop the placeholder LINES, not the whole section: the rest of a
        # half-written section is real content and discarding it would punish
        # progress. A section that is nothing but placeholders disappears,
        # which is correct — it says nothing.
        body = "\n".join(
            line for line in body.splitlines()
            if not _BRIEF_PLACEHOLDER_RE.search(line)
        ).strip()
        if body:
            heading = m.group(1)
            if _BRIEF_PLACEHOLDER_RE.search(heading):
                heading = ""      # unnamed, but its content still counts
            sections.append({"heading": heading, "body": body})

    return {
        "schema_version": SCHEMA_VERSION,
        # The identity, not the file. See the docstring.
        "state": _brief_state(name, purpose, placeholders, sections),
        "name": name,
        "purpose": purpose,
        # Each section's body **rendered**, beside the source (ISS-0151). The
        # band printed `body` as text under `white-space: pre-wrap`, so the
        # file's own newlines became hard breaks and its markdown rendered as
        # syntax — a defect that reads exactly like a wrapped source file and
        # invites reflowing documents that are already correct.
        #
        # Rendered here rather than in the shell: the sidecar renders and the
        # shell arranges, which is the boundary every other note already
        # keeps. `body` stays, because a caller wanting the source should not
        # have to unparse HTML to get it.
        "sections": [
            {**s, "body_html": _markdown_fragment(s.get("body", ""), path)}
            for s in sections
        ],
        "placeholders": placeholders,
        "rel": "LLM_BRIEF.md",
    }


def designs_payload(index: Index) -> dict:
    """The design register (FEAT-0042 / TASK-0214).

    Membership is by `type: "[[design]]"`, never by path. Two fields shape how
    a design is framed and both are declared rather than inferred:

    ``role``      `system` = the standing reference designs conform to (one per
                  project); anything else is a time-bounded proposal. A system
                  and a proposal behave differently enough that the surface must
                  know which it has.

    ``viewport``  px width when the artifact IS a surface. **Absence is
                  meaningful**: it says the artifact is a document *about* a
                  surface -- a dossier of mocks -- and framing one at a device
                  width demonstrates nothing (found in review of PHASE-009:
                  DES-0001 is a scrolling dossier fixed at 1240px, so a 900px
                  preset would have "passed" an exit criterion while exercising
                  nothing). Derived from what the note declares rather than an
                  enumerated kind, because a kind like `mobile` restates the
                  project's platform on every note.
    """
    designs = []
    for r in sorted(index.notes_by_type("design"),
                    key=lambda r: (r.note_id or "", r.rel_path)):
        fm = r.frontmatter or {}
        asset = str(fm.get("asset", "") or "").strip()
        asset_rel = ""
        if asset:
            base = r.rel_path.rsplit("/", 1)[0] if "/" in r.rel_path else ""
            asset_rel = (base + "/" + asset) if base else asset
        viewport = fm.get("viewport")
        try:
            viewport = int(viewport) if viewport not in (None, "") else None
        except (TypeError, ValueError):
            viewport = None
        designs.append({
            "id": r.note_id or "",
            "title": r.title or r.note_id or r.rel_path,
            "rel": r.rel_path,
            "status": (fm.get("status") or "") if isinstance(fm.get("status"), str) else "",
            "role": (fm.get("role") or "proposal") if isinstance(fm.get("role"), str) else "proposal",
            "asset": asset_rel,
            "has_asset": bool(asset_rel and (index.docs_root / asset_rel).is_file()),
            "viewport": viewport,
            "implements": _design_link_ids(fm.get("implements")),
            "rationale": _design_rationale(index, fm),
            # Project-relative stylesheets this design reads (TASK-0230).
            # Declaring them here is what makes them servable: the route's
            # allow-list IS this list, gathered across every design note, so a
            # path nobody declared is a path nobody can fetch.
            "stylesheets": _design_stylesheets(fm),
            # Live variants (TASK-0300). `scripts: true` in frontmatter is the
            # opt-in; without it the bench sandboxes without scripts, because a
            # mockup that can run code is a mockup that can read the cockpit.
            "variants": design_variants(_read_note_body(r)),
            "variant_scripts": str(fm.get("scripts") or "").strip().lower() == "true",
            "chosen_variant": str(fm.get("chosen_variant") or "").strip(),
        })
    return {"schema_version": SCHEMA_VERSION, "designs": designs}


def stats_payload(
    index: Index, scope: str | None = None
) -> dict[str, Any] | None:
    """Aggregated dashboard payload (FEAT-0017 / TASK-0109).

    All counts are computed from the live index; no extra file IO.

    ``scope`` (FEAT-0023 / TASK-0128) narrows everything — hero,
    status mix, phases, activity — to one ``PHASE-####``: items whose
    phase resolves to the scope (directly or inherited via the parent
    feature), plus phase-less items linked to a scoped feature. Scoped
    payloads additionally carry ``scope`` (id/title/status/rel) and
    ``exit_criteria`` parsed from the phase note. Returns ``None``
    when the scope names no known phase note.
    """
    import re
    from collections import Counter
    from datetime import date, timedelta

    features     = index.notes_by_type("feature")
    tasks        = index.notes_by_type("task")
    issues       = index.notes_by_type("issue")
    requirements = index.notes_by_type("requirement")
    tests        = index.notes_by_type("test")
    risks        = index.notes_by_type("risk")
    changes      = index.notes_by_type("change")
    phase_recs   = index.notes_by_type("phase")

    # Per-type done sets are module-level (TASK-0176/0181/0191) so the hero
    # tiles, the phase boxes, and the agent work-item enrichment all share
    # one definition — an item is a filled box iff it also counts done.
    OPEN_ISS  = {"open", "doing", "triage", "backlog"}
    OPEN_RISK = {"open", "doing"}

    def _norm(s: object) -> str:
        return str(s or "").lower().strip()

    def _is_done(rec: Any) -> bool:
        return is_done_status(getattr(rec, "note_type", ""), rec.status)

    def _hero_count(records, done_set):
        total = len(records)
        done = sum(1 for r in records if _norm(r.status) in done_set)
        return {"total": total, "done": done}

    # Activity-date resolution order (most → least authoritative):
    #   1. frontmatter `updated`  — when the note was last touched
    #   2. frontmatter `created`  — when the note was first added
    #   3. the `CHG-YYYYMMDD…` prefix on the ID, as a last-ditch hint
    # The ID-derived form is loose (no trailing-dash requirement) so
    # letter-suffixed disambiguators like `CHG-20260418b-…` still match.
    _CHG_DATE_RE = re.compile(r"CHG-(\d{4})(\d{2})(\d{2})")

    def _activity_date(rec) -> str:
        fm = rec.frontmatter
        for key in ("updated", "created"):
            raw = fm.get(key)
            if not raw:
                continue
            s = str(raw).strip()
            # Accept "YYYY-MM-DD" or any ISO-8601 prefix of that shape.
            if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                return s[:10]
        if rec.note_id:
            m = _CHG_DATE_RE.match(rec.note_id)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return ""

    _PHASE_RE = re.compile(r"(PHASE-\d+)")
    _FEAT_ID_RE = re.compile(r"(FEAT-\d+)")

    # Canonical child→feature link field per type, from the project-os
    # templates under `docs/__templates__/`:
    #   tasks  →  `parent: "[[FEAT-…]]"`
    #   issues →  `parent: "[[FEAT-…]]"`
    #   reqs   →  `implements: "[[FEAT-…]]"`   (see requirement.md)
    # Anything else is ignored — non-canonical fields like `feature:`
    # or `features:` won't bind a child to its parent feature; the
    # author should normalise their notes to match the templates.
    _PARENT_FIELD_BY_TYPE: dict[str, str] = {
        "task":        "parent",
        "issue":       "parent",
        "requirement": "implements",
    }

    def _parent_feature_id(rec: Any) -> str | None:
        field = _PARENT_FIELD_BY_TYPE.get((rec.note_type or "").lower())
        if not field:
            return None
        val = rec.frontmatter.get(field)
        if not val:
            return None
        for c in (val if isinstance(val, list) else [val]):
            m = _FEAT_ID_RE.search(str(c))
            if m:
                return m.group(1)
        return None

    # Records indexed by note_id so we can resolve `_parent_feature_id`
    # against the actual feature record (for phase inheritance).
    records_by_id: dict[str, Any] = {}
    for rec in [*features, *tasks, *requirements, *issues]:
        if rec.note_id:
            records_by_id[rec.note_id] = rec

    def _phase_id_of(rec: Any, _depth: int = 0) -> str | None:
        ph = rec.frontmatter.get("phase")
        if ph:
            m = _PHASE_RE.search(str(ph))
            if m:
                return m.group(1)
        if _depth >= 3:
            return None
        fid = _parent_feature_id(rec)
        if fid:
            feat = records_by_id.get(fid)
            if feat is not None and feat is not rec:
                return _phase_id_of(feat, _depth + 1)
        return None

    # Phase-note records by canonical PHASE-#### key — used for the
    # phases list and for scope resolution.
    phase_record_by_id: dict[str, Any] = {}
    for p in phase_recs:
        if p.note_id:
            m = _PHASE_RE.search(p.note_id)
            if m:
                phase_record_by_id[m.group(1)] = p

    scope_block: dict[str, Any] | None = None
    exit_criteria: list[dict[str, Any]] | None = None
    if scope:
        scope_rec = phase_record_by_id.get(scope)
        if scope_rec is None:
            return None
        scope_block = {
            "id": scope,
            "title": scope_rec.title or scope,
            "status": scope_rec.status or "",
            "rel": scope_rec.rel_path,
        }
        exit_criteria = _exit_criteria_from_body(scope_rec.body)
        scoped_feature_ids = {
            r.note_id for r in features
            if r.note_id and _phase_id_of(r) == scope
        }

        def _linked_feature_ids(rec: Any) -> set[str]:
            out: set[str] = set()
            for field in ("features", "related", "implements", "parent"):
                val = rec.frontmatter.get(field)
                if not val:
                    continue
                for c in (val if isinstance(val, list) else [val]):
                    for fm_match in _FEAT_ID_RE.finditer(str(c)):
                        out.add(fm_match.group(1))
            return out

        def _in_scope(rec: Any) -> bool:
            pid = _phase_id_of(rec)
            if pid:
                return pid == scope
            # No direct or inherited phase — fall back to any linked
            # feature living in the scope (covers tests via
            # `features:`, changes via `features:`, risks via
            # `related:`).
            return bool(_linked_feature_ids(rec) & scoped_feature_ids)

        features     = [r for r in features if _phase_id_of(r) == scope]
        tasks        = [r for r in tasks if _in_scope(r)]
        issues       = [r for r in issues if _in_scope(r)]
        requirements = [r for r in requirements if _in_scope(r)]
        tests        = [r for r in tests if _in_scope(r)]
        risks        = [r for r in risks if _in_scope(r)]
        changes      = [r for r in changes if _in_scope(r)]
    else:
        def _in_scope(rec: Any) -> bool:  # noqa: ARG001 — unscoped
            return True

    sorted_chgs = sorted(changes, key=_activity_date, reverse=True)
    last_change = None
    if sorted_chgs:
        r = sorted_chgs[0]
        last_change = {
            "id": r.note_id,
            "title": r.title or r.note_id or "",
            "rel": r.rel_path,
            "date": _activity_date(r),
        }

    hero = {
        "features": _hero_count(features, DONE_FEAT),
        "tasks":    _hero_count(tasks, DONE_TASK),
        "issues": {
            "total": len(issues),
            "open":  sum(1 for r in issues if _norm(r.status) in OPEN_ISS),
        },
        "tests": {
            "total":   len(tests),
            "passing": sum(1 for r in tests if _norm(r.status) in PASSING),
        },
        "risks": {
            "total": len(risks),
            "open":  sum(1 for r in risks if _norm(r.status) in OPEN_RISK),
        },
        "requirements": _hero_count(requirements, DONE_REQ),
        "last_change": last_change,
    }

    def _mix(records) -> dict[str, int]:
        c: Counter[str] = Counter()
        for r in records:
            c[_norm(r.status) or "unknown"] += 1
        return dict(c)

    status_mix = {
        "features":     _mix(features),
        "tasks":        _mix(tasks),
        "issues":       _mix(issues),
        "requirements": _mix(requirements),
        "tests":        _mix(tests),
        "risks":        _mix(risks),
    }

    # Bucketed alongside the raw mix (TASK-0200): the overview's mix-bars
    # need four segments, and deciding which bucket a status falls into is
    # a *vocabulary* question. ISS-0023 is exactly what happens when a
    # surface answers that question locally, so the sidecar answers it once
    # here — using is_done_status and statuses.py — and the renderer only
    # draws the widths it is given.
    def _mix_buckets(records: Any, kind: str) -> dict[str, int]:
        out = {"done": 0, "doing": 0, "attention": 0, "backlog": 0}
        for r in records:
            status = _norm(r.status)
            if is_done_status(kind, status):
                out["done"] += 1
            elif statuses.band_of(status) == "active":
                out["doing"] += 1
            elif statuses.band_of(status) == "blocked":
                out["attention"] += 1
            elif status == "triage" or (
                status == "open" and kind in ("issue", "risk")
            ):
                out["attention"] += 1
            else:
                out["backlog"] += 1
        return out

    status_buckets = {
        "features":     _mix_buckets(features, "feature"),
        "tasks":        _mix_buckets(tasks, "task"),
        "issues":       _mix_buckets(issues, "issue"),
        "requirements": _mix_buckets(requirements, "requirement"),
        "tests":        _mix_buckets(tests, "test"),
        "risks":        _mix_buckets(risks, "risk"),
    }

    DOING_PHASE_BUCKET = {"doing", "active", "in_progress"}
    staleness_days = _staleness_days(index.docs_root)

    # Include features alongside tasks in the phase progress bars —
    # otherwise phases that have features tagged but no top-level
    # tasks render empty.
    phase_buckets: dict[str, Counter[str]] = {}
    for record in [*tasks, *features]:
        pid = _phase_id_of(record) or "unphased"
        bucket = ("done" if _is_done(record)
                  else "in_progress" if _norm(record.status) in DOING_PHASE_BUCKET
                  else "backlog")
        phase_buckets.setdefault(pid, Counter())[bucket] += 1

    # Per-phase drill-down: features in the phase + each feature's
    # children (tasks / requirements / issues with `parent: FEAT-...`).
    # Items in the phase that don't belong to any feature get bundled
    # as "loose" so they still show up.

    def _status_bucket(rec: Any) -> str:
        if _is_done(rec): return "done"
        if _norm(rec.status) in DOING_PHASE_BUCKET: return "in_progress"
        return "backlog"

    # ---- DES-0004: the square's state, and whether it needs a human --------
    #
    # `bucket` stays exactly as it was (done / in_progress / backlog) because
    # the mix bars and the phase progress fractions read it. `state` is the
    # finer encoding the squares render, and `attn` composes with any of them.

    def _square_state(rec: Any) -> str | None:
        """One of delivered / dropped / deferred / doing / unproven, or None
        for 'not started'. Mutually exclusive by construction: every status
        belongs to exactly one band in statuses.py.

        `unproven` overlays an otherwise-delivered item — that is the whole
        point, since the claim being unproven is what the mark says.
        """
        status = _norm(rec.status)
        if status == "deferred":
            return "deferred"
        if status in statuses.BANDS["archived"]:
            return "dropped"
        if _is_done(rec):
            return "unproven" if _is_unproven(rec) else "delivered"
        if status in DOING_PHASE_BUCKET:
            return "doing"
        return None

    def _is_unproven(rec: Any) -> bool:
        """Terminal, but the verification behind it is missing or expired.

        Two sources, both already in the corpus:
          * a recorded `verification_waiver` — a standing statement that the
            gate was skipped;
          * a manual test whose `last_verified` is older than the project's
            staleness threshold.

        The threshold and its config key are the validator's
        (`DEFAULT_STALENESS_DAYS`, `SNAPSHOT.yaml verification.staleness_days`),
        deliberately not a second one — a parallel staleness rule is the defect
        ISS-0024 and ISS-0069 are both about.
        """
        fm = rec.frontmatter or {}
        if str(fm.get("verification_waiver") or "").strip():
            return True
        if (rec.note_type or "").lower() != "test":
            return False
        if str(fm.get("command") or "").strip():
            return False           # executable: the runner stamps it, not a human
        return _is_stale_verification(fm, staleness_days)

    def _needs_human(rec: Any) -> bool:
        """DES-0004's dot: a specific human action is outstanding.

        `triage` and `review` are decisions waiting to be made; a `ready` test
        is defined and never executed. `open` and `deferred` are deliberately
        excluded — accepted work waiting on capacity, and a decision already
        taken (owner's call, 2026-07-30).

        Blocked-ness is computed from `depends:`, never read off a status:
        STATUSES.md is explicit that it is a relationship, no note carries
        `status: blocked`, and an item can be blocked while still `doing`.
        """
        status = _norm(rec.status)
        if status in ("triage", "review"):
            return True
        # `failing` was the one legal status with no mark and no dot: it fell
        # through to plain hollow, so a failing test rendered identically to
        # unstarted work — on a strip this change had just added tests to,
        # right after deleting `appendAsyncWaitingRows`, whose `failing` branch
        # at rank 0 was the overview's only surface for it (ISS-0071).
        #
        # The dot rather than a new mark: a failing test IS an outstanding human
        # action in exactly the sense the dot means, and the `blocked` band it
        # belongs to (failing / reopened) is the same idea.
        if status in statuses.BANDS["blocked"]:
            return True
        if (rec.note_type or "").lower() == "test" and status == "ready":
            return True
        return _has_unresolved_dependency(rec)

    def _has_unresolved_dependency(rec: Any) -> bool:
        if _is_done(rec) or _norm(rec.status) == "deferred":
            return False           # its own state settles it; a blocker is moot
        raw = (rec.frontmatter or {}).get("depends")
        if not isinstance(raw, list):
            return False
        for entry in raw:
            if not isinstance(entry, str):
                continue
            target = _strip_wikilink(entry).strip()
            if not target:
                continue
            path = index.by_id(target)
            blocker = index.get(path) if path else None
            if blocker is None:
                continue           # dangling target: the validator's problem
            if not _is_done(blocker):
                return True
        return False

    def _slim(rec: Any, kind: str) -> dict[str, Any]:
        slim = {
            "id": rec.note_id,
            "title": rec.title or rec.note_id or "",
            "rel": rec.rel_path,
            "status": rec.status or "",
            "bucket": _status_bucket(rec),
            "state": _square_state(rec),
            "type": kind,
        }
        if _needs_human(rec):
            slim["attn"] = True
        # Issues carry severity so attention surfaces can order by it;
        # absent severity reads "low", matching the right pane (TASK-0035).
        if kind == "issue":
            slim["severity"] = _norm(rec.frontmatter.get("severity")) or "low"
        return slim

    # Nest a child under its parent feature only when they share a phase.
    # A child explicitly moved to a different phase (e.g. a deferred task
    # parked in PHASE-999 whose parent feature lives in PHASE-004) must not
    # render under its parent's phase section — otherwise the project
    # overview shows it there while a scoped phase page (which filters by
    # the child's OWN phase) omits it. Such a child surfaces as loose under
    # its own phase instead (`loose_by_phase` below already places it), so
    # both views agree on where it lives (TASK-0182).
    children_by_parent_id: dict[str, list[Any]] = {}
    # Tests join the strip (DES-0004 / PHASE-012). They were absent, so a
    # `ready` test — defined and never executed — had no square to carry its
    # dot. 20 of 22 carry a `phase:`; the rest land under "Unphased" like any
    # other unphased note. Risks still cannot join: none of them carry a
    # phase at all, which is a corpus change rather than a rendering one.
    child_records = [*tasks, *requirements, *issues, *tests]
    for c in child_records:
        fid = _parent_feature_id(c)
        if not fid:
            continue
        parent = records_by_id.get(fid)
        if parent is not None and (
            (_phase_id_of(c) or "unphased") != (_phase_id_of(parent) or "unphased")
        ):
            continue
        children_by_parent_id.setdefault(fid, []).append(c)

    # Index features by phase so we can list them per phase below.
    features_by_phase: dict[str, list[Any]] = {}
    for feat in features:
        features_by_phase.setdefault(_phase_id_of(feat) or "unphased", []).append(feat)

    # Build the per-phase loose set: any child whose phase resolves to
    # the same phase as where it lives, but isn't attached to a feature
    # IN that phase.
    feature_ids_by_phase: dict[str, set[str]] = {
        ph: {f.note_id for f in feats if f.note_id}
        for ph, feats in features_by_phase.items()
    }

    loose_by_phase: dict[str, list[Any]] = {}
    for child in child_records:
        cph = _phase_id_of(child) or "unphased"
        fid = _parent_feature_id(child)
        belongs_to_phase_feature = bool(
            fid and fid in feature_ids_by_phase.get(cph, set())
        )
        if not belongs_to_phase_feature:
            loose_by_phase.setdefault(cph, []).append(child)

    all_phase_keys = sorted(set(list(phase_buckets.keys()) + list(phase_record_by_id.keys())))
    if scope:
        all_phase_keys = [scope]
    phases_list: list[dict[str, Any]] = []
    for k in all_phase_keys:
        rel: str | None = None
        if k == "unphased":
            title, st = "Unphased", None
        else:
            rec = phase_record_by_id.get(k)
            title = (rec.title if rec else None) or k
            st = rec.status if rec else None
            rel = rec.rel_path if rec else None
        b = phase_buckets.get(k, Counter())
        phase_features_payload = []
        for feat in features_by_phase.get(k, []):
            children = children_by_parent_id.get(feat.note_id or "", []) if feat.note_id else []
            phase_features_payload.append({
                **_slim(feat, "feature"),
                "children": [_slim(c, (c.note_type or "task").lower()) for c in children],
            })
        loose_payload = [_slim(c, (c.note_type or "task").lower())
                         for c in loose_by_phase.get(k, [])]
        # Phase-header markers (DES-0004). Two things no square can carry:
        #
        #   `waiting`   — how many items in this phase need a human. A
        #                 collapsed phase renders its squares with
        #                 offsetParent null, so without this the encoding
        #                 LOSES information the Waiting-on-you list showed.
        #                 A count, not ids: a header listing ids would be
        #                 that list with extra steps.
        #   `unclosed`  — every item done and the phase not closed. A
        #                 property of the phase, so nothing with a square
        #                 can hold it, and the only row in the old list that
        #                 nothing else on the page could tell you.
        every_item = [
            *(f for f in phase_features_payload),
            *(c for f in phase_features_payload for c in f["children"]),
            *loose_payload,
        ]
        # `unclosed` asks the VALIDATOR'S question, over the validator's
        # population: would PHASE-CHILDREN fire if this phase closed?
        #
        # Computing it from `every_item` was wrong twice. First cut used the
        # task/feature buckets and missed issues. Second cut used the strip's
        # items — which exclude risks, because none carry a phase and DES-0004
        # scoped them out — so a risk parked on a phase made the marker offer a
        # close-out the gate would refuse (ISS-0071). The strip's scope is a
        # rendering decision; the gate's is not.
        blockers = (
            phase_close_blockers(index, k) if k != "unphased" else ["unphased"]
        )
        phases_list.append({
            "key": k,
            "title": title,
            "status": st,
            "rel": rel,
            "tasks": {
                "done": b["done"],
                "in_progress": b["in_progress"],
                "backlog": b["backlog"],
            },
            "waiting": sum(1 for i in every_item if i.get("attn")),
            # `superseded` closes a phase too — the validator arms
            # PHASE-CHILDREN against both, so offering a superseded phase for
            # close-out would be a second disagreement with the gate.
            "unclosed": bool(
                not blockers
                and bool(every_item)
                and _norm(st) not in CLOSED_PHASE_STATUSES
            ),
            "features": phase_features_payload,
            "loose": loose_payload,
        })

    today = date.today()
    monday_today = today - timedelta(days=today.weekday())
    weeks_meta: list[dict[str, Any]] = []
    for w in range(12, -1, -1):
        start = monday_today - timedelta(days=7 * w)
        weeks_meta.append({
            "start_date": start.isoformat(),
            "week_iso": start.strftime("%G-W%V"),
            "count": 0,
        })
    # Activity counts EVERY interesting touch: each note contributes
    # one event for its `created` date AND one for its `updated` date
    # AND (when applicable) the CHG-YYYYMMDD ID prefix. We dedupe per
    # note so a same-day created == updated only counts once.
    by_start = {w["start_date"]: w for w in weeks_meta}
    activity_records: list[Any] = []
    for note_type in (
        "change", "task", "feature", "issue", "requirement",
        "risk", "test", "adr", "release", "workflow", "plan",
    ):
        activity_records.extend(index.notes_by_type(note_type))
    if scope:
        activity_records = [r for r in activity_records if _in_scope(r)]

    def _event_dates(rec: Any) -> set[str]:
        out: set[str] = set()
        fm = rec.frontmatter
        for key in ("created", "updated"):
            raw = fm.get(key)
            if not raw:
                continue
            s = str(raw).strip()
            if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                out.add(s[:10])
        if rec.note_id:
            m = _CHG_DATE_RE.match(rec.note_id)
            if m:
                out.add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        return out

    for rec in activity_records:
        for ds in _event_dates(rec):
            try:
                d = date.fromisoformat(ds)
            except ValueError:
                continue
            monday = d - timedelta(days=d.weekday())
            slot = by_start.get(monday.isoformat())
            if slot:
                slot["count"] += 1

    # Recent feed: any note from the same activity_records pool, sorted
    # by most-recent activity date. CHG-only was a leftover from the
    # earlier histogram design — most workspaces edit tasks/features
    # without filing a CHG, so a CHG-only feed under-reports.
    sorted_activity = sorted(
        activity_records,
        key=lambda r: _activity_date(r) or "",
        reverse=True,
    )
    recent: list[dict[str, Any]] = []
    for r in sorted_activity[:10]:
        ds = _activity_date(r)
        if not ds:
            continue
        recent.append({
            "id": r.note_id,
            "title": r.title or r.note_id or "",
            "rel": r.rel_path,
            "date": ds,
            "type": (r.note_type or "").lower(),
            "features": list(r.frontmatter.get("features") or []),
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": scope_block,
        "exit_criteria": exit_criteria,
        "focus": focus_block(index),
        "hero": hero,
        "phases": phases_list,
        "status_mix": status_mix,
        "status_buckets": status_buckets,
        "activity": {
            "weekly": weeks_meta,
            "recent": recent,
        },
    }


COMMITS_DEFAULT_LIMIT = 20
COMMITS_MAX_LIMIT = 100
_GIT_TIMEOUT_SECONDS = 5.0
_COMMIT_FIELD_SEP = "\x1f"
_COMMIT_RECORD_SEP = "\x1e"


DESIGN_REVISIONS_MAX = 50

_REGION_RE = re.compile(r'data-design-region="([^"]+)"')


def design_regions(docs_root: Path, asset_rel: str) -> list[str]:
    """Region ids an artifact declares, in document order, deduped.

    Read from the artifact rather than from the note, so the note cannot claim
    a region the artifact does not have — the note documents what the regions
    are *for*, the artifact is what actually carries them.
    """
    path = docs_root / asset_rel
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    seen, out = set(), []
    for rid in _REGION_RE.findall(text):
        if rid not in seen:
            seen.add(rid)
            out.append(rid)
    return out


def design_comments_payload(
    docs_root: Path, index: Index, design_id: str,
) -> dict[str, Any]:
    """Comments plus the regions they anchor to, with orphans flagged.

    An **orphan** is a comment whose region the artifact no longer declares.
    It is shown, never dropped: a comment that vanishes because someone renamed
    a region takes the objection with it, and the reviewer has no way to know
    it happened. Renaming is indistinguishable from delete-and-add, which is
    why the authoring contract says a region id is a published name.
    """
    from . import note_writes

    record = next((d for d in designs_payload(index)["designs"]
                   if d["id"] == design_id), None)
    if record is None:
        return {"schema_version": SCHEMA_VERSION, "id": design_id,
                "regions": [], "comments": [], "orphans": []}

    regions = design_regions(docs_root, record["asset"]) if record["asset"] else []
    note_path = docs_root / record["rel"]
    comments: list[dict[str, str]] = []
    if note_path.is_file():
        try:
            _fm, body = note_writes._split_frontmatter(
                note_path.read_text(encoding="utf-8"))
            comments = note_writes.read_design_comments(body)
        except Exception:  # noqa: BLE001 — a malformed note must not 500 the surface
            comments = []

    known = set(regions)
    for c in comments:
        # "" is the document lane — deliberately not an orphan.
        c["orphaned"] = bool(c["region"]) and c["region"] not in known
    return {
        "schema_version": SCHEMA_VERSION,
        "id": design_id,
        "regions": regions,
        "comments": comments,
        "orphans": [c for c in comments if c["orphaned"]],
    }


def design_note_digest(record: NoteRecord) -> str:
    """A stable digest of a design note's *substance* (ISS-0057).

    `design_revisions_payload` follows the **artifact** path, so `at_revision`,
    `head_revision` and `design_revision` all describe the artifact and say
    nothing about the note. A reviewer could accept a design and then have its
    Problem, Approach, Regions or Tokens rewritten under them, with every
    staleness signal still reading current.

    Two questions made that hard to fix, and both are answered by making this
    **additive**:

    * *Does a revision mean the artifact or the pair?* Neither — `design_revision`
      keeps meaning exactly what it meant, so no existing verdict changes
      meaning. This is a second, separate signal.
    * *What about `## Review`, which a review appends to?* Excluded, along with
      the review frontmatter fields and `## Revisions`. Otherwise filing a
      review would invalidate itself the instant it was recorded — the objection
      that kept this in triage.

    So the digest covers the parts a reviewer judged and nothing that recording
    the judgement touches.
    """
    import hashlib

    EXCLUDED_SECTIONS = ("## Review", "## Revisions")
    # `status` is excluded because `stamp_design_verdict` WRITES it on accept
    # (draft -> accepted), so leaving it in meant an accepting verdict changed
    # its own digest — the exact objection ISS-0057 claims to answer, found in
    # review as ISS-0071. Measured before the fix: 75f3c3b31b1b -> bf126afd62d7,
    # sole difference `status: draft -> accepted`.
    EXCLUDED_FIELDS = ("reviewed_by", "review_date", "review_verdict",
                       "design_revision", "updated", "status",
                       "superseded_by")

    body_lines: list[str] = []
    skipping = False
    for line in (record.body or "").splitlines():
        if line.startswith("## "):
            skipping = any(line.startswith(s) for s in EXCLUDED_SECTIONS)
        if not skipping:
            body_lines.append(line.rstrip())

    fields = {
        k: v for k, v in sorted((record.frontmatter or {}).items())
        if k not in EXCLUDED_FIELDS
    }
    material = repr(fields) + "\n" + "\n".join(body_lines).strip()
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]


def design_revisions_payload(
    project_root: Path, index: Index, design_id: str,
) -> dict[str, Any]:
    """An artifact's revision history from git (TASK-0216).

    Reads ``git log --follow`` over the asset path so a rename does not
    truncate the history — a design that gets renamed has not lost its past.

    Also reports whether the artifact is **dirty**. That matters more than it
    looks: the render surface shows the working copy, so an uncaptured edit is
    a revision the compare view cannot see and the log does not record. Saying
    so is the difference between "this design has three revisions" and "this
    design has three revisions plus whatever you have not committed".

    Same hardening as ``commits_payload``: fixed argv, no shell, clamped
    count, and a plain ``available: False`` outside a git repo rather than an
    exception. The only caller-derived value is the design id, and it is
    resolved through the register to a path the register already trusts —
    never interpolated into the command.
    """
    import subprocess

    unavailable = {"schema_version": SCHEMA_VERSION, "available": False,
                   "revisions": [], "dirty": False}
    record = next((d for d in designs_payload(index)["designs"]
                   if d["id"] == design_id), None)
    if record is None or not record["asset"]:
        return unavailable
    if not (project_root / ".git").exists():
        return unavailable

    asset_rel = "docs/" + record["asset"]
    sep = _COMMIT_FIELD_SEP
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "-C", str(project_root), "log", f"-n{DESIGN_REVISIONS_MAX}",
             "--follow", f"--format={sep.join(['%h', '%H', '%aI', '%s', '%an'])}",
             "--", asset_rel],
            capture_output=True, text=True, timeout=5, check=False,
        )
        status = subprocess.run(  # noqa: S603
            ["git", "-C", str(project_root), "status", "--porcelain", "--", asset_rel],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return unavailable
    if proc.returncode != 0:
        return unavailable

    revisions = []
    for line in proc.stdout.splitlines():
        parts = line.split(sep)
        if len(parts) != 5:
            continue
        short, full, iso, subject, author = parts
        # The reason lives in the commit message, which is why capture requires
        # one: it is the only readable record between two regenerated HTML
        # files whose diff is a wall of noise.
        reason = subject.split(": ", 1)[1] if subject.startswith("design(") else subject
        revisions.append({
            "sha": short, "full_sha": full, "date": iso[:10],
            "subject": subject, "reason": reason, "author": author,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "available": True,
        "id": design_id,
        "asset": record["asset"],
        "revisions": revisions,
        "dirty": bool(status.stdout.strip()),
    }


def design_asset_at(
    project_root: Path, index: Index, design_id: str, sha: str,
) -> bytes | None:
    """The artifact as it was at one revision, without touching the tree.

    ``git show <sha>:<path>`` rather than a checkout — reading history must
    never mutate the working copy, and a compare view that stashed the user's
    uncommitted work to render a diff would be a data-loss bug wearing a
    feature's clothes.
    """
    import re as _re
    import subprocess

    if not _re.fullmatch(r"[0-9a-fA-F]{4,40}", sha or ""):
        return None
    record = next((d for d in designs_payload(index)["designs"]
                   if d["id"] == design_id), None)
    if record is None or not record["asset"]:
        return None
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, sha validated above
            ["git", "-C", str(project_root), "show",
             f"{sha}:docs/{record['asset']}"],
            capture_output=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def commits_payload(
    project_root: Path, index: Index, limit: int = COMMITS_DEFAULT_LIMIT
) -> dict[str, Any]:
    """Recent commits as *documentation* events (TASK-0199 / FEAT-0040).

    Each commit lists the doc notes it touched — resolved through the live
    index by ``rel_path`` — with the item's id, type and current status, and
    a ``done`` marker so a completion reads at a glance. Commits that touch
    no notes are flagged ``undocumented``: FEAT-0022's traceability
    guardrail, applied per commit rather than per session.

    Hardening (TASK-0199 DoD): the subprocess runs with a fixed argv — the
    only caller-derived value is ``limit``, clamped to an int and passed as
    ``-n`` — so no client string ever reaches git. The call is bounded by
    ``_GIT_TIMEOUT_SECONDS`` and a commit cap, and every failure mode (not a
    repo, git absent, timeout, empty history) degrades to
    ``{"available": False}`` rather than raising. Values are returned as
    data and escaped by the renderer like all other note-derived content.
    The render server binds 0.0.0.0 by design for tablet viewing, so this
    exposes only commit metadata of the same repository whose notes are
    already being served — see the RISK-0001 and RISK-0004 threat models.
    """
    import subprocess

    try:
        count = int(limit)
    except (TypeError, ValueError):
        count = COMMITS_DEFAULT_LIMIT
    count = max(1, min(count, COMMITS_MAX_LIMIT))

    unavailable = {
        "schema_version": SCHEMA_VERSION,
        "available": False,
        "commits": [],
    }
    if not (project_root / ".git").exists():
        return unavailable

    fmt = _COMMIT_FIELD_SEP.join(["%h", "%H", "%aI", "%s", "%an"])
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            [
                "git",
                "-C",
                str(project_root),
                "log",
                f"-n{count}",
                "--no-merges",
                "--name-only",
                f"--format={_COMMIT_RECORD_SEP}{fmt}",
            ],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return unavailable
    if proc.returncode != 0:
        return unavailable

    # rel_path is relative to docs_root; git paths are relative to the repo
    # root. Build the prefix once so the join is a dict lookup per file.
    docs_prefix = ""
    try:
        docs_prefix = index.docs_root.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except (ValueError, OSError):
        docs_prefix = ""
    prefix = f"{docs_prefix}/" if docs_prefix else ""

    by_rel: dict[str, Any] = {}
    for record in index.iter_records():
        if record.note_id:
            by_rel[record.rel_path.lower()] = record

    commits: list[dict[str, Any]] = []
    for chunk in proc.stdout.split(_COMMIT_RECORD_SEP):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        header, _, files_blob = chunk.partition("\n")
        fields = header.split(_COMMIT_FIELD_SEP)
        if len(fields) < 5:
            continue
        short_sha, full_sha, date_iso, subject, author = fields[:5]

        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for line in files_blob.splitlines():
            line = line.strip()
            if not line or not line.lower().endswith(".md"):
                continue
            if prefix and not line.startswith(prefix):
                continue
            rel = line[len(prefix):] if prefix else line
            record = by_rel.get(rel.lower())
            if record is None or not record.note_id:
                continue
            if record.note_id in seen_ids:
                continue
            seen_ids.add(record.note_id)
            items.append({
                "id": record.note_id,
                "title": record.title or record.note_id,
                "rel": record.rel_path,
                "type": (record.note_type or "").lower(),
                "status": record.status or "",
                "done": is_done_status(record.note_type, record.status),
            })

        items.sort(key=lambda i: (_TYPE_ORDER.get(i["type"], 99), i["id"]))
        commits.append({
            "sha": short_sha,
            "full_sha": full_sha,
            "date": date_iso[:10],
            "subject": subject,
            "author": author,
            "items": items,
            # No note touched: the change left no documentation trace.
            "undocumented": not items,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "available": True,
        "commits": commits,
    }


# Canonical-ish ordering so a commit's items read feature → task → issue …
_TYPE_ORDER: dict[str, int] = {
    "feature": 0, "requirement": 1, "task": 2, "issue": 3,
    "test": 4, "change": 5, "adr": 6, "decision": 6, "risk": 7,
    "phase": 8, "release": 9, "plan": 10,
}


# ----------------------------------------------------------------------
# Review desk (FEAT-0041)
# ----------------------------------------------------------------------

#: Intake states that put a note in the queue on their own — these are
#: existing vocabulary, not new statuses (ADR-0007 / owner decision:
#: no new states). Feature/task proposal sets queue via review requests
#: instead, because their vocabulary has no intake state to borrow.
QUEUE_INTAKE_STATES: dict[str, tuple[str, ...]] = {
    "adr": ("proposed",),
    "decision": ("proposed",),
    "requirement": ("draft",),
    "test": ("ready",),
    # A design enters the queue when it is offered for review. `draft` is
    # deliberately absent — the author is still writing it — and so is
    # `implemented`, which is the state AFTER the design was built. Queueing
    # either would ask for a decision nobody owes, the mistake plans made.
    "design": ("proposed",),
}
# Plans are deliberately absent. A plan's status *follows its parent
# feature* and is advanced at close-out (STATUSES.md, `[[plan]]`), so
# `draft` on a plan means "the feature hasn't started", not "a human owes
# this a decision". Queueing them asked Edwin to review things no reviewer
# can act on — and they carry no `id:` either, so a queue row could not
# even address them. Reported 2026-07-26.


def _slim_note(record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.note_id or "",
        "rel": record.rel_path,
        "type": (record.note_type or "").lower(),
        "status": record.status or "",
    }


def review_queue_payload(
    index: Index, store: Any = None,
) -> dict[str, Any]:
    """The ~review queue (TASK-0206).

    Four groups, each sourced from something that already exists:

    * **Decisions** — ADRs at ``proposed``.
    * **Proposals** — dispatch-ledger review requests (runtime state; the
      notes stay at ``backlog``). Requirements/plans at ``draft`` join
      here since they are proposals in the same sense.
    * **Questions** — question requests from the store.
    * **Test runs** — manual tests at ``ready``: defined, never executed.

    No status is invented anywhere; see ``review.py`` for why the queue is
    runtime state rather than note state.
    """
    decisions: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []

    # Subjects with an open ledger request. A design can arrive by status
    # intake AND by being offered (TASK-0229); it must appear once, and the
    # ledger row wins because it carries the revision the reviewer was asked
    # about. Without this a `proposed` design that someone also offered would
    # produce two rows a human cannot tell apart.
    offered: set[str] = set()
    if store is not None:
        for request in store.open_requests():
            subject = str(request.get("subject") or "").strip().upper()
            if subject:
                offered.add(subject)

    for note_type, states in QUEUE_INTAKE_STATES.items():
        for record in index.notes_by_type(note_type):
            status = (record.status or "").lower().strip()
            if status not in states:
                continue
            if (record.note_id or "").strip().upper() in offered:
                continue
            item = _slim_note(record)
            item["kind"] = (
                "decide" if note_type in ("adr", "decision")
                else "run" if note_type == "test"
                else "review"
            )
            if note_type == "test":
                # Only manual tests are runnable from the desk; an
                # automated test at `ready` is waiting on a runner, not
                # on a human.
                if not _is_manual_test(record):
                    continue
                item["steps"] = len(manual_test_steps(record.body))
                runs.append(item)
            elif note_type in ("adr", "decision"):
                decisions.append(item)
            else:
                proposals.append(item)

    if store is not None:
        for request in store.open_requests():
            entry = {
                "request_id": request.get("request_id"),
                "kind": "answer" if request.get("kind") == "question" else "review",
                "title": request.get("title") or "",
                "body": request.get("body") or "",
                "ts": request.get("ts"),
                "session_id": request.get("session_id"),
                "agent": request.get("agent"),
                "items": [],
            }
            subject = str(request.get("subject") or "").strip().upper()
            if subject:
                entry["subject"] = subject
                entry["at_revision"] = str(request.get("at_revision") or "")
                path = index.by_id(subject)
                record = index.get(path) if path else None
                if record is not None:
                    entry["subject_note"] = _slim_note(record)
                    entry["subject_type"] = (record.note_type or "").lower()
                else:
                    # The design was deleted or renamed after being offered.
                    # Say so: a queue row pointing at nothing is worse than a
                    # row that explains itself, and silently dropping it would
                    # strand the request forever.
                    entry["subject_missing"] = True
            for note_id in request.get("items") or []:
                path = index.by_id(note_id)
                record = index.get(path) if path else None
                entry["items"].append(
                    _slim_note(record) if record else {"id": note_id}
                )
            if request.get("kind") == "question":
                questions.append(entry)
            else:
                proposals.append(entry)

    for bucket in (decisions, proposals, questions, runs):
        bucket.sort(key=lambda i: str(i.get("id") or i.get("ts") or ""))

    total = len(decisions) + len(proposals) + len(questions) + len(runs)
    # ADR-0007 chose an advisory phase explicitly so gating could be decided
    # with data ("revisit when ~20 sets have passed through the desk, or at
    # PHASE-008 close-out"). The store was already counting outcomes and
    # nothing read them, which would have made that revisit a judgement call
    # with no evidence — the exact failure ADR-0006 was written about.
    outcomes = store.outcome_counts() if store is not None else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "total": total,
        "outcomes": outcomes,
        "reviewed": sum(outcomes.values()),
        "groups": [
            {"key": "decisions", "label": "Decisions", "items": decisions},
            {"key": "proposals", "label": "Proposals", "items": proposals},
            {"key": "questions", "label": "Questions", "items": questions},
            {"key": "runs", "label": "Tests to do", "items": runs},
        ],
        "registers": {
            "tests": _tests_register(index),
            "reviewed": _reviewed_register(index),
        },
    }


def _tests_register(index: Index) -> list[dict[str, Any]]:
    """Every acceptance test in the corpus (FEAT-0049 / TASK-0241).

    Distinct from the ``runs`` queue group above, which is gated to
    manual tests at ``ready`` — "what is waiting on me" against "what do
    we verify at all". The queue slice was about four rows out of 21
    here, and the register lived only in Library, so the corpus-wide
    answer was one mode-switch away from the surface that asks the
    question.

    The per-scope Verification panel (TASK-0211) is untouched: it answers
    "does *this* feature pass", which is a third question again.
    """
    out: list[dict[str, Any]] = []
    for record in index.notes_by_type("test"):
        fm = record.frontmatter
        item = _slim_note(record)
        item.update({
            "last_verified": str(
                fm.get("last_verified") or fm.get("last_run") or ""
            ),
            "manual": _is_manual_test(record),
            "command": str(fm.get("command") or ""),
            # FEAT-0018's badge data (waived / review_verdict / adequacy)
            # travels with the register. It used to ride on the Library
            # test rows; the register is where those rows went, and a
            # test listed without its adequacy flag is the "green count,
            # unexamined guard" the flag exists to expose.
            **_verification_flags(record),
        })
        out.append(item)
    out.sort(key=lambda t: str(t.get("id") or ""))
    return out


#: Verdicts that leave work owed — a reviewer asked for something.
OWED_VERDICTS: frozenset[str] = frozenset({"changes-requested", "rejected"})


def _verdict_is_owed(
    verdict: str, status: str | None, note_type: object = None,
) -> bool:
    """True when a verdict still owes somebody work (ISS-0121).

    The verdict alone is not enough, and reading it alone is the defect this
    replaces: ``review_verdict`` is **sticky**. A reviewer writes
    ``changes-requested``, the work is done, the note reaches ``fixed`` /
    ``done`` / ``merged`` — and nothing clears the stamp. Measured 2026-08-10:
    all ten rows the desk headed *Changes requested* were terminal. Genuinely
    owed: zero.

    So the subject's **current status** is the discriminator, and it is the only
    one available. The obvious alternative — compare the note's ``updated``
    against its ``review_date``, on the theory that work landing after a verdict
    settles it — was measured first and does not work: stamping the verdict *is*
    an edit, so ``updated`` is set to the review's own day. 10 of the 10, and 85
    of the 103 verdicts in the corpus, have ``updated <= review_date``. The
    comparison would call every one of them still-owed, which is backwards.

    **Known limitation, recorded rather than hidden.** A genuine re-review of
    already-finished work — a ``merged`` change someone then asks changes of —
    reads as settled here. Separating it needs the date the note *became*
    terminal, which frontmatter does not carry; ``status_diff`` recovers it from
    ``git log`` and wiring that into a per-request register is disproportionate
    to a case this corpus has never produced. If it occurs, that is the fix.

    **The terminal test is per TYPE, not per band** ([[ISS-0245]]). This asked
    `statuses.is_completed`, and `band_of("accepted")` is **`active`** -- so for
    the four types whose terminal status IS `accepted` (`adr`, `design`,
    `reference`, `requirement`) the obligation could never clear. A reviewer
    wrote `changes-requested`, the author fixed everything, the note reached
    `accepted`, and the row stayed in `Needs you` for the life of the record:
    exactly the sticky verdict this function exists to end, surviving on the
    one axis its fix did not cover.

    It is also [[REQ-0059]]'s forbidden shape -- one question, two
    implementations -- and `_covers_an_issue` was caught committing it a week
    earlier. `is_done_status` is the app's answer to *is this note finished*,
    so this asks that.

    **Found because a test went green for the wrong reason.** `ADR-0040` was
    stamped `changes-requested`, then accepted, and
    `test_every_row_of_the_rehoming_table_is_reachable` failed. The suite went
    green again when the reviewer updated its own verdict -- a legitimate act
    that masked the defect, and one it named rather than let pass.

    `note_type` defaults to `None` so a caller that cannot supply it falls back
    to the old band test rather than raising; both real call sites have the
    record in hand and pass it.
    """
    if verdict not in OWED_VERDICTS:
        return False
    if note_type is not None:
        return not is_done_status(note_type, status)
    return not statuses.is_completed(status)


def unreleased_payload(index: Index) -> dict[str, Any]:
    """Done features no shipped release names (FEAT-0072 / TASK-0315).

    *"Done" and "shipped" are different facts and the cockpit knows only one.*
    This is the second fact.

    **Membership, not dates.** A feature counts as shipped when a `[[release]]`
    note names it in `features:`. Deriving it from dates instead would need a
    completion timestamp features do not carry — `updated:` moves for a typo —
    and would silently mis-sort anything closed out late.

    **Only a `released` release ships anything.** `draft` means *"prepared and
    verified, not yet live"* (STATUSES.md), so a drafted note must not empty
    this card: drafting is not shipping, and a count that fell to zero the
    moment somebody wrote a plan would be asserting the release had happened.
    That mattered here for exactly one day. **REL-0001 went `released` on
    2026-08-11** at 1.0.0, so the card stopped counting every done feature (86)
    and started measuring against a release (59 — the 27 it names are shipped).
    The paragraph above is why the number moved by 27 rather than to zero.

    Returns the count, the newest shipped release if there is one, and the
    rows themselves so the card can navigate.
    """
    shipped_ids: set[str] = set()
    latest: dict[str, Any] | None = None
    for record in index.notes_by_type("release"):
        if record.rel_path.startswith("__templates__/"):
            continue
        if str(record.status or "").strip().lower() != "released":
            continue
        # `_design_link_ids` despite the name — it is the module's one
        # wikilink-to-ids reader and works on any `[[TYPE-0000-Slug]]`.
        shipped_ids.update(_design_link_ids(record.frontmatter.get("features")))
        # Newest by date, falling back to id so a note with no date still
        # orders deterministically rather than by filesystem order.
        key = (str(record.frontmatter.get("date") or ""), record.note_id or "")
        if latest is None or key > latest["_key"]:
            latest = {
                "_key": key,
                "id": record.note_id or "",
                "title": record.title or "",
                "rel": record.rel_path,
                "date": str(record.frontmatter.get("date") or ""),
            }

    rows: list[dict[str, Any]] = []
    for record in index.notes_by_type("feature"):
        if record.rel_path.startswith("__templates__/"):
            continue
        if not statuses.is_completed(record.status or ""):
            continue
        if (record.note_id or "") in shipped_ids:
            continue
        rows.append(_slim_note(record))
    rows.sort(key=lambda r: str(r.get("id") or ""))

    since = None
    if latest is not None:
        since = {k: v for k, v in latest.items() if k != "_key"}
    return {
        "schema_version": SCHEMA_VERSION,
        "count": len(rows),
        "since": since,
        "items": rows,
    }


def _reviewed_register(index: Index) -> list[dict[str, Any]]:
    """Items carrying an independent-review verdict (TASK-0242).

    Sourced from **note frontmatter**, not the review store. The store
    does retain resolved requests (``status: "resolved"`` +
    ``resolved_at``), so reading them would be cheaper — but
    ``_MAX_REQUESTS = 200`` trims oldest-first on every save, so a
    store-sourced register would silently lose its tail. Frontmatter has
    no such ceiling and is the authored record (ADR-0009).

    The store keeps the *outcome counts*, which the notes genuinely
    cannot answer: `accepted-amended` and `changes-requested` are
    properties of the review interaction, not of the note's final
    verdict. That is the ADR-0007 measurement and it stays where it is.
    """
    out: list[dict[str, Any]] = []
    for record in index.iter_records():
        verdict = record.frontmatter.get("review_verdict")
        if not isinstance(verdict, str) or not verdict.strip():
            continue
        item = _slim_note(record)
        normalised = verdict.strip().lower()
        item.update({
            "verdict": normalised,
            "reviewed_by": str(record.frontmatter.get("reviewed_by") or ""),
            "review_date": str(record.frontmatter.get("review_date") or ""),
            "owed": _verdict_is_owed(normalised, record.status, record.note_type),
            #: **What the author did about it** ([[ISS-0253]]). The verdict is
            #: sticky and nothing refreshes it: 43 notes reached a terminal
            #: status still reading `changes-requested`, every one true as a
            #: fact about a moment and false as a description of the note
            #: today. `review_response:` is where *"the findings were
            #: addressed"* goes -- it does NOT touch the verdict, because a
            #: verdict is the reviewer's and self-clearing it turns an
            #: independent gate into a formality (ADR-0011).
            "response": str(record.frontmatter.get("review_response") or ""),
            "response_date": str(
                record.frontmatter.get("review_response_date") or ""),
        })
        out.append(item)
    # Most recent first. A note with no `review_date` still lists — it
    # sorts last rather than being dropped, because a recorded verdict
    # with a missing date is exactly the kind of thing worth seeing.
    out.sort(
        key=lambda r: (r.get("review_date") or "", str(r.get("id") or "")),
        reverse=True,
    )
    return out


def scope_tests_payload(index: Index, note_id: str) -> dict[str, Any]:
    """Acceptance tests that validate one scope (TASK-0211).

    A test belongs to a scope when it links to it — via `features:`,
    `verifies:`, `validates:`, `tests:` or `parent:` — or, for a phase,
    when its own phase resolves there. Read from the notes only: the
    panel is the durable record, so it must not depend on the review
    queue existing or having been used.
    """
    target = (note_id or "").strip().upper()
    if not target:
        return {"schema_version": SCHEMA_VERSION, "tests": []}

    path = index.by_id(target)
    record = index.get(path) if path else None
    scope_type = (record.note_type or "").lower() if record else ""

    # For a phase, the scope is every feature inside it plus the phase id.
    scope_ids = {target}
    if scope_type == "phase":
        for feature in index.notes_by_type("feature"):
            fm_phase = str(feature.frontmatter.get("phase") or "")
            if target in fm_phase.upper() and feature.note_id:
                scope_ids.add(feature.note_id.upper())

    link_fields = ("covers", "features", "verifies", "validates", "tests", "parent",
                   "implements", "related", "phase")

    days = _staleness_days(index.docs_root)
    out: list[dict[str, Any]] = []
    for test in index.notes_by_type("test"):
        linked: set[str] = set()
        for field in link_fields:
            value = test.frontmatter.get(field)
            if not value:
                continue
            for entry in (value if isinstance(value, list) else [value]):
                for match in _FOCUS_ID_RE.finditer(str(entry).upper()):
                    linked.add(match.group(0))
        if not (linked & scope_ids):
            continue
        fm = test.frontmatter
        out.append({
            "id": test.note_id,
            "title": test.title or test.note_id or "",
            "rel": test.rel_path,
            "status": test.status or "",
            "last_run": str(fm.get("last_run") or fm.get("last_verified") or ""),
            "manual": _is_manual_test(test),
            "steps": len(manual_test_steps(test.body)),
            # TASK-0371: the panel used to decide staleness itself, in the
            # renderer, at 60 days on `last_run` and only for manual tests —
            # while the validator and the overview's `unproven` marker used
            # 90 on `last_verified` for everything. Two rules, one question.
            # The server's is the project's, so it is the one that ships.
            "stale": _test_is_stale(fm, days),
        })
    out.sort(key=lambda t: str(t["id"] or ""))

    # Decisions that reach this scope, resolved through the *link graph*
    # rather than by matching ids in titles. The renderer had a
    # title-substring heuristic here first; it is the kind of shortcut
    # that looks right on this corpus and silently misses an ADR whose
    # title happens not to name its subject.
    decisions: list[dict[str, Any]] = []
    for adr in [*index.notes_by_type("adr"), *index.notes_by_type("decision")]:
        reached: set[str] = set()
        for field in ("related", "affects", "supersedes", "superseded_by",
                      "scope", "impacts", "source"):
            value = adr.frontmatter.get(field)
            if not value:
                continue
            for entry in (value if isinstance(value, list) else [value]):
                for match in _FOCUS_ID_RE.finditer(str(entry).upper()):
                    reached.add(match.group(0))
        if reached & scope_ids:
            decisions.append({
                "id": adr.note_id,
                "title": adr.title or adr.note_id or "",
                "rel": adr.rel_path,
                "status": adr.status or "",
            })
    decisions.sort(key=lambda d: str(d["id"] or ""), reverse=True)

    # **What stands between this scope and terminal** (ADR-0034 / REQ-0043).
    # The first production caller of `blocking_for`: independent review found
    # gating-at-any-granularity implemented and used by nothing, which is the
    # difference between a capability and a feature.
    #
    # Scoped to THIS note's ids, so a feature's panel answers *what blocks this
    # feature* rather than *what blocks the release* — the question a reader
    # opening one scope is actually asking, and the one the release-shaped gate
    # could never answer.
    blocking: list[dict[str, Any]] = []
    try:
        suite = _acceptance.load(index.docs_root, index)
    except OSError:                                   # pragma: no cover
        suite = None
    if suite is not None:
        for item in suite.blocking_for(scope_ids):
            blocking.append({
                "id": item.note_id or item.number,
                "title": item.name,
                "rel": item.rel,
                "tier": item.tier,
                "mark": item.mark,
                # Named rather than implied: an unattributable check blocks
                # every scope, and a reader seeing it under one feature is owed
                # the reason it is there.
                "unattributed": not item.refs,
            })

    return {
        "schema_version": SCHEMA_VERSION,
        "tests": out,
        "decisions": decisions,
        "blocking": blocking,
    }


def _is_manual_test(record: NoteRecord) -> bool:
    """Who runs this test: the machine if it declares a `command:`, else a person.

    **One field, no heuristics** (ADR-0034 decision 4). This consulted
    `command`, then `automation`/`kind`/`mode`/`method`, then the shape of the
    body — four fallbacks approximating one question. `kind:` was deleted, and
    independent review caught that leaving `automation:` in the list would have
    MOVED the ambiguity rather than removed it: it is set on 671 of 788 fleet
    notes and reads `manual` on 466, so it became the second who-runs-this field
    the moment the first one went.

    `automation:` answers *does a machine cover this check* — `full`/`partial`/
    `manual`. It was a claim about **coverage**, not about who
    performs the walk. The two were conflated because before ADR-0031 they
    described the same population.

    **The remaining rule is total and needs no fallback**: a note with no
    `command:` cannot be run by anything except a person. That is not an
    inference about intent — it is what the corpus can and cannot execute — and
    it makes the previously-possible state *"treated as automated, declares no
    way to run"* unreachable rather than merely rare. `your-sudoku`'s TST-0013
    was in exactly that state and is now correctly owed to a person.
    """
    return not str(record.frontmatter.get("command") or "").strip()


# Manual tests in the wild head their procedure several ways — this repo's
# own TST-0011 uses "Checklist", the template suggests "Steps". Accepting
# the corpus's vocabulary rather than one canonical spelling is the same
# lesson ADR-0006 recorded: a surface follows what is written, not what a
# convention wishes were written.
#
# `cases` added by ISS-0172 — `your-trainer`'s TST-0018, written for the
# feature that repo was actively building, heads its procedure `## Cases` and
# parsed to nothing.
_STEP_HEADING_RE = re.compile(
    r"^(#{2,6})\s*(steps|checklist|procedure|scenario|script|cases)\b",
    re.IGNORECASE,
)
#: Captures the level so a procedure can contain SUBSECTIONS (ISS-0172). The
#: predecessor matched any heading and the loop broke on it, so `## Steps`
#: followed by `### Export` ended the procedure at its own first subheading and
#: yielded zero steps — 8 of the 15 manual tests `your-trainer` was asking a
#: person to walk, including two written the day before it was reported. None
#: of those notes was malformed; two levels is the natural shape for a
#: procedure with parts.
_HEADING_LEVEL_RE = re.compile(r"^(#{1,6})\s")
#: A list marker must be followed by WHITESPACE, which Markdown requires and
#: the predecessor did not check: `[-*]` with `\s*` after it made `**Offline
#: entitlement** — on a device…` a step, because a bold run opens with the same
#: character as a bullet. Found while reading the parser's own output on
#: `your-trainer`'s TST-0018 (ISS-0172) — a paragraph lead-in rendered as step
#: 1 of 11, with its closing `**` still attached.
_STEP_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]\s+|[-*+]\s+)(?:\[[ xX]\]\s*)?(.+)$")
#: A checkbox item, specifically — the fallback's unit (ISS-0172). Four of the
#: eight had no procedure heading at ALL: their whole body is sections of
#: checkboxes (`## A — Input screens`, sixteen `## N. Area` sections). A
#: checkbox is an explicit *this is a thing to do* mark, which a bullet inside
#: a Purpose paragraph is not — so the fallback reads those and not prose.
#: Narrow by measurement: 6 of the 65 TST notes fleet-wide contain one.
_CHECKBOX_ITEM_RE = re.compile(r"^\s*[-*+]\s+\[[^\]]*\]\s*(.+?)\s*$")
# Markdown emphasis is noise in a stepper's one-line label.
_MD_EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)(.+?)\1")
#: Matched against the line with emphasis already stripped, and allowing a list
#: marker, because the corpus writes the expectation as `- **Expected**: …`
#: under its step. The predecessor anchored on a bare `Expected:` at line
#: start, so every one of those lines missed this and was picked up by
#: `_STEP_ITEM_RE` as a step of its own — a procedure of eleven steps rendered
#: as twenty-two, alternating action and expectation.
_EXPECTED_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:expect(?:ed|s)?|then)\s*[:：]\s*(.*)$", re.IGNORECASE,
)
# An inline "… Expect: <what should happen>" clause inside a step line.
_INLINE_EXPECT_RE = re.compile(r"\bexpect(?:ed|s)?\s*[:：]\s*(.+)$", re.IGNORECASE)


def _build_step(n: int, text: str) -> dict[str, Any] | None:
    """One step from its raw list-item text, or None when it is empty."""
    step: dict[str, Any] = {"n": n, "text": text}
    # "Do the thing. Expect: it works" on one line — the shape this repo's
    # own manual tests actually use.
    inline = _INLINE_EXPECT_RE.search(text)
    if inline:
        step["text"] = text[:inline.start()].rstrip(" .—-–")
        step["expected"] = inline.group(1).strip()
    step["text"] = _MD_EMPHASIS_RE.sub(r"\2", str(step["text"])).strip()
    if "expected" in step:
        step["expected"] = _MD_EMPHASIS_RE.sub(r"\2", step["expected"]).strip()
    return step if step["text"] else None


def manual_test_steps(body: str) -> list[dict[str, Any]]:
    """Parse a manual test's procedure into ordered steps (ISS-0172).

    Two rules, in order:

    1. **A procedure heading**, which runs until a heading **at or above its
       own level** — so its subsections are part of it rather than the thing
       that ends it.
    2. **Failing that, every checkbox in the body.** A note whose whole body is
       sections of checkboxes has no procedure heading to find, and its
       checkboxes are its procedure.

    An ``Expected:`` line, with or without a list marker, or an inline
    ``… Expect: …`` clause, attaches to its step as the expectation the runner
    shows beside Pass/Fail.

    Returning ``[]`` is a real answer and callers must render it as one: an
    affordance that silently disappears is what ISS-0172 was filed about.
    """
    lines = (body or "").splitlines()
    steps: list[dict[str, Any]] = []
    level = 0

    for line in lines:
        heading = _HEADING_LEVEL_RE.match(line)
        # Ends only at a heading that is not INSIDE the procedure.
        if level and heading and len(heading.group(1)) <= level:
            break
        start = _STEP_HEADING_RE.match(line)
        if start and not level:
            level = len(start.group(1))
            continue
        if not level or heading:
            continue
        plain = _MD_EMPHASIS_RE.sub(r"\2", line)
        expected = _EXPECTED_RE.match(plain)
        if expected and steps:
            steps[-1]["expected"] = expected.group(1).strip()
            continue
        item = _STEP_ITEM_RE.match(line)
        if not item:
            continue
        step = _build_step(len(steps) + 1, item.group(1).strip())
        if step:
            steps.append(step)

    if steps or level:
        return steps

    # No procedure heading anywhere: the checkboxes are the procedure.
    for line in lines:
        item = _CHECKBOX_ITEM_RE.match(line)
        if not item:
            plain = _MD_EMPHASIS_RE.sub(r"\2", line)
            expected = _EXPECTED_RE.match(plain)
            if expected and steps:
                steps[-1]["expected"] = expected.group(1).strip()
            continue
        step = _build_step(len(steps) + 1, item.group(1).strip())
        if step:
            steps.append(step)
    return steps


#: How a manifest entry reads as a nav row. Borrowed from the status
#: vocabulary rather than invented, so the navigator's own fold and sort work
#: on these without learning a fifth set of words (the ISS-0023 rule).
_STANDING_STATUS: dict[str, str] = {
    "missing": "blocked",
    "ambiguous": "blocked",
    "stub": "draft",
    "stale": "review",
    "has_status": "review",
}


def _standing_group(index: Index) -> list[dict[str, Any]]:
    """The standing set, as the Intent view's landing (TASK-0382).

    *"What is this project?"* is the question this view answers, and these are
    the documents that answer it — so the view opens on them rather than on a
    file list. That also settles the empty-state question without a separate
    design decision: two answers, one surface.

    **Not a second list.** The Library shows these as files in a tree, which
    ISS-0125 keeps deliberately; here they are the project's own answer, with
    their freshness. One item, two addresses, on the boundary FEAT-0087 records
    — and ISS-0068 forbids two lists of the same OBLIGATION, which the Library
    tree is not.

    Every entry renders, present or not. A manifest of eight that showed six
    would be answering "which of these exist" with silence, and a missing
    ARCHITECTURE is the most interesting row in the set.
    """
    from . import standing

    try:
        # One walk, shared with the registry (TASK-0416). This function used to
        # resolve paths and pick routes itself while `obligations` counted
        # findings separately; they agreed by coincidence until they did not.
        #
        # `standing.entries` resolves and describes — including the `~root/`
        # route for the members that live beside the docs tree rather than
        # inside it (LLM_BRIEF, SECURITY), which `/docs/<rel>` cannot address
        # and where every one of those rows was a dead click (ISS-0037).
        entries = standing.entries(index.docs_root)
    except OSError:                      # pragma: no cover — unreadable tree
        return []
    if not entries:
        return []

    # Which entries are OWED, and under what verb, is the registry's judgment
    # and is asked of it rather than re-derived here — the marking on this
    # group and the count on the badge are now the same answer.
    owed_by_id = {
        str(row["id"]): row
        for row in _obligations.note_less_rows(index).get(
            _obligations.STANDING_OBLIGATION.view, [])
        if row.get("type") == _obligations.STANDING_OBLIGATION_KIND
    }

    items: list[dict[str, Any]] = []
    owed = 0
    for entry in entries:
        item: dict[str, Any] = {
            "id": entry.name,
            "title": entry.question,
            "status": _STANDING_STATUS.get(entry.kind, "") if entry.kind else "active",
            "url": entry.url,
            "subtitle": entry.detail,
            "type": "reference",
        }
        owed_row = owed_by_id.get(entry.name)
        if owed_row is not None:
            item["owed"] = True
            item["owed_verb"] = owed_row["verb"]
            owed += 1
        items.append(item)

    group: dict[str, Any] = {
        "key": "standing",
        "label": "What this project is",
        "url": None,
        "status": None,
        "item_layout": "stacked",
        "items": items,
    }
    if owed:
        group["needs_human"] = True
    return [group]


def _standing_rel_paths(docs_root: Path) -> frozenset[str]:
    """Rel paths of every document the standing manifest claims (ISS-0146).

    Read from the same resolution the standing group renders, so a manifest
    entry cannot be claimed by one group and missed by the other.
    """
    from . import standing

    try:
        resolutions = standing.resolve(docs_root)
    except OSError:  # pragma: no cover — unreadable tree, as the sibling has
        return frozenset()
    out: set[str] = set()
    for res in resolutions:
        for path in res.paths:
            try:
                try:
                    out.add(path.relative_to(docs_root).as_posix())
                except ValueError:
                    # A repo-root member: it has no docs-relative path, and the
                    # Reference group it would collide with only ever lists
                    # documents inside `docs/`.
                    continue
            except ValueError:
                continue
    return frozenset(out)


#: Views whose navigator already leads with what they owe, under a name that
#: says more than "needs you" — `Needs triage` and `Needs a run`. Adding the
#: shared group there would duplicate in the one place it buys nothing, which
#: ADR-0025 permits and does not require.
#: Views that gather what they owe into their own groups, so prepending a
#: `Needs you` list would put one item on screen twice.
#:
#: **`publication` is NOT one of them**, and briefly was. Reading Edwin's
#: *"why in the needs you section"* as an objection to the group was wrong —
#: he was asking why the CONTROLS were there, and then said plainly: *"I don't
#: mind the needs you section, it makes sense to have all the publication
#: completion tasks to be in the needs you section instead of below."*
#:
#: Which is ADR-0025 exactly. Its shortcut rule is *"a shortcut list, not a
#: second home — the rows also stay in their structural place, marked"*, and
#: publication's rungs are a **ladder**: a record of how far work has
#: travelled, not a gathering of obligations. The ladder is the structural
#: place; `Needs you` is the shortcut. Removing it made the reader hunt the
#: ladder for the two rows that could be acted on.
_VIEWS_THAT_ALREADY_GATHER: frozenset[str] = frozenset(
    {"issues", "tests", "publication"},
)


def _needs_you_group(index: Index, view: str) -> list[dict[str, Any]]:
    """The leading `Needs you` group for a view (FEAT-0094 / TASK-0393).

    **A shortcut list, not a second home** (ADR-0025). The rows also stay in
    their structural place, marked, because a requirement that vanished from
    under its feature *because* it needs approving would make the tree wrong at
    the moment the reader most needs it right — they are about to approve it
    and cannot see what it belongs to.

    From `obligations.owed_items`, which is the walk behind the badge and the
    landing page, so the three surfaces cannot disagree. Absent at zero: a
    permanent `Needs you · 0` is the shape a reader learns to stop seeing.
    """
    if view in _VIEWS_THAT_ALREADY_GATHER:
        return []
    # Every owed row, note-backed or not, from one walk (TASK-0416). This used
    # to fetch note-backed rows here and scrape the note-less ones out of the
    # standing group — a second source that drifted, and Intent's group came
    # out 3 against a badge of 5. `owed_items` now carries both.
    rows = _obligations.owed_items(index).get(view, [])
    if not rows:
        return []
    items: list[dict[str, Any]] = []
    for row in rows:
        items.append({
            "id": row["id"],
            "title": row["title"],
            # A note-less subject carries its own route: a standing document
            # may live beside the docs tree rather than inside it, and
            # composing `/docs/<rel>` for it produced a dead click.
            "url": row.get("url") or f"/docs/{row['rel']}",
            "status": row["status"],
            "type": row["type"],
            # The registry's verb, never the surface's (TASK-0357's rule).
            "owed": True,
            "owed_verb": row["verb"],
            # …and, where the registry can name one, the route that verb
            # performs. Absent for the kinds whose verb is discharged
            # elsewhere (Approve, Triage, Push) — a row with no action simply
            # opens its subject, which is what every row did before.
            **({"action": row["action"]} if row.get("action") else {}),
        })
    return [{
        "key": "needs-you",
        "label": "Needs you",
        "url": None,
        "status": None,
        "item_layout": "stacked",
        "needs_human": True,
        "items": items,
    }]


def suppressed_group(index: Index, view: str) -> list[dict[str, Any]]:
    """What the in-flight rule quieted, as one collapsed group (TASK-0425).

    **Not owed, and not gone.** [[ADR-0028]] stops an obligation asking while
    its subject rests; this is where the reader sees that it decided, and
    disagrees in one click. Derived silence that cannot be opened is Edwin's
    original complaint — *"the items which need my attention are still a little
    bit invisible"* — with the sign reversed, and this project has been bitten
    by the neighbouring failure twice: a count that never clears is a count a
    reader learns to stop seeing.

    **Phase is the label, never the rule.** The grouping reads the subject's
    phase because *"21 · PHASE-999 Future"* is the sentence that explains the
    quiet; the rule itself reads the subject's status, because a phase's status
    is authored independently of its children's and three of the twelve repos
    have no phase notes at all.

    Absent at zero, like every other group here.
    """
    rows = _obligations.suppressed_items(index).get(view, [])
    if not rows:
        return []
    phases: list[str] = []
    for row in rows:
        for phase in row.get("phases") or []:
            if phase not in phases:
                phases.append(phase)
    detail = ", ".join(sorted(phases)) if phases else "no phase"
    return [{
        "key": "suppressed",
        "label": f"Quiet · {len(rows)} · {detail}",
        "url": None,
        "status": None,
        "item_layout": "stacked",
        # Explicitly NOT `needs_human`: this group is the opposite claim, and
        # marking it would put the number back on the surface it was taken off.
        "suppressed": True,
        "reason": "no feature in flight",
        "items": [
            {
                "id": row["id"],
                "title": row["title"],
                "url": row.get("url") or f"/docs/{row['rel']}",
                "status": row["status"],
                "type": row["type"],
                # The subject and ITS status — the reason, on the row, so the
                # group explains rather than merely counting.
                "subtitle": " · ".join(
                    f"{s['id']} {s['status']}" for s in row.get("subjects") or []
                ) or "names no subject",
                "owed_verb": row["verb"],
            }
            for row in rows
        ],
    }]


def _design_groups(index: Index, platform: str | None) -> list[dict[str, Any]]:
    """Nav groups for the design mode (TASK-0224).

    The design *system* is separated from proposals because they behave
    differently: a project has one system that never leaves, and many
    proposals that arrive, get decided and go quiet. Listing them together
    would bury the standing reference among transient ones.
    """
    # ISS-0089: one list. The `role: system` split put a single note in a
    # section of its own and scattered three designs across two headings,
    # for a frontmatter field the reader never asked about. The live and
    # completed split the navigator already applies is the one that
    # matters here, and a design system note is simply a design that is
    # `implemented`.
    designs = [
        {**_rare_item(index, r), **_owed_flag(r, index), "url": f"~design/{r.note_id}"}
        for r in sorted(index.notes_by_type("design"),
                        key=lambda r: (r.note_id or "", r.rel_path))
        if _platform_match(r, platform)
    ]
    out: list[dict[str, Any]] = []
    #: Computed once, outside the loop: `acceptance.load` walks the suite.
    _surface_counts = surface_coverage(index)
    out.extend(_standing_group(index))
    if designs:
        out.append({"key": "designs", "label": "Designs", "url": None,
                    "status": None, "item_layout": "stacked", "items": designs})

    # The view widens into the project's constraints (TASK-0374 / FEAT-0087).
    #
    # The line: **project-level constraints here; feature-level specifications
    # stay with their feature.** An ADR, a risk or the glossary bounds the whole
    # project. A *requirement* bounds one feature, is already nested under it,
    # and "what must this feature do" belongs beside the feature — so the 32
    # requirements deliberately do not move.
    #
    # `risk` is here by Edwin's decision (2026-08-10, ISS-0128): a risk is a
    # standing constraint on the project rather than a problem you have. It
    # leaves the Issues navigator in the same change — one type, one owning
    # view, or the badge counts it twice or neither.
    # Every file the standing manifest already claims, by REL PATH (ISS-0146).
    # All eight appeared twice on this view — once from the manifest and once
    # in `Reference` — because the two name them differently: the manifest
    # synthesises an id from the document's role (`ARCHITECTURE`, `README`,
    # `STYLEGUIDE`) while the note carries its own (`ARCH`, `DOCS-README`,
    # `STYLE`). **A duplicate that renames itself is invisible to a check that
    # compares names**, which is why ISS-0068's guard saw nothing for a
    # fortnight. The path is the identity that cannot be forged.
    claimed = _standing_rel_paths(index.docs_root)
    for key, label, types in (
        ("decisions", "Decisions", ("adr", "decision")),
        ("risks", "Risks", ("risk",)),
        # ISS-0142: releases were the one note type no nav mode carried, so
        # `REL-0001` into a bar reading "Search files, IDs, or commands…"
        # returned **No matches** while every other id answered. They were
        # reachable — the overview's record column links them — but not
        # findable, and FEAT-0072 added them four days after the comment
        # below was written about exactly this class of gap.
        #
        # A group here rather than a third special-case fetch beside the two
        # in `buildQuickCorpus`: the quick corpus is built *from* nav modes,
        # so one entry in this loop makes releases navigable and findable at
        # once, and inherits the template, standing-manifest and platform
        # filters the patches each have to restate. Releases sit on `intent`
        # because they are few, permanent and project-level — the same reason
        # decisions and risks are here.
        #: **Surfaces sit here** ([[TASK-0516]]). Edwin: *"where should they be
        #: visible, probably in the design?"* -- and the answer holds for the
        #: reason this whole group exists: the design view carries what BOUNDS
        #: the project, and a surface is a place the product has, permanent and
        #: project-level, exactly like a decision or a risk.
        #:
        #: A group in this loop rather than a fetch of its own also makes them
        #: **findable**: the quick corpus is built from nav modes, so one entry
        #: here answers the palette and the navigator at once -- which is the
        #: gap [[TASK-0514]] recorded in `KNOWN_ABSENT` and this closes.
        ("surfaces", "Surfaces", ("surface",)),
        ("releases", "Releases", ("release",)),
        ("workflows", "Workflows", ("workflow",)),
        ("reference", "Reference", ("reference", "architecture", "glossary")),
    ):
        records = [
            r for ty in types for r in index.notes_by_type(ty)
            if _platform_match(r, platform)
            and not r.rel_path.startswith("__templates__/")
            and r.rel_path not in claimed
            # Container-directory signposts are not constraints. ISS-0125
            # measured `reference` doing three unrelated jobs — five project
            # singletons, nine `docs/*/README.md` directory markers, four
            # templates. Only the first belongs here; the signposts keep their
            # home in the Library's docs tree, so nothing is orphaned.
            and not (Path(r.rel_path).name == "README.md"
                     and Path(r.rel_path).parent != Path("."))
        ]
        if not records:
            continue
        records.sort(key=lambda r: (r.note_id or "\uffff", r.rel_path))
        #: **A surface carrying zero checks is visible ON THE HEAD**
        #: ([[TASK-0516]]). Edwin: *"a surface with no coverage is the row this
        #: whole type exists to make possible."*
        #:
        #: On the head rather than on the row, and the first attempt is why: it
        #: went into `subtitle`, which `buildNavRow` documents as **deliberately
        #: not rendered** -- [[ISS-0225]]'s defect exactly, sent and never
        #: drawn, reintroduced inside the phase that removed it. The other drawn
        #: candidate was `progress`, and it is worse: it paints a COMPLETION
        #: bar, and an uncovered surface has no unfinished work, it has no work.
        #: The head already carries counts on this pane ([[ISS-0241]]), it is
        #: drawn, and it needs no renderer change.
        head = label
        if key == "surfaces":
            bare = sum(1 for r in records
                       if _surface_counts.get(r.note_id or "", 0) == 0)
            if bare:
                head = f"{label} · {bare} with no checks"
        out.append({
            "key": key,
            "label": head,
            "url": None,
            "status": None,
            "item_layout": "stacked",
            # TASK-0375: an owed row says so, from the registry. A `proposed`
            # ADR and a `proposed` design are this view's obligations, and the
            # mark and the badge counting it are the same predicate — read,
            # never re-derived, so the two cannot disagree on one screen.
            "items": [
                {**_rare_item(index, r), **_owed_flag(r, index)}
                for r in _open_first(records)
            ],
        })
    return out


def nav_payload(
    index: Index,
    mode: str | None = None,
    platform: str | None = None,
    pinned: list[str] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Left-pane payload for the requested mode.

    Falls back to :data:`DEFAULT_MODE` (``"features"``) if ``mode`` is
    missing or unknown. When ``platform`` is set (and not ``"all"``),
    items are filtered to those matching :func:`_platform_match`. The
    ``available_platforms`` field surfaces the distinct non-empty
    platform values present in the corpus so the JS client can decide
    whether to show the picker at all.
    """
    m = (mode or DEFAULT_MODE).lower()
    m = MODE_ALIASES.get(m, m)
    if m not in NAV_MODES:
        m = DEFAULT_MODE
    plat = _normalise_platform(platform)

    # `_design_groups` keeps its name: it builds groups OF designs (plus the
    # decisions, risks and references the Intent view gathers). The VIEW was
    # renamed, not the note type (TASK-0385).
    if m == "intent":
        groups = _design_groups(index, plat)
    elif m == "features":
        groups = _features_groups(index, plat)
    elif m == "tasks":
        groups = _tasks_groups(index, plat)
    elif m == "issues":
        groups = _issues_groups(index, plat)
    elif m == "tests":
        groups = _tests_groups(index, plat)
    elif m == "publication":
        groups = _publication_groups(index, project_root)
    elif m == "active":
        groups = _active_groups(index, plat)
    elif m == "recent":
        groups = _recent_groups(index, plat)
    elif m == "library":
        groups = _library_groups(index, plat, pinned or [], project_root)
    else:  # pragma: no cover — guarded above
        groups = []

    # What needs a person goes first, in every view that does not already
    # gather it (FEAT-0094 / ADR-0025). Prepended here rather than inside each
    # builder so the four views cannot drift into four answers, which is the
    # state this replaces.
    groups = _needs_you_group(index, m) + groups
    # …and what the in-flight rule quieted, LAST (TASK-0425). Appended rather
    # than prepended: it is the one group that is explicitly not asking, and
    # putting it at the top would give the quiet the position the obligations
    # hold. `tests` builds its own — see `_tests_groups` — because that view
    # gathers instead of receiving a `Needs you`.
    if m not in _VIEWS_THAT_ALREADY_GATHER:
        groups = groups + suppressed_group(index, m)

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": m,
        "platform": plat or "all",
        "available_platforms": available_platforms(index),
        "groups": groups,
    }


def context_payload(
    index: Index,
    this: str | None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Right-pane payload for an active note.

    ``this`` may be a note ID/alias or a docs-root-relative path. Returns
    an empty payload (no ``active`` block, empty lists) when ``this`` is
    missing or unresolvable. ``platform`` filters the linked + backlinks
    sets the same way :func:`nav_payload` filters its groups.
    """
    plat = _normalise_platform(platform)

    record: NoteRecord | None = None
    if this:
        path = _resolve_this(index, this)
        if path is not None:
            record = index.get(path)

    if record is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "platform": plat or "all",
            "active": None,
            "linked": [],
            "backlinks": [],
        }

    out_paths = index.links_from(record.path)
    in_paths = index.links_to(record.path) - out_paths

    return {
        "schema_version": SCHEMA_VERSION,
        "platform": plat or "all",
        "active": {
            "id": record.note_id,
            "title": record.title,
            "url": index.url_for(record.path),
        },
        "linked": _grouped_items(index, out_paths, plat),
        "backlinks": _grouped_items(index, in_paths, plat),
    }


# ---------------------------------------------------------------------------
# Nav modes
# ---------------------------------------------------------------------------


def _features_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Mode 1: features grouped by phase, with each feature carrying its
    requirements as ``children`` (collapsed-by-default in the UI).

    Requirements that don't link to any feature via ``specifies`` /
    ``scope`` surface in a final "Unattached requirements" group so they
    don't disappear from the navigator.
    """
    features = [r for r in index.notes_by_type("feature") if _platform_match(r, platform)]
    requirements = [
        r for r in index.notes_by_type("requirement") if _platform_match(r, platform)
    ]

    reqs_by_feature: dict[str, list[NoteRecord]] = {}
    attached_req_paths: set[Path] = set()
    for req in requirements:
        feat_ids = _requirement_feature_ids(index, req)
        for fid in feat_ids:
            reqs_by_feature.setdefault(fid, []).append(req)
            attached_req_paths.add(req.path)

    # Tasks join their feature beside its requirements and plan (TASK-0366).
    # `_task_records` rather than `notes_by_type` — three tasks carry no
    # frontmatter and are reachable only by the path sweep (ISS-0067).
    tasks_by_feature: dict[str, list[NoteRecord]] = {}
    attached_task_paths: set[Path] = set()
    all_tasks = [
        r for r in _task_records(index)
        if not r.rel_path.startswith("__templates__/") and _platform_match(r, platform)
    ]
    for task in all_tasks:
        fid = _task_feature_id(index, task)
        if fid:
            tasks_by_feature.setdefault(fid, []).append(task)
            attached_task_paths.add(task.path)

    grouped: dict[str | None, list[NoteRecord]] = {}
    for record in features:
        grouped.setdefault(_phase_target(record), []).append(record)

    sortable: list[tuple[Any, str | None, list[NoteRecord]]] = []
    for target, records in grouped.items():
        if target is None:
            sortable.append((float("inf"), None, records))
            continue
        phase_record = _resolve_phase(index, target)
        order = _coerce_int(
            phase_record.frontmatter.get("order") if phase_record else None
        )
        sortable.append((order if order is not None else float("inf"), target, records))
    # Phases in flight first, then upcoming, then finished — phase order
    # preserved within each band, so the finished half still reads as a
    # chronology (TASK-0268). Measured when this was written: 1 of 18
    # groups had work in flight, and it sorted seventeenth.
    sortable.sort(
        key=lambda t: (
            _phase_group_rank(_resolve_phase(index, t[1]) if t[1] else None, t[2]),
            t[0],
            t[1] or "",
        )
    )

    out: list[dict[str, Any]] = []
    for _order, target, records in sortable:
        phase_record = _resolve_phase(index, target) if target else None
        phase_id = phase_record.note_id if phase_record else None
        phase_title = (
            phase_record.title if phase_record and phase_record.title
            else (target or "Unphased")
        )
        label = (
            f"{phase_id} · {phase_title}" if phase_id and phase_title
            else phase_id or phase_title
        )
        items: list[dict[str, Any]] = []
        # Open features first, ID order preserved beneath (TASK-0267).
        ordered = sorted(records, key=lambda x: (x.note_id or "", x.rel_path))
        for r in sorted(ordered, key=open_first_key):
            item = _feature_item(index, r)
            children: list[dict[str, Any]] = []
            child_reqs = reqs_by_feature.get(r.note_id or "", [])
            if child_reqs:
                child_reqs_sorted = sorted(
                    child_reqs, key=lambda x: (x.note_id or "", x.rel_path)
                )
                children.extend(
                    _requirement_child_item(index, c) for c in child_reqs_sorted
                )
            # The plan sorts last: requirements say what the feature must
            # do, the plan says how it gets built.
            plan = _feature_plan(index, r)
            if plan is not None:
                children.append(_plan_child_item(index, plan))
            # Tasks last: requirements say what the feature must do, the plan
            # says how it gets built, and the tasks are that plan being done.
            child_tasks = tasks_by_feature.get(r.note_id or "", [])
            if child_tasks:
                child_tasks_sorted = sorted(
                    child_tasks, key=lambda x: (x.note_id or "", x.rel_path)
                )
                children.extend(
                    _task_child_item(index, c) for c in child_tasks_sorted
                )
            if children:
                item["children"] = children
            items.append(item)
        out.append(
            {
                "key": phase_id or phase_title or "unphased",
                "label": label,
                "url": index.url_for(phase_record.path) if phase_record else None,
                "status": phase_record.status if phase_record else None,
                # The type this head NAMES (ISS-0164). The quick corpus carries
                # a navigable head as a row of its own now, and a row needs its
                # type for the verb filters — inferring one from the key's
                # shape would be a second place that decides what a `PHASE-`
                # prefix means.
                "type": (phase_record.note_type or "phase") if phase_record else None,
                "items": items,
            }
        )

    task_orphans = [r for r in all_tasks if r.path not in attached_task_paths]
    if task_orphans:
        task_orphans.sort(key=lambda x: (x.note_id or "", x.rel_path))
        out.append(
            {
                "key": "unattached-tasks",
                "label": "Unattached tasks",
                "url": None,
                "status": None,
                "items": [_task_child_item(index, r) for r in task_orphans],
            }
        )

    orphans = [r for r in requirements if r.path not in attached_req_paths]
    if orphans:
        orphans.sort(key=lambda x: (x.note_id or "", x.rel_path))
        out.append(
            {
                "key": "unattached-reqs",
                "label": "Unattached requirements",
                "url": None,
                "status": None,
                "items": [_requirement_child_item(index, r) for r in orphans],
            }
        )

    return out


def _requirement_feature_ids(
    index: Index, record: NoteRecord
) -> set[str]:
    """Resolve a requirement's parent-feature links to canonical feature
    IDs (FEAT-####). Reads ``specifies`` / ``implements`` / ``scope`` —
    the requirement template uses ``implements`` (REQ "implements" /
    is-implemented-by FEAT), older notes use ``specifies``, and ``scope``
    is a legacy single-feature pointer. Anything that doesn't resolve to
    a feature record is dropped silently and feeds the orphan-group
    fallback.
    """
    candidates: list[str] = []
    for field in ("specifies", "implements"):
        raw = record.frontmatter.get(field)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    candidates.append(_strip_wikilink(item))
        elif isinstance(raw, str):
            candidates.append(_strip_wikilink(raw))
    scope = record.frontmatter.get("scope")
    if isinstance(scope, str):
        candidates.append(_strip_wikilink(scope))

    ids: set[str] = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        path = index.by_id(candidate)
        if path is None:
            continue
        rec = index.get(path)
        if rec is not None and rec.note_type == "feature" and rec.note_id:
            ids.add(rec.note_id)
    return ids


def _task_feature_id(index: Index, record: NoteRecord) -> str | None:
    """The feature a task belongs to, or ``None`` (TASK-0366).

    **The declared edge wins**, resolved through the index the way
    :func:`_requirement_feature_ids` resolves its own. A slug-matched directory
    lookup must not masquerade as the relationship — that substitution is
    ISS-0062, and it cost 19 plans their only surface.

    **Three fields, because the fleet writes three.** ``parent`` is the task
    template's field and the only one this repo uses (379 of 384). But the
    cockpit renders twelve repos: ``your-trainer`` has 660 tasks on ``parent``
    and **387 on ``implements``**, plus 3 on ``feature``. A ``parent``-only
    resolver would orphan 387 tasks in a corpus this tool is expected to show.
    ``parent`` takes precedence where a note carries more than one.

    **Path is the fallback for a task that declares nothing**, and measurement
    is why. Of 384 task notes here: 3 carry no frontmatter at all (the ISS-0067
    population, reachable only because :func:`_task_records` sweeps the path),
    and 2 carry frontmatter without any feature field. **All five sit under a
    `features/<slug>/plan/tasks/` directory**, so their feature is unambiguous;
    resolving strictly by declaration would send 5 of 5 to an orphan group whose
    entire population had an obvious home.

    That is the rule :func:`_task_records` already states for the type — *"the
    type is the claim wherever it is written. The path is only the fallback for
    notes that make no claim"* — and the one :func:`_feature_plan` applies to
    plans. A task that declares a parent and a task that declares nothing are
    different cases, and only the second reads the filesystem.
    """
    for field in ("parent", "implements", "feature"):
        raw = record.frontmatter.get(field)
        candidates: list[str] = []
        if isinstance(raw, str):
            candidates.append(_strip_wikilink(raw))
        elif isinstance(raw, list):
            candidates.extend(
                _strip_wikilink(v) for v in raw if isinstance(v, str)
            )
        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate:
                continue
            path = index.by_id(candidate)
            rec = index.get(path) if path else None
            if rec is not None and rec.note_type == "feature" and rec.note_id:
                return rec.note_id
        if candidates:
            # The note named something that is not a feature. It made a claim
            # and the claim is wrong; do not silently re-home it by path —
            # the orphan group is where that becomes visible.
            return None

    parts = record.rel_path.split("/")
    if len(parts) >= 4 and parts[0] == "features" and parts[-2] == "tasks":
        feature_dir = Path(record.rel_path).parent.parent.parent
        for sibling in index.notes_by_type("feature"):
            if Path(sibling.rel_path).parent == feature_dir and sibling.note_id:
                return sibling.note_id
    return None


def _task_child_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    """Compact item shape for a task nested under its feature (TASK-0366).

    An untyped task still gets a row, for the reason :func:`_task_records`
    exists: three of them carry no frontmatter and would otherwise reach no
    surface at all.
    """
    return {
        "id": record.note_id or record.path.stem,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": "",
        "type": record.note_type or "task",
        **_verification_flags(record),
    }


def _requirement_child_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    """Compact item shape for requirements nested under a feature card and
    for the Unattached-requirements fallback group."""
    return {
        "id": record.note_id or record.path.stem,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": "",
        "type": record.note_type or "requirement",
        **_verification_flags(record),
        **_owed_flag(record, index),
    }


def _feature_plan(index: Index, record: NoteRecord) -> NoteRecord | None:
    """The delivery plan belonging to a feature, resolved **by path**.

    A plan lives at ``features/<slug>/plan/PLAN.md``, beside the feature
    note at ``features/<slug>/FEAT-*.md``. The relationship is already in
    the filesystem, so reading it needs no frontmatter.

    That matters more than it looks: 19 of this repo's 33 ``PLAN.md``
    files carry no frontmatter at all, so ``notes_by_type("plan")`` sees
    14 of them (ISS-0062). The other 19 were unreachable from anywhere in
    the UI — ``features`` is a DOC_TREE_EXCLUDED_ROOTS root, so they never
    joined the Docs tree either. The index does hold them (it derives a
    title from the H1); nothing rendered them.
    """
    return index.get(record.path.parent / "plan" / "PLAN.md")


def _plan_child_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    """Compact item shape for a plan nested under its feature.

    An untyped plan still gets a row — that is the whole point — so the
    status chip is omitted rather than faked when the note has none.
    """
    return {
        "id": "",
        "title": record.title or "Plan",
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": "",
        "type": "plan",
    }


def _task_records(index: Index) -> list[NoteRecord]:
    """Every task note, typed or not (ISS-0067).

    `notes_by_type("task")` reads frontmatter, and three notes under
    `features/*/plan/tasks/` have none — so they were missing from the Tasks
    mode, and `features/` is a DOC_TREE_EXCLUDED_ROOTS root, so they reached
    no surface at all. Exactly ISS-0062's mechanism, which PHASE-010 fixed for
    plans and not for tasks.

    Union rather than a path-only sweep: a task note living somewhere else is
    still a task, and the type is the claim wherever it is written. The path is
    only the fallback for notes that make no claim.
    """
    typed = list(index.notes_by_type("task"))
    seen = {r.path for r in typed}
    for record in index.iter_records():
        if record.path in seen:
            continue
        if record.note_type:
            continue                      # types itself as something else
        parts = record.rel_path.split("/")
        if len(parts) >= 4 and parts[0] == "features" and parts[-2] == "tasks":
            typed.append(record)
    return typed


# Retired from both front doors in TASK-0368 — tasks now hang under the
# feature they serve (TASK-0366), and the flat status list showed 356 rows of
# which 282 were `done`, none `doing`, with phase appearing nowhere.
#
# **Still served, deliberately.** `nav_payload(mode="tasks")` remains a working
# endpoint: FEAT-0008's API-stability commitment is the same reason `active`
# and `recent` kept theirs when TASK-0204 took their buttons. A retired button
# is a UI decision; deleting an endpoint is a contract change, and nothing here
# needs one.
def _tasks_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Mode 3: tasks grouped by status."""
    tasks = [r for r in _task_records(index) if _platform_match(r, platform)]
    grouped: dict[str, list[NoteRecord]] = {}
    for record in tasks:
        key = (record.status or "unset").lower()
        grouped.setdefault(key, []).append(record)

    ordered_keys = sorted(
        grouped,
        key=lambda s: (_TASK_STATUS_RANK.get(s, len(TASK_STATUS_ORDER)), s),
    )
    return [
        {
            "key": key,
            "label": key.replace("-", " ").title(),
            "url": None,
            "status": key if key != "unset" else None,
            "items": [
                _task_item(index, r)
                for r in sorted(
                    grouped[key], key=lambda x: (x.note_id or "", x.rel_path)
                )
            ],
        }
        for key in ordered_keys
    ]


def _settled_last(
    buckets: list[tuple[str, list[NoteRecord]]],
) -> list[tuple[str, list[NoteRecord]]]:
    """Buckets with open work first, severity order preserved beneath.

    Applied to the issue buckets and the risk buckets **separately**:
    they are two blocks on one surface by design (FEAT-0047), and
    interleaving them would make the Issues stat-tile count disagree with
    what the pane shows.

    A `medium` bucket holding the one open issue outranking an all-fixed
    `critical` bucket is the intended reading, not a regression —
    severity ranks what to do first among things there are to do, and a
    settled bucket contains none.
    """
    return sorted(buckets, key=lambda b: _group_is_settled(b[1]))


def _group_is_settled(records: list[NoteRecord]) -> int:
    """1 when every record in the group is terminal (TASK-0268).

    Sorts as a leading key, so ``settled`` groups fall below unsettled
    ones while each half keeps its natural order — severity stays
    severity. An empty group counts as settled: there is nothing in it to
    act on.
    """
    return 0 if any(open_first_key(r)[0] == 0 for r in records) else 1


def _phase_group_rank(
    phase_record: NoteRecord | None, records: list[NoteRecord]
) -> int:
    """0 in flight, 1 upcoming, 2 finished — the features navigator's
    leading sort key.

    A plain settled/unsettled split was wrong here, and the review caught
    it: ``PHASE-999 · Future / Unphased`` is the backlog pen, permanently
    ``planned`` and therefore permanently unsettled, so it would sit above
    the phase actually being worked **forever**. Worse, closing a phase
    settles it — so the phase you just finished sinks and the pen takes
    the top. The evidence written into PHASE-022's exit criteria
    ("moved from 17th to 1st") was measured mid-flight and had already
    stopped being true by close-out.

    Three bands rather than two fixes both: the pen is *upcoming*, not
    *in flight*, and it sorts between them.

    Ranks on the phase note's **authored status** where there is one —
    that is the field a person maintains and ADR-0009 makes the source of
    state. Falls back to inferring from the children only when the link
    resolves to nothing, so a corpus with no phase notes still orders.
    """
    band = statuses.band_of(phase_record.status if phase_record else None)
    if band in ("active", "blocked"):
        return 0
    # `pending` is a phase not started; `reference` is `deferred`, a phase
    # parked out of scope (STATUSES.md line 81 allows exactly `planned`,
    # `active`, `done`, `deferred`, `superseded`). Both are "not now" and
    # both rank UPCOMING.
    #
    # Round-2 review caught `deferred` falling through to the unknown-status
    # arm and ranking IN FLIGHT, where it tied with the active phase and won
    # on `order`. It is in the vocabulary; it was simply not enumerated.
    if band in ("pending", "reference"):
        return 1
    if band in ("done", "archived"):
        return 2
    if phase_record is not None:
        # The note exists but its status is outside the vocabulary — a typo,
        # or a value from a corpus that has not migrated. Rank it IN FLIGHT,
        # matching `open_first_key`: sinking it would hide the thing worth
        # noticing.
        return 0
    # No phase note at all (an unresolvable link, or a corpus that links
    # phases by title alone): fall back to what the children say.
    return 0 if _group_is_settled(records) == 0 else 2


def _open_first(records: list[NoteRecord]) -> list[NoteRecord]:
    """ID order, then open work lifted above completed (TASK-0267).

    Two passes rather than one composite key so the natural order is
    visibly the thing being preserved: a stable sort by
    :func:`open_first_key` moves terminal items to the back and touches
    nothing else.
    """
    ordered = sorted(records, key=lambda x: (x.note_id or "", x.rel_path))
    return sorted(ordered, key=open_first_key)


def _severity_buckets(records: list[NoteRecord]) -> list[tuple[str, list[NoteRecord]]]:
    """Bucket notes by their ``severity:`` field, in severity order."""
    grouped: dict[str, list[NoteRecord]] = {}
    for record in records:
        sev = str(record.frontmatter.get("severity") or "unset").lower()
        grouped.setdefault(sev, []).append(record)
    ordered_keys = sorted(
        grouped,
        key=lambda s: (_SEVERITY_RANK.get(s, len(SEVERITY_ORDER)), s),
    )
    return [(key, grouped[key]) for key in ordered_keys]


def _issues_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Mode 4: issues grouped by severity, then risks the same way.

    Risks share this surface (FEAT-0047) because "what is wrong" and
    "what could go wrong" are the same question in different tenses, read
    at the same moment, and both types already carry ``severity:`` in the
    same vocabulary. Before this they appeared only in a Library
    by-type group, and the overview's Risks stat tile navigated nowhere
    (ISS-0063).

    Risks get their **own** severity groups rather than being mixed into
    the issue buckets: mixing would make the Issues stat-tile count
    disagree with what the pane shows, and a risk is not triaged the way
    an issue is.
    """
    def _severity_cards(
        records: list[NoteRecord], prefix: str, label_for: Any, layout: str | None,
    ) -> list[dict[str, Any]]:
        """One card per (severity, completion) pair.

        Buckets used to be severity alone, so a severity holding both open
        and closed issues produced ONE card that the completed/live split
        then had to place whole — and it placed it live, hiding fifty-six
        fixed issues behind a card headed `Medium`.

        Splitting on completion first makes every bucket homogeneous, so
        the navigator's existing rule (settled groups go below the
        divider) puts each half where it belongs without knowing anything
        about severity.
        """
        cards: list[dict[str, Any]] = []
        for done in (False, True):
            half = [r for r in records if statuses.is_completed(r.status) is done]
            for key, bucket in _severity_buckets(half):
                card: dict[str, Any] = {
                    # The key carries the half, or the two cards for one
                    # severity would collide in any per-key state (the
                    # collapse memory keys off it).
                    "key": f"{prefix}{key}{':done' if done else ''}",
                    "label": label_for(key),
                    "url": None,
                    "status": None,
                    "items": [_issue_item(index, r) for r in _open_first(bucket)],
                }
                if layout:
                    card["item_layout"] = layout
                cards.append(card)
        return cards

    issues = [r for r in index.notes_by_type("issue") if _platform_match(r, platform)]

    # The triage tray, above the severities (TASK-0284). `triage` means a
    # judgment is owed, and it was the one obligation the review desk never
    # carried — measured 2026-08-10 across the fleet: 39 issues at `triage`,
    # median age 56 days, 23 of them older than 30. Severity does not order
    # them because deciding the severity is the judgment being asked for.
    #
    # Absent when empty. A permanent `Needs triage · 0` is the shape of thing
    # a reader learns to stop seeing.
    triage = [r for r in issues if (r.status or "").strip().lower() == "triage"]
    out: list[dict[str, Any]] = []
    if triage:
        out.append({
            "key": "needs-triage",
            "label": "Needs triage",
            "url": None,
            "status": None,
            "needs_human": True,
            "items": [_issue_item(index, r) for r in sorted(
                triage, key=lambda r: (_note_updated(r) or _dt.date.min),
            )],
        })

    # Severity cards get everything the tray did not. An issue in both would
    # be one item as two rows on one screen — the failure ISS-0068 names, and
    # the reason the tray is a REGROUPING rather than an addition.
    triaged_paths = {r.path for r in triage}
    out.extend(_severity_cards(
        [r for r in issues if r.path not in triaged_paths],
        "", lambda k: k.title() if k != "unset" else "Severity unset", None,
    ))

    # Risks moved to the Intent view (Edwin, 2026-08-10 — ISS-0128). FEAT-0047
    # put them here because "what is wrong" and "what could go wrong" are the
    # same question in different tenses; the decision went the other way. A
    # risk is a standing constraint on the project, and an `open` risk is not
    # an obligation — it is a hazard being carried, which may never arrive.
    #
    # One type, one owning view: leaving them in both would count them twice
    # in the badges FEAT-0089 builds, or neither.
    return out


def _test_feature_ids(index: Index, record: NoteRecord) -> list[str]:
    """The features a test verifies (TASK-0371).

    **``covers:`` is the answer** (ADR-0032) — one field, one direction, on the
    many side. It returns a **list** because a test legitimately verifies more
    than one feature: 20 of the fleet's 117 do, and this repo's TST-0011 covers
    nine.

    The legacy names (``features``/``verifies``/``validates``) and the
    subject-shaped ones (``parent``/``implements``) are still read, because this
    cockpit renders twelve repos and only this one has consolidated its fields.
    That is a **rename** transition and not a return to the bidirectional pair:
    every name here points test → subject. A subject's own ``tests:`` is not
    read, and the directory path is not read at all.
    """
    out: list[str] = []
    for field in ("covers", "features", "verifies", "validates", "parent", "implements"):
        raw = record.frontmatter.get(field)
        candidates: list[str] = []
        if isinstance(raw, str):
            candidates.append(_strip_wikilink(raw))
        elif isinstance(raw, list):
            candidates.extend(_strip_wikilink(v) for v in raw if isinstance(v, str))
        for candidate in candidates:
            path = index.by_id(candidate.strip())
            rec = index.get(path) if path else None
            if rec is not None and rec.note_type == "feature" and rec.note_id:
                if rec.note_id not in out:
                    out.append(rec.note_id)
    # **No path fallback** (ADR-0032). Where a test LIVES is a filing decision,
    # not a statement about what it verifies -- the same sentence the acceptance
    # README has always made about checks, now true of tests too. It was the
    # encoding that produced the impression a test cannot span features, and a
    # link that exists only when another is absent is a rule nobody can state.
    #
    # Measured before deleting it, fleet-wide: exactly **3** tests resolved by
    # path alone, all in this repo, and all three now carry `covers:`. The other
    # 34 under a feature directory declare their subjects.
    return out


#: One run under `## Runs`, as `_append_run_log` writes it:
#: `### 2026-08-18 — passing (by user:edwin)`.
_RUN_HEADING_RE = re.compile(
    r"^###\s+(\d{4}-\d{2}-\d{2})\s+[—-]\s+(\S+)(?:\s+\(by\s+([^)]+)\))?\s*$",
    re.MULTILINE)
#: One step result inside it: `- **pass** · Do the thing — evidence`.
_RUN_STEP_RE = re.compile(r"^-\s+\*\*([^*]+)\*\*\s+·\s+(.*)$")


def manual_test_runs(body: str) -> list[dict[str, Any]]:
    """Read `## Runs` back (ISS-0197) — the half that was never written.

    `stamp_test_run` has written a per-step result under this heading since the
    runner existed, and **nothing has ever parsed it**: `_RUNS_HEADING_RE`
    occurred only in the writer. So the results were prose, the note's own
    status was the only state a run left behind, and *"which of TST-0013's 107
    steps is currently unproven"* had no answer — a walk interrupted at step 60
    recorded sixty results and reported nothing.

    Newest first here, because every caller wants the current answer; the
    document stays newest-last, because it reads as a chronological log.

    **Parsed with the writer's own shape**, deliberately: if the two ever
    diverge this returns nothing rather than something plausible, and
    `test_the_runs_section_round_trips` fails on the same commit that breaks it.
    """
    runs: list[dict[str, Any]] = []
    matches = list(_RUN_HEADING_RE.finditer(body or ""))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        steps: list[dict[str, str]] = []
        for line in body[match.end():end].splitlines():
            step = _RUN_STEP_RE.match(line.strip())
            if not step:
                continue
            text, _, evidence = step.group(2).partition(" — ")
            steps.append({
                "result": step.group(1).strip(),
                "text": text.strip(),
                "evidence": evidence.strip(),
            })
        runs.append({
            "date": match.group(1), "outcome": match.group(2),
            "runner": (match.group(3) or "").strip(), "steps": steps,
        })
    runs.reverse()
    return runs


def manual_test_step_state(body: str) -> dict[str, Any]:
    """Which steps currently stand, and which are unproven (ISS-0197).

    The question the write-only log could not answer. A step's state is its
    result **in the most recent run that mentions it** — not in the most recent
    run, because a partial walk does not un-prove the steps it did not reach.
    """
    latest: dict[str, str] = {}
    for run in reversed(manual_test_runs(body)):          # oldest first
        for step in run["steps"]:
            if step["text"]:
                latest[step["text"]] = step["result"].lower()
    declared = [s["text"] for s in manual_test_steps(body)]
    proven = [t for t in declared if latest.get(t) in ("pass", "passing", "ok")]
    unproven = [t for t in declared if t not in proven]
    return {
        "declared": len(declared), "proven": len(proven),
        "unproven": unproven, "results": latest,
    }




def _test_as_surface(index: Index, record: NoteRecord, days: int) -> dict[str, Any]:
    """A non-acceptance manual test, shaped like a surface so it can share a
    section with the acceptance checks instead of forming a second group under
    the same name.

    A nav group picks ONE item renderer (`item_layout`), so two shapes cannot
    share one — and two groups both labelled `Feature tests` is precisely the
    "one item, two homes" defect ISS-0068 exists to prevent, wearing a
    different hat.

    The population is small and shrinking by design: 5 here, 65 fleet-wide,
    and ADR-0033's conclusion — which ADR-0034 kept while superseding it — is
    that a human-completed test IS an acceptance test. This is what the
    remainder looks like until they migrate.
    """
    row = _test_item(index, record, days)
    settled = 0 if row.get("owed") else 1
    #: **Every field the row carried survives.** The surface is the row plus a
    #: shape, not a replacement for it: `scope_tests_payload` and this view are
    #: compared field by field precisely because two payloads describing one
    #: test is how two rules survived side by side for a month, and a surface
    #: that quietly dropped `stale` would restart that.
    return {
        **row,
        "type": "surface",
        "progress": {"done": settled, "total": 1,
                     "stale": int(bool(row.get("stale"))),
                     "pct": settled * 100},
        #: **No children.** A surface standing for ONE test whose only child
        #: is that same test renders the row twice on one screen — the parent
        #: and the child carry the same id, the same title and the same url.
        #: That is ISS-0068's defect exactly, and it was caught here by the
        #: one-item-one-home guard rather than by looking at the UI.
        "items": [],
    }


def _all_refs(record: NoteRecord) -> list[str]:
    """Every id a note's `covers:` names, of any type.

    What `ids_are_unbuilt` must be given: *any* built subject makes the row
    walkable, so a filter that hides one lies to it by omission.
    """
    return [
        m.group(0)
        for ref in (record.frontmatter.get("covers") or [])
        for m in re.finditer(r"[A-Z]+-\d+", str(ref))
    ]


def _feat_refs(record: NoteRecord) -> list[str]:
    """The `FEAT-*` ids a note's `covers:` names ([[ISS-0247]]).

    Only features: the quiet group's label says *no feature in flight*, and a
    bucket that quieted an issue-covering check under it would be saying
    something untrue about a row it removed.
    """
    return [
        m.group(0)
        for ref in (record.frontmatter.get("covers") or [])
        for m in re.finditer(r"FEAT-\d+", str(ref))
    ]


def _covers_an_issue(record: NoteRecord) -> bool:
    """Does this test verify a past defect rather than current behaviour?

    **Delegates to `acceptance.section_of` rather than asking again.** It
    carried its own regex and its own reading -- `re.search` here against
    `re.match` there -- so `covers: ["[[FEAT-0001]] and ISS-0002"]` classified
    one way in the navigator and the other on the generated page, and swapping
    the two passed the entire suite. Independent review, 2026-08-20.

    [[REQ-0059]] asked for ONE predicate. Two implementations of it is the
    thing the requirement forbids, written by the same hand as the
    requirement.

    **The question is "is this in the Regression section", which is narrower
    than the summary line.** A command-bearing note covering an `ISS-*` answers
    `False` here, because `command:` wins the precedence -- and that is
    correct, not a gap: `_tests_groups` routes automated records away before
    this is ever called, so the only records reaching it are the ones for which
    section and subject coincide. Stated because three notes in this repo
    (`TST-0017`, `TST-0019`, `TST-0022`) are exactly that shape, and a future
    caller that skipped the routing would get a surprising answer.

    No `level:` is forced onto the synthetic frontmatter. An earlier version
    set it, which did nothing -- `item_from_note` never reads the field -- and
    read as though the classification depended on it.
    """
    fm = dict(record.frontmatter or {})
    fm.setdefault("id", record.note_id or "")
    fm.setdefault("title", record.title or "")
    item = _acceptance.item_from_note(fm, rel="")
    if item is None:
        return False
    return _acceptance.section_of(item) == _acceptance.SECTION_REGRESSION


def _test_item(
    index: Index, record: NoteRecord, days: int,
) -> dict[str, Any]:
    """One row in the Tests view."""
    fm = record.frontmatter
    features = _test_feature_ids(index, record)
    manual = _is_manual_test(record)
    verified = _test_last_verified(fm)
    bits = [f"{len(features)} features" if len(features) > 1 else (features[0] if features else "system-wide")]
    bits.append("manual" if manual else "automated")
    bits.append(f"verified {verified[:10]}" if verified else "never verified")
    return {
        "id": record.note_id or record.path.stem,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": " · ".join(bits),
        "type": record.note_type or "test",
        "manual": manual,
        "features": features,
        "last_verified": verified,
        "stale": _test_is_stale(fm, days),
        "steps": len(manual_test_steps(record.body)),
        # ISS-0197: how many of those steps currently stand. Before the read-back
        # this row could say a test had 107 steps and nothing about whether any
        # of them held -- so a walk abandoned at step 60 looked exactly like one
        # nobody had started. Absent when the note carries no run, because "0 of
        # 107 proven" and "never walked" are different sentences.
        **({"steps_proven": _proven["proven"]}
           if (_proven := manual_test_step_state(record.body))["results"] else {}),
        **_owed_flag(record, index),
        **_verification_flags(record),
    }


#: Statuses that mean *this test was checked and it passed*. `Verified` is
#: entered by membership here and by nothing else (REQ-0046, ISS-0212) — it
#: used to be the `else` branch, which made the group whose label asserts
#: evidence the destination for every status nobody had thought about.
_PASSING_STATUSES: frozenset[str] = frozenset({"passing", "verified", "done"})

#: Resolved, and NOT a pass. A retired test is not a passing one, and the
#: distinction is the whole of ISS-0212: `your-trainer` reported a retired
#: *run plan* as a verified test.
_RESOLVED_NOT_PASSING: frozenset[str] = frozenset(
    {"retired", "superseded", "cancelled", "canceled", "obsolete"})


def _tests_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Tests mode (TASK-0371): every ``TST-*`` in the corpus, by what it needs.

    Tests had no view. The 23 notes here were reachable through a register on
    the review desk, a per-scope verification panel, and a stat tile — three
    surfaces that each answer a *different* question ("what is waiting on me",
    "does this feature pass", "how many pass"), and none of which answers
    *what do we verify*.

    **Both storage locations, one list.** LIFECYCLE.md's hybrid rule puts
    feature-scoped tests under ``docs/features/<slug>/plan/tests/`` and
    system-wide ones under ``docs/tests/``. That split is a filing decision and
    it is not the reader's problem: every test appears here, and a row says
    which feature it verifies rather than which directory it sits in.

    **Groups name their own state**, so the order is by what is owed rather
    than by category:

    * ``Needs a run`` — the registry's obligation for this view (``test @
      ready``, manual only). ``needs_human``. Named *Needs a walk* by TASK-0495
      and returned to *Needs a run* by TASK-0521: DES-0012 D2 makes ``command:``
      the single answer to who runs a test, so one verb covers both — a runner
      runs the ones with a command, a person runs the rest.
    * ``Failing`` — the test ran and did not pass.
    * ``Stale`` — passing, but last verified longer ago than the project's
      threshold allows.
    * ``Never verified`` — no ``last_verified`` and no ``last_run``.
    * ``Verified`` — everything else. Today that is all 23.

    Every group is **absent when empty**. A permanent ``Failing · 0`` is the
    shape of thing a reader learns to stop seeing, and this pane has been
    taught that lesson twice.

    **Exactly one group per test**, asserted: a test in two would be one item
    as two rows on one screen, which is the failure ISS-0068 names.
    """
    days = _staleness_days(index.docs_root)
    # **Acceptance tests are excluded here and rendered by
    # `_acceptance_tier_groups` below** (ISS-0068: one item, one home).
    #
    # Before ADR-0031 this was free — a check was a different type and
    # `notes_by_type("test")` could not see one. The merge removed that
    # separation and the exclusion has to be written down, or every acceptance
    # test renders twice on one screen: once in a `Verified`/`Needs a run`
    # bucket and once under its tier. Caught by the guard rather than by
    # reading, which is the argument for the guard.
    tests = [
        r for r in index.notes_by_type("test")
        if _platform_match(r, platform)
        and str(r.frontmatter.get("level", "") or "").strip().lower() != "acceptance"
    ]

    def sort_key(record: NoteRecord) -> tuple[str, str]:
        # "By verification state first, then by owning feature" — the state is
        # the group, so the feature is the order inside it. A system-wide test
        # sorts last rather than first: an empty string would put the two least
        # specific rows at the top of every group.
        features = _test_feature_ids(index, record)
        return (features[0] if features else "~", str(record.note_id or ""))

    #: **Six sections, every one derived** ([[ADR-0039]]). What was here was
    #: eight groups keyed on a VERDICT STATE -- `Failing`, `Stale`, `Never
    #: verified`, `Verified`, `Resting`, and an unrecognised-status catch-all.
    #: Under [[ADR-0038]] an automated test holds no verdict and a check's
    #: verdict lives in the ledger, so those groups sorted on a field that no
    #: longer exists for most of the population: measured 2026-08-19, **37 of
    #: this repo's 38 automated tests sat in one collapsed `Verified` group**,
    #: and 89 of `your-trainer`'s 91 were scattered through the tier surfaces.
    #: There was nowhere in the navigator that showed the suite as the suite.
    buckets: dict[str, list[NoteRecord]] = {
        "needs-you": [], "feature": [], "regression": [],
        "automated": [], "broken-command": [], "retired": [],
        #: **What the in-flight rule quieted** ([[ISS-0247]]). Every other view
        #: receives this from `suppressed_group`; `nav_payload` skips `tests`
        #: because *"that view gathers instead of receiving a `Needs you`"* --
        #: and the gathering never included the quiet half, so a check whose
        #: subject does not exist yet was counted as outstanding work.
        "quiet": [],
    }
    repo_root = index.docs_root.parent
    for record in tests:
        status = (record.status or "").strip().lower()
        command = str((record.frontmatter or {}).get("command") or "").strip()
        if status in _RESOLVED_NOT_PASSING:
            # A retired test is a fact about the past, not work (ISS-0212).
            buckets["retired"].append(record)
        elif command:
            # **The one obligation an automated test can carry**: its command
            # stopped resolving, so nothing is verifying it. Empty across all
            # 139 automated notes in the fleet today, which is exactly why it
            # is proved on constructed input rather than from the corpus.
            if command_targets.is_broken(command, repo_root):
                buckets["broken-command"].append(record)
            else:
                buckets["automated"].append(record)
        elif _owed_flag(record, index).get("owed"):
            buckets["needs-you"].append(record)
        #: **`ids_are_unbuilt`, NOT `_owed_flag`'s `suppressed`** -- and the
        #: first attempt at this used the second and was reverted.
        #:
        #: `suppressed` means *not in flight*, and a **terminal** subject is
        #: not in flight either. Measured on this repo: of three rows it
        #: quieted, `TST-0024` covers `FEAT-0099` at `backlog` -- correctly
        #: quiet -- while `TST-0029` and `TST-0030` both cover `FEAT-0103`,
        #: which is **done**. Those two are SHIPPED AND UNVERIFIED, and
        #: quieting them hides exactly the population `FEATURE-UNCOVERED`
        #: ([[TASK-0523]]) exists to surface.
        #:
        #: [[ADR-0028]] decision 3 is about subjects that do not exist YET.
        #: Reusing it for subjects that are FINISHED inverts what it means, so
        #: this asks the narrower question the release gate already asks.
        #: **FEAT-shaped subjects only** (independent review, 2026-08-20).
        #: `NOT_YET_BUILT` contains `deferred`, which is a legal **issue**
        #: status -- so a regression check covering a `deferred` `ISS-*` landed
        #: here, under a label reading *"no feature in flight"*, and never
        #: reached `Regression tests`. That is the same category slip
        #: [[ISS-0247]] diagnoses at the terminal end, committed at the other.
        #:
        #: A check whose subject is an issue is a regression guard; whether
        #: that issue is deferred is [[TASK-0526]]'s question on the release
        #: gate, not this bucket's.
        #: **All refs to `ids_are_unbuilt`; only the LABEL is feature-shaped**
        #: (independent review, fourth pass — this bucket's third correction).
        #:
        #: Passing `_feat_refs` alone defeated the clause `ids_are_unbuilt`'s
        #: own docstring states: *"`any` built subject makes the row
        #: walkable."* A check covering `FEAT@backlog` **and**
        #: `REQ@implemented` was quieted, because the built requirement was
        #: invisible to a filter that only looked at features. Neighbouring
        #: cases were safe by luck — the owed branch fires first — so the leak
        #: was one shape: a **built non-feature subject paired with an unbuilt
        #: feature**.
        #:
        #: `_feat_refs` still gates entry, because the group's label says *no
        #: feature in flight* and a row with no feature at all does not belong
        #: under it; `_covers_an_issue` still excludes regression guards. What
        #: decides *unbuilt* is the whole subject list, which is the question
        #: the release gate asks.
        elif (_feat_refs(record) and not _covers_an_issue(record)
              and _obligations.ids_are_unbuilt(_all_refs(record), index)):
            buckets["quiet"].append(record)
        elif _covers_an_issue(record):
            buckets["regression"].append(record)
        else:
            buckets["feature"].append(record)

    labels = (
        # `Needs you`, not `Needs a run` -- the name every other view uses
        # (ADR-0025, `_needs_you_group`), and no verb at all. *Run* and *walk*
        # are both out of the UI (Edwin, 2026-08-19): the verbs are do,
        # execute, check and complete.
        ("needs-you", "Needs you"),
        ("feature", "Feature tests"),
        ("regression", "Regression tests"),
        # **A manifest, not a list anybody completes.** No checkbox and no
        # todo count: a tickbox beside something no person executes is what
        # put nine automated checks into `your-trainer`'s blocking 68
        # (ISS-0237).
        ("automated", "Automated tests"),
        ("broken-command", "Broken command"),
        ("retired", "Retired · no longer verified"),
        #: LAST, and explicitly not asking -- the position and the reasoning
        #: `nav_payload` uses for every other view.
        ("quiet", "Quiet · no feature in flight"),
    )
    out: list[dict[str, Any]] = []
    for key, label in labels:
        records = buckets[key]
        if not records:
            continue
        group: dict[str, Any] = {
            "key": key,
            "label": label,
            "url": None,
            "status": None,
            "items": [
                _test_item(index, r, days) for r in sorted(records, key=sort_key)
            ],
            # Kept only until the merge below consumes it; a group that reaches
            # a client still carrying this would be shipping note objects.
            "_records": sorted(records, key=sort_key),
        }
        if key in ("needs-you", "broken-command"):
            # `Broken command` is an obligation too, and the only one an
            # automated test can carry: nothing is verifying it.
            group["needs_human"] = True
        if key == "quiet":
            group["suppressed"] = True
            group["reason"] = "no feature in flight"
        if key in ("automated", "retired", "quiet"):
            # **Collapsed, not deleted** (TASK-0508, and REQ-0047 criterion 1:
            # the landing state is not a list of every test). Neither section
            # is asking for anything — CI executes one and the other is a fact
            # about the past — so both survive being one line, and 40 rows
            # here is the same wall as 579.
            group["default_open"] = False
        out.append(group)

    # **Feature tests first** (TASK-0510). Edwin: *"the feature tests are shown
    # below those sections, even though I think these sections should be
    # clearly at the forefront."* They are the substance of the view and sat
    # under three flat state groups. Ordering only — no group gains or loses a
    # member, which is what `test_every_test_appears_in_exactly_one_group` keeps
    # true. (The name `test_exactly_one_group_per_test` was cited here and in
    # FEAT-0128 for months and has never existed.)
    #
    # `Needs a run` stays above them: it is the one group that is asking, and
    # a view that opens on work owed is the whole of REQ-0047.
    #: **One section per name** ([[ADR-0039]]). The acceptance checks arrive
    #: as area surfaces and the non-acceptance tests as rows, and both derive
    #: to the same three sections -- so they are MERGED rather than emitted as
    #: two groups sharing a label. Two groups called `Feature tests` is
    #: [[ISS-0068]]'s one-item-two-homes defect wearing a different hat.
    #:
    #: The acceptance surfaces come first inside a section: they are the bulk
    #: of it (34 of 39 here, 581 of 586 in `your-trainer`) and they carry the
    #: area structure the reader navigates by.
    tiers = _acceptance_tier_groups(index)
    by_key = {g.get("key"): g for g in tiers}
    merged: list[dict[str, Any]] = []
    for group in out:
        key = group.get("key")
        host = by_key.pop(_SECTION_TO_TIER_KEY.get(key, ""), None)
        if host is None:
            #: **A section with no acceptance checks still gets a section head**
            #: ([[ISS-0242]]). Edwin: *"Why does automated tests look different
            #: in this project then on the your-trainer project?"*
            #:
            #: Because this repo's suite holds **no automated acceptance checks
            #: at all** (`feature: 27, regression: 7`), so `_acceptance_tier_
            #: groups` emitted no host for it and the group fell through with a
            #: bare label -- its count relegated to the trailing summary while
            #: every sibling carried one inline. Same section, same name, a
            #: different head, decided by whether the repo happens to hold a
            #: check of that kind.
            #:
            #: The three DERIVED sections share one head format. `Needs you`,
            #: `Broken command` and `Retired` keep their trailing summary
            #: deliberately: they are cross-cutting state groups, not sections
            #: of the suite, and [[ISS-0241]] left that alone on purpose.
            records = group.pop("_records", [])
            if key in _SECTION_TO_TIER_KEY and records:
                group["_head"] = {
                    "heading": str(group.get("label") or ""),
                    "manual": key != "automated",
                    "total": 0, "unchecked": 0,
                    "rerun": 0, "stale": 0, "reconciled": 0,
                    "extra_total": len(records),
                    "extra_outstanding": sum(
                        1 for r in records
                        if not statuses.is_completed(r.status or "")),
                }
                group["label"] = _section_head_label(group["_head"])
                group["head_counts"] = True
            merged.append(group)
            continue
        extras = [_test_as_surface(index, r, days)
                  for r in group.pop("_records", [])]
        host["items"] = list(host["items"]) + extras
        #: **The head counts what the section HOLDS** ([[ISS-0242]]). It was
        #: built before this merge, so every row appended here was invisible to
        #: it -- and in this repo that made `Feature tests · all 27 done` a
        #: claim over a group holding three `ready` tests.
        #:
        #: **`statuses.is_completed`, not the row's `owed` flag.** Both were
        #: tried. `owed` asks *does this need a person right now* -- the
        #: obligations registry's question ([[ADR-0027]]) -- and it answers
        #: `False` for a test sitting at `ready`, which is how the first cut of
        #: this fix still printed `all 32 done` over three tests nobody has
        #: got passing. The head's question is the narrower one the whole view
        #: is about: **is this finished**. `passing` and `retired` are; `ready`,
        #: `active` and `failing` are not.
        #:
        #: One predicate, from `statuses`, which is where the bands are already
        #: canonical for six surfaces -- not a second reading invented here
        #: ([[REQ-0059]], and `_covers_an_issue` was caught doing exactly that).
        head = host.get("_head")
        if head is not None:
            head["extra_total"] = len(extras)
            head["extra_outstanding"] = sum(
                1 for e in extras if not statuses.is_completed(str(e.get("status") or "")))
            host["label"] = _section_head_label(head)
        merged.append(host)
    # A section with acceptance checks and no non-acceptance tests still exists.
    for key in ("tier1", "tier2", "tier3"):
        leftover = by_key.pop(key, None)
        if leftover is not None:
            merged.append(leftover)
    ordered = sorted(
        merged, key=lambda g: _SECTION_ORDER_INDEX.get(str(g.get("key")), 99))
    #: `_head` is scaffolding for the rebuild above and must not reach a
    #: client -- a key the server sends and no renderer reads is [[ISS-0225]].
    for g in ordered:
        g.pop("_head", None)
    owed = [g for g in ordered if g.get("needs_human")]
    rest = [g for g in ordered if not g.get("needs_human")]
    return owed + rest


#: A derived section's own key, and the key `_acceptance_tier_groups` emits for
#: the same section. The second is `tier1`/`tier2`/`tier3` only because the
#: front ends address a group by it; nothing reads a `tier:` from a note.
_SECTION_TO_TIER_KEY: dict[str, str] = {
    "feature": "tier1", "regression": "tier2", "automated": "tier3",
}

#: Display order. `Needs you` leads because it is the one group that is asking
#: (REQ-0047); `Broken command` sits with it because it is the same claim about
#: an automated test.
_SECTION_ORDER_INDEX: dict[str, int] = {
    "needs-you": 0, "broken-command": 1,
    "tier1": 2, "feature": 2, "tier2": 3, "regression": 3,
    "tier3": 4, "automated": 4, "retired": 5,
}


#: Which sections a checked box is "done" for. The Tests navigator folds on
#: `status`, so a checklist item borrows the status vocabulary rather than
#: inventing one — `passing` for a completed step, `ready` for one still owed,
#: `reconciled` for one settled by decision.
#:
#: That third value was first emitted from here as a bare string, which is the
#: ISS-0023 failure exactly: `groupIsSettled` ranks an unrecognised status
#: **open**, deliberately, so two fully-settled sections rendered as
#: outstanding work while their own gate read clear. Found by independent
#: review. It is now a member of `statuses.BANDS["archived"]` — terminal, and
#: terminal without the thing having been done — which is what makes every
#: surface agree at once.
#:
#: **This block used to end "`tier:` itself is untouched — it is still the
#: field, still the grouping"**, two lines above the block that says it is
#: gone. That was true when only the LABEL dropped its number (Edwin,
#: 2026-08-19: *"let's drop the Tier 1/2/3 part of it, this has no meaning"*)
#: and false from the moment ADR-0039 made the section derived. Caught by a
#: third independent review, which is where a contradiction two lines apart
#: gets found rather than by reading.
#: **Gone with `tier:`** (ADR-0039). The three names survive as the labels of
#: DERIVED sections and live in `acceptance.SECTION_LABELS`, so the navigator
#: and the generated page cannot disagree about what a section is called. The
#: third one changed meaning as well as owner: *Verification tests* was a
#: temporary tier a person moved checks into on their way to deletion, and 67
#: of `your-trainer`'s 68 arrived that way; *Automated tests* is derived from
#: `command:` and nobody files into it.


#: Where the acceptance suite is walked once it is notes. A page, not a nav
#: mode: the suite lives inside Tests, and a ninth mode would put one corpus in
#: two places — ISS-0068's defect, which this project has already paid for.
CHECKS_VIEW_ROUTE = "~checks"


def _area_slug(area: str) -> str:
    """A surface's address component.

    **Derived, and therefore fragile** — `area:` is free text, so renaming a
    surface silently breaks a bookmark to it. [[FEAT-0130]] is the fix (a
    `SUR-*` note with an id of its own); until then this is stated here rather
    than discovered by somebody whose link stopped working.
    """
    out = "".join(c.lower() if c.isalnum() else "-" for c in (area or ""))
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "unnamed"


def _is_incomplete(item: dict[str, Any]) -> bool:
    """Whether a check is still owed ([[TASK-0556]]).

    **One predicate**, shared by the percentage, the bar and every sort below.
    A second definition is how a surface's number and its position come to
    disagree about the same set.

    A stale tick counts as incomplete: it stands over evidence a change
    overtook, and folding it into done is what made `../your-trainer`'s honest
    blocking number 113 read as a reported 60.
    """
    settled = (item.get("checked") or item.get("reconciled")
               or item.get("excepted"))
    return not settled or bool(item.get("stale"))


def _surface_ref(shared: set, index: "Index | None") -> dict[str, Any]:
    """The issue a surface IS — its id **and its own title**.

    Edwin: *"for regression tests it should show `[issue-id] issue title`."*
    The `area:` string and the issue's title are different things — the first
    is free text somebody typed on a check, the second is the note's own — and
    the row was showing the first while linking the second.
    """
    ref = shared.pop()
    #: **An issue, and only an issue** ([[ISS-0235]]).
    #:
    #: This took any ref every check in the surface shared — and for Tier 1
    #: that is the `FEAT-*` they all `covers:`, so `Profile Management`
    #: rendered as *"User Management"*: the feature's title in place of the
    #: area's name.
    #:
    #: Two relations conflated. **`covers:` is what a check VERIFIES; it is
    #: not what the surface IS.** A Tier 2 surface *is* an issue — TESTING.md:
    #: each Tier 2 test references the `ISS-*` that created it — while a Tier 1
    #: surface is a place in the application that happens to verify a feature.
    #: Substituting one title for the other is the same category error as
    #: giving a surface a runner's status ([[ISS-0226]]).
    if not ref.startswith("ISS-"):
        return {}
    out: dict[str, Any] = {"ref": ref}
    if index is not None:
        found = index.by_id(ref)
        record = index.get(found) if found else None
        if record is not None and record.title:
            out["ref_title"] = record.title
    return out


def _surface_rows(items: list[dict[str, Any]], url: str, tier: int,
                  index: "Index | None" = None) -> list[dict[str, Any]]:
    """One row per surface, each **its own address with its own children**.

    Three defects fixed together, because they are one row ([[ISS-0225]],
    [[ISS-0226]], [[ISS-0227]]):

    * **Its own url.** Every row used to carry `~checks/tier/N`, so the label
      differed and the destination did not — which is [[ISS-0203]] verbatim,
      fixed for tiers one day and reintroduced for surfaces the next, in the
      function written to add them. A filter in the ADDRESS is also what lets
      back and forward move between surfaces.
    * **Its own children.** A surface expands to its checks. [[REQ-0047]]
      criterion 3 is *"every collapsed group expands to exactly the rows it
      collapsed"*, and a surface row that expanded to nothing had taken 579
      rows away rather than organising them.
    * **No test status, and progress the renderer will actually draw.** See
      `progress` below and the absence of `status`.
    """
    order: list[str] = []
    per: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        area = str(item.get("area") or "").strip() or "—"
        if area not in per:
            per[area] = []
            order.append(area)
        per[area].append(item)

    rows: list[dict[str, Any]] = []
    for area in order:
        found = per[area]
        total = len(found)
        stale = sum(1 for i in found if i.get("stale"))
        #: **Stale is not done** — excluded from the numerator rather than
        #: named beside it. Counting a tick that stands over evidence a change
        #: overtook is what made `your-trainer`'s honest blocking number 113
        #: read as a reported 60.
        settled = sum(1 for i in found
                      if (i.get("checked") or i.get("reconciled")
                          or i.get("excepted")) and not i.get("stale"))
        rows.append({
            "id": area,
            "title": area,
            #: **Drawn, not merely sent** ([[ISS-0225]]). `subtitle` is
            #: documented as never rendered — the percentage went there and
            #: was discarded, computed and serialised and dropped, while every
            #: test passed because every test read the payload. `progress` is
            #: a key `buildNavRow` draws.
            "progress": {
                "done": settled, "total": total, "stale": stale,
                "pct": round(settled * 100 / total) if total else 0,
            },
            #: **No `status`** ([[ISS-0226]]). It carried `ready`/`passing` —
            #: the runner's vocabulary, for a place in the application that is
            #: not run and cannot pass. It was also a second encoding of the
            #: bar, which is the thing this phase exists to remove.
            "url": (f"{url}/tier/{tier}/area/{_area_slug(area)}"
                    if url == CHECKS_VIEW_ROUTE else url),
            "type": "surface",
            #: **The issue a surface IS, where it is one** (Edwin, 2026-08-19:
            #: *"when the area is an issue then it should show the issue and
            #: allow the issue to be opened"*). Tier 2's areas are individual
            #: past bugs — `TESTING.md` says each Tier 2 test references the
            #: `ISS-*` that created it, and [[DES-0012]] D3 measured 46 such
            #: areas over 158 checks. So the row can carry that id and open it,
            #: the way a phase row carries `PHASE-*` and drills in.
            #:
            #: Only when the whole surface agrees: a ref shared by every check
            #: in it is the surface's own subject, and one carried by some of
            #: them is a reference from a check.
            **(_surface_ref(shared, index) if len(
                shared := set.intersection(*(set(i.get("refs") or ())
                                             for i in found)) or set()) == 1
               else {}),
            #: **Incomplete first**, then id order inside each band — so a
            #: reader who knows where a check was still finds it, and what is
            #: owed is at the top where the eye lands.
            "items": [
                {
                    "id": i.get("id") or i["number"],
                    "title": i["name"],
                    #: **The ledger mark, not a test status** ([[ISS-0232]]).
                    #: `passing` belongs to the runner; an acceptance check
                    #: rests at `active` and its outcome is an event's mark.
                    #: A check with no entry carries none — *no entry* IS the
                    #: state, and inventing a word for it is what [[ADR-0037]]
                    #: decision 5 removed.
                    "mark": i.get("mark") or "",
                    #: **Stale travels with the mark, because the sort used it
                    #: and nothing else could see it** ([[ISS-0275]]).
                    #: `_is_incomplete` counts a stale tick as owed — that is
                    #: the rule that made `your-trainer`'s honest 113 stop
                    #: reading as 60 — but the item carried only `mark`, so a
                    #: `pass` that a change had overtaken was indistinguishable
                    #: here from a `pass` that stands. Anything checking this
                    #: order had to invent a second predicate to do it, which
                    #: is exactly what `_is_incomplete`'s docstring says not to
                    #: do, and `test_the_nav_leads_with_what_is_owed` did.
                    "stale": bool(i.get("stale")),
                    "url": (f"/docs/{i['rel']}" if i.get("rel") else url),
                    "type": "test",
                }
                for i in sorted(found, key=lambda x: (
                    not _is_incomplete(x), str(x.get("id") or x["number"])))
            ],
        })
    #: **By percentage INCOMPLETE, descending** (Edwin, 2026-08-19). Ties: more
    #: open checks first, then title. Both are needed — without the first a
    #: surface with 2 of 2 open sits below one with 2 of 200, and without the
    #: second the order shifts between renders, which is a view nobody can
    #: walk.
    #:
    #: A finished surface therefore sinks to the bottom. That is what sorting
    #: by what is owed means, and it is [[REQ-0047]]'s rule — the view opens on
    #: the work.
    rows.sort(key=lambda r: (
        r["progress"]["pct"],
        -(r["progress"]["total"] - r["progress"]["done"]),
        str(r["title"]),
    ))
    return rows


def _section_head_label(head: dict[str, Any]) -> str:
    """The head of a tests-view section, built from one place.

    **Built here rather than inline so the MERGE can rebuild it** ([[ISS-0242]]).
    `_tests_groups` appends non-acceptance `TST-*` rows into these sections --
    [[ADR-0039]] requires one section per name, so they are merged rather than
    emitted as a second group under the same label -- and the head was computed
    before that happened. Measured 2026-08-20:

    | section | checks the head counted | rows merged in and NOT counted |
    |---|---|---|
    | `project-os-cockpit` Feature tests | 27 | 5 |
    | `your-trainer` Feature tests | 406 | 5 |
    | `your-trainer` Automated tests | 89 | 2 |

    **The `your-trainer` rows are its WORKING TREE on 2026-08-20, not `HEAD`.**
    At `HEAD` that repo carries zero command-bearing checks, so it has no
    automated section at all and its Feature tests total is 507. The defect is
    basis-independent -- a head built before a merge cannot see what the merge
    appends -- but the scale comes from the uncommitted migration.

    The first row is the one that shows what it costs: this repo's head read
    **`all 27 done`** while three of the five merged rows sat at `ready`. A
    head asserting that everything is finished, over a group holding three
    things that are not, is [[ISS-0241]]'s defect arriving through a second
    door -- and it is why `Automated tests` looked different between the two
    repos, which is the question that found it.

    `extra_total` and `extra_outstanding` are the merged population. They are
    zero for a section nothing merged into, which makes the merge a no-op here
    rather than a special case.
    """
    heading = str(head.get("heading") or "")
    total = int(head.get("total") or 0) + int(head.get("extra_total") or 0)
    #: **An automated section reports what it HOLDS, not what is owed**
    #: ([[ADR-0039]]). No fraction, no obligation vocabulary: nobody is
    #: progressing through a list a machine executes.
    if not head.get("manual", True):
        return f"{heading} · {total}"
    outstanding = int(head.get("unchecked") or 0) + int(head.get("extra_outstanding") or 0)
    #: **What is OUTSTANDING, once** ([[ISS-0241]], Edwin's word: not `todo`).
    #: The head carried `{checked}/{total} completed` and `{unchecked} todo`
    #: together, and the second is the first subtracted -- no input exists that
    #: makes them disagree.
    label = (f"{heading} · {outstanding} of {total} outstanding" if outstanding
             else f"{heading} · all {total} done")
    #: These three SURVIVE, because none restates the first. `re-check` is an
    #: explicit act, `stale` is a tick standing over overtaken evidence,
    #: `reconciled` is a decision the release note carries -- three different
    #: things that happened, not one thing counted three ways.
    for n, word in ((head.get("rerun"), "need re-check"),
                    (head.get("stale"), "stale"),
                    (head.get("reconciled"), "reconciled")):
        if n:
            label = f"{label} · {n} {word}"
    return label


def _acceptance_tier_groups(index: Index) -> list[dict[str, Any]]:
    """The acceptance suite's tiers, beneath the test notes (TASK-0373).

    **Two populations, deliberately kept apart.** A ``TST-*`` note is a formal
    specification — 22 of the 23 here are pytest modules CI runs on every
    commit. A suite item is a manual checkbox describing user-visible
    behaviour. TESTING.md says in as many words that the two systems coexist,
    and merging them into one list would put an automated contract test beside
    "click each stat tile" as though a person owed both.

    So they are separate groups in one view, which is what ISS-0068 permits: it
    forbids one item appearing twice, not two populations sharing a surface.

    Absent entirely when the repo has no suite — which was every repo until
    2026-08-10. A tier group reading `Tier 1 · 0` in a repo that never
    instantiated the contract would say "nothing to verify" about a project
    that has verified nothing.
    """
    data = _acceptance.payload(index.docs_root, index)
    if not data.get("exists"):
        return []
    rel = str(data.get("rel") or "")
    # `/docs/<rel>`, not `/<rel>` — the renderer's `extractRel` accepts only
    # `/docs/…` or `~…`, so the bare form was a dead click. Pre-existing and
    # invisible because an empty tier is skipped before its url is ever used;
    # TASK-0429's gate group renders at zero and exposed it.
    #
    # Once the suite is notes there is no document to open, and `/docs/` on a
    # DIRECTORY is a 404 wearing a path. The head opens the generated view
    # instead (FEAT-0114) — which is also the better destination, because that
    # is where the marks can be written.
    url = (CHECKS_VIEW_ROUTE if data.get("shape") == _acceptance.SHAPE_NOTES
           else (f"/docs/{rel}" if rel else None))

    out: list[dict[str, Any]] = []
    for tier in data.get("tiers") or []:
        items = tier.get("items") or []
        if not items:
            continue
        unchecked = sum(
            1 for i in items if not (i.get("checked") or i.get("reconciled"))
        )
        # `26/27 · 1 reconciled`, never `26/26` (ISS-0141): the denominator is
        # what the document holds, and a check settled by decision is named
        # rather than quietly removed from both halves of the fraction.
        reconciled = int(tier.get("reconciled") or 0)
        # **The re-run count** (TASK-0509). Edwin: *"it would be nice to show a
        # tracking line how many tsts have been completed and how many tests
        # will need to be rerun."* Both halves are already loaded — `rerun` is
        # a mark since ISS-0200 — so this is a tally, not new data. A check
        # needing a re-run was walked and then overtaken, which is neither
        # `checked` nor untouched, and folding it into either is what made the
        # honest blocking number on `your-trainer` 113 against a reported 60.
        #
        # **Two things mean "needs re-run" and they are counted separately.**
        # `mark: rerun` is the explicit act — somebody cleared the tick and
        # named the change. `stale` is the tick still standing over evidence
        # the record says was overtaken. Folding them loses which one a person
        # is looking at, and the second is the larger population: 53 of
        # `your-trainer`'s ticked rows are stale, which is why its honest
        # blocking number is 113 against a reported 60.
        rerun = sum(1 for i in items if (i.get("mark") or "") == "rerun")
        # From the ITEMS, not `tier["stale"]` — this payload has no such key
        # (that is `checks_view`'s), so reading it would have been a clause
        # that could never fire. Caught before it shipped by printing the
        # payload rather than trusting the field name.
        stale = sum(1 for i in items if i.get("stale"))
        #: **`completed` and `todo`**, not `walked` and `to walk` (Edwin,
        #: 2026-08-19). *Walk* survived [[DES-0012]] D5's decision to use one
        #: verb — `Run` — in the surfaces it did not name, and it is the wrong
        #: word regardless: a check with a `command:` is not walked by anybody.
        #: `completed` says what happened without claiming who did it.
        #: **An automated section reports what it holds, not what is owed**
        #: (ADR-0039). `completed`, `todo`, `re-run` and `reconciled` are all
        #: statements about a person's progress, and no person is progressing
        #: through a list CI executes. Reporting `0/67 completed` there is the
        #: same lie that put nine automated checks into `your-trainer`'s
        #: blocking 68 ([[ISS-0237]]) -- a number a reader can only act on by
        #: doing something nobody should do.
        name = tier.get("section_key") or ""
        heading = tier.get("label") or name
        if not tier.get("manual", True):
            #: **The count, and no claim about who ran it** ([[ISS-0241]]).
            #: This read `{total} executed by CI`, which the cockpit derived
            #: from `command:` being present and from nothing else -- it looks
            #: at no CI run, and no fleet workflow executes these AS CHECKS.
            #: Measured in `your-trainer`'s **working tree** on 2026-08-20 --
            #: **not at `HEAD`**, where that repo carries zero command-bearing
            #: checks and this branch never runs at all. Corrected after
            #: independent review: the basis is the phase's own recorded lesson
            #: and it was repeated here. All 89 carry `evidence: []` and an
            #: empty `verdict_date`, and 9 are `mark: todo`, so
            #: the phrase told a reader that 89 checks were in hand over a
            #: record holding no result for any of them. That is [[ISS-0237]]
            #: inverted -- it removed a false OBLIGATION, and the fix put a
            #: false ASSURANCE where the obligation had been.
            #:
            #: The section is already named `Automated tests`, so the word does
            #: not appear a second time here; a `done` pill on a card called
            #: `Done` is what [[ISS-0089]] and [[ISS-0090]] took off the group
            #: heads, and it should not return through this door.
            label = ""  # built by _section_head_label below
        else:
            #: **What is OUTSTANDING, once** ([[ISS-0241]], Edwin's word: not
            #: `todo`). This head carried `{checked}/{total} completed` and
            #: `{unchecked} todo` together, and the second is the first
            #: subtracted -- `unchecked` is `total - checked - reconciled` by
            #: construction, so no input exists that makes them disagree. A
            #: number that cannot vary against its neighbour is the neighbour,
            #: printed again.
            #:
            #: The denominator stays. `45 outstanding` on a suite of 406 and on
            #: a suite of 50 are different situations, and the head is where
            #: that is legible without opening the section.
            #:
            #: **A finished section says so rather than printing a zero.**
            #: `0 of 27 outstanding` is a sentence about absence; `all 27 done`
            #: is the fact the reader wants, and it is the one state where the
            #: total alone is the whole answer.
            label = ""  # built by _section_head_label below
        head = {
            "heading": heading, "manual": bool(tier.get("manual", True)),
            "total": int(tier["total"]), "unchecked": unchecked,
            "rerun": rerun, "stale": stale, "reconciled": reconciled,
        }
        label = _section_head_label(head)
        group: dict[str, Any] = {
            "key": f"tier{tier['tier']}",
            "label": label,
            # **Its own tier, not the whole suite** (ISS-0203). Every tier head
            # carried the identical `~checks`, so the label differed and the
            # destination did not — selecting Tier 2 rendered what Tier 1 had.
            # Swept across seven nav modes on both sidecars, these were the only
            # sibling groups in the navigator sharing a url.
            #
            # A filter in the ADDRESS rather than in a click is also what lets
            # back/forward move between tiers, and what the release page links
            # to instead of re-rendering rows.
            "url": (f"{url}/tier/{tier['tier']}"
                    if url == CHECKS_VIEW_ROUTE else url),
            "status": None,
            # **Collapsed** (TASK-0509). Edwin: *"there is no point showing all
            # the tests inside the left hand Tier x - sections."* 579 rows on
            # `your-trainer` across three tiers, under headings that already
            # carry the counts. The rows are not removed — REQ-0047 criterion 3
            # — they are one click behind a line that says how many there are.
            "default_open": False,
            # **`surface`, not `stacked`** — these rows are drawn like a phase in
            # the overview, which is the thing Edwin named. See
            # `navItemSurface`.
            "item_layout": "surface",
            # **The rows are SURFACES, not checks** ([[ISS-0222]]).
            #
            # Edwin: *"I expected the %bar and the areas/surface to group
            # things in the left hand pane."* The surfaces and the progress
            # both existed — on the generated page — because the request was
            # built where its note was rather than where its sentence pointed:
            # *"the same as we do for phases"* is a statement about this pane,
            # the only place a phase bar appears.
            #
            # It also removes a wall this list had all along. `your-trainer`
            # put **579 individual checks** in here; it now puts 77 surfaces,
            # and the checks are on the page that can actually walk them.
            # Nothing is hidden ([[REQ-0047]] criterion 3) — a surface row
            # expands to its checks one click away, and says how many.
            "items": _surface_rows(items, url, tier["tier"], index),
            # **This head already carries its counts** ([[ISS-0241]]), so the
            # front ends must not append their own trailing summary to it.
            #
            # The two numbers were counting DIFFERENT POPULATIONS: the label
            # counts CHECKS and `groupHeadSummary` counts the group's nav ROWS,
            # which here are area surfaces. `your-trainer` read
            # `Feature tests · 361/406 completed · 45 todo` with `50 · 1 done`
            # trailing it -- adjacent, both readable as "how many tests are in
            # here", eight times apart, and nothing on screen explaining which
            # was which.
            #
            # A FLAG rather than a rule the clients infer from the label: the
            # trailing count is the only count a phase, feature or task group
            # has, and dropping it there would leave a head that cannot say how
            # big it is. Only the sections built here are count-bearing, and
            # only they say so.
            "head_counts": True,
            #: **The numbers the head was built from**, so `_tests_groups` can
            #: rebuild it after merging non-acceptance tests in ([[ISS-0242]]).
            #: Popped before the payload is emitted -- a key the client never
            #: reads is the [[ISS-0225]] defect.
            "_head": head,
        }
        # Only the gating tiers ask anything of a person. Tier 3 is a
        # verification aid — TESTING.md is explicit that it does not gate.
        if tier.get("gating") and unchecked:
            group["needs_human"] = True
        out.append(group)
    return out


#: How a publication rung reads as a group heading.
_RUNG_LABELS: dict[str, str] = {
    # `Committed` with `count = state.dirty` read *"Committed · 42"* about 42
    # notes that were NOT committed — the label said the opposite of the
    # number beside it. The rung is the bottom of the ladder and what stands
    # at it is work that has not climbed yet.
    "commit": "To commit",
    "push": "To push",
    "deploy": "To deploy",
    "release": "Released",
}


def _publication_groups(
    index: Index, project_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Publication mode (FEAT-0107) — **a list of releases**, and nothing else.

    Edwin, after five rounds of something else: *"what do we need to do for a
    release, what tests need to pass, what documentation needs to be updated
    … all that should be available on the publication view and previous
    releases should be available with the functionality that was in the
    release, the tests and the documentation which was used as part of the
    publication."*

    So the navigator lists releases and each one's content nests beneath it —
    the shape `_features_groups` already uses, where a feature carries its
    requirements, plan and tasks as `children`. What each release *is* lives
    on its page (`~release/<id>`), which is where every other view in this app
    puts the acting.

    **The ladder is gone.** Commit, push and deploy are not releases; they had
    working homes on `~history` and the overview, and turning them into
    navigator groups is what made a list of releases into seven. An
    independent review counted nine concepts on this surface and could
    justify two.
    """
    from . import publication as _pub

    root = project_root or Path(str(index.docs_root)).parent
    out: list[dict[str, Any]] = []

    unshipped = unreleased_payload(index)
    live = _pub.open_releases(index)
    held = live[0] if live else None

    # ---- the next release, always first ----------------------------------
    #
    # Present even with no note behind it, which is the ordinary case: the
    # open release is derived from `unreleased_payload` and nothing is written
    # until a person declares one (FEAT-0105).
    since = unshipped.get("since") or {}
    since_id = since.get("id", "") if isinstance(since, dict) else str(since)
    label = (
        f"Preparing · {held['version']}" if held and held["preparing"]
        else f"Next release · {held['version']}" if held
        else "Next release"
    )
    if since_id:
        label = f"{label} · since {since_id}"
    #: **Through `shipping_in`, not `unreleased_payload`** ([[ISS-0261]]).
    #: This read the card's items directly, so the navigator and the release
    #: page derived the same set by two routes -- and when the page learned to
    #: scope by platform, the left pane went on listing nine iOS features under
    #: an Android release. Two implementations of one question is [[REQ-0059]]'s
    #: forbidden shape, and this is the second time it has been found in this
    #: computation.
    _next_ids = [str(row.get("id") or "")
                 for row in _pub.shipping_in(index, held["id"] if held else "")]
    _next_content = _release_content_rows(
        index, _next_ids, held, row_status="ready", shipped=False,
    )
    out.append({
        "key": "release-next",
        "label": label,
        "url": f"~release/{held['id']}" if held else "~release/next",
        "status": "draft" if held else None,
        "type": "release",
        "item_layout": "stacked",
        # **Status `ready`, never the feature's own** (ISS-0179). These rows
        # carried each feature's status, and a next release is full of `done`
        # features — so `groupIsSettled` read the whole group as finished and
        # filed it in the COMPLETED band at the bottom, while shipped
        # releases, whose rows carried no status at all, sorted to the top as
        # open work. Edwin: *"the current / next release is hidden at the end
        # below all existing releases and in the completed releases section
        # and completed releases are in the open release section at the
        # top???"*. Exactly inverted, and this is why.
        #
        # The status a row carries here is its state IN THIS RELEASE — these
        # are done-but-unshipped, so from the release's point of view they are
        # pending, not finished. The acceptance row is the one exception and
        # is not an exception to the rule, only to the value: `blocked` IS its
        # state in this release (ISS-0191).
        #
        # A repo with nothing unshipped and no release note has no subgroups
        # at all, and a group with neither items nor subgroups renders
        # NOTHING — so the whole view would be blank in a project that has
        # simply not released anything yet. It says so instead.
        #
        # **Keyed on what is unshipped, not on whether the subgroups came back
        # empty** (ISS-0191). The old condition had quietly become
        # unreachable: the acceptance row was appended unconditionally, so
        # `_next_content` was never empty and this placeholder could not
        # render in the state it exists for. It also matters for a second
        # reason — with the acceptance row now able to read `passing`, a repo
        # with nothing unshipped and a settled gate would offer the group only
        # terminal rows, and `groupIsSettled` would file `Next release` under
        # COMPLETED. That is ISS-0179 exactly, reached by a different road.
        # This row is the group's guarantee of something unfinished to say.
        "items": ([] if _next_ids else [{
            "id": "", "title": "Nothing unshipped",
            "subtitle": "no features are waiting on a release",
            "status": "", "type": "release", "url": "~release/next",
        }]),
        "subgroups": _next_content,
    })

    # ---- what has shipped, newest first ----------------------------------
    for release in _pub._releases(index):
        if release["status"] != "released":
            continue
        when = release.get("date") or ""
        label = f"{release['id']} · {release['version'] or release['title'][:30]}"
        if when:
            label = f"{label} · {when[:10]}"
        out.append({
            "key": f"release-{release['id']}",
            "label": label,
            "url": f"~release/{release['id']}",
            "status": "released",
            "type": "release",
            "item_layout": "stacked",
            "items": [],
            "subgroups": _release_content_rows(
                index, [_first_id(f) for f in release["features"]],
                release, row_status="released", shipped=True,
            ),
            "default_open": False,
        })

    for stale in _pub.stale_drafts(index):
        out.append({
            "key": f"stale-draft-{stale['id']}",
            "label": f"Draft overtaken · {stale['id']} {stale['version']}",
            "url": f"/docs/{stale['rel']}",
            "status": "draft", "type": "release", "item_layout": "stacked",
            "default_open": False,
            "items": [{
                "id": stale["id"], "title": stale["title"],
                "subtitle": "a later version has shipped — this draft is "
                            "record-keeping, and it does not gate",
                "status": "draft", "type": "release",
                "url": f"/docs/{stale['rel']}",
            }],
        })
    return out


def _release_content_rows(
    index: Index, feature_ids: list[str], release: dict[str, Any] | None,
    *, row_status: str, shipped: bool,
) -> list[dict[str, Any]]:
    """A release's own content, **grouped by what each thing is** (ISS-0180).

    Edwin: *"I would like the acceptance tests (and other documents, tests,
    issues etc …) to be accessible from the left pane. You can group the
    features and other such ticket types together?"*

    So a release's group carries subgroups — Acceptance tests, Features,
    Issues, Documents — rather than one flat list where a play-store XML sat
    between a feature and a test. The nav already renders `subgroups`; this is
    the shape `_features_groups` uses for a phase.

    **The tests come first** (ISS-0190), and the order is Edwin's argument
    rather than a preference: everything else in this group is inventory —
    what the release contains — and the suite is the only part of it that
    somebody still has to *do*.

    Everything here is in the record already and was reachable only from the
    page: `features:`, `issues:` and the `ISS-*` a release's `related:` names,
    `tests_verified:`, and the files beside the note.
    """
    from . import publication as _pub

    release_id = str((release or {}).get("id") or "") or "next"

    def row(nid: str, kind: str, subtitle: str = "") -> dict[str, Any]:
        return {
            "id": nid, "title": _title_for_id(index, nid) or nid,
            "subtitle": subtitle, "status": row_status, "type": kind,
            # **The item AS IT STANDS IN THIS RELEASE** (FEAT-0117 /
            # TASK-0472), never the bare note. Edwin: *"having features defined
            # as they are now, makes them selectable in this view but instead
            # you would like to have one view per item."* The thing selected
            # and the thing received were mismatched — a row inside a release
            # opened a note with no release context at all.
            #
            # Features and issues only. A test note or a play-store XML has no
            # per-item release answer to give, so those keep opening the file,
            # which is the honest destination for them.
            "url": (f"~release/{release_id}/{nid}"
                    if kind in ("feature", "issue") and nid
                    else _rel_for_id(index, nid)),
        }

    record = None
    if release and release.get("id"):
        path = index.by_id(str(release["id"]))
        record = index.get(path) if path is not None else None

    groups: list[dict[str, Any]] = []

    # **Acceptance tests FIRST** (ISS-0190). Edwin: *"since this needs to be
    # completed (the features/issues are things that simply ship with this
    # release)"* — which is the distinction the old order missed. A feature on
    # a release is a FACT ABOUT WHAT IS IN IT; an unchecked Tier 1 check is AN
    # ERRAND. Ordering by the record's structure put the errand third.
    tests = [
        row(_wikilink_target(str(raw)), "test", "verified")
        for raw in (release or {}).get("tests_verified") or []
    ]
    label = f"Acceptance tests · {len(tests)}"
    if not shipped:
        # **The state, read — not a literal** (ISS-0191). This row carried
        # `status: "ready"`, hard-coded, and `ready` means *a test that is
        # defined and has not been executed* (ADR-0008/ADR-0010; statuses.py
        # says so on the line that carries it). Of your-trainer's 542 checks
        # several hundred are ticked, so the row asserted something false
        # about every repo that has ever walked one — and, being a literal,
        # it would have gone on asserting it however many were marked.
        #
        # Read from `gate_payload`, which is what the release page's
        # `Release gate · N unchecked` heading counts. Two surfaces, one
        # computation, so they cannot disagree. No index and no project_root:
        # this needs the counts, not the delta, and the delta costs git.
        gate = _acceptance.gate_payload(index.docs_root, index=index)
        # A row pointing at a file that need not exist was a dead click in
        # every repo that has not instantiated the contract. The release page
        # states the absence instead — silence about a missing suite reads as
        # a clear gate, which is the one thing `acceptance.load` refuses to
        # let a surface imply.
        if gate.get("exists"):
            counts = (gate.get("counts") or {}).values()
            unchecked = sum(int(c.get("unchecked") or 0) for c in counts)
            total = sum(int(c.get("total") or 0) for c in counts)
            tests.append({
                "id": "",
                # Named for what it opens, which the migration changed under
                # it: a repo storing checks as notes has no such file, and a
                # row titled after a deleted document is a 404 wearing a
                # filename (ADR-0030).
                "title": ("Acceptance checks"
                          if gate.get("shape") == _acceptance.SHAPE_NOTES
                          else "ACCEPTANCE_TESTS.md"),
                "subtitle": (
                    f"{unchecked} of {total} Tier 1/2 checks todo — a "
                    "release is blocked while any is"
                    if unchecked else
                    f"all {total} Tier 1/2 checks settled"
                ),
                # Both are canonical values, and neither refiles the group the
                # way ISS-0179's did: `blocked` is its own band, and `passing`
                # is terminal but sits beside unshipped features that are not.
                "status": "blocked" if unchecked else "passing",
                "type": "test",
                "url": (CHECKS_VIEW_ROUTE
                        if gate.get("shape") == _acceptance.SHAPE_NOTES
                        else f"/docs/{gate['rel']}"),
            })
            # The number a person is deciding on, in the heading. `· 1` counted
            # FILES under a label that reads as a count of TESTS.
            label = (f"Acceptance tests · {unchecked} unchecked" if unchecked
                     else "Acceptance tests · all settled")
    if tests:
        groups.append({"key": "rel-tests",
                       "label": label,
                       "url": None, "status": None, "item_layout": "stacked",
                       "items": tests})

    features = [row(f, "feature") for f in feature_ids if f]
    if features:
        groups.append({"key": "rel-features", "label": f"Features · {len(features)}",
                       "url": None, "status": None, "item_layout": "stacked",
                       "items": features})

    # Issues: the `issues:` field, plus any `ISS-*` the note relates to. A
    # release note names the issues it closed and the ones it shipped around,
    # and both are the reader's question.
    seen: set[str] = set()
    issues: list[dict[str, Any]] = []
    if record is not None:
        for field in ("issues", "related"):
            for raw in record.frontmatter.get(field) or []:
                for found in re.findall(r"(ISS-\d{3,4})", str(raw)):
                    if found not in seen:
                        seen.add(found)
                        issues.append(row(found, "issue"))
    if issues:
        groups.append({"key": "rel-issues", "label": f"Issues · {len(issues)}",
                       "url": None, "status": None, "item_layout": "stacked",
                       "items": issues})

    # **No `Release note` row.** The group's own header opens the release, so
    # a row underneath was a second way to the same subject — and a
    # confusing one, because the header opens the release PAGE and the row
    # opened the raw note. Edwin: *"why to have 2 ways to get to the actual
    # release? Keep only the top one, do not have a separate link
    # underneath."*
    docs: list[dict[str, Any]] = []
    for art in _pub.artifacts_for(index.docs_root, str((release or {}).get("id") or "")):
        docs.append({
            "id": "", "title": art["name"], "subtitle": art["kind"],
            "status": row_status, "type": "change",
            "url": f"/docs/{art['rel']}",
        })
    if docs:
        groups.append({"key": "rel-docs", "label": f"Documents · {len(docs)}",
                       "url": None, "status": None, "item_layout": "stacked",
                       "items": docs})
    return groups


def _wikilink_target(raw: str) -> str:
    """`"[[X|label]]"` -> `X`. Named for what it does rather than `_first_link`,
    which already exists 1200 lines below and silently shadowed this one — the
    second name collision in this phase, after `create_release`."""
    found = re.search(r"\[\[([^\]|]+)", raw)
    return found.group(1) if found else raw.strip()


def _title_for_id(index: Index, note_id: str) -> str:
    path = index.by_id(note_id)
    record = index.get(path) if path is not None else None
    return (record.title or "") if record else ""


def _first_id(link: str) -> str:
    """`"[[FEAT-0104-Slug]]"` -> `FEAT-0104`, or the raw string."""
    found = re.search(r"([A-Z]{2,6}-\d{3,4})", str(link))
    return found.group(1) if found else str(link)


def _rel_for_id(index: Index, note_id: str) -> str | None:
    path = index.by_id(note_id)
    return f"/docs/{index.get(path).rel_path}" if path and index.get(path) else None


def _active_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Active mode (TASK-0164): in-flight items across every type,
    grouped Doing / Next / Done today, newest activity first. This is
    the honest landing view for phase-less projects."""
    today = _dt.date.today()
    doing: list[NoteRecord] = []
    nxt: list[NoteRecord] = []
    done_today: list[NoteRecord] = []
    for path in index.paths():
        record = index.get(path)
        if record is None or record.note_type is None:
            continue
        if record.rel_path.startswith("__templates__/"):
            continue
        if not _platform_match(record, platform):
            continue
        st = (record.status or "").strip().lower()
        # A note whose `active` is not about work never reaches the in-flight
        # buckets — but it is still eligible for `Done today`, where a plan
        # closing with its feature is a real event.
        if record.note_type in _ACTIVE_NON_WORK_TYPES and st not in _ACTIVE_DONE:
            continue
        if st in _ACTIVE_DOING:
            doing.append(record)
        elif st in _ACTIVE_NEXT:
            nxt.append(record)
        elif st in _ACTIVE_DONE and _note_updated(record) == today:
            done_today.append(record)
    for lst in (doing, nxt, done_today):
        lst.sort(
            key=lambda r: (_note_updated(r) or _dt.date.min),
            reverse=True,
        )
    out: list[dict[str, Any]] = []
    for key, label, records in (
        ("doing", "Doing", doing),
        ("next", "Next", nxt),
        ("done", "Done today", done_today),
    ):
        if not records:
            continue
        out.append({
            "key": key,
            "label": label,
            "url": None,
            "status": None,
            "items": [_recent_item(index, r) for r in records],
        })
    return out


def _recent_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Mode 5: recent activity, top N by ``updated`` date.

    Notes without an ``updated`` field fall back to ``created``; notes with
    neither sort to the bottom and land in the "Earlier" bucket.
    """
    today = _dt.date.today()

    candidates: list[tuple[_dt.date | None, NoteRecord]] = []
    for path in index.paths():
        record = index.get(path)
        if record is None:
            continue
        if record.rel_path.startswith("__templates__/"):
            continue
        if record.note_type is None:
            continue
        if not _platform_match(record, platform):
            continue
        candidates.append((_note_updated(record), record))

    # Sort by date desc; None last.
    candidates.sort(key=lambda t: (t[0] is None, -(t[0].toordinal() if t[0] else 0)))
    candidates = candidates[:_RECENT_LIMIT]

    buckets: dict[str, list[NoteRecord]] = {k: [] for k, _ in _RECENT_BUCKETS}
    for date, record in candidates:
        bucket = _bucket_for_date(date, today)
        buckets[bucket].append(record)

    out: list[dict[str, Any]] = []
    for key, label in _RECENT_BUCKETS:
        records = buckets[key]
        if not records:
            continue
        out.append(
            {
                "key": key,
                "label": label,
                "url": None,
                "status": None,
                "items": [_recent_item(index, r) for r in records],
            }
        )
    return out


def _library_groups(
    index: Index,
    platform: str | None,
    pinned: list[str],
    project_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Mode 5: Library — pinned + directory trees + by-type-rare."""
    out: list[dict[str, Any]] = []

    # ----- Pinned section (status+id+title, "stacked" layout) -----
    pinned_records: list[NoteRecord] = []
    seen: set[str] = set()
    for raw in pinned:
        path = _resolve_this(index, raw)
        if path is None:
            continue
        record = index.get(path)
        if record is None or not _platform_match(record, platform):
            continue
        if record.rel_path in seen:
            continue
        seen.add(record.rel_path)
        pinned_records.append(record)
    if pinned_records:
        out.append(
            {
                "key": "pinned",
                "label": "Pinned",
                "url": None,
                "status": None,
                "item_layout": "stacked",
                "items": [_rare_item(index, r) for r in pinned_records],
            }
        )

    # The Design group lived here from TASK-0212 until PHASE-010
    # (TASK-0243). It predated the Design mode: FEAT-0043 made design a
    # top-level surface with its own system/proposals split, at which
    # point this group was pointing at the same `~design/<id>` URLs that
    # mode already owns. Removed as a duplicate, not as a demotion.

    docs_tree = _markdown_tree_group(
        index,
        platform,
        key="docs-tree",
        label="Docs tree",
        excluded_roots=DOC_TREE_EXCLUDED_ROOTS,
        untyped_only=True,
        extra_types=DOC_TREE_INLINE_TYPES,
        extra_root_items=_project_root_tree_items(project_root),
    )
    if docs_tree is not None:
        out.append(docs_tree)

    # The by-type groups (Changes, Decisions, Plans, Risks, Tests,
    # Workflows) lived here until PHASE-010 removed them; LIBRARY_RARE_TYPES
    # is now empty and documents why. `_changes_subgroups` survives — it
    # moved to `changes_payload` (TASK-0239), because CHG is the one type
    # whose archive genuinely needs that bucketing.

    # ----- By type — auto-discovered (personal-vault types like Panel,
    #       Character, Daily, etc.). Each group nests items under their
    #       parent note via an auto-detected frontmatter field.
    out.extend(_library_by_type_groups(index, platform))

    return out


def decisions_payload(
    index: Index, platform: str | None = None
) -> dict[str, Any]:
    """Every ADR in the corpus, for the overview's record column (ISS-0065).

    A purpose payload rather than a nav-mode harvest, which is the whole
    lesson of that issue. The record column used to build itself from
    ``GET /api/cockpit/nav?mode=library`` — so when PHASE-010 reduced
    Library to the Docs tree, whose items carry no ``id``, the harvest
    went from 149 items to 0 and the Decisions and Verification cards
    silently stopped being built. Every card sits behind a
    ``length > 0`` guard, so nothing errored; the surface just emptied.

    The circularity is worth naming, because it is what made the
    reduction look safe: "the Library Decisions group duplicates the
    record column" was true only because the record column *was* that
    group, reshaped. Removing the duplicate removed the source.

    Asking the sidecar "what decisions exist" and answering it directly
    cannot fail that way.
    """
    records = [
        r for r in (*index.notes_by_type("adr"), *index.notes_by_type("decision"))
        if _platform_match(r, platform)
    ]
    records.sort(key=lambda r: (r.note_id or "", r.rel_path), reverse=True)
    return {
        "schema_version": SCHEMA_VERSION,
        "total": len(records),
        "decisions": [_slim_note(r) for r in records],
    }


def changes_payload(
    index: Index, platform: str | None = None
) -> dict[str, Any]:
    """CHG notes for the overview's history band (FEAT-0048).

    The overview's lower half already answers "what happened" —
    ``buildActivityTile`` (weekly note churn) and ``buildCommitsTile``
    (git). CHG notes are the missing middle grain: coarser than a commit,
    finer than a week's churn count, and the only one of the three that
    carries a written reason.

    The hybrid bucketing built by TASK-0039/0040/0041 is reused
    **unchanged** — CHG is the one type with a genuinely unbounded
    archive, and that structure is what makes it readable. The only thing
    added here is the split: the open-by-default bucket becomes
    ``recent`` (rendered expanded) and everything else becomes
    ``buckets`` (rendered as collapsed disclosures beneath it), so the
    archive travels with the recent items instead of being left behind on
    a surface that no longer exists.
    """
    records = [
        r for r in index.notes_by_type("change") if _platform_match(r, platform)
    ]
    subgroups = _changes_subgroups(index, records) if records else []
    recent: list[dict[str, Any]] = []
    buckets: list[dict[str, Any]] = []
    for group in subgroups:
        if group.get("default_open"):
            recent.extend(group.get("items") or [])
        else:
            buckets.append(group)
    return {
        "schema_version": SCHEMA_VERSION,
        "total": len(records),
        "recent": recent,
        "buckets": buckets,
    }


def _changes_subgroups(
    index: Index, records: list[NoteRecord]
) -> list[dict[str, Any]]:
    """Hybrid bucketing for the Changes group.

    Current month (no "May 2026" wrapper):
      • Current week                (Mon–Sun including today)
      • Last week                   — only when items exist earlier than
                                      last week in the current month
      • Earlier this month          — only when items older than current
                                      week exist in the current month;
                                      absorbs last week's items if no
                                      even-older content (so the
                                      Last-week bucket isn't redundant)

    Past months (one bucket per month, no wrapper around the current
    month's three buckets):
      • "Month Year"                — collapsed by default
        • per-week date ranges      — clipped to month boundaries,
                                      reverse-chronological

    Only the Current week bucket carries ``default_open: True``.
    """
    today = _dt.date.today()
    this_monday = today - _dt.timedelta(days=today.weekday())
    last_monday = this_monday - _dt.timedelta(days=7)
    current_month_start = today.replace(day=1)

    # Bucket records by date.
    cw_records: list[NoteRecord] = []
    lw_records: list[NoteRecord] = []
    em_records: list[NoteRecord] = []
    past_by_month: dict[tuple[int, int], list[NoteRecord]] = {}
    for record in records:
        date = _record_change_date(record)
        if date is None:
            # No usable date — drop into earlier-this-month for visibility
            # rather than orphan; rare in practice.
            em_records.append(record)
            continue
        if date >= current_month_start:
            if date >= this_monday:
                cw_records.append(record)
            elif date >= last_monday:
                lw_records.append(record)
            else:
                em_records.append(record)
        else:
            past_by_month.setdefault((date.year, date.month), []).append(record)

    subgroups: list[dict[str, Any]] = []

    def _stacked(key: str, label: str, recs: list[NoteRecord],
                 *, default_open: bool, subs: list[dict[str, Any]] | None = None
                 ) -> dict[str, Any]:
        recs_sorted = sorted(recs, key=_record_sort_key, reverse=True)
        out: dict[str, Any] = {
            "key": key,
            "label": label,
            "url": None,
            "status": None,
            "item_layout": "stacked",
            "items": [_rare_item(index, r) for r in recs_sorted],
            "default_open": default_open,
        }
        if subs is not None:
            out["items"] = []
            out["subgroups"] = subs
        return out

    if cw_records:
        subgroups.append(_stacked(
            "rare:change:current-week", "Current week",
            cw_records, default_open=True,
        ))
    # Conditional rendering of Last week vs Earlier this month — per the
    # user's rule, Last week only appears when something even older
    # exists in the current month; otherwise last-week items absorb
    # into Earlier this month.
    if lw_records and em_records:
        subgroups.append(_stacked(
            "rare:change:last-week", "Last week",
            lw_records, default_open=False,
        ))
        subgroups.append(_stacked(
            "rare:change:earlier-this-month", "Earlier this month",
            em_records, default_open=False,
        ))
    elif em_records:
        subgroups.append(_stacked(
            "rare:change:earlier-this-month", "Earlier this month",
            em_records, default_open=False,
        ))
    elif lw_records:
        subgroups.append(_stacked(
            "rare:change:earlier-this-month", "Earlier this month",
            lw_records, default_open=False,
        ))

    for (year, month) in sorted(past_by_month.keys(), reverse=True):
        month_recs = past_by_month[(year, month)]
        key = f"rare:change:{year:04d}-{month:02d}"
        label = f"{_MONTH_NAMES[month]} {year}"
        if len(month_recs) >= _CHG_PAST_MONTH_WEEK_SPLIT_MIN:
            month_start = _dt.date(year, month, 1)
            if month == 12:
                month_end = _dt.date(year + 1, 1, 1) - _dt.timedelta(days=1)
            else:
                month_end = _dt.date(year, month + 1, 1) - _dt.timedelta(days=1)
            week_subs = _past_month_week_subgroups(
                index, month_recs, month_start, month_end
            )
            subgroups.append(_stacked(
                key, label, month_recs, default_open=False, subs=week_subs,
            ))
        else:
            # Sparse month — render items directly under the month label,
            # skip the weekly sub-bucket layer.
            subgroups.append(_stacked(
                key, label, month_recs, default_open=False,
            ))

    return subgroups


def _past_month_week_subgroups(
    index: Index,
    records: list[NoteRecord],
    month_start: _dt.date,
    month_end: _dt.date,
) -> list[dict[str, Any]]:
    """Bucket past-month records by ISO week clipped to month boundaries.
    Reverse-chronological. Returns at most ~5 sub-subgroups per month."""
    by_monday: dict[_dt.date, list[NoteRecord]] = {}
    for record in records:
        date = _record_change_date(record)
        if date is None:
            # Should be rare here (caller already filtered to past months).
            continue
        monday = date - _dt.timedelta(days=date.weekday())
        by_monday.setdefault(monday, []).append(record)
    subgroups: list[dict[str, Any]] = []
    for monday in sorted(by_monday.keys(), reverse=True):
        start = max(month_start, monday)
        end = min(month_end, monday + _dt.timedelta(days=6))
        label = _format_week_range(start, end)
        recs_sorted = sorted(by_monday[monday], key=_record_sort_key, reverse=True)
        subgroups.append({
            "key": f"rare:change:{month_start.year:04d}-{month_start.month:02d}:wk-{monday.isoformat()}",
            "label": label,
            "url": None,
            "status": None,
            "item_layout": "stacked",
            "items": [_rare_item(index, r) for r in recs_sorted],
            "default_open": False,
        })
    return subgroups


def _detect_parent_field(index: Index, type_name: str) -> str | None:
    """Auto-detect which frontmatter field carries the parent-link for a
    given note type.

    Strategy (in order):

    1. **Curated names.** If any note of this type has one of
       :data:`_PARENT_FIELD_CANDIDATES` with a non-empty value, the
       first one (in curated priority) wins — even if the value
       doesn't resolve to an indexed note. This lets a
       ``project: [[Mother Interview]]`` field group the note under
       its project even when the project folder has no `.md`.

    2. **Resolved-link fallback.** Among the non-curated, non-metadata
       fields, pick the one most often containing a wikilink that
       resolves to another indexed note. Excludes
       :data:`_NON_PARENT_FIELDS` (template, modified, image, ...).

    Returns ``None`` when neither path finds a candidate — the type
    renders as a flat list under its group.
    """
    records = index.notes_by_type(type_name)
    if not records:
        return None

    # Step 1: curated names, present-in-any-note check.
    curated_present: set[str] = set()
    for record in records:
        for field_name in record.frontmatter.keys():
            if isinstance(field_name, str):
                fn = field_name.lower()
                if fn in _PARENT_FIELD_CANDIDATES:
                    raw = record.frontmatter.get(field_name)
                    if _frontmatter_has_value(raw):
                        curated_present.add(fn)
    for curated in _PARENT_FIELD_CANDIDATES:
        if curated in curated_present:
            return curated

    # Step 2: resolved-link fallback.
    counts: dict[str, int] = {}
    for record in records:
        for field_name, raw in record.frontmatter.items():
            if not isinstance(field_name, str):
                continue
            fn = field_name.lower()
            if fn in _NON_PARENT_FIELDS:
                continue
            if fn in {"type", "title", "status", "tags", "aliases", "id"}:
                continue
            candidates: list[str] = []
            if isinstance(raw, str):
                candidates.append(raw)
            elif isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str):
                        candidates.append(item)
            for candidate in candidates:
                target = _strip_wikilink(candidate).strip()
                if not target:
                    continue
                if index.by_id(target):
                    counts[fn] = counts.get(fn, 0) + 1
                    break
    if not counts:
        return None
    return max(counts.items(), key=lambda x: x[1])[0]


def _frontmatter_has_value(raw: Any) -> bool:
    """True if a frontmatter value is non-empty (string with chars, or
    a list with at least one string entry)."""
    if isinstance(raw, str):
        return bool(raw.strip())
    if isinstance(raw, list):
        return any(isinstance(x, str) and x.strip() for x in raw)
    return False


def _resolve_parent_key(
    record: NoteRecord, field_name: str, index: Index
) -> tuple[Path | None, str | None]:
    """Resolve a record's parent-link field to ``(path, label)``.

    - ``(Path, label)`` if the value resolves to an indexed note.
    - ``(None, label)`` if the value is a non-empty string but doesn't
      resolve — the cockpit groups under the raw label (e.g.,
      ``"Mother Interview"`` when no `Mother Interview.md` exists).
    - ``(None, None)`` when the field is missing or empty.

    For list fields, the first non-empty entry wins.
    """
    raw = record.frontmatter.get(field_name)
    candidates: list[str] = []
    if isinstance(raw, str):
        candidates.append(raw)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                candidates.append(item)
    for candidate in candidates:
        target = _strip_wikilink(candidate).strip()
        if not target:
            continue
        path = index.by_id(target)
        if path is not None:
            return path, None
        return None, target
    return None, None


def _library_by_type_groups(
    index: Index, platform: str | None
) -> list[dict[str, Any]]:
    """Auto-discovered Library "By type" groups.

    For each note type present in the index whose count is at least
    :data:`_BY_TYPE_MIN_COUNT` and that isn't already surfaced
    elsewhere (project-os canonical types, dedicated rare types, the
    inline-into-docs-tree types), emit a collapsible group whose
    items are nested under their auto-detected parent note.

    Groups whose parent field can't be detected render as a flat list.
    """
    counts = index.type_counts()
    out: list[dict[str, Any]] = []
    for type_name in sorted(counts.keys()):
        if counts[type_name] < _BY_TYPE_MIN_COUNT:
            continue
        if type_name in _BY_TYPE_SKIP_IN_LIBRARY:
            continue
        records = [
            r for r in index.notes_by_type(type_name)
            if _platform_match(r, platform)
        ]
        if not records:
            continue
        parent_field = _detect_parent_field(index, type_name)
        items_sorted = sorted(records, key=lambda r: (r.title or "", r.rel_path))
        if parent_field is None:
            # No parent — flat list.
            out.append({
                "key": f"by-type:{type_name}",
                "label": _by_type_label(type_name),
                "url": None,
                "status": None,
                "item_layout": "stacked",
                "items": [_rare_item(index, r) for r in items_sorted],
            })
            continue
        # Bucket by parent. Resolved-note parents key by Path; unresolved
        # string targets (a folder name or stub mention) key by the raw
        # label string so notes pointing at the same dangling target
        # still group together.
        resolved_by_parent: dict[Path, list[NoteRecord]] = {}
        unresolved_by_label: dict[str, list[NoteRecord]] = {}
        orphans: list[NoteRecord] = []
        for record in records:
            parent_path, parent_label = _resolve_parent_key(
                record, parent_field, index
            )
            if parent_path is not None:
                resolved_by_parent.setdefault(parent_path, []).append(record)
            elif parent_label:
                unresolved_by_label.setdefault(parent_label, []).append(record)
            else:
                orphans.append(record)
        subgroups: list[dict[str, Any]] = []
        # Resolved-note buckets — alphabetised by parent title.
        parented: list[tuple[str, Path]] = []
        for parent_path in resolved_by_parent:
            parent_rec = index.get(parent_path)
            title = (parent_rec.title if parent_rec else None) or parent_path.stem
            parented.append((title.lower(), parent_path))
        parented.sort()
        for _sort_key, parent_path in parented:
            parent_rec = index.get(parent_path)
            label = (parent_rec.title if parent_rec else None) or parent_path.stem
            url = index.url_for(parent_path) if parent_rec else None
            children = sorted(
                resolved_by_parent[parent_path],
                key=lambda r: (r.title or "", r.rel_path),
            )
            subgroups.append({
                "key": f"by-type:{type_name}:{parent_path}",
                "label": label,
                "url": url,
                "status": parent_rec.status if parent_rec else None,
                "item_layout": "stacked",
                "items": [_rare_item(index, r) for r in children],
                "default_open": False,
            })
        # Unresolved-label buckets (e.g., a project folder with no `.md`).
        # Marked with a small "·" suffix in the key for uniqueness;
        # rendered with the raw label so the user can see what target
        # the notes claim to belong to.
        for label in sorted(unresolved_by_label, key=str.lower):
            children = sorted(
                unresolved_by_label[label],
                key=lambda r: (r.title or "", r.rel_path),
            )
            subgroups.append({
                "key": f"by-type:{type_name}:unresolved:{label}",
                "label": label,
                "url": None,
                "status": None,
                "item_layout": "stacked",
                "items": [_rare_item(index, r) for r in children],
                "default_open": False,
            })
        if orphans:
            orphans_sorted = sorted(orphans, key=lambda r: (r.title or "", r.rel_path))
            subgroups.append({
                "key": f"by-type:{type_name}:orphans",
                "label": f"Without {parent_field}",
                "url": None,
                "status": None,
                "item_layout": "stacked",
                "items": [_rare_item(index, r) for r in orphans_sorted],
                "default_open": False,
            })
        out.append({
            "key": f"by-type:{type_name}",
            "label": _by_type_label(type_name),
            "url": None,
            "status": None,
            "item_layout": "stacked",
            "items": [],
            "subgroups": subgroups,
        })
    return out


def _by_type_label(type_name: str) -> str:
    """Human-readable label for an auto-discovered Library 'By type'
    group. Title-case the type verbatim — no naive ``+ "s"`` plural
    (``daily`` → ``Daily``, not ``Dailys``; ``default note`` →
    ``Default Note``, not ``Default Notes``). The (n) count rendered
    by the JS in the group header carries the cardinality."""
    return type_name.strip().title() or type_name


def _format_week_range(start: _dt.date, end: _dt.date) -> str:
    """``Apr 1``, ``Apr 6–12``, or ``Apr 27–30`` for a clipped week."""
    if start == end:
        return f"{_MONTH_ABBR[start.month]} {start.day}"
    if start.month == end.month:
        return f"{_MONTH_ABBR[start.month]} {start.day}–{end.day}"
    return (
        f"{_MONTH_ABBR[start.month]} {start.day}–"
        f"{_MONTH_ABBR[end.month]} {end.day}"
    )


def _record_change_date(record: NoteRecord) -> _dt.date | None:
    """Extract a date from a CHG record. Prefers the CHG-YYYYMMDD- id;
    falls back to frontmatter ``updated`` / ``created``."""
    match = _CHG_DATE_RE.match(record.note_id or "")
    if match:
        try:
            return _dt.date(
                int(match.group(1)), int(match.group(2)), int(match.group(3))
            )
        except ValueError:
            pass
    for key in ("updated", "created"):
        date = _coerce_date(record.frontmatter.get(key))
        if date is not None:
            return date
    return None


def _record_sort_key(record: NoteRecord) -> tuple[str, str]:
    """Sort changes by id (date-prefixed) then rel_path for stability."""
    return (record.note_id or "", record.rel_path)


def _project_root_tree_items(project_root: Path | None) -> list[dict[str, Any]]:
    """Items for top-level project files (README/ROADMAP/SECURITY).

    Rendered at the root of the Docs tree group so users see them alongside
    the rest of the file tree rather than in a separate "Top-level docs"
    section. Filename is the title; URL is ``/<filename>`` (the server
    allowlists these via :data:`PROJECT_SUPPORT_ROOT_FILES`).
    """
    if project_root is None:
        return []
    root = project_root.resolve()
    return [
        {
            "id": "",
            "title": rel,
            "status": None,
            # `~root/<file>`, not `/<file>` (ISS-0037). The old shape was
            # indistinguishable from a docs note once the leading slash was
            # stripped — which both `extractRel` and `/api/render` did — so
            # `/README.md` and `/docs/README.md` collapsed onto one fetch and
            # these rows were dead clicks from FEAT-0010 until 2026-07-30.
            # The `~` prefix routes through the same virtual-page mechanism
            # `~design` and `~review` use, and carries the disambiguator.
            "url": f"~root/{rel}",
            "subtitle": "",
            "type": "",
        }
        for rel in PROJECT_SUPPORT_ROOT_FILES
        if (root / rel).is_file()
    ]


def _markdown_tree_group(
    index: Index,
    platform: str | None,
    *,
    key: str,
    label: str,
    root_prefix: str = "",
    excluded_roots: tuple[str, ...] = (),
    untyped_only: bool = False,
    extra_types: tuple[str, ...] = (),
    extra_root_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Build a recursive directory tree for indexed Markdown notes.

    ``extra_root_items`` are merged into the root-level items list (sorted
    alongside the indexed entries by the standard tree sort). Used to
    surface project-root files (README, ROADMAP, SECURITY) inside the
    Docs tree rather than as a sibling group.

    ``extra_types`` widens the ``untyped_only`` filter so notes of these
    types are also included (used to inline reference-typed notes into
    the Docs tree — TASK-0036).
    """
    prefix = root_prefix.strip("/")
    root: dict[str, Any] = {
        "key": key,
        "label": label,
        "url": None,
        "status": None,
        "item_layout": "compact",
        "items": [],
        "subgroups": [],
    }
    nodes: dict[str, dict[str, Any]] = {"": root}
    extra_types_set = set(extra_types)

    for path in index.paths():
        record = index.get(path)
        if record is None:
            continue
        if not _platform_match(record, platform):
            continue
        is_extra_type = record.note_type in extra_types_set if extra_types_set else False
        if untyped_only and record.note_type is not None and not is_extra_type:
            continue
        # Path-based exclusions apply to every type: __templates__/ is
        # always blocked; the canonical project-os container dirs
        # (decisions/, tests/, ...) are blocked too — references inside
        # them are deliberately hidden since those dirs are owned by
        # other nav surfaces (TASK-0037).
        if _exclude_from_docs_tree(record.rel_path, excluded_roots=excluded_roots):
            continue
        if prefix:
            if record.rel_path == prefix:
                display_rel = record.path.name
            elif record.rel_path.startswith(f"{prefix}/"):
                display_rel = record.rel_path[len(prefix) + 1:]
            else:
                continue
        else:
            display_rel = record.rel_path

        parts = display_rel.split("/")
        if not parts:
            continue
        parent_key = ""
        for dir_name in parts[:-1]:
            node_key = f"{parent_key}/{dir_name}" if parent_key else dir_name
            parent = nodes[parent_key]
            node = nodes.get(node_key)
            if node is None:
                node = {
                    "key": f"{key}:{node_key}",
                    "label": f"{dir_name}/",
                    "url": None,
                    "status": None,
                    "item_layout": "compact",
                    "items": [],
                    "subgroups": [],
                }
                nodes[node_key] = node
                parent["subgroups"].append(node)
            parent_key = node_key
        nodes[parent_key]["items"].append(_tree_item(record))

    if extra_root_items:
        root["items"].extend(extra_root_items)

    _sort_tree_group(root)
    if not root["items"] and not root["subgroups"]:
        return None
    return root


def _exclude_from_docs_tree(
    rel_path: str,
    *,
    excluded_roots: tuple[str, ...] = (),
) -> bool:
    return _excluded_by_prefix(rel_path) or _excluded_by_root(rel_path, excluded_roots)


def _excluded_by_prefix(rel_path: str) -> bool:
    """Always-excluded prefixes (templates, etc.) regardless of note type."""
    return any(rel_path.startswith(prefix) for prefix in DOC_TREE_EXCLUDED_PREFIXES)


def _excluded_by_root(rel_path: str, excluded_roots: tuple[str, ...]) -> bool:
    """Type-canonical root dirs (decisions/, risks/, …) — bypassed for
    inline-type notes so a reference living inside one still surfaces."""
    root = rel_path.split("/", 1)[0]
    return root in excluded_roots


def _sort_tree_group(group: dict[str, Any]) -> None:
    group["items"].sort(
        key=lambda item: (
            0 if item["title"].lower() == "readme.md" else 1,
            item["title"].lower(),
            item["url"].lower(),
        )
    )
    group["subgroups"].sort(key=lambda subgroup: subgroup["label"].lower())
    for subgroup in group["subgroups"]:
        _sort_tree_group(subgroup)


def _pluralise_for_label(type_name: str) -> str:
    """Human-readable plural label for a type group header."""
    table = {
        "adr": "Decisions",
        "release": "Releases",
        "risk": "Risks",
        "test": "Tests",
        "workflow": "Workflows",
        "plan": "Plans",
        "reference": "References",
    }
    return table.get(type_name, type_name.title() + "s")


def surface_coverage(index: Index) -> dict[str, int]:
    """How many acceptance checks name each surface ([[TASK-0516]]).

    **A surface with no coverage is the row this whole type exists to make
    possible.** Nothing else in the record can state it: an uncovered *feature*
    is [[TASK-0523]]'s subject, but a place in the product with no checks at
    all is invisible until surfaces are notes -- there was no row for it to be
    absent from.

    **Matched on the title, because that is all there is today.** A check
    carries `area:` as a STRING; making it a `SUR-*` link is [[TASK-0515]]'s
    mapping and it has not happened. So this joins on the exact name, which is
    the string the type exists to replace -- and a surface whose title matches
    no `area:` reads as zero, which is correct rather than a gap in the join:
    at this moment it genuinely covers nothing.
    """
    from . import acceptance as _acc

    counts: dict[str, int] = {}
    areas: dict[str, int] = {}
    try:
        suite = _acc.load(index.docs_root, index=index)
    except Exception:                                 # pragma: no cover
        suite = None
    for item in (suite.items if suite is not None else []):
        key = str(item.area or "").strip().lower()
        if key:
            areas[key] = areas.get(key, 0) + 1
    for record in index.notes_by_type("surface"):
        if record.rel_path.startswith("__templates__/"):
            continue
        title = str(record.title or "").strip().lower()
        counts[record.note_id or ""] = areas.get(title, 0)
    return counts


def _rare_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    """Item shape for Pinned + typed-structured rare-type sections
    (Decisions, Releases, Risks, Tests, Workflows, Plans).

    These notes carry meaningful frontmatter ``title`` and ``id`` fields
    and live under conventional subdirs (``decisions/``, ``risks/``...),
    so the JS renders the standard ``[icon][id][title]`` stacked shape
    without any path subtitle.
    """
    return {
        "id": record.note_id or record.path.stem,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": "",
        "type": record.note_type or "",
        **_verification_flags(record),
    }


def _reference_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    """Item shape for the References group.

    References are loose docs without meaningful project-os IDs, so the
    filename takes the ``id`` slot. The title row is dropped (the filename
    is identifying enough); the relative parent directory is shown as a
    mono subtitle so the user can tell at a glance where the file lives.
    """
    if "/" in record.rel_path:
        parent_dir = record.rel_path.rsplit("/", 1)[0] + "/"
    else:
        parent_dir = ""
    return {
        "id": record.path.name,
        "title": "",
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": parent_dir,
        "type": record.note_type or "reference",
    }


def _tree_item(record: NoteRecord) -> dict[str, Any]:
    """Compact file item for recursive directory-tree navigation."""
    return {
        "id": "",
        "title": record.path.name,
        "status": None,
        "url": f"/docs/{record.rel_path}",
        "subtitle": "",
        "type": record.note_type or "",
    }


# ---------------------------------------------------------------------------
# Per-item shapes
# ---------------------------------------------------------------------------


def _has_frontmatter_value(raw: Any) -> bool:
    """Truthiness for badge-driving frontmatter — empty string / list /
    dict / None all count as "not recorded"."""
    if raw is None:
        return False
    if isinstance(raw, str):
        return bool(raw.strip())
    if isinstance(raw, (list, dict, tuple, set)):
        return bool(raw)
    return True


def _verification_flags(record: NoteRecord) -> dict[str, Any]:
    """Verification-surface badge flags for list rows (FEAT-0018 /
    TASK-0113). Additive, schema-compatible fields:

    - ``waived: true`` when ``verification_waiver`` is non-empty — a
      terminal status held under a recorded waiver must be visually
      distinct from a verified one.
    - ``review_verdict`` (lower-cased) when the independent-review
      verdict is recorded (``approved`` / ``changes-requested``).
    - ``adequacy`` (bool, ``test`` notes only): whether the note
      records adequacy evidence (``adequacy`` or ``mutation_score``)
      — unguarded "guarding" tests stand out in test views.
    """
    flags: dict[str, Any] = {}
    fm = record.frontmatter or {}
    if _has_frontmatter_value(fm.get("verification_waiver")):
        flags["waived"] = True
    verdict = fm.get("review_verdict")
    if isinstance(verdict, str) and verdict.strip():
        flags["review_verdict"] = verdict.strip().lower()
    if (record.note_type or "") == "test":
        flags["adequacy"] = (
            _has_frontmatter_value(fm.get("adequacy"))
            or _has_frontmatter_value(fm.get("mutation_score"))
        )
    return flags


def _first_body_paragraph(body: str, *, max_chars: int = 220) -> str:
    """Return the first paragraph of body text, skipping the H1 and any
    leading section headings (``## Problem``, ``## Goal``, ...).

    Used as the inline description on Tasks and Issues cards so the user
    can scan the substance of a note without opening it. Heuristic on
    purpose — we collect the first non-heading paragraph and stop at the
    next blank line or heading.
    """
    if not body:
        return ""
    para: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if para:
                break
            continue
        if _HEADING_RE.match(stripped):
            if para:
                break
            continue
        para.append(stripped)
    text = " ".join(para)
    text = _WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), text)
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _INLINE_FMT_RE.sub(r"\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def _owed_flag(
    record: NoteRecord, index: "Index | None" = None,
) -> dict[str, Any]:
    """Mark a row the registry says is owed (TASK-0376).

    Read from `obligations`, never re-derived: the verb and the states live in
    one module, and a row that decided for itself would drift from the badge
    counting it — which is the same number disagreeing with itself on one
    screen.

    **The index is what lets the in-flight rule apply** (ADR-0028). Without it
    this answers the type's declaration alone and marks rows the badge does not
    count — precisely the drift above, reintroduced by an omitted argument.
    Passing it is therefore not optional for any caller building a row a badge
    also counts; `suppressed` says which side of the rule the row fell on, so a
    surface can render the quiet rather than dropping it.
    """
    ob = _obligations.for_type(record.note_type)
    if ob is None or not _obligations._is_owed(record, ob):
        # **Both registries** (TASK-0468). A feature can be owed through a
        # note-less source — the acceptance sweep, whose subject is a note but
        # whose trigger is a MISSING field — and reading only the per-type
        # table left that row in `Needs you` while its structural copy in the
        # tree was unmarked. Two appearances, one of them unexplained, is
        # exactly what the structural-copy rule forbids.
        extra = (_obligations.note_less_row_for(index, record.note_id or "")
                 if index is not None else None)
        if extra is not None:
            return {"owed": True, "owed_verb": str(extra.get("verb") or "")}
        return {}
    # A note owed under BOTH registries shows the type's verb, because that is
    # the one its own status is asking for. The other is still counted and
    # still listed in `Needs you` under its own kind — so nothing is lost, and
    # the row is not made to say two things at once.
    if index is not None and record.note_type in _obligations.SUBJECT_FIELDS:
        if not _obligations.subject_is_in_flight(record, index):
            return {"suppressed": True, "owed_verb": ob.verb}
    return {"owed": True, "owed_verb": ob.verb}


def _feature_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": record.frontmatter.get("goal") or "",
        "type": record.note_type or "feature",
        **_verification_flags(record),
        **_owed_flag(record, index),
    }


def _task_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": _first_body_paragraph(record.body),
        "type": record.note_type or "task",
        **_verification_flags(record),
    }


def _issue_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": _first_body_paragraph(record.body),
        "type": record.note_type or "issue",
        **_verification_flags(record),
    }


def _recent_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    updated = _note_updated(record)
    parts = [record.note_type or "note"]
    if updated:
        parts.append(updated.isoformat())
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": " · ".join(parts),
        "type": record.note_type or "",
        **_verification_flags(record),
    }


# ---------------------------------------------------------------------------
# Right pane (relationships) — unchanged structurally; reuses TYPE_ORDER.
# ---------------------------------------------------------------------------


def _context_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    """Right-pane item shape.

    Issues show ``severity`` (defaulting to ``"low"`` when frontmatter
    lacks one) instead of ``priority`` — severity is the issue-vocabulary
    field and is meaningful even when unset. Other types continue to
    surface ``priority`` (relevant on requirements).
    """
    priority = record.frontmatter.get("priority")
    severity: str | None = None
    if record.note_type == "issue":
        raw = record.frontmatter.get("severity")
        sev = raw.strip().lower() if isinstance(raw, str) and raw.strip() else "low"
        severity = sev
        priority = None
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "priority": priority,
        "severity": severity,
        "url": index.url_for(record.path),
        "type": record.note_type or "",
        **_verification_flags(record),
    }


def _grouped_items(
    index: Index, paths: set[Path], platform: str | None = None
) -> list[dict[str, Any]]:
    groups: dict[str, list[NoteRecord]] = {}
    for path in paths:
        record = index.get(path)
        if record is None:
            continue
        if record.rel_path.startswith("__templates__/"):
            continue
        if not _platform_match(record, platform):
            continue
        bucket = record.note_type or "untyped"
        groups.setdefault(bucket, []).append(record)

    ordered_keys = sorted(
        groups,
        key=lambda t: (_TYPE_RANK.get(t, len(TYPE_ORDER)), t),
    )
    return [
        {
            "type": key,
            "items": [
                _context_item(index, r)
                for r in sorted(
                    groups[key], key=lambda x: (x.note_id or "", x.rel_path)
                )
            ],
        }
        for key in ordered_keys
    ]


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------


#: The canonical part of a phase link. A phase's identity is its **ID**;
#: the rest of the slug is a title, and titles are expected to change.
_PHASE_ID_RE = re.compile(r"(PHASE-\d+)")


def _phase_target(record: NoteRecord) -> str | None:
    """The grouping key for ``record``'s phase — its ID where it has one.

    Keying on the full slug forks a group whenever a phase is retitled:
    ISS-0077's merge renamed ``PHASE-016-Errors-Become-Work`` to
    ``PHASE-016-The-Overview-Answers-Questions``, and four notes still
    pointing at the old slug rendered a second, unresolvable PHASE-016
    group in the navigator. The overview was unaffected because its own
    ``_phase_id_of`` already extracted the ID — the two paths reading the
    same field differently *was* the bug (ISS-0082).

    Falls back to the stripped slug when no ID is present, so a corpus
    linking phases by title alone still groups.
    """
    raw = record.frontmatter.get("phase")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if not isinstance(raw, str):
        return None
    stripped = _strip_wikilink(raw).strip()
    m = _PHASE_ID_RE.search(stripped)
    return m.group(1) if m else (stripped or None)


def _resolve_phase(index: Index, target: str) -> NoteRecord | None:
    path = index.by_id(target)
    if path is None:
        return None
    return index.get(path)


def _resolve_this(index: Index, this: str) -> Path | None:
    by_id = index.by_id(this)
    if by_id is not None:
        return by_id
    rel = this.lstrip("/")
    if rel.startswith("docs/"):
        rel = rel[len("docs/"):]
    candidate = (index.docs_root / rel).resolve()
    if candidate.suffix.lower() != ".md":
        return None
    record = index.get(candidate)
    return candidate if record is not None else None


def _first_link(raw: Any) -> str | None:
    if isinstance(raw, list):
        return _first_link(raw[0]) if raw else None
    if isinstance(raw, str):
        s = raw.strip()
        return s or None
    return None


def _strip_wikilink(s: str) -> str:
    s = s.strip()
    if s.startswith("[[") and s.endswith("]]"):
        s = s[2:-2]
    if "|" in s:
        s = s.split("|", 1)[0]
    return s.strip()


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _note_updated(record: NoteRecord) -> _dt.date | None:
    for key in ("updated", "created"):
        value = record.frontmatter.get(key)
        date = _coerce_date(value)
        if date is not None:
            return date
    return None


def _coerce_date(value: Any) -> _dt.date | None:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        try:
            return _dt.date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def _normalise_platform(platform: str | None) -> str | None:
    """Return ``None`` for "no filter" (missing / blank / "all"), else the lowercase value."""
    if not platform:
        return None
    p = platform.strip().lower()
    if not p or p == "all":
        return None
    return p


def _record_platform(record: NoteRecord) -> str:
    """Lowercased platform value, or ``""`` if absent."""
    raw = record.frontmatter.get("platform")
    if raw is None:
        return ""
    return str(raw).strip().lower()


def available_platforms(index: Index) -> list[str]:
    """Sorted list of distinct non-empty ``platform`` values in the corpus.

    Templates are excluded. Empty strings (cross-platform / agnostic notes)
    are excluded — they carry no signal that the project actually uses
    platform tagging. The JS client hides the picker when this list is
    empty.
    """
    seen: set[str] = set()
    for path in index.paths():
        record = index.get(path)
        if record is None:
            continue
        if record.rel_path.startswith("__templates__/"):
            continue
        p = _record_platform(record)
        if p:
            seen.add(p)
    return sorted(seen)


def _platform_match(record: NoteRecord, platform: str | None) -> bool:
    """Filter predicate used by every nav mode and the right pane.

    Semantics:

    * ``platform`` is ``None`` / ``"all"`` → always include.
    * Otherwise, include records whose own ``platform`` is the picked
      value, ``shared`` (always cross-platform), or empty/missing
      (platform-agnostic notes — phases, ADRs, etc.).
    """
    if platform is None:
        return True
    p = _record_platform(record)
    return p in ("", "shared", platform)


def _bucket_for_date(date: _dt.date | None, today: _dt.date) -> str:
    if date is None:
        return "earlier"
    delta = (today - date).days
    if delta <= 0:
        return "today"
    if delta == 1:
        return "yesterday"
    if delta <= 7:
        return "week"
    if delta <= 31:
        return "month"
    return "earlier"


# ------------------------------------------------- history (FEAT-0052)

#: Marker for the log's per-commit record. `%x01` cannot occur in a subject.
_HISTORY_REC_SEP = "\x01"

#: `status: value` in a diff line — the frontmatter field this system treats
#: as the authored unit of state (ADR-0009).
_STATUS_LINE_RE = re.compile(r"^([+-])status:\s*(\S+)\s*$")
_DIFF_PATH_RE = re.compile(r"^\+\+\+ b/(.+)$")


#: States that mean a person owes a judgment, for the digest's `needs_you`
#: half. Deliberately the same set the views surface — `triage` because
#: ADR-0020 made it an obligation, `changes-requested` because a reviewer
#: asked for something, `draft`/`proposed`/`ready` because each queues for a
#: decision somebody has to make.
#:
#: NOT a second obligation vocabulary. When FEAT-0089's registry lands this
#: reads from it; until then it is one list in one module, and the digest is
#: the only consumer.
# `DIGEST_NEEDS_YOU` lived here — a second list of what needs a person, six
# types and their states, written before the registry existed. TASK-0313's own
# note said what to do about it: *"it reads from FEAT-0089's registry once that
# lands. If it outlives the registry it becomes exactly the drift ISS-0023
# describes."*
#
# It has landed, so this reads it. The difference is not cosmetic: the list
# above omitted `change` (81 owed here) and `feature` (`acceptance: requested`),
# and had no way to express the `test` predicate's manual-only clause. A digest
# built from it would have told the returning human that 8 things needed them
# while the badges said 96.


def _parse_instant(value: str) -> _dt.datetime | None:
    """An aware datetime out of an ISO-8601 string, or None (ISS-0134).

    Returns None for a **date-only** value on purpose: `2026-08-11` names a
    day, not an instant, and silently promoting it to midnight would order
    every commit that day as "after the watermark" — reintroducing the bug
    this exists to fix, in the opposite direction and invisibly.

    Naive input is read as UTC. The watermark and git's `%aI` both carry an
    offset in practice; this keeps a hand-edited `last-seen.json` comparable
    rather than silently unordered.
    """
    raw = (value or "").strip()
    if len(raw) <= 10:
        return None
    try:
        parsed = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed


def landing_payload(index: "Index", view: str) -> dict[str, Any]:
    """What a view owes, for the page it lands on (FEAT-0092 / TASK-0387).

    **One computation behind the badge and the page.** The rows come from
    `obligations.owed_items` and the counts from `obligations.counts_by_kind`,
    which walk the same predicate — a page whose number disagreed with the
    button that opened it is the failure `FEAT-0089` was built to prevent, and
    the fastest way to reintroduce it is a second count here.

    Grouped by kind and labelled with the registry's own verb and noun, so the
    page says `Approve requirement` and never `1 item`. Absent groups are
    absent: a view that owes nothing gets an empty list and the surface decides
    what silence looks like, which is this project's standing rule about zero.
    """
    view = (view or "").strip().lower()
    if view not in _obligations.VIEWS:
        return {"view": view, "known": False, "groups": [], "total": 0}
    rows = _obligations.owed_items(index).get(view, [])
    counts = _obligations.counts_by_kind(index).get(view, {})
    groups: list[dict[str, Any]] = []
    for kind in sorted(counts):
        items = [r for r in rows if r["type"] == kind]
        singular, plural = _obligations.KIND_NOUNS.get(kind, (kind, kind + "s"))
        n = counts[kind]
        # A note-less kind has no note type, so `for_type` cannot answer for
        # it — its verb lives on its source. Without this the group rendered
        # "2 standing documents" with no verb, which is the "N items" phrasing
        # the registry exists to replace.
        note_less = _obligations.note_less_sources().get(kind)
        if items:
            verb = str(items[0]["verb"])
        elif note_less is not None:
            verb = note_less.verb
        else:
            ob_kind = _obligations.for_type(kind)
            verb = ob_kind.verb if ob_kind else ""
        groups.append({
            "kind": kind,
            "count": n,
            "verb": verb,
            "noun": singular if n == 1 else plural,
            "label": f"{verb} {n} {singular if n == 1 else plural}".strip(),
            # Empty for the standing-document obligation, whose subject is a
            # manifest entry rather than a note — the Intent view renders those
            # from `standing.check`, and a row-less group still carries its
            # count so the page and the badge agree.
            "items": items,
        })
    return {
        "view": view,
        "known": True,
        "groups": groups,
        "total": sum(counts.values()),
    }


def digest_payload(
    project_root: Path,
    index: Index,
    seen_at: str,
    limit: int = 200,
) -> dict[str, Any]:
    """What happened since the human last said they were caught up (FEAT-0071).

    Two halves, and the split is the point (DES-0008): **what changed** is
    informational, **what needs you** is owed. The band lifts the second above
    the first because a reader who stops halfway should have seen the
    obligations, not the news.

    `seen_at` is a watermark, and an unset one arrives as the epoch — so the
    first digest shows everything rather than nothing. That asymmetry is
    deliberate: over-reporting on a fresh install is recoverable by reading;
    under-reporting is invisible.
    """
    history = history_payload(project_root, index, limit=limit)
    marker = (seen_at or "").strip()

    since: list[dict[str, Any]] = []
    marker_at = _parse_instant(marker)
    for commit in history.get("commits") or []:
        # **The granularity mismatch is gone** (ISS-0134). Commits now carry
        # their full `%aI` instant as `ts` beside the day, so when the
        # watermark also has one they are ordered exactly and a catch-up
        # advances *within* a day. That was the whole defect: `computed_at`
        # was a day, every commit was a day, so on any day somebody was
        # working the comparison could never move and three clicks of
        # `Caught up` changed nothing.
        #
        # The day rule survives as the fallback, and keeps its original
        # reasoning: strictly-less, so the watermark's own day is INCLUDED.
        # Re-showing a commit already seen is corrected by reading; hiding one
        # made after catching up is invisible.
        when = str(commit.get("date") or "")
        commit_at = _parse_instant(str(commit.get("ts") or ""))
        if marker_at is not None and commit_at is not None:
            if commit_at <= marker_at:
                continue
        elif marker and when and when < marker[:10]:
            continue
        for transition in commit.get("transitions") or []:
            since.append({**transition, "sha": commit.get("sha"), "date": when})

    # **The registry's walk, not a second one** (ISS-0159). This built its own
    # pass over `index.paths()` and asked `_owed_flag` per record — the right
    # predicate, the wrong walk, because a walk over notes cannot see an
    # obligation whose subject is not a note. Measured 2026-08-13: the digest
    # said 13 where the badges said 14, and the difference WAS the note-less
    # count (ADR-0027's standing documents and unpublished commits).
    #
    # That is the failure PHASE-030 existed to end, surviving inside it: the
    # registry's promise is one walk so the badge and the page cannot disagree,
    # and `counts_by_kind` is asserted against `owed_items` for exactly that
    # reason. A third walk sits outside that assertion and so cannot be caught
    # by it.
    needs_you: list[dict[str, Any]] = []
    for rows in _obligations.owed_items(index).values():
        for row in rows:
            item: dict[str, Any] = {
                "id": row["id"],
                "title": row["title"],
                "type": row["type"],
                "status": row["status"],
                "rel": row["rel"],
                "owed": True,
                "owed_verb": row["verb"],
            }
            # A note-less row carries its own route; `_slim_note` cannot build
            # one for a subject that has no note behind it.
            if row.get("url"):
                item["url"] = row["url"]
            elif row["rel"]:
                item["url"] = f"/docs/{row['rel']}"
            needs_you.append(item)
    # …plus the one set the registry deliberately does not count: a note whose
    # `review_verdict` still owes work. ISS-0121's discriminator applies — the
    # stamp is sticky, so the subject's CURRENT status decides. Declared here
    # rather than arriving from a second pass nobody named, so the digest is
    # the registry's total plus an enumerable set and never silently less.
    for record in index.iter_records():
        verdict = str(record.frontmatter.get("review_verdict") or "").strip().lower()
        if _verdict_is_owed(verdict, record.status, record.note_type):
            needs_you.append(_slim_note(record))

    # One item, one row — the same rule the triage tray had to learn.
    seen_ids: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in needs_you:
        key = str(item.get("id") or item.get("rel") or "")
        if key in seen_ids:
            continue
        seen_ids.add(key)
        deduped.append(item)

    return {
        "schema_version": SCHEMA_VERSION,
        "seen_at": marker,
        "available": history.get("available", False),
        # The timestamp a `Caught up` should record — the digest's own, not
        # the moment the button is pressed, so nothing that lands while the
        # human reads is marked seen (TASK-0312).
        #
        # The newest commit's full INSTANT, not its day (ISS-0134). As a day
        # it could never order against same-day commits, so catching up on a
        # working day wrote a watermark that changed nothing — measured at
        # `caught_up_count: 3` with the digest unmoved. Falls back to the day
        # only when git gave no instant, and to now when there are no commits
        # at all, so the button always records something orderable.
        "computed_at": (
            (history.get("commits") or [{}])[0].get("ts")
            or (history.get("commits") or [{}])[0].get("date")
            or _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        ),
        "transitions": since,
        "transition_count": len(since),
        "needs_you": deduped,
        "needs_you_count": len(deduped),
    }


def history_payload(
    project_root: Path,
    index: Index,
    limit: int = COMMITS_DEFAULT_LIMIT,
    until: str | None = None,
    fresh: bool = False,
) -> dict[str, Any]:
    """Documentation history: status transitions, grouped by commit.

    The overview's history band used to answer the same question three
    ways — a weekly edit count, the change notes, and the git log with
    notes as chips. All three read git or the filesystem as the subject.
    This inverts it: the **row is a note's status transition** and the
    **commit is a divider** saying what is saved.

    A transition is not a touch, and the difference is not pedantic.
    Measured on this repo's phase-hygiene commit: 20 notes touched, **4**
    statuses changed — the other sixteen had a ``phase:`` field
    corrected. A touch-based list renders bookkeeping as the largest
    event of the day.

    ``created`` distinguishes a note *born* at a status from one that
    *moved* to it: a ``+status:`` with no matching ``-status:`` in the
    same file diff is a new note. Most notes in a busy commit are written
    and closed in one pass, and an arrow would imply a journey they never
    took.

    A commit whose diff carries no transition is **still returned**, with
    ``transitions: []`` and the existing ``undocumented`` sense preserved
    — a commit that moved code with nothing recording why is the one that
    most needs to be visible, and it is the one a naive implementation
    drops for having no rows (FEAT-0022's guardrail).

    ``uncommitted`` lists notes whose working tree differs from HEAD, so
    "not saved yet" is answerable without leaving the page.

    ``until`` (``YYYY-MM-DD``) anchors the window at a date rather than
    at HEAD, which is what makes a contribution-grid cell a destination:
    the grid spans the whole history while a page shows a window, so
    without this a click on an old day has nothing loaded to land on.
    Found in TASK-0259's live pass, where clicking 2026-05-07 silently
    landed on 2026-07-28 — the oldest commit that happened to be loaded.
    The uncommitted band is suppressed for an anchored window: work in
    flight belongs to now, not to a date in the past.

    Same hardening as :func:`commits_payload`: fixed argv, clamped limit,
    bounded timeout, and every failure mode degrading to
    ``{"available": False}`` rather than raising.
    """
    import subprocess

    try:
        count = int(limit)
    except (TypeError, ValueError):
        count = COMMITS_DEFAULT_LIMIT
    count = max(1, min(count, COMMITS_MAX_LIMIT))

    unavailable: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "available": False,
        "commits": [],
        "uncommitted": [],
    }
    if not (project_root / ".git").exists():
        return unavailable

    docs_prefix = ""
    try:
        docs_prefix = index.docs_root.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except (ValueError, OSError):
        docs_prefix = ""
    prefix = f"{docs_prefix}/" if docs_prefix else ""
    scope = [prefix or ".", "SNAPSHOT.yaml"]

    anchored = bool(until) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", until or ""))
    window: list[str] = [f"--until={until} 23:59:59"] if anchored else []

    by_rel: dict[str, Any] = {}
    for record in index.iter_records():
        if record.note_id:
            by_rel[record.rel_path.lower()] = record

    def _resolve(git_path: str) -> Any:
        if prefix and git_path.lower().startswith(prefix.lower()):
            return by_rel.get(git_path[len(prefix):].lower())
        return None

    fmt = f"{_HISTORY_REC_SEP}%h\t%H\t%aI\t%an\t%s"
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            [
                "git", "-C", str(project_root), "log",
                f"-n{count}", "--no-merges", "-U0", "--no-color",
                f"--format={fmt}", *window, "--", *scope,
            ],
            capture_output=True, text=True,
            timeout=_GIT_TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return unavailable
    if proc.returncode != 0:
        return unavailable

    commits = _parse_history_log(proc.stdout, _resolve)
    # Mark what is committed but not published (FEAT-0100 / TASK-0418), by
    # IDENTITY rather than by position. The count alone would let a surface
    # infer "the first N are unpushed", which is true only while nothing
    # filters or reorders the list — an assumption that costs nothing to avoid
    # and is silently wrong the day it breaks.
    #
    # The ladder this completes: the uncommitted band says NOT SAVED, these say
    # SAVED BUT NOT PUBLISHED, and the rest are published — top to bottom, in
    # the order those things happen.
    #
    # `fresh` is the caller saying "I have a reason to believe the cached
    # reading is false" — in practice, a push that has just returned (ISS-0168).
    # The push runs in the Electron main process, so nothing here can observe
    # it, and `CACHE_SECONDS` would otherwise hand the surface that offered the
    # push its own pre-push numbers back.
    try:
        read = _git_state.read_fresh if fresh else _git_state.read
        state = read(project_root)
    except OSError:                      # pragma: no cover — unreadable repo
        state = _git_state.GitState(remote=None, kind="none", ahead=None, commits=())
    unpublished = {c.sha for c in state.commits}
    if unpublished:
        for commit in commits:
            # `sha` is the short form here and in `git_state`; both come from
            # `%h`, so they compare directly.
            if commit.get("sha") in unpublished:
                commit["unpublished"] = True
    return {
        "schema_version": SCHEMA_VERSION,
        "available": True,
        "anchored_at": until if anchored else None,
        "commits": commits,
        # How the unpublished commits may leave: `backup` offers a push,
        # `deploy` names it and refuses, `none` has nowhere to go at all.
        "remote_kind": state.kind,
        # The TRUE count, which is not the number of marked commits in this
        # window. The overview tile loads a handful, and counting the marks
        # inside it undercounted the run — measured live at 6 against 7, on a
        # button that would have pushed all seven while offering to push six.
        # A push publishes everything; the label has to mean that.
        #
        # `None` when the count could not be taken at all — a branch with no
        # upstream, where `git rev-list @{u}..HEAD` fails. That is **not** a
        # zero, and the two must stay distinguishable all the way to the
        # surface: ADR-0027's fourth admission test refuses an unknown
        # presented as a count, and this returned 0 until 2026-08-14, so the
        # History band silently showed nothing to publish on a repo whose
        # commits had nowhere to go.
        "unpublished_count": (None if state.ahead is None else len(state.commits)),
        "publication_known": state.ahead is not None,
        # Work in flight belongs to now. Showing it above a window that
        # ends three months ago would place today's edits inside May.
        "uncommitted": ([] if anchored
                        else _uncommitted_notes(project_root, scope, _resolve)),
    }


def _parse_history_log(
    text: str, resolve: Callable[[str], Any]
) -> list[dict[str, Any]]:
    """Parse ``git log -U0`` output into commits carrying transitions.

    Split out so it can be tested without a repository — the parsing is
    where this can be wrong, and a fixture repo per case would make the
    suite slow enough that nobody adds cases to it.
    """
    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    path: str | None = None
    # Per file within one commit: the `-status:` seen (if any) and the
    # `+status:` seen. Pairing them is what separates moved from created.
    pending: dict[str, dict[str, str]] = {}

    def _flush() -> None:
        if current is None:
            return
        for file_path, seen in pending.items():
            to = seen.get("to")
            if to is None:
                continue
            record = resolve(file_path)
            current["transitions"].append({
                "id": getattr(record, "note_id", None),
                "type": getattr(record, "note_type", None),
                "title": getattr(record, "title", None),
                "rel": getattr(record, "rel_path", None),
                "path": file_path,
                "from": seen.get("from"),
                "to": to,
                "created": "from" not in seen,
            })
        current["transitions"].sort(key=lambda t: (t.get("id") or "￿"))
        commits.append(current)

    for line in text.splitlines():
        if line.startswith(_HISTORY_REC_SEP):
            _flush()
            parts = line[len(_HISTORY_REC_SEP):].split("\t", 4)
            if len(parts) < 5:
                current, pending, path = None, {}, None
                continue
            sha, full, when, author, subject = parts
            current = {
                "sha": sha, "full_sha": full, "date": when[:10],
                # The full `%aI` instant, kept alongside the day (ISS-0134).
                # It was being truncated here and nowhere else had it, which
                # is why the digest could only ever compare whole days — and
                # so could never advance its watermark on a day someone was
                # still committing. Display keeps using `date`.
                "ts": when,
                "author": author, "subject": subject, "transitions": [],
            }
            pending, path = {}, None
            continue
        if current is None:
            continue
        m = _DIFF_PATH_RE.match(line)
        if m:
            path = m.group(1)
            continue
        m = _STATUS_LINE_RE.match(line)
        if m and path:
            sign, value = m.group(1), m.group(2)
            slot = pending.setdefault(path, {})
            slot["to" if sign == "+" else "from"] = value
    _flush()
    # `undocumented` keeps commits_payload's sense: nothing documented
    # moved. Reported rather than dropped — a commit that changed code
    # with no note behind it is the one worth seeing (FEAT-0022).
    for commit in commits:
        commit["undocumented"] = not commit["transitions"]
    return commits


def _uncommitted_notes(
    project_root: Path, scope: list[str], resolve: Callable[[str], Any]
) -> list[dict[str, Any]]:
    """Notes whose working tree differs from HEAD.

    The half of "what happened" that git history cannot answer: work in
    flight. Failure is silent — an absent or slow git means the band is
    empty, never that the page breaks.

    **The walk is** :func:`git_state.dirty_paths` **and this decorates it**
    (TASK-0422). It ran its own `git status` until 2026-08-14, with its own
    copy of the rename handling, while the fleet card counted the same files
    through a third implementation in TypeScript — the `dirty` half of
    [[ISS-0165]]. What is left here is the part that is genuinely this
    surface's: turning a path into the note it belongs to.
    """
    out: list[dict[str, Any]] = []
    for code, git_path in _git_state.dirty_paths(project_root, tuple(scope)):
        record = resolve(git_path)
        out.append({
            "id": getattr(record, "note_id", None),
            "type": getattr(record, "note_type", None),
            "title": getattr(record, "title", None),
            "rel": getattr(record, "rel_path", None),
            "path": git_path,
            "status": getattr(record, "status", None),
            "code": code,
        })
    out.sort(key=lambda r: (r.get("id") or "￿", r["path"]))
    return out


def activity_payload(project_root: Path, index: Index) -> dict[str, Any]:
    """Per-day documentation activity across the whole history (FEAT-0053).

    Feeds the contribution grid. Counts **status transitions** rather than
    commits or file touches, so the darkest day is the day most things
    were finished — the same unit :func:`history_payload` uses for its
    rows, which is what lets a cell be a destination.

    ``buckets`` are the quartile thresholds of this repo's own **active**
    days. GitHub's fixed 1/4/7/10 scale saturates instantly here:
    measured on this corpus, 16 days carry any activity at all and the
    median active day has 34 transitions, so every lit cell would sit in
    the top bucket and the grid would carry one bit per day. Computing
    the scale server-side also stops the client inventing one.

    ``first_commit`` lets the grid render pre-history as **absent**
    rather than as a day with no activity. Those are different facts,
    and conflating them is why a young project's contribution graph
    reads as neglect.

    Whole-history by design and therefore cacheable on HEAD — unlike
    :func:`history_payload`, whose uncommitted band is precisely the part
    that must never be served stale. Opposite requirements are why these
    are two endpoints.
    """
    import subprocess

    unavailable: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "available": False,
        "days": {},
        "first_commit": None,
        "last_commit": None,
        "buckets": [],
    }
    if not (project_root / ".git").exists():
        return unavailable

    docs_prefix = ""
    try:
        docs_prefix = index.docs_root.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except (ValueError, OSError):
        docs_prefix = ""
    scope = [f"{docs_prefix}/" if docs_prefix else ".", "SNAPSHOT.yaml"]

    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            [
                "git", "-C", str(project_root), "log",
                "--no-merges", "-U0", "--no-color",
                f"--format={_HISTORY_REC_SEP}%h\t%ad", "--date=short",
                "--", *scope,
            ],
            capture_output=True, text=True,
            timeout=_GIT_TIMEOUT_SECONDS * 4, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return unavailable
    if proc.returncode != 0:
        return unavailable

    days: dict[str, dict[str, int]] = {}
    day: str | None = None
    path: str | None = None
    for line in proc.stdout.splitlines():
        if line.startswith(_HISTORY_REC_SEP):
            parts = line[len(_HISTORY_REC_SEP):].split("\t", 1)
            day = parts[1].strip() if len(parts) > 1 else None
            path = None
            if day:
                days.setdefault(day, {"transitions": 0, "commits": 0})
                days[day]["commits"] += 1
            continue
        if day is None:
            continue
        m = _DIFF_PATH_RE.match(line)
        if m:
            path = m.group(1)
            continue
        if path and line.startswith("+status:"):
            days[day]["transitions"] += 1

    if not days:
        return {**unavailable, "available": True}

    ordered = sorted(days)
    active = sorted(d["transitions"] for d in days.values() if d["transitions"] > 0)
    return {
        "schema_version": SCHEMA_VERSION,
        "available": True,
        "days": days,
        "first_commit": ordered[0],
        "last_commit": ordered[-1],
        "buckets": _quartile_buckets(active),
    }


def _quartile_buckets(active: list[int]) -> list[int]:
    """Upper bounds of four intensity steps, from the active days only.

    Including the zero days would put every threshold at 0 and every lit
    cell in the top step — the saturation this exists to avoid. Returned
    as three cut points: a value at or below ``b[0]`` is step 1, above
    ``b[2]`` is step 4.
    """
    if not active:
        return []
    def _at(frac: float) -> int:
        idx = min(len(active) - 1, max(0, int(round(frac * (len(active) - 1)))))
        return active[idx]
    cuts = [_at(0.25), _at(0.5), _at(0.75)]
    # Strictly increasing, so four distinct steps exist even when the
    # distribution is flat enough that two quartiles coincide.
    for i in range(1, len(cuts)):
        if cuts[i] <= cuts[i - 1]:
            cuts[i] = cuts[i - 1] + 1
    return cuts


#: How a touched path is bucketed. Order matters — first match wins — and the
#: buckets answer the reader's question ("did this touch what it claims to")
#: rather than mirroring the directory tree.
_SHAPE_KINDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("tests", ("tests/", "test_")),
    ("notes", ("docs/",)),
    ("tools", ("tools/",)),
    ("source", ("src/", "desktop/src/")),
    ("assets", (".css", ".png", ".svg", ".html")),
)


def _shape_kind(path: str) -> str:
    low = path.lower()
    for kind, needles in _SHAPE_KINDS:
        for needle in needles:
            if needle.startswith(".") and low.endswith(needle):
                return kind
            if not needle.startswith(".") and (low.startswith(needle) or needle in low):
                return kind
    return "other"


def change_shape_payload(
    project_root: Path, note_id: str, limit: int = 200,
) -> dict[str, Any]:
    """What a note's commits actually touched (ISS-0096).

    History answers *what moved* — status transitions grouped by commit, which
    [[FEAT-0052]] measured as the honest signal. It cannot answer **the shape
    of a change**: this task touched 6 files, 4 notes and 2 CSS.

    That gap matters at acceptance time specifically. The reader is judging
    *did this touch what it claims to touch*, and a task promising a CSS fix
    that rewrote the validator is one line of shape and invisible in prose.
    `commits_payload` cannot answer it because it **discards every non-`.md`
    path** — deliberately, for its own question.

    **Counts, not contents.** The cockpit is not an editor and the persona is
    not reading implementations; the full diff stays one deliberate click
    away, which is this issue's own out-of-scope line.
    """
    import subprocess          # local, as every other git caller here does

    wanted = (note_id or "").strip().upper()
    unavailable = {"schema_version": SCHEMA_VERSION, "id": wanted,
                   "available": False, "commits": [], "kinds": {}, "files": 0}
    if not wanted or not (project_root / ".git").exists():
        return unavailable

    sep = _COMMIT_RECORD_SEP
    fmt = _COMMIT_FIELD_SEP.join(["%h", "%aI", "%s"])
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "-C", str(project_root), "log", f"-n{limit}", "--no-merges",
             "--name-only", f"--grep={wanted}", f"--format={sep}{fmt}"],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return unavailable
    if proc.returncode != 0:
        return unavailable

    commits: list[dict[str, Any]] = []
    kinds: dict[str, int] = {}
    seen_files: set[str] = set()
    for chunk in proc.stdout.split(sep):
        if not chunk.strip():
            continue
        head, _, rest = chunk.partition("\n")
        parts = head.split(_COMMIT_FIELD_SEP)
        if len(parts) < 3:
            continue
        sha, when, subject = parts[0], parts[1], parts[2]
        files = [ln.strip() for ln in rest.splitlines() if ln.strip()]
        per_commit: dict[str, int] = {}
        for f in files:
            kind = _shape_kind(f)
            per_commit[kind] = per_commit.get(kind, 0) + 1
            if f not in seen_files:
                seen_files.add(f)
                kinds[kind] = kinds.get(kind, 0) + 1
        commits.append({
            "sha": sha, "date": when[:10], "ts": when, "subject": subject,
            "files": len(files), "kinds": per_commit,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "id": wanted,
        "available": True,
        "commits": commits,
        "kinds": kinds,
        "files": len(seen_files),
    }
