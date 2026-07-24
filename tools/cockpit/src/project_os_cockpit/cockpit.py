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
from typing import Any

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

SCHEMA_VERSION: int = 2

PROJECT_SUPPORT_ROOT_FILES: tuple[str, ...] = (
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
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
TASK_STATUS_ORDER: tuple[str, ...] = (
    "doing", "in-progress", "in-review", "next",
    "blocked", "failing", "reopened", "deferred",
    "ready", "active", "approved", "accepted",
    "planned", "triage",
    "todo", "open", "pending", "backlog",
    "draft", "proposed",
    "done", "merged", "fixed", "fulfilled", "met", "complete",
    "verified", "passing", "published", "closed",
    "obsolete", "retired", "cancelled", "superseded", "wont-fix", "reverted",
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

NAV_MODES: tuple[str, ...] = ("features", "tasks", "issues", "recent", "library")
DEFAULT_MODE = "features"

# Library mode discovery rules.
DOC_TREE_EXCLUDED_PREFIXES: tuple[str, ...] = ("__templates__/",)
DOC_TREE_EXCLUDED_ROOTS: tuple[str, ...] = (
    # Canonical project-os container dirs — each houses lifecycle-managed
    # notes that already have a dedicated nav surface (Features mode,
    # Tasks mode, rare-type groups, etc.). Hide them from the Docs tree
    # so the tree only carries non-project-os user content. __templates__/
    # is separately blocked via DOC_TREE_EXCLUDED_PREFIXES.
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
    "workflows",
)
# Note types that get their own group under "By type — rare" in Library mode.
# Anything covered by a primary nav mode (feature, task, issue) is excluded.
# Reference is NOT in this list — references render inline in the Docs tree
# alongside untyped Markdown (TASK-0036), using the book-open type icon.
# "change" leads the list (TASK-0038) — change notes are the most-active
# log surface; everything below it is referenced occasionally.
LIBRARY_RARE_TYPES: tuple[str, ...] = (
    "change", "adr", "release", "risk", "test", "workflow", "plan",
)
# Types that join the untyped Markdown tree in Library mode's Docs-tree group.
DOC_TREE_INLINE_TYPES: tuple[str, ...] = ("reference",)

# Hard cap on items returned by the recent mode. Anything older falls off.
_RECENT_LIMIT = 60


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
    if m not in NAV_MODES:
        m = DEFAULT_MODE
    plat = _normalise_platform(platform)

    if m == "features":
        groups = _features_groups(index, plat)
    elif m == "tasks":
        groups = _tasks_groups(index, plat)
    elif m == "issues":
        groups = _issues_groups(index, plat)
    elif m == "recent":
        groups = _recent_groups(index, plat)
    elif m == "library":
        groups = _library_groups(index, plat, pinned or [], project_root)
    else:  # pragma: no cover — guarded above
        groups = []

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
    sortable.sort(key=lambda t: (t[0], t[1] or ""))

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
        for r in sorted(records, key=lambda x: (x.note_id or "", x.rel_path)):
            item = _feature_item(index, r)
            child_reqs = reqs_by_feature.get(r.note_id or "", [])
            if child_reqs:
                child_reqs_sorted = sorted(
                    child_reqs, key=lambda x: (x.note_id or "", x.rel_path)
                )
                item["children"] = [
                    _requirement_child_item(index, c) for c in child_reqs_sorted
                ]
            items.append(item)
        out.append(
            {
                "key": phase_id or phase_title or "unphased",
                "label": label,
                "url": index.url_for(phase_record.path) if phase_record else None,
                "status": phase_record.status if phase_record else None,
                "items": items,
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
    }


def _tasks_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Mode 3: tasks grouped by status."""
    tasks = [r for r in index.notes_by_type("task") if _platform_match(r, platform)]
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


def _issues_groups(
    index: Index, platform: str | None = None
) -> list[dict[str, Any]]:
    """Mode 4: issues grouped by severity."""
    issues = [r for r in index.notes_by_type("issue") if _platform_match(r, platform)]
    grouped: dict[str, list[NoteRecord]] = {}
    for record in issues:
        sev = str(record.frontmatter.get("severity") or "unset").lower()
        grouped.setdefault(sev, []).append(record)

    ordered_keys = sorted(
        grouped,
        key=lambda s: (_SEVERITY_RANK.get(s, len(SEVERITY_ORDER)), s),
    )
    return [
        {
            "key": key,
            "label": key.title() if key != "unset" else "Severity unset",
            "url": None,
            "status": None,
            "items": [
                _issue_item(index, r)
                for r in sorted(
                    grouped[key], key=lambda x: (x.note_id or "", x.rel_path)
                )
            ],
        }
        for key in ordered_keys
    ]


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

    # ----- By type — rare (stacked layout, no type label) -----
    # Typed-structured types (decisions, releases, risks, tests, workflows,
    # plans) keep the standard ``id + human title`` shape — these notes have
    # meaningful frontmatter titles and IDs, and live in well-known subdirs
    # so a path subtitle adds no signal. Reference-typed notes do not appear
    # here — they merge into the Docs tree above via DOC_TREE_INLINE_TYPES.
    for type_name in LIBRARY_RARE_TYPES:
        records = [
            r for r in index.notes_by_type(type_name)
            if _platform_match(r, platform)
        ]
        if not records:
            continue
        records.sort(key=lambda r: (r.note_id or "", r.rel_path))
        group: dict[str, Any] = {
            "key": f"rare:{type_name}",
            "label": _pluralise_for_label(type_name),
            "url": None,
            "status": None,
            "item_layout": "stacked",
            "items": [_rare_item(index, r) for r in records],
        }
        if type_name == "change":
            # CHG notes accumulate fast — bucket by Current week / Last
            # week / Earlier this month for the current month, and by
            # calendar month + per-week date ranges for past months.
            # Only Current week opens by default.
            group["items"] = []
            group["subgroups"] = _changes_subgroups(index, records)
        out.append(group)

    return out


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
            "url": f"/{rel}",
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


def _feature_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": record.frontmatter.get("goal") or "",
        "type": record.note_type or "feature",
    }


def _task_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": _first_body_paragraph(record.body),
        "type": record.note_type or "task",
    }


def _issue_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": _first_body_paragraph(record.body),
        "type": record.note_type or "issue",
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


def _phase_target(record: NoteRecord) -> str | None:
    raw = record.frontmatter.get("phase")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if not isinstance(raw, str):
        return None
    return _strip_wikilink(raw) or None


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
