"""Guarded note write-back for the review desk (FEAT-0041).

Two mutations, both narrow by construction:

* :func:`stamp_review` — writes the three independent-review fields
  (``reviewed_by`` / ``review_date`` / ``review_verdict``), optionally
  with a guarded status transition.
* :func:`stamp_test_run` — writes a manual test's outcome (``status`` +
  ``last_run``) and appends a run log under ``## Runs``.

Everything else about a note is off-limits. That is a deliberate design
constraint rather than an implementation shortcut: PHASE-007 drew the
line at "the cockpit is a viewer", and ADR-0007 crosses it only far
enough to record a decision a human made in the UI. The allow-list below
is what keeps that crossing honest, and the tests assert it.

Hardening (TASK-0207 DoD, folded in from the preflight risk scan rather
than filed as a separate RISK):

* **Field allow-list** — a payload naming any other frontmatter key is
  rejected outright; the writer never merges caller-supplied dicts.
* **Guarded transitions** — a status must exist in ``statuses.py`` and be
  one of the transitions this module permits; anything else is a 4xx with
  nothing written.
* **Path canonicalisation** — targets resolve through the index and must
  land inside ``docs_root`` (the TASK-0174 case-canonicalisation
  precedent), so no traversal reaches the filesystem.
* **Concurrency** — an ``mtime`` precondition from the reader means a
  note edited underneath the reviewer fails loudly instead of silently
  clobbering the newer text.
* **Snapshot untouched** — ADR-0009: notes are the authored source, and
  ``sync-snapshot.py`` propagates at pre-commit. This module never edits
  SNAPSHOT.yaml.

The endpoints that call this refuse non-loopback callers — a per-request
peer-address check on the shared 0.0.0.0 socket, not a separate bind. The
distinction matters: the render server binds 0.0.0.0 so a tablet can read
the notes, and the guard is what keeps mutation off that surface (the
RISK-0001 threat model; the terminal endpoint gets a real second bind
because it can afford one).
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

from . import statuses
from .index import Index

#: The only frontmatter keys this module may create or overwrite.
REVIEW_FIELDS: frozenset[str] = frozenset({
    "reviewed_by", "review_date", "review_verdict",
})
TEST_RUN_FIELDS: frozenset[str] = frozenset({
    "status", "last_run", "last_verified",
})
#: `updated` is written by both paths — every note edit touches it, and
#: leaving it stale would make the corpus lie about its own freshness.
#: It is in the allow-list because it IS written, not as an exception.
BOOKKEEPING_FIELDS: frozenset[str] = frozenset({"updated"})

#: Fields a design review verdict may touch. `design_revision` records WHICH
#: revision was accepted — without it an approval given to v3 silently launders
#: v6, which is the one way a design review can be worse than none.
DESIGN_REVIEW_FIELDS: frozenset[str] = frozenset({
    "reviewed_by", "review_date", "review_verdict", "design_revision",
})

#: Fields a design capture may touch. Nothing about status or review — a
#: capture records that a revision happened, never that it was any good.
DESIGN_CAPTURE_FIELDS: frozenset[str] = frozenset({"updated"})

ALLOWED_FIELDS: frozenset[str] = (
    REVIEW_FIELDS | TEST_RUN_FIELDS | BOOKKEEPING_FIELDS | DESIGN_REVIEW_FIELDS
)

#: Request-body keys each endpoint accepts. Kept here beside the field
#: allow-list so the two cannot drift — an earlier cut duplicated these
#: as literals in `server.py`, which meant the exported allow-list was
#: decorative (independent review, 2026-07-26).
REVIEW_REQUEST_KEYS: frozenset[str] = frozenset({
    "id", "reviewer", "verdict", "status", "mtime",
})
TEST_RUN_REQUEST_KEYS: frozenset[str] = frozenset({
    "id", "outcome", "steps", "runner", "mtime", "aborted",
})
DECIDE_REQUEST_KEYS: frozenset[str] = frozenset({
    "id", "reviewer", "accept", "mtime",
})

#: Plan acceptance must never be mistaken for close-out independent
#: review. Close-out writes `approved` (QUALITY.md); the desk writes
#: `plan-accepted`, so the close-out gate cannot be satisfied by having
#: had one's plan approved — recorded as an ADR-0007 consequence.
PLAN_ACCEPTED_VERDICT = "plan-accepted"
PLAN_REJECTED_VERDICT = "plan-rejected"
DESK_VERDICTS: frozenset[str] = frozenset({
    PLAN_ACCEPTED_VERDICT, PLAN_REJECTED_VERDICT,
})
CLOSE_OUT_VERDICTS: frozenset[str] = frozenset({"approved", "changes-requested"})

#: Note types whose `review_verdict` the *close-out* gate reads
#: (ADR-0011 checks tests and changes for an independent-review stamp).
#: The desk must never write a verdict onto one of these: the validator
#: accepts any non-`changes-requested` value, so a plan stamp landing on
#: a TST or CHG would silence a gate it never satisfied. Refusing by type
#: closes the hole that refusing the string `approved` only narrowed
#: (independent review, 2026-07-26).
GATE_BEARING_TYPES: frozenset[str] = frozenset({"test", "change"})

#: Status transitions this module may perform. Rejecting a proposal set
#: is the only status write the review path needs; the runner writes test
#: outcomes. Everything else stays a human edit in the note.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "review": frozenset({"cancelled"}),
    "test-run": frozenset({"passing", "failing"}),
}

#: Deciding a *lone* queued note is a real lifecycle move, and the move
#: differs by type — which is why the set-review path's single `cancelled`
#: transition left ADR-0007 and every draft requirement un-actionable
#: (reported 2026-07-26). Each entry is (accept, decline), drawn from that
#: type's own vocabulary in STATUSES.md:
#:
#: * ADR — `proposed → accepted`. There is no "reject": STATUSES.md is
#:   explicit that a decision not taken is *deleted or superseded*, never
#:   marked rejected, because a rejected proposal worth keeping is worth
#:   recording as the alternative it lost to.
#: * Requirement — `draft → approved`, or `cancelled` if it will not be built.
#: The design statuses this module knows how to reason about. Used for ONE
#: thing: failing closed on a status it has never seen, which otherwise got
#: silently demoted.
#:
#: This was a rank table until independent review proved the ranks were dead —
#: replacing the whole backwards comparison with `False` left all 496 tests
#: passing, because accept's candidate is `accepted` and every status ranking
#: above it is in `_DESIGN_SETTLED`, which is checked first. The comment said
#: the ranks refused a move that would rewrite history; `_DESIGN_SETTLED`
#: refuses it. Keeping ordering nobody consults, under a comment claiming it
#: guards something, is the exact defect this review kept finding elsewhere.
_DESIGN_KNOWN_STATUSES: frozenset[str] = frozenset({
    "draft", "proposed", "accepted", "implemented", "superseded", "cancelled",
})

#: Statuses a review verdict must never move a design out of. Rank alone
#: cannot express this: `cancelled` ranks ABOVE `implemented`, so cancelling a
#: shipped design reads as a FORWARD move (independent review round 3). A
#: design that shipped cannot be un-shipped by a verdict — deciding to replace
#: it is a new design or an issue, not a status flip on the old one.
_DESIGN_SETTLED: frozenset[str] = frozenset({
    "implemented", "superseded", "cancelled",
})

DECIDE_TRANSITIONS: dict[str, tuple[str, str | None]] = {
    "adr": ("accepted", "superseded"),
    "decision": ("accepted", "superseded"),
    "requirement": ("approved", "cancelled"),
    # A design that is accepted is not yet built — `implemented` is what the
    # code shipping means, and only TASK-0219's parity check can honestly
    # claim it. Rejecting a design `cancelled` rather than `superseded`,
    # because superseded means a LATER design replaced it, which is a
    # different fact about the future.
    "design": ("accepted", "cancelled"),
}


class WriteError(Exception):
    """Refusal with a caller-facing reason. Never partially applied."""

    def __init__(self, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def _today() -> str:
    return _dt.date.today().isoformat()


def resolve_note(index: Index, note_id: str) -> Path:
    """Resolve an id to a path inside the docs tree, or refuse.

    Resolution goes through the index (never string concatenation), and
    the result is re-checked against ``docs_root`` so a symlink or a
    crafted alias cannot escape (TASK-0174 precedent).
    """
    if not isinstance(note_id, str) or not note_id.strip():
        raise WriteError("missing note id")
    path = index.by_id(note_id.strip())
    if path is None:
        raise WriteError(f"unknown note: {note_id}", status=404)
    try:
        resolved = path.resolve()
        root = index.docs_root.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        raise WriteError("note resolves outside the docs tree", status=403) from None
    if resolved.suffix.lower() != ".md":
        raise WriteError("not a markdown note", status=400)
    return resolved


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    """Return (frontmatter lines, body). Refuses a note without one —
    writing frontmatter into a note that has none would restructure it."""
    if not text.startswith("---\n"):
        raise WriteError("note has no frontmatter block", status=409)
    end = text.find("\n---", 3)
    if end == -1:
        raise WriteError("unterminated frontmatter block", status=409)
    fm_block = text[4:end]
    rest = text[end + len("\n---"):]
    if rest.startswith("\n"):
        rest = rest[1:]
    return fm_block.splitlines(), rest


#: A key introducing a block scalar (`status: >` / `|`) or an empty value
#: that opens a nested block. Replacing only the key's own line would
#: orphan the indented continuation lines beneath it and produce invalid
#: YAML — refuse instead of corrupting (independent review, 2026-07-26).
_BLOCK_OPENER_RE = re.compile(r":\s*([|>][+-]?\d*)?\s*$")


def _get_field(lines: list[str], key: str) -> str:
    """A scalar frontmatter value, or "" — enough to read a status back."""
    prefix = key + ":"
    for line in lines:
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def _set_field(lines: list[str], key: str, value: str) -> list[str]:
    """Replace ``key``'s line in place, or append it.

    Only the one top-level key is touched: the `^` anchor means nested
    keys and keys quoted inside list values are left byte-identical. A
    key whose value is a block scalar or an opened nested block is
    refused rather than rewritten, because its continuation lines are
    not on the line being replaced.
    """
    pattern = re.compile(rf"^{re.escape(key)}\s*:", re.IGNORECASE)
    rendered = f'{key}: "{value}"'
    for i, line in enumerate(lines):
        if not pattern.match(line):
            continue
        follows_indented = (
            i + 1 < len(lines)
            and lines[i + 1][:1].isspace()
            and lines[i + 1].strip() != ""
        )
        if _BLOCK_OPENER_RE.search(line) and follows_indented:
            raise WriteError(
                f"{key!r} holds a multi-line value; refusing to rewrite it "
                "in place — edit the note directly",
                status=409,
            )
        lines[i] = rendered
        return lines
    lines.append(rendered)
    return lines


def _check_mtime(path: Path, expected: float | None) -> None:
    if expected is None:
        return
    try:
        actual = path.stat().st_mtime
    except OSError as exc:
        raise WriteError(f"cannot stat note: {exc}", status=500) from None
    # Filesystem mtimes are float seconds; compare with a tolerance well
    # under a human edit but above timestamp granularity.
    if abs(actual - float(expected)) > 0.01:
        raise WriteError(
            "note changed on disk since it was read — reload and retry",
            status=409,
        )


def _write(path: Path, fm_lines: list[str], body: str) -> None:
    text = "---\n" + "\n".join(fm_lines) + "\n---\n" + body
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def stamp_review(
    index: Index,
    note_id: str,
    *,
    reviewer: str,
    verdict: str,
    status: str | None = None,
    mtime: float | None = None,
) -> dict[str, Any]:
    """Write the three review fields, optionally with a status transition.

    ``verdict`` must be the desk's plan-acceptance value — the close-out
    vocabulary is refused here so a plan approval can never satisfy the
    verification gate QUALITY.md guards.
    """
    if verdict in CLOSE_OUT_VERDICTS:
        raise WriteError(
            f"{verdict!r} is the close-out review vocabulary; the desk writes "
            f"{PLAN_ACCEPTED_VERDICT!r} so plan acceptance cannot satisfy the "
            "close-out gate",
            status=400,
        )
    if verdict not in DESK_VERDICTS:
        raise WriteError(f"unsupported verdict: {verdict}", status=400)
    if not reviewer.strip():
        raise WriteError("missing reviewer")

    path = resolve_note(index, note_id)
    record = index.get(path)
    note_type = (getattr(record, "note_type", "") or "").lower()
    if note_type in GATE_BEARING_TYPES:
        raise WriteError(
            f"{note_id} is a {note_type} note — the close-out review gate reads "
            "its review_verdict, so the desk will not stamp one; review it "
            "through close-out instead",
            status=403,
        )
    _check_mtime(path, mtime)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteError(f"cannot read note: {exc}", status=500) from None
    fm_lines, body = _split_frontmatter(text)

    if status is not None:
        _guard_transition("review", status)
        fm_lines = _set_field(fm_lines, "status", status)
    fm_lines = _set_field(fm_lines, "reviewed_by", reviewer.strip())
    fm_lines = _set_field(fm_lines, "review_date", _today())
    fm_lines = _set_field(fm_lines, "review_verdict", verdict)
    fm_lines = _set_field(fm_lines, "updated", _today())
    _write(path, fm_lines, body)
    return {
        "id": note_id, "rel": str(path.relative_to(index.docs_root.resolve())),
        "review_verdict": verdict, "status": status,
    }


def stamp_decision(
    index: Index,
    note_id: str,
    *,
    reviewer: str,
    accept: bool,
    mtime: float | None = None,
) -> dict[str, Any]:
    """Decide a single queued note: advance it, or decline it.

    Unlike :func:`stamp_review` — which records a verdict on a *set* whose
    notes stay where they are — this performs the lifecycle move the note
    is queued for, so the transition is validated against that type's own
    vocabulary rather than a shared allow-list.

    Gate-bearing types are refused here too: a test or change reaching this
    path would mean the desk deciding something close-out owns.
    """
    path = resolve_note(index, note_id)
    record = index.get(path)
    note_type = (getattr(record, "note_type", "") or "").lower()
    if note_type in GATE_BEARING_TYPES:
        raise WriteError(
            f"{note_id} is a {note_type} note — decided at close-out, not here",
            status=403,
        )
    pair = DECIDE_TRANSITIONS.get(note_type)
    if pair is None:
        raise WriteError(
            f"{note_type or 'this'} notes are not decided from the review desk",
            status=400,
        )
    target = pair[0] if accept else pair[1]
    if target is None:
        raise WriteError(
            f"{note_type} notes have no decline transition", status=400,
        )
    normalised = target.lower()
    if normalised not in statuses.VOCABULARY:
        raise WriteError(
            f"{target!r} is not in the project-os status vocabulary", status=400,
        )
    if not reviewer.strip():
        raise WriteError("missing reviewer")

    _check_mtime(path, mtime)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteError(f"cannot read note: {exc}", status=500) from None
    fm_lines, body = _split_frontmatter(text)
    fm_lines = _set_field(fm_lines, "status", normalised)
    fm_lines = _set_field(fm_lines, "reviewed_by", reviewer.strip())
    fm_lines = _set_field(fm_lines, "review_date", _today())
    # ADR-0007 names the future gate predicate as "has an accepting
    # `review_verdict`", not a status check. Writing it here keeps a
    # lone-note decision legible to that gate if the advisory phase ever
    # promotes — and legible to the measurement in the meantime.
    fm_lines = _set_field(
        fm_lines, "review_verdict",
        PLAN_ACCEPTED_VERDICT if accept else PLAN_REJECTED_VERDICT,
    )
    fm_lines = _set_field(fm_lines, "updated", _today())
    _write(path, fm_lines, body)
    return {
        "id": note_id, "status": normalised, "accepted": accept,
        "review_verdict": PLAN_ACCEPTED_VERDICT if accept else PLAN_REJECTED_VERDICT,
    }


def _guard_transition(kind: str, status: str) -> None:
    normalised = (status or "").strip().lower()
    if normalised not in statuses.VOCABULARY:
        raise WriteError(
            f"{status!r} is not in the project-os status vocabulary", status=400,
        )
    allowed = ALLOWED_TRANSITIONS.get(kind, frozenset())
    if normalised not in allowed:
        raise WriteError(
            f"{status!r} is not a transition this endpoint may perform "
            f"(allowed: {sorted(allowed)})",
            status=403,
        )


def stamp_test_run(
    index: Index,
    note_id: str,
    *,
    outcome: str,
    steps: list[dict[str, Any]],
    runner: str = "",
    mtime: float | None = None,
    aborted: bool = False,
) -> dict[str, Any]:
    """Record a manual test run: status + ``last_run`` and a ``## Runs`` log.

    An aborted run writes **no status** — a half-finished run is not
    evidence either way — but its partial log is still appended, marked
    aborted, because "we started and stopped here" is worth keeping.
    """
    path = resolve_note(index, note_id)
    _check_mtime(path, mtime)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteError(f"cannot read note: {exc}", status=500) from None
    fm_lines, body = _split_frontmatter(text)

    today = _today()
    if not aborted:
        _guard_transition("test-run", outcome)
        fm_lines = _set_field(fm_lines, "status", outcome)
        fm_lines = _set_field(fm_lines, "last_run", today)
        if outcome == "passing":
            fm_lines = _set_field(fm_lines, "last_verified", today)
    fm_lines = _set_field(fm_lines, "updated", today)

    body = _append_run_log(
        body, today=today, outcome="aborted" if aborted else outcome,
        steps=steps, runner=runner,
    )
    _write(path, fm_lines, body)
    return {
        "id": note_id, "outcome": "aborted" if aborted else outcome,
        "last_run": None if aborted else today,
    }


_RUNS_HEADING_RE = re.compile(r"^##\s+Runs\s*$", re.IGNORECASE | re.MULTILINE)
_REVISIONS_HEADING_RE = re.compile(r"^##\s+Revisions\s*$", re.IGNORECASE | re.MULTILINE)


def _append_run_log(
    body: str, *, today: str, outcome: str,
    steps: list[dict[str, Any]], runner: str,
) -> str:
    """Append one run under ``## Runs``, creating the section if absent.

    Newest last: the section reads as a chronological log, which is how a
    "has this ever passed, and when did it start failing?" question gets
    answered by scrolling rather than by diffing git.
    """
    lines = [f"### {today} — {outcome}" + (f" (by {runner})" if runner else "")]
    for step in steps:
        result = str(step.get("result") or "").strip() or "—"
        text = str(step.get("text") or "").strip()
        entry = f"- **{result}** · {text}"
        evidence = str(step.get("evidence") or "").strip()
        if evidence:
            entry += f" — {evidence}"
        lines.append(entry)
    block = "\n".join(lines)

    match = _RUNS_HEADING_RE.search(body)
    if not match:
        return body.rstrip("\n") + "\n\n## Runs\n\n" + block + "\n"
    # Insert at the END of the Runs section — which is not the end of the
    # body unless Runs happens to be the last heading. Appending blindly
    # filed runs under whatever section followed (independent review,
    # 2026-07-26).
    rest = body[match.end():]
    next_heading = re.search(r"^##\s", rest, re.MULTILINE)
    cut = match.end() + (next_heading.start() if next_heading else len(rest))
    head, tail = body[:cut], body[cut:]
    return head.rstrip("\n") + "\n\n" + block + "\n\n" + tail.lstrip("\n")


_REVIEW_HEADING_RE = re.compile(r"^##\s+Review\s*$", re.IGNORECASE | re.MULTILINE)

#: One comment line. Parsed back out so the surface can render pins, which is
#: why the shape is fixed rather than free prose — but it stays readable as
#: Markdown, because REQ-0023's "readable without the tool" clause covers the
#: comments, not just the verdicts.
_COMMENT_RE = re.compile(
    r"^- \*\*(?P<region>[^*]+)\*\* · (?P<date>\d{4}-\d{2}-\d{2})"
    r"(?: · (?P<author>[^—]+?))? — (?P<text>.+)$",
    re.MULTILINE,
)


def append_design_comment(
    body: str, *, region: str, date: str, author: str, text: str,
) -> str:
    """Add one region-anchored comment under ``## Review``.

    The anchor is a **region id, never a coordinate**. Pixel pins die on the
    next revision, and the founding artifact went through six in one session —
    coordinate anchoring would have produced a comment set that was worthless
    by v2.

    A region of ``""`` is the document-level lane, for criticism that has no
    region: "too much violet everywhere", or a complaint about the relationship
    between two areas. Inventing a region to host those would make the region
    list a fiction.
    """
    label = region.strip() or "(document)"
    who = f" · {author.strip()}" if author.strip() else ""
    entry = f"- **{label}** · {date}{who} — {text.strip()}"
    match = _REVIEW_HEADING_RE.search(body)
    if not match:
        return body.rstrip("\n") + "\n\n## Review\n\n" + entry + "\n"
    rest = body[match.end():]
    next_heading = re.search(r"^##\s", rest, re.MULTILINE)
    cut = match.end() + (next_heading.start() if next_heading else len(rest))
    head, tail = body[:cut], body[cut:]
    return head.rstrip("\n") + "\n" + entry + "\n\n" + tail.lstrip("\n")


def read_design_comments(body: str) -> list[dict[str, str]]:
    """Parse ``## Review`` back into comments, in written order."""
    match = _REVIEW_HEADING_RE.search(body)
    if not match:
        return []
    rest = body[match.end():]
    next_heading = re.search(r"^##\s", rest, re.MULTILINE)
    section = rest[:next_heading.start()] if next_heading else rest
    out = []
    for m in _COMMENT_RE.finditer(section):
        region = m.group("region").strip()
        out.append({
            "region": "" if region == "(document)" else region,
            "date": m.group("date"),
            "author": (m.group("author") or "").strip(),
            "text": m.group("text").strip(),
        })
    return out


