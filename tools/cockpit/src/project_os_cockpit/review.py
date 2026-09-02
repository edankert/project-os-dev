"""Review queue store — the desk's runtime state (FEAT-0041).

The ~review desk shows two kinds of thing, and they are stored very
differently on purpose:

* **Durable record** — statuses, review verdicts, run logs. Those live in
  the notes, written through the review/test-run endpoints, and are what
  survives once the queue empties. Nothing here.
* **Transient queue** — "this proposal set is waiting for a human",
  "the agent asked a question". Those live *here*, in
  ``.cockpit/review-requests.json``, and never touch note frontmatter.

That split is the ADR-0007 mechanism, chosen by the owner on 2026-07-26
to avoid inventing new statuses: pending-ness is runtime state (the same
philosophy as REQ-0018's attention items), while the verdict a human
reaches is recorded in the note through the existing independent-review
fields. A feature awaiting review therefore sits at plain ``backlog``,
exactly as it did before the desk existed.

The store is deliberately small and file-backed: a proposal can wait days
across sidecar restarts, so the session ledger (which is session-scoped)
is the wrong home for it. Dispatch records still *reference* these
requests — filing one records a dispatch entry too, so the provenance
chain from prompt → session → request stays intact.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import threading
import uuid
from pathlib import Path
from typing import Any

#: Request kinds the queue understands. `review` is a proposal set
#: awaiting accept/reject; `question` is the agent asking the human
#: something and blocking on the answer.
#: `annotation` is a comment anchored to a place on a design (FEAT-0069):
#: not a proposal to accept and not a question blocking an agent, but a note
#: pinned to a spot that a later revision may move or delete.
KINDS: tuple[str, ...] = ("review", "question", "annotation")

#: What an annotation's anchor may say. **Never a coordinate**: pixel pins die
#: on the next revision, and the founding artifact went through six in one
#: session (`append_design_comment`'s lesson, applied to a richer anchor).
#:
#: * ``variant``  — the `## Variant <name>` section it sits in
#: * ``path``     — a CSS path within that variant's fragment
#: * ``quote``    — the text it was attached to, which is what lets a moved
#:                  anchor be RE-FOUND rather than guessed at
ANCHOR_KEYS: frozenset[str] = frozenset({"variant", "path", "quote"})


def normalise_anchor(raw: object) -> dict[str, str]:
    """Keep only the anchor keys, as strings, dropping empties.

    A coordinate arriving under any name is dropped with everything else that
    is not in `ANCHOR_KEYS` — the schema is an allow-list precisely so a caller
    cannot smuggle `{x, y}` in and have it silently persisted.
    """
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key in sorted(ANCHOR_KEYS):
        value = str(raw.get(key) or "").strip()
        if value:
            out[key] = value[:300]
    return out

#: Terminal outcomes, recorded for ADR-0007's advisory-phase measurement:
#: the decision to gate (or not) should rest on how often review actually
#: changes a plan, which is only knowable if outcomes are counted.
OUTCOMES: tuple[str, ...] = (
    "accepted",            # every item accepted as proposed
    "accepted-amended",    # accepted with some items unticked
    "changes-requested",   # sent back to the agent
    "rejected",            # set cancelled
    "answered",            # question answered
)

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MAX_REQUESTS = 200


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class ReviewStore:
    """File-backed queue of open review requests and questions.

    Thread-safe (the HTTP server is threaded) and crash-tolerant: writes
    go through a temp file + replace, and a corrupt store degrades to
    empty rather than taking the sidecar down with it.
    """

    def __init__(self, project_root: Path) -> None:
        self._path = project_root / ".cockpit" / "review-requests.json"
        self._lock = threading.Lock()
        self._requests: list[dict[str, Any]] = []
        self._load()

    # ---- persistence ---------------------------------------------------

    def _load(self) -> None:
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError:
            return
        try:
            data = json.loads(raw)
        except ValueError:
            # A truncated write from a hard kill shouldn't wedge the desk.
            return
        if isinstance(data, dict) and isinstance(data.get("requests"), list):
            self._requests = [r for r in data["requests"] if isinstance(r, dict)]

    def _persist_locked(self) -> None:
        payload = {"version": 1, "requests": self._requests[-_MAX_REQUESTS:]}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self._path)
        except OSError:
            # Best-effort: an unwritable workspace loses the queue on
            # restart but must not break the running desk.
            pass

    # ---- queue -----------------------------------------------------------

    def add(
        self,
        kind: str,
        *,
        items: list[str] | None = None,
        title: str = "",
        body: str = "",
        session_id: str | None = None,
        prompt: str | None = None,
        agent: str | None = None,
        subject: str | None = None,
        anchor: object = None,
        at_revision: str | None = None,
        at_note_digest: str | None = None,
    ) -> dict[str, Any]:
        """File a request. Returns the stored record.

        ``subject`` names what the request is *about* when that is one note
        rather than a set — a design offered for review (TASK-0229). It is what
        makes a request de-duplicable against status intake: without it, a
        design queued by both routes appears twice and a human cannot tell the
        rows apart.

        ``at_revision`` records the revision the request was raised against.
        A review is of a **revision**, not of "the design": TASK-0218 already
        requires `design_revision` on accept and validates it against real
        history, and without the same on the request a reviewer can accept
        something other than what they were shown, with neither party knowing.

        ``at_note_digest`` is the same argument applied to the other half
        (ISS-0057). `at_revision` follows the artifact; a design's note carries
        its Problem, Approach, Regions and Tokens, and could be rewritten under
        a reviewer with every revision signal still reading current. Additive:
        `at_revision` keeps its meaning exactly, so no stored request or
        recorded verdict changes meaning.
        """
        if kind not in KINDS:
            raise ValueError(f"unknown kind: {kind}")
        record: dict[str, Any] = {
            "request_id": uuid.uuid4().hex[:12],
            "kind": kind,
            "items": [str(i).strip().upper() for i in (items or []) if str(i).strip()],
            "title": title.strip(),
            "body": body.strip(),
            "ts": _utc_now_iso(),
            "status": "open",
        }
        if session_id:
            record["session_id"] = str(session_id)
        if prompt:
            record["prompt"] = str(prompt)[:500]
        if agent:
            record["agent"] = str(agent)
        if subject:
            record["subject"] = str(subject).strip().upper()
        if at_revision:
            record["at_revision"] = str(at_revision).strip()[:40]
        if anchor:
            record["anchor"] = normalise_anchor(anchor)
        if at_note_digest:
            record["at_note_digest"] = str(at_note_digest).strip()[:64]
        with self._lock:
            # Check-then-act under ONE lock. `open_for_subject` followed by
            # `add` was a race: each call took and released the lock, so 16
            # concurrent offers of one design produced 9 open requests and 9
            # indistinguishable rows (found by independent review, ISS-0056).
            # Not reachable by double-click — the button disables
            # synchronously — but reachable from a second window or any
            # scripted caller.
            if record.get("subject"):
                for existing in self._requests:
                    if (existing.get("status") == "open"
                            and existing.get("subject") == record["subject"]):
                        return dict(existing)
            self._requests.append(record)
            self._persist_locked()
        return dict(record)

    def open_for_subject(self, subject: str) -> dict[str, Any] | None:
        """The open request about ``subject``, if any.

        Filing is idempotent through this: offering the same design twice
        returns the existing request rather than queueing it again, because a
        human asked to look at one thing should see one row.
        """
        key = (subject or "").strip().upper()
        if not key:
            return None
        with self._lock:
            for r in self._requests:
                if r.get("status") == "open" and r.get("subject") == key:
                    return dict(r)
        return None

    def annotate(self, request_id: str, **fields: Any) -> dict[str, Any] | None:
        """Attach JSON-safe scalars to an open request.

        Deliberately scalars only: the ledger is read by the desk and written
        by endpoints, and a nested bag here would become a second schema
        nobody validates.
        """
        if not _ID_RE.match(request_id or ""):
            return None
        clean = {k: v for k, v in fields.items()
                 if isinstance(v, (str, int, float, bool)) or v is None}
        with self._lock:
            for r in self._requests:
                if r.get("request_id") == request_id:
                    r.update(clean)
                    self._persist_locked()
                    return dict(r)
        return None

    def open_requests(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._requests if r.get("status") == "open"]

    def get(self, request_id: str) -> dict[str, Any] | None:
        if not _ID_RE.match(request_id or ""):
            return None
        with self._lock:
            for r in self._requests:
                if r.get("request_id") == request_id:
                    return dict(r)
        return None

    def resolve(
        self, request_id: str, outcome: str, *, note: str = "",
    ) -> dict[str, Any] | None:
        """Close a request with an outcome. Idempotent-ish: resolving an
        already-resolved request returns it unchanged."""
        if outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome: {outcome}")
        if not _ID_RE.match(request_id or ""):
            return None
        with self._lock:
            for r in self._requests:
                if r.get("request_id") != request_id:
                    continue
                if r.get("status") == "open":
                    r["status"] = "resolved"
                    r["outcome"] = outcome
                    r["resolved_at"] = _utc_now_iso()
                    if note:
                        r["resolution_note"] = note[:500]
                    self._persist_locked()
                return dict(r)
        return None

    def outcome_counts(self) -> dict[str, int]:
        """Resolved-outcome tally — the measurement ADR-0007's advisory
        phase is supposed to produce before anyone argues for gating."""
        counts: dict[str, int] = {}
        with self._lock:
            for r in self._requests:
                outcome = r.get("outcome")
                if isinstance(outcome, str):
                    counts[outcome] = counts.get(outcome, 0) + 1
        return counts


def resolve_anchor(anchor: dict[str, str], design_text: str) -> dict[str, object]:
    """Re-find an annotation's anchor in the design as it stands now.

    **Never floats to the wrong spot** (TASK-0308). An anchor is re-resolved at
    render, and when it cannot be found the annotation says so — because a
    comment silently re-attached to different content is worse than one that
    admits it is lost: the reader trusts it and it is about something else.

    Resolution is deliberately in this order, weakest claim last:

    1. the **quote** still appears — the strongest evidence the thing being
       commented on survived, and independent of any structure;
    2. otherwise the **variant** still exists — the comment is still about a
       shape that is present, but the exact spot moved;
    3. otherwise **lost**.
    """
    from .cockpit import design_variants

    quote = (anchor or {}).get("quote", "")
    variant = (anchor or {}).get("variant", "")
    names = [v["name"] for v in design_variants(design_text)]

    if quote and quote in design_text:
        return {"state": "found", "by": "quote", "variant": variant}
    if variant and variant in names:
        return {
            "state": "moved", "by": "variant", "variant": variant,
            "detail": "the quoted text is gone; the variant it was in still exists",
        }
    return {
        "state": "lost", "by": "", "variant": variant,
        "detail": "neither the quoted text nor the variant it named is in the design now",
    }
