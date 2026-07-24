"""HTML page assembly: shell, metadata strip, breadcrumb, status chips.

The shell follows REQ-0012 — theme tokens live in ``base.css``; the inline
``<head>`` script resolves the theme before stylesheet apply so the user
never sees a wrong-theme flash on first paint.

Note pages ship with the 3-pane cockpit chrome (REQ-0013) — ``page()`` takes
a ``cockpit_active`` dict and wraps the body in the cockpit layout. Pages
without an active note (landing, index, directory listings, notices) skip
the chrome.
"""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import PurePosixPath
from typing import Any, Iterable

from . import __version__ as _VERSION
from .wikilinks import Resolver, resolve_text_to_html

# Project name shown in the header home-link. Set once at server startup
# (see :func:`project_os_cockpit.server.serve`) from the docs root's parent dir.
# Falls back to the docs root name if no parent is meaningful.
_PROJECT_NAME: str = "project-os-cockpit"


def set_project_name(name: str) -> None:
    """Configure the header label (clickable link to ``/``)."""
    global _PROJECT_NAME
    _PROJECT_NAME = name or _PROJECT_NAME

# Bare project-os ID strings (e.g. ``FEAT-0001``, ``CHG-20260507-...``)
# encountered in frontmatter list/scalar values. When a frontmatter field
# carries the bare ID instead of the wikilink form (``"[[FEAT-0001]]"``),
# we still want it to render as a link in the metadata strip — Obsidian
# users routinely write both forms.
_PROJECT_OS_ID_RE: re.Pattern[str] = re.compile(
    r"^(?:ADR|CHG|FEAT|ISS|PHASE|PLAN|REL|REQ|RISK|TASK|TST|WF)-[\w-]+$"
)

# Frontmatter keys that get top billing in the metadata strip, in display order.
# Anything else in frontmatter is folded into a generic "other" row at the end.
PRIMARY_META_KEYS: tuple[str, ...] = (
    "id",
    "type",
    "status",
    "phase",
    "owner",
    "parent",
    "implements",
    "specifies",
    "fixes",
    "validates",
    "blocks",
    "depends",
    "related",
    "source",
    "tags",
    "created",
    "updated",
    "due",
    "effort",
    "priority",
    "platform",
)

# Hidden in the strip (noise / housekeeping).
HIDDEN_META_KEYS: frozenset[str] = frozenset({"aliases", "title"})

THEME_BOOTSTRAP = """\
(function () {
  try {
    var saved = localStorage.getItem('project-os-cockpit.theme');
    var dark = saved === 'dark' ||
      (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  } catch (e) {}
})();
"""

THEME_TOGGLE_SCRIPT = """\
(function () {
  var btn = document.querySelector('.theme-toggle');
  if (!btn) return;
  function update() {
    var t = document.documentElement.getAttribute('data-theme') || 'light';
    btn.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
    btn.textContent = t === 'dark' ? '\\u25D1' : '\\u25D0';
  }
  btn.addEventListener('click', function () {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('project-os-cockpit.theme', next); } catch (e) {}
    update();
  });
  update();
})();
"""