def stamp_design_verdict(
    index: Index,
    note_id: str,
    *,
    reviewer: str,
    verdict: str,
    revision: str,
    accept: bool | None = None,
    mtime: float | None = None,
) -> dict[str, Any]:
    """Record a design review verdict, pinned to the revision it judged.

    ``design_revision`` is the field that makes this honest. A verdict given to
    v3 says nothing about v6, and a design surface that lost that distinction
    would let an old approval launder a new design — the one way a design
    review is worse than no review at all.

    ``accept`` optionally advances the status through ``DECIDE_TRANSITIONS``:
    ``accepted`` or ``cancelled``. Note that accepting a design does **not**
    make it ``implemented`` — that is what the code shipping means, and only
    the parity check can honestly claim it.
    """
    path = resolve_note(index, note_id)
    record = index.get(path)
    note_type = (getattr(record, "note_type", "") or "").lower()
    if note_type != "design":
        raise WriteError(f"{note_id} is a {note_type or 'note'}, not a design",
                         status=409)
    _check_mtime(path, mtime)

    text = path.read_text(encoding="utf-8")
    fm_lines, body = _split_frontmatter(text)
    today = _dt.date.today().isoformat()

    fm_lines = _set_field(fm_lines, "reviewed_by", reviewer)
    fm_lines = _set_field(fm_lines, "review_date", today)
    fm_lines = _set_field(fm_lines, "review_verdict", verdict)
    fm_lines = _set_field(fm_lines, "design_revision", revision)
    fm_lines = _set_field(fm_lines, "updated", today)

    new_status = None
    if accept is not None:
        transitions = DECIDE_TRANSITIONS["design"]
        candidate = transitions[0] if accept else transitions[1]
        # Never move a design BACKWARDS (ISS-0056 round 2). `accepted` means
        # "agreed, not yet built"; `implemented` means the code shipped. A
        # design at `implemented` that is accepted at a revision would be
        # demoted to a status that is no longer true — and every design that
        # can be offered for review today is `implemented`, which is this
        # feature's own premise. The verdict is still recorded; only the
        # status move is declined, because the verdict is the honest part.
        current = str(_get_field(fm_lines, "status") or "").strip().strip('"')
        # Settled first, and for BOTH verdicts. The round-2 fix guarded only
        # `accept`, so Reject still wrote `cancelled` over `implemented` — the
        # mirror of the bug it fixed, and invisible to rank because `cancelled`
        # sits above `implemented`.
        if current in _DESIGN_SETTLED:
            new_status = None
        else:
            # Unknown status fails CLOSED — it used to be demoted silently.
            known = current in _DESIGN_KNOWN_STATUSES or not current
            new_status = candidate if known else None
        if new_status:
            fm_lines = _set_field(fm_lines, "status", new_status)

    path.write_text("---\n" + "\n".join(fm_lines) + "\n---\n" + body,
                    encoding="utf-8")
    return {"ok": True, "id": note_id, "verdict": verdict,
            "design_revision": revision, "status": new_status}


