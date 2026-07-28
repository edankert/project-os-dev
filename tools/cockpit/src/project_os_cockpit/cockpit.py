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

from . import statuses
from . import token_sources
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
    "deprecated",
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
    "design", "features", "tasks", "issues", "active", "recent", "library",
)

# Active mode (FEAT-0036 / TASK-0164) — in-flight items across all types.
_ACTIVE_DOING: frozenset[str] = frozenset({
    "doing", "in_progress", "review", "active",
    "mitigating", "reproducing", "reopened", "blocked", "failing",
})
_ACTIVE_NEXT: frozenset[str] = frozenset({
    "next", "ready", "planned", "approved", "accepted", "triage",
})
_ACTIVE_DONE: frozenset[str] = frozenset(statuses.COMPLETED_STATUSES)
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

# Reference notes living here are *design input* — dossiers, mockups and
# research a feature was built from (TASK-0212). They surface as their own
# Library group and lead the record column's Library card.

# Types that already have their own UX surface elsewhere (dedicated nav
# modes or rare-type groups) and therefore do NOT appear in the Library
# "By type" auto-discovery section. Without this skip-set, personal
# vaults with `task` notes would end up with a duplicate Tasks group in
# Library on top of the Tasks mode.
_BY_TYPE_SKIP_IN_LIBRARY: frozenset[str] = frozenset({
    "feature", "issue", "requirement", "phase", "task",
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
    "test": PASSING,
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
        "sections": sections,
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

    def _slim(rec: Any, kind: str) -> dict[str, Any]:
        slim = {
            "id": rec.note_id,
            "title": rec.title or rec.note_id or "",
            "rel": rec.rel_path,
            "status": rec.status or "",
            "bucket": _status_bucket(rec),
            "type": kind,
        }
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
    child_records = [*tasks, *requirements, *issues]
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
            {"key": "runs", "label": "Test runs", "items": runs},
        ],
    }


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

    link_fields = ("features", "verifies", "validates", "tests", "parent",
                   "implements", "related", "phase")

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

    return {
        "schema_version": SCHEMA_VERSION,
        "tests": out,
        "decisions": decisions,
    }


def _is_manual_test(record: NoteRecord) -> bool:
    """Manual tests are the ones a human can run from the desk.

    Convention: frontmatter ``automation``/``kind``/``mode`` saying manual,
    or a body with a Steps section and no automated-runner reference.
    """
    fm = record.frontmatter
    for key in ("automation", "kind", "mode", "method"):
        value = str(fm.get(key) or "").lower()
        if "manual" in value:
            return True
        if value in ("automated", "auto", "ci"):
            return False
    return bool(manual_test_steps(record.body))


# Manual tests in the wild head their procedure several ways — this repo's
# own TST-0011 uses "Checklist", the template suggests "Steps". Accepting
# the corpus's vocabulary rather than one canonical spelling is the same
# lesson ADR-0006 recorded: a surface follows what is written, not what a
# convention wishes were written.
_STEP_HEADING_RE = re.compile(
    r"^#{2,6}\s*(steps|checklist|procedure|scenario|script)\b", re.IGNORECASE,
)
_ANY_HEADING_RE = re.compile(r"^#{1,6}\s")
_STEP_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s*(?:\[[ xX]\]\s*)?(.+)$")
_EXPECTED_RE = re.compile(r"^\s*(?:expect(?:ed|s)?|then)\s*[:：]\s*(.*)$", re.IGNORECASE)
# An inline "… Expect: <what should happen>" clause inside a step line.
_INLINE_EXPECT_RE = re.compile(r"\bexpect(?:ed|s)?\s*[:：]\s*(.+)$", re.IGNORECASE)
# Markdown emphasis is noise in a stepper's one-line label.
_MD_EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)(.+?)\1")


