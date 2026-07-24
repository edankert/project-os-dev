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
from pathlib import Path
from typing import Any, Iterable

from .index import Index, NoteRecord

SCHEMA_VERSION: int = 2

PROJECT_SUPPORT_ROOT_FILES: tuple[str, ...] = (
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
)

# Project mode indexes ``docs/``. The only non-docs Markdown surfaced by
# default is selected top-level human-facing project documentation.
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
# actively touching first; archived states last.
TASK_STATUS_ORDER: tuple[str, ...] = (
    "doing", "in-progress", "in-review", "next",
    "blocked", "failing", "reopened",
    "ready", "active", "approved", "accepted",
    "planned", "triage",
    "todo", "open", "pending", "backlog",
    "draft", "proposed",
    "done", "merged", "fixed", "fulfilled", "met", "complete",
    "verified", "passing", "published", "closed",
    "obsolete", "retired", "cancelled", "superseded", "wont-fix", "reverted",
    "reference", "deferred",
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
    "changes",
    "decisions",
    "features",
    "issues",
    "phases",
    "requirements",
    "risks",
    "tests",
    "workflows",
)
# Note types that get their own group under "By type — rare" in Library mode.
# Anything covered by a primary nav mode (feature, task, issue) is excluded.
LIBRARY_RARE_TYPES: tuple[str, ...] = (
    "adr", "release", "risk", "test", "workflow", "plan", "reference",
)

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
    """Mode 1: features grouped by phase."""
    features = [r for r in index.notes_by_type("feature") if _platform_match(r, platform)]
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
        out.append(
            {
                "key": phase_id or phase_title or "unphased",
                "label": label,
                "url": index.url_for(phase_record.path) if phase_record else None,
                "status": phase_record.status if phase_record else None,
                "items": [
                    _feature_item(index, r)
                    for r in sorted(records, key=lambda x: (x.note_id or "", x.rel_path))
                ],
            }
        )
    return out


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
    )
    if docs_tree is not None:
        out.append(docs_tree)

    support_group = _project_support_group(project_root)
    if support_group is not None:
        out.append(support_group)

    # ----- By type — rare (status+id+title, "stacked" layout, no type label) -----
    for type_name in LIBRARY_RARE_TYPES:
        records = [
            r for r in index.notes_by_type(type_name)
            if _platform_match(r, platform)
        ]
        if not records:
            continue
        records.sort(key=lambda r: (r.note_id or "", r.rel_path))
        out.append(
            {
                "key": f"rare:{type_name}",
                "label": _pluralise_for_label(type_name),
                "url": None,
                "status": None,
                "item_layout": "stacked",
                "items": [_rare_item(index, r) for r in records],
            }
        )

    return out


def _project_support_group(project_root: Path | None) -> dict[str, Any] | None:
    if project_root is None:
        return None
    root = project_root.resolve()

    root_items = [
        _project_support_item(root / rel, rel)
        for rel in PROJECT_SUPPORT_ROOT_FILES
        if (root / rel).is_file()
    ]

    subgroups: list[dict[str, Any]] = []
    for rel_dir, label, max_depth in PROJECT_SUPPORT_DIRS:
        area = root / rel_dir
        if not area.is_dir():
            continue
        items = [
            _project_support_item(path, path.relative_to(root).as_posix())
            for path in _iter_support_markdown(area, max_depth=max_depth)
        ]
        if not items:
            continue
        subgroups.append(
            {
                "key": f"support:{rel_dir}",
                "label": label,
                "url": f"/{rel_dir}/",
                "status": None,
                "item_layout": "compact",
                "items": items,
            }
        )

    if not root_items and not subgroups:
        return None
    return {
        "key": "project-support",
        "label": "Top-level docs",
        "url": None,
        "status": None,
        "item_layout": "compact",
        "items": root_items,
        "subgroups": subgroups,
    }


def _iter_support_markdown(root: Path, *, max_depth: int) -> Iterable[Path]:
    base = root.resolve()
    for path in sorted(base.rglob("*.md"), key=lambda p: p.relative_to(base).as_posix().lower()):
        try:
            rel_parts = path.relative_to(base).parts
        except ValueError:
            continue
        if len(rel_parts) > max_depth:
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in rel_parts):
            continue
        yield path


def _project_support_item(path: Path, rel_path: str) -> dict[str, Any]:
    return {
        "id": "",
        "title": _support_title(path),
        "status": None,
        "url": f"/{rel_path}",
        "subtitle": rel_path,
    }


def _support_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[:80]:
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
    except OSError:
        pass
    if path.name == "SKILL.md":
        return path.parent.name
    return path.name


def _markdown_tree_group(
    index: Index,
    platform: str | None,
    *,
    key: str,
    label: str,
    root_prefix: str = "",
    excluded_roots: tuple[str, ...] = (),
    untyped_only: bool = False,
) -> dict[str, Any] | None:
    """Build a recursive directory tree for indexed Markdown notes."""
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

    for path in index.paths():
        record = index.get(path)
        if record is None:
            continue
        if not _platform_match(record, platform):
            continue
        if untyped_only and record.note_type is not None:
            continue
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

    _sort_tree_group(root)
    if not root["items"] and not root["subgroups"]:
        return None
    return root


def _exclude_from_docs_tree(
    rel_path: str,
    *,
    excluded_roots: tuple[str, ...] = (),
) -> bool:
    if any(rel_path.startswith(prefix) for prefix in DOC_TREE_EXCLUDED_PREFIXES):
        return True
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
    """Item shape for Pinned + "rare types" sections (ADRs, Tests, etc.).

    Status/id/title only — type label is dropped (the group header already
    says "Decisions" / "Risks" / etc.). The JS renders this in "stacked"
    layout: status+id on the top line, title underneath.
    """
    return {
        "id": record.note_id or record.path.stem,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": "",
    }


def _tree_item(record: NoteRecord) -> dict[str, Any]:
    """Compact file item for recursive directory-tree navigation."""
    return {
        "id": "",
        "title": record.path.name,
        "status": None,
        "url": f"/docs/{record.rel_path}",
        "subtitle": "",
    }


# ---------------------------------------------------------------------------
# Per-item shapes
# ---------------------------------------------------------------------------


def _feature_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": record.frontmatter.get("goal") or "",
    }


def _task_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    parent = _first_link(record.frontmatter.get("implements")) or record.frontmatter.get("parent")
    parent_id = _strip_wikilink(parent) if parent else ""
    effort = record.frontmatter.get("effort") or ""
    parts = [p for p in (parent_id, effort) if p]
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": " · ".join(parts),
    }


def _issue_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    affects = _first_link(record.frontmatter.get("affects"))
    component = record.frontmatter.get("component") or ""
    parts: list[str] = []
    if affects:
        parts.append(_strip_wikilink(affects))
    if component:
        parts.append(component)
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": " · ".join(parts),
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
    }


# ---------------------------------------------------------------------------
# Right pane (relationships) — unchanged structurally; reuses TYPE_ORDER.
# ---------------------------------------------------------------------------


def _context_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "priority": record.frontmatter.get("priority"),
        "url": index.url_for(record.path),
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