def append_revision_log(body: str, *, date: str, reason: str) -> str:
    """Record one revision under ``## Revisions`` (TASK-0220).

    Not redundant with git, for three reasons found in review:

    * **The asset diff is noise.** Two regenerated 139KB HTML files diff as a
      wall of changes, so the reasoning between revisions collapses to the
      commit subject. One line here is the only readable record.
    * **Git history is invisible to the validator**, and a squash or rebase
      destroys it silently. A log in the note is checkable.
    * REQ-0023's "readable without the tool" clause covered comments and
      verdicts but not the *process*. This closes that.

    Newest last, matching ``## Runs`` — a chronological log answers "when did
    this start looking wrong?" by scrolling rather than by bisecting.

    **No commit sha.** An entry cannot name the commit that contains it: write
    the sha, commit, and the sha is already stale; amend to correct it and the
    amend changes it again. That is self-reference, not a bug to code around.
    So the note records the *reason* and git records the *revision*, and they
    are paired by order and date — which also means the pairing survives a
    rebase that rewrites every sha.
    """
    entry = f"- {date} — {reason.strip()}"
    match = _REVISIONS_HEADING_RE.search(body)
    if not match:
        return body.rstrip("\n") + "\n\n## Revisions\n\n" + entry + "\n"
    # Insert at the end of the Revisions SECTION, not the end of the body —
    # the same bug an independent review caught in the run log on 2026-07-26.
    rest = body[match.end():]
    next_heading = re.search(r"^##\s", rest, re.MULTILINE)
    cut = match.end() + (next_heading.start() if next_heading else len(rest))
    head, tail = body[:cut], body[cut:]
    return head.rstrip("\n") + "\n" + entry + "\n\n" + tail.lstrip("\n")


def draft_issue_body(
    test_id: str, test_title: str, step: dict[str, Any],
) -> dict[str, str]:
    """Shape a failing step into an issue-intake draft (TASK-0209).

    Returned as data for the user to confirm — the desk never files an
    ISS on its own, because allocating an id is a documentation decision
    and LIFECYCLE puts that in preflight, not in a UI callback.
    """
    expected = str(step.get("expected") or "").strip() or "(not recorded in the test)"
    observed = str(step.get("evidence") or "").strip() or "(not recorded)"
    title = f"{test_title or test_id} — step {step.get('n')} failed"
    body = (
        f"Found while running [[{test_id}]] manually from the review desk.\n\n"
        f"**Step {step.get('n')}:** {str(step.get('text') or '').strip()}\n\n"
        f"**Expected:** {expected}\n\n"
        f"**Observed:** {observed}\n"
    )
    return {"title": title, "body": body, "test_id": test_id}