def page(
    *,
    title: str,
    body_html: str,
    rel_path: str | None = None,
    metadata: dict[str, Any] | None = None,
    resolver: Resolver | None = None,
    reload_source: str | None = None,
    path_prefix: str = "/docs",
    cockpit_active: dict[str, Any] | None = None,
) -> str:
    """Assemble a full HTML document for a rendered note or status page.

    ``reload_source`` controls the live-reload behaviour:
    - a relative ``.md`` path (e.g. ``"features/render-server/FEAT-...md"``)
      means "reload only when this file changes";
    - the literal ``"*"`` means "reload on any file event" (used by the
      landing, index, and directory-listing pages whose content depends on
      the whole tree);
    - ``None`` (default) suppresses live reload entirely.

    ``cockpit_active`` (when set) wraps the body in the 3-pane cockpit
    layout (REQ-0013). The dict carries the active note's ``id`` / ``path``
    / ``url`` so the JS client knows what to fetch from the cockpit API.
    Pages without ``cockpit_active`` render in the non-cockpit single-pane
    layout (landing, index pages, directory listings, 403/404 notices).
    """
    breadcrumb = _breadcrumb_html(rel_path, path_prefix=path_prefix) if rel_path else ""
    meta_html = _metadata_strip_html(metadata, resolver) if metadata else ""
    safe_title = escape(title)

    reload_meta = ""
    reload_script = ""
    if reload_source:
        reload_meta = (
            '<meta name="project-os-cockpit:source" '
            f'content="{escape(reload_source)}">\n'
        )
        reload_script = '<script src="/_static/sse-reload.js" defer></script>\n'

    # Body shape: cockpit-wrapped vs single-pane.
    if cockpit_active is not None:
        cockpit_config = json.dumps(cockpit_active, ensure_ascii=False)
        body_block = (
            f'<script type="application/json" id="cockpit-config">{cockpit_config}</script>\n'
            '<div class="cockpit">\n'
            '  <aside id="cockpit-left" class="cockpit-pane cockpit-left" aria-label="Features by phase"></aside>\n'
            '  <main id="cockpit-centre" class="cockpit-centre">\n'
            f"{meta_html}"
            f'<article class="content">\n{body_html}\n</article>\n'
            "  </main>\n"
            '  <aside id="cockpit-right" class="cockpit-pane cockpit-right" aria-label="Relationships"></aside>\n'
            "</div>\n"
            '<script src="/_static/cockpit.js" defer></script>\n'
        )
        cockpit_link = '<link rel="stylesheet" href="/_static/cockpit.css">\n'
    else:
        body_block = (
            '<main class="page">\n'
            f"{meta_html}"
            f'<article class="content">\n{body_html}\n</article>\n'
            "</main>\n"
        )
        cockpit_link = ""

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{safe_title} — project-os-cockpit</title>\n"
        f"{reload_meta}"
        '<link rel="stylesheet" href="/_static/base.css">\n'
        f"{cockpit_link}"
        f"<script>{THEME_BOOTSTRAP}</script>\n"
        f"{reload_script}"
        "</head>\n"
        '<body>\n'
        '<header class="page-header">\n'
        '  <div class="page-header-row page-header-row-1">\n'
        f'    <a class="home-link" href="/" title="Home — {escape(_PROJECT_NAME)}">{escape(_PROJECT_NAME)}</a>\n'
        '    <div id="cockpit-mode-slot" class="cockpit-mode-slot"></div>\n'
        '    <div id="cockpit-platform-slot" class="cockpit-platform-slot"></div>\n'
        '    <div id="cockpit-filter-slot" class="cockpit-filter-slot"></div>\n'
        '    <button class="theme-toggle" type="button" aria-label="Toggle light / dark theme" aria-pressed="false">◐</button>\n'
        '  </div>\n'
        + (
            '  <div class="page-header-row page-header-row-2">\n'
            '    <div id="cockpit-pin-slot" class="cockpit-pin-slot"></div>\n'
            f'    <nav class="breadcrumb" aria-label="Breadcrumb">{breadcrumb}</nav>\n'
            '  </div>\n'
            if breadcrumb else
            '  <div class="page-header-row page-header-row-2 is-empty">\n'
            '    <div id="cockpit-pin-slot" class="cockpit-pin-slot"></div>\n'
            '    <nav class="breadcrumb" aria-label="Breadcrumb"></nav>\n'
            '  </div>\n'
        )
        + "</header>\n"
        f"{body_block}"
        f'<footer class="page-footer">'
        f'<span class="brand-mark">project-os-cockpit</span>'
        f'<span class="version-mark">v{escape(_VERSION)}</span>'
        '</footer>\n'
        f"<script>{THEME_TOGGLE_SCRIPT}</script>\n"
        "</body>\n"
        "</html>\n"
    )


def notice_page(
    *,
    title: str,
    heading: str,
    body_html: str,
    error: bool = False,
) -> str:
    """Minimal page for 403 / 404 / placeholder content."""
    cls = "notice error" if error else "notice"
    body = (
        f'<div class="{cls}">\n'
        f"<h2>{escape(heading)}</h2>\n"
        f"{body_html}\n"
        "</div>\n"
    )
    return page(title=title, body_html=body)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _breadcrumb_html(rel_path: str, *, path_prefix: str = "/docs") -> str:
    parts = [p for p in PurePosixPath(rel_path).parts if p not in (".", "/")]
    if not parts:
        return f'<a href="/">docs</a>'

    crumbs: list[str] = [f'<a href="/">docs</a>']
    prefix = path_prefix.rstrip("/")
    accum = ""
    for i, part in enumerate(parts):
        accum = f"{accum}/{part}" if accum else part
        is_last = i == len(parts) - 1
        if is_last:
            crumbs.append(f"<span>{escape(part)}</span>")
        else:
            href = f"{prefix}/{accum}/" if prefix else f"/{accum}/"
            crumbs.append(f'<a href="{escape(href)}">{escape(part)}</a>')
    return '<span class="sep">/</span>'.join(crumbs)