def manual_test_steps(body: str) -> list[dict[str, Any]]:
    """Parse a manual test's procedure section into ordered steps.

    Same shape as ``_exit_criteria_from_body`` — tolerant of heading level
    and list marker. An indented ``Expected:`` line, or an inline
    ``… Expect: …`` clause, attaches to its step as the expectation the
    runner shows beside Pass/Fail.
    """
    steps: list[dict[str, Any]] = []
    in_section = False
    for line in (body or "").splitlines():
        if in_section and _ANY_HEADING_RE.match(line):
            break
        if _STEP_HEADING_RE.match(line):
            in_section = True
            continue
        if not in_section:
            continue
        expected = _EXPECTED_RE.match(line)
        if expected and steps:
            steps[-1]["expected"] = expected.group(1).strip()
            continue
        item = _STEP_ITEM_RE.match(line)
        if not item:
            continue
        text = item.group(1).strip()
        if not text:
            continue
        step: dict[str, Any] = {"n": len(steps) + 1, "text": text}
        # "Do the thing. Expect: it works" on one line — the shape this
        # repo's own manual tests actually use.
        inline = _INLINE_EXPECT_RE.search(text)
        if inline:
            step["text"] = text[:inline.start()].rstrip(" .—-–")
            step["expected"] = inline.group(1).strip()
        step["text"] = _MD_EMPHASIS_RE.sub(r"\2", str(step["text"])).strip()
        if "expected" in step:
            step["expected"] = _MD_EMPHASIS_RE.sub(r"\2", step["expected"]).strip()
        if step["text"]:
            steps.append(step)
    return steps


def _design_groups(index: Index, platform: str | None) -> list[dict[str, Any]]:
    """Nav groups for the design mode (TASK-0224).

    The design *system* is separated from proposals because they behave
    differently: a project has one system that never leaves, and many
    proposals that arrive, get decided and go quiet. Listing them together
    would bury the standing reference among transient ones.
    """
    systems, proposals = [], []
    for r in sorted(index.notes_by_type("design"),
                    key=lambda r: (r.note_id or "", r.rel_path)):
        if not _platform_match(r, platform):
            continue
        role = (r.frontmatter or {}).get("role")
        item = {**_rare_item(index, r), "url": f"~design/{r.note_id}"}
        (systems if role == "system" else proposals).append(item)

    out: list[dict[str, Any]] = []
    if systems:
        out.append({"key": "design-system", "label": "Design system", "url": None,
                    "status": None, "item_layout": "stacked", "items": systems})
    if proposals:
        out.append({"key": "design-proposals", "label": "Designs", "url": None,
                    "status": None, "item_layout": "stacked", "items": proposals})
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
    if m not in NAV_MODES:
        m = DEFAULT_MODE
    plat = _normalise_platform(platform)

    if m == "design":
        groups = _design_groups(index, plat)
    elif m == "features":
        groups = _features_groups(index, plat)
    elif m == "tasks":
        groups = _tasks_groups(index, plat)
    elif m == "issues":
        groups = _issues_groups(index, plat)
    elif m == "active":
        groups = _active_groups(index, plat)
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
        **_verification_flags(record),
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

    # ----- Design input (TASK-0212) -----
    # Reference notes under `references/design/` wrap the dossiers and
    # mockups a feature was built from. They get their own group rather
    # than merging into the Docs tree because "what shaped this?" is a
    # question people ask directly, and the answer is otherwise buried
    # three folders deep. The notes stay ordinary references — this is a
    # grouping over an existing type, not a new one.
    # Membership by TYPE, not by path. This was `notes_by_type("reference")`
    # filtered through a `references/design/` regex until the `[[design]]` type
    # landed upstream (project-os-dev FEAT-0019) -- a design note that lived
    # anywhere else was invisible, and a reference that happened to sit in that
    # folder was mislabelled a design. The type is the claim; the path is where
    # someone happened to put the file.
    design_records = [
        r for r in index.notes_by_type("design")
        if _platform_match(r, platform)
    ]
    if design_records:
        design_records.sort(key=lambda r: (r.note_id or "", r.rel_path))
        out.append({
            "key": "design",
            "label": "Design",
            "url": None,
            "status": None,
            "item_layout": "stacked",
            # Point at the BENCH, not the note. The note is prose about a
            # design; the artifact is the design. A Library entry that opened
            # the note left the render surface with no door into it — built,
            # tested, and unreachable (found by Edwin, 2026-07-28).
            "items": [
                {**_rare_item(index, r), "url": f"~design/{r.note_id}"}
                for r in design_records if r.note_id
            ],
        })

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

    # ----- By type — auto-discovered (personal-vault types like Panel,
    #       Character, Daily, etc.). Each group nests items under their
    #       parent note via an auto-detected frontmatter field.
    out.extend(_library_by_type_groups(index, platform))

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


def _feature_item(index: Index, record: NoteRecord) -> dict[str, Any]:
    return {
        "id": record.note_id,
        "title": record.title or record.path.stem,
        "status": record.status,
        "url": index.url_for(record.path),
        "subtitle": record.frontmatter.get("goal") or "",
        "type": record.note_type or "feature",
        **_verification_flags(record),
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