def _metadata_strip_html(meta: dict[str, Any], resolver: Resolver | None) -> str:
    if not meta:
        return ""

    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for key in PRIMARY_META_KEYS:
        if key in HIDDEN_META_KEYS:
            continue
        if key in meta and meta[key] not in (None, "", [], {}):
            pairs.append((key, _render_meta_value(key, meta[key], resolver)))
            seen.add(key)

    for key, value in meta.items():
        if key in HIDDEN_META_KEYS or key in seen:
            continue
        if value in (None, "", [], {}):
            continue
        pairs.append((key, _render_meta_value(key, value, resolver)))

    if not pairs:
        return ""

    rows = "\n".join(
        f"  <dt>{escape(k)}</dt>\n  <dd>{v}</dd>"
        for k, v in pairs
    )
    return f'<aside class="metadata-strip"><dl>\n{rows}\n</dl></aside>\n'


def _render_meta_value(key: str, value: Any, resolver: Resolver | None) -> str:
    """Render a single frontmatter value as HTML.

    Status renders as a chip; lists render as comma-separated entries
    inside a wrapping span; scalar values render as text with wikilinks
    resolved when a ``resolver`` is provided. Wikilink-shaped strings go
    through the resolver like any other — including ``type: "[[feature]]"``,
    which will render as an unresolved (broken) wikilink unless a
    corresponding type-stub note exists. This matches Obsidian's behaviour.
    """
    if key == "status":
        return _status_chip(value)
    if isinstance(value, list):
        if not value:
            return ""
        items = [_render_scalar(v, resolver) for v in value]
        return '<span class="meta-list">' + ", ".join(items) + "</span>"
    if isinstance(value, dict):
        items = [
            f"{escape(str(k))}: {_render_scalar(v, resolver)}"
            for k, v in value.items()
        ]
        return '<span class="meta-list">' + ", ".join(items) + "</span>"
    return _render_scalar(value, resolver)


def _render_scalar(value: Any, resolver: Resolver | None) -> str:
    if value is None:
        return ""
    text = str(value)
    if resolver is None or not text:
        return escape(text)
    if "[[" in text:
        return resolve_text_to_html(text, resolver)
    # Bare project-os IDs — common in frontmatter when authors don't bother
    # with the wikilink form. Try resolving; fall back to plain text.
    if _PROJECT_OS_ID_RE.match(text):
        url = resolver(text)
        if url is not None:
            return f'<a href="{escape(url)}">{escape(text)}</a>'
    return escape(text)


def _status_chip(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(_status_chip(v) for v in value if v)
    text = str(value).strip()
    if not text:
        return ""
    slug = text.lower().replace(" ", "-")
    return f'<span class="status-chip" data-status="{escape(slug)}">{escape(text)}</span>'


# ---------------------------------------------------------------------------
# Index pages (TASK-0004)
# ---------------------------------------------------------------------------

# Lower rank = earlier in the page. Tuned to satisfy REQ-0007:
#   active/doing/in-progress first → backlog/triage middle → done/closed last.
STATUS_RANK: dict[str, int] = {
    # active / in-progress
    "active": 10, "doing": 11, "in-progress": 11, "next": 12,
    "approved": 13, "accepted": 13,
    # backlog
    "backlog": 30, "planned": 31, "proposed": 31, "draft": 32,
    "todo": 32, "open": 33, "pending": 33, "triage": 34, "reference": 35,
    # done
    "done": 60, "fixed": 60, "merged": 60, "published": 60,
    "verified": 65, "passing": 65,
    # dead / blocked
    "closed": 80, "obsolete": 81, "blocked": 90, "reopened": 91, "failing": 92,
}
STATUS_RANK_DEFAULT: int = 50

# Statuses whose collapsible group defaults to closed (still expandable).
COLLAPSED_BY_DEFAULT: frozenset[str] = frozenset(
    {"done", "fixed", "merged", "published", "verified", "passing",
     "closed", "obsolete"}
)


def index_page_html(
    *,
    type_label: str,        # "features", "tasks", ...
    type_singular: str,     # "feature", "task", ... (matches normalised type)
    notes: list,            # list[NoteRecord]
    docs_root_name: str,
) -> str:
    """Render an index page: notes of one type, grouped by status."""
    if not notes:
        body = (
            f'<h1>{escape(type_label.title())}</h1>\n'
            f'<p class="meta">No notes of type '
            f'<code>{escape(type_singular)}</code> found.</p>'
        )
        return page(
            title=f"index: {type_label}",
            body_html=body,
            rel_path=None,
            reload_source="*",
        )

    # Group by status.
    groups: dict[str, list] = {}
    for note in notes:
        key = note.status or "(no status)"
        groups.setdefault(key, []).append(note)

    # Sort within each group by note_id, then title, then path.
    for key in groups:
        groups[key].sort(
            key=lambda r: (r.note_id or "", r.title or "", r.rel_path)
        )

    # Sort groups by status rank.
    ordered = sorted(
        groups.items(),
        key=lambda kv: (STATUS_RANK.get(kv[0], STATUS_RANK_DEFAULT), kv[0]),
    )

    sections: list[str] = []
    for status, items in ordered:
        open_attr = "" if status in COLLAPSED_BY_DEFAULT else " open"
        rows = "\n".join(_index_row_html(n) for n in items)
        sections.append(
            f'<section class="index-group">\n'
            f'  <details{open_attr}>\n'
            f'    <summary>'
            f'<span class="status-chip" data-status="{escape(status)}">'
            f'{escape(status)}</span>'
            f'<span class="count">{len(items)}</span>'
            f'</summary>\n'
            f'    <ul class="index-items">\n{rows}\n    </ul>\n'
            f'  </details>\n'
            f'</section>'
        )

    body_html = (
        f'<h1>{escape(type_label.title())} '
        f'<span class="muted-count">({len(notes)})</span></h1>\n'
        f'<p class="meta">Index of <code>type: '
        f'[[{escape(type_singular)}]]</code> notes under '
        f'<code>{escape(docs_root_name)}/</code>, grouped by status.</p>\n'
        + "\n".join(sections)
    )
    return page(
        title=f"index: {type_label}",
        body_html=body_html,
        rel_path=None,
        reload_source="*",
    )


def _index_row_html(note) -> str:
    title = note.title or note.path.stem
    href = f"/docs/{note.rel_path}"
    id_part = (
        f'<span class="index-id">{escape(note.note_id)}</span> — '
        if note.note_id else ""
    )
    return (
        f'      <li>{id_part}'
        f'<a href="{escape(href)}">{escape(title)}</a></li>'
    )


def home_page_html(
    *,
    snapshot: dict | None,
    type_counts: dict[str, int],
    plural_for: dict[str, str],
    docs_root_name: str,
    feature_count_by_phase: dict[str, int] | None = None,
    readme_html: str | None = None,
    resolver: Resolver | None = None,
) -> str:
    """Synthesise the cockpit landing's centre-pane content.

    Priority:

    1. ``snapshot`` (parsed SNAPSHOT.yaml) → render the project overview
       (focus + phase progress + at-a-glance counts + recent changes).
    2. ``readme_html`` → use the rendered README if no snapshot.
    3. Minimal type-counts summary → never let ``/`` 404.

    The result is wrapped in the cockpit shell by the caller via
    :func:`page` with ``cockpit_active={}`` (no active note).
    """
    if snapshot is not None:
        body = _render_snapshot_home(
            snapshot, type_counts, plural_for, docs_root_name,
            feature_count_by_phase or {}, resolver,
        )
    elif readme_html:
        body = readme_html
    else:
        body = _render_minimal_home(type_counts, plural_for, docs_root_name)
    return page(
        title=docs_root_name,
        body_html=body,
        rel_path=None,
        reload_source="*",
        cockpit_active={},   # cockpit shell, but no active note
    )


def _render_snapshot_home(
    snapshot: dict,
    type_counts: dict[str, int],
    plural_for: dict[str, str],
    docs_root_name: str,
    feature_count_by_phase: dict[str, int],
    resolver: Resolver | None,
) -> str:
    sections: list[str] = []
    sections.append(f'<h1 class="home-title">{escape(docs_root_name)}</h1>')

    # ----- Focus -----
    focus = snapshot.get("focus") or {}
    focus_items: list[str] = []
    for label, key in (("Phase", "phase"), ("Feature", "feature"),
                       ("Task", "task"), ("Issue", "issue")):
        raw = focus.get(key)
        if not raw:
            continue
        link_html = _render_scalar(str(raw), resolver) if resolver else escape(str(raw))
        focus_items.append(
            f'  <div class="home-focus-row">'
            f'<span class="home-focus-label">{label}</span>'
            f'<span class="home-focus-value">{link_html}</span>'
            f'</div>'
        )
    if focus_items:
        sections.append(
            '<section class="home-focus">\n'
            '  <h2>Active focus</h2>\n'
            + "\n".join(focus_items) + "\n"
            "</section>"
        )

    # ----- Phase progress -----
    phases = (snapshot.get("items") or {}).get("phases") or {}
    if isinstance(phases, dict) and phases:
        sorted_phases = sorted(
            phases.items(),
            key=lambda kv: (
                _coerce_int(kv[1].get("order") if isinstance(kv[1], dict) else None) or 99,
                kv[0],
            ),
        )
        rows: list[str] = []
        for phase_id, body in sorted_phases:
            if not isinstance(body, dict):
                continue
            title = body.get("title") or phase_id
            status = body.get("status") or ""
            count = feature_count_by_phase.get(phase_id, 0)
            chip = (
                f'<span class="status-chip" data-status="{escape(status.lower())}">{escape(status)}</span>'
                if status else ""
            )
            link_html = _render_scalar(phase_id, resolver) if resolver else escape(phase_id)
            rows.append(
                f'  <li class="home-phase-row">'
                f'<span class="home-phase-id">{link_html}</span> '
                f'<span class="home-phase-title">{escape(title)}</span> '
                f'{chip} '
                f'<span class="muted-count">{count} feature{"s" if count != 1 else ""}</span>'
                f'</li>'
            )
        if rows:
            sections.append(
                '<section class="home-phases">\n'
                '  <h2>Phase progress</h2>\n'
                f'  <ul class="home-phase-list">\n{chr(10).join(rows)}\n  </ul>\n'
                "</section>"
            )

    # ----- At-a-glance counts -----
    metrics = (snapshot.get("metrics") or {}).get("counts") or {}
    if isinstance(metrics, dict) and metrics:
        sections.append(_render_metrics_grid(metrics))

    # ----- Recent changes -----
    changes = (snapshot.get("items") or {}).get("changes") or {}
    if isinstance(changes, dict) and changes:
        sorted_changes = sorted(changes.items(), reverse=True)[:5]
        rows: list[str] = []
        for chg_id, body in sorted_changes:
            if not isinstance(body, dict):
                continue
            title = body.get("title") or chg_id
            status = body.get("status") or ""
            chip = (
                f'<span class="status-chip" data-status="{escape(status.lower())}">{escape(status)}</span>'
                if status else ""
            )
            link_html = _render_scalar(chg_id, resolver) if resolver else escape(chg_id)
            rows.append(
                f'  <li class="home-change-row">'
                f'{chip} '
                f'<span class="home-change-id">{link_html}</span> '
                f'<span class="home-change-title">{escape(title)}</span>'
                f'</li>'
            )
        if rows:
            sections.append(
                '<section class="home-changes">\n'
                '  <h2>Recent changes</h2>\n'
                f'  <ul class="home-change-list">\n{chr(10).join(rows)}\n  </ul>\n'
                "</section>"
            )

    # ----- Browse-by-type fallback at bottom (always useful) -----
    sections.append(_render_index_links(type_counts, plural_for))

    return '<div class="cockpit-home">\n' + "\n".join(sections) + "\n</div>"


def _render_metrics_grid(metrics: dict) -> str:
    rows: list[str] = []

    def add(label: str, key_done: str | None, key_total: str | None,
            simple_key: str | None = None) -> None:
        if simple_key is not None:
            v = metrics.get(simple_key)
            if v is None:
                return
            rows.append(
                f'    <li class="home-metric"><span class="home-metric-label">{escape(label)}</span>'
                f'<span class="home-metric-value">{escape(str(v))}</span></li>'
            )
            return
        done = metrics.get(key_done)
        total = metrics.get(key_total)
        if done is None and total is None:
            return
        rows.append(
            f'    <li class="home-metric"><span class="home-metric-label">{escape(label)}</span>'
            f'<span class="home-metric-value">{escape(str(done or 0))} / {escape(str(total or 0))}</span></li>'
        )

    add("Features done", "features_done", "features_total")
    add("Tasks done", "tasks_done", "tasks_total")
    add("Tests passing", "tests_passing", "tests_total")
    add("Issues open", None, None, "issues_open")
    add("Risks open", None, None, "risks_open")
    add("Releases", None, None, "releases_total")
    add("Decisions", None, None, "decisions_total")
    if not rows:
        return ""
    return (
        '<section class="home-metrics">\n'
        '  <h2>At a glance</h2>\n'
        f'  <ul class="home-metric-grid">\n{chr(10).join(rows)}\n  </ul>\n'
        "</section>"
    )


def _render_index_links(type_counts: dict[str, int], plural_for: dict[str, str]) -> str:
    items: list[str] = []
    for type_singular in sorted(plural_for):
        plural = plural_for[type_singular]
        count = type_counts.get(type_singular, 0)
        if count == 0:
            continue   # synthesised home doesn't need to advertise empty types
        items.append(
            f'      <li><a href="/index/{escape(plural)}">'
            f'{escape(plural.title())}</a> '
            f'<span class="muted-count">({count})</span></li>'
        )
    if not items:
        return ""
    return (
        '<section class="home-indexes">\n'
        '  <h2>Browse by type</h2>\n'
        '  <ul class="index-list">\n' + "\n".join(items) + "\n  </ul>\n"
        "</section>"
    )


def _render_minimal_home(
    type_counts: dict[str, int],
    plural_for: dict[str, str],
    docs_root_name: str,
) -> str:
    return (
        f'<h1 class="home-title">{escape(docs_root_name)}</h1>\n'
        '<p class="meta">No SNAPSHOT.yaml or README.md found at the docs root. '
        'Browse the type indexes below to navigate the corpus.</p>\n'
        + _render_index_links(type_counts, plural_for)
    )


def _coerce_int(v) -> int | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v.strip())
        except ValueError:
            return None
    return None


def landing_page_html(
    *,
    type_counts: dict[str, int],
    plural_for: dict[str, str],
    docs_root_name: str,
    focus: dict[str, str] | None = None,
    resolver: Resolver | None = None,
) -> str:
    """The ``/`` landing page — counts per indexable type + focus surface."""
    items: list[str] = []
    # Drive the list off plural_for (the canonical set of indexable types) so
    # zero-count types still show up with (0) — gives the user a complete
    # taxonomy view at a glance.
    for type_singular in sorted(plural_for):
        plural = plural_for[type_singular]
        count = type_counts.get(type_singular, 0)
        items.append(
            f'      <li><a href="/index/{escape(plural)}">'
            f'{escape(plural.title())}</a> '
            f'<span class="muted-count">({count})</span></li>'
        )
    indices_html = (
        '<ul class="index-list">\n' + "\n".join(items) + "\n    </ul>"
        if items
        else '<p class="meta">No typed notes indexed yet.</p>'
    )

    focus_html = ""
    if focus:
        focus_rows = "\n".join(
            f'  <dt>{escape(k)}</dt>\n  <dd>{_render_scalar(v, resolver)}</dd>'
            for k, v in focus.items() if v
        )
        if focus_rows:
            focus_html = (
                '<aside class="metadata-strip">\n'
                '  <h2 class="meta-heading">Current focus</h2>\n'
                f'  <dl>\n{focus_rows}\n  </dl>\n'
                '</aside>\n'
            )

    body = (
        f'<h1>{escape(docs_root_name)}</h1>\n'
        f'<p class="meta">Project-os documentation tree. '
        f'Browse by type below, or open '
        f'<a href="/docs/">the filesystem listing</a>.</p>\n'
        f'{focus_html}'
        f'<h2>Indexes</h2>\n'
        f'    {indices_html}\n'
    )
    return page(
        title=docs_root_name,
        body_html=body,
        rel_path=None,
        reload_source="*",
    )


def directory_listing_html(entries: Iterable[tuple[str, str, bool]]) -> str:
    """Render a simple directory listing.

    ``entries`` is an iterable of ``(href, label, is_dir)`` tuples.
    """
    items: list[str] = []
    for href, label, is_dir in entries:
        cls = "dir" if is_dir else "file"
        items.append(
            f'<li class="{cls}"><a href="{escape(href)}">{escape(label)}</a></li>'
        )
    return '<ul class="dir-listing">\n' + "\n".join(items) + "\n</ul>"
