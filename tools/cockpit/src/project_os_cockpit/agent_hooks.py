"""Hook-fed agent session tracking (FEAT-0019 / TASK-0114).

Claude Code (and Codex, via an adapter forwarder) can POST structured
lifecycle events to ``/api/agent-hook`` — ``SessionStart``,
``UserPromptSubmit``, ``PreToolUse``, ``PostToolUse``,
``PermissionRequest``, ``Notification``, ``Stop``, ``SessionEnd``, plus
a cockpit-defined ``Statusline`` event carrying cost/context data. This
module owns the per-workspace accumulation of those events:

* the **headline state mapping** (``UserPromptSubmit`` → ``busy``,
  ``PermissionRequest`` → ``needs-input``, ``Stop`` → ``waiting``,
  ``SessionEnd`` → ``idle``) that feeds the existing ``CockpitState``
  agent-state machine,
* the **activity feed** (current prompt, tool, file) fanned out as
  ``cockpit:agent-activity`` SSE events,
* the **session index** (TASK-0123): a bounded, atomically-persisted
  record of past sessions under ``.cockpit/sessions.json``,
* the **undocumented-work rule** (TASK-0125): source files edited with
  no TASK/ISS/CHG note touched,
* **CHG provenance** (TASK-0126): correlating CHG notes created during
  a live session.

Trust model (RISK-0004): payloads arrive from localhost but are
*untrusted input* — any local process can POST here. Everything is
shape-validated, size-capped, and clipped before storage; nothing from
a payload is ever rendered as HTML by this layer. Unknown events are
logged and dropped rather than erroring, so hook-schema drift in the
CLIs cannot break ingestion.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from .events import relative_to_ci

log = logging.getLogger("project_os_cockpit.agent_hooks")

# Hard cap on accepted request bodies. PostToolUse payloads for Write
# carry whole file contents in ``tool_input``, so this is deliberately
# generous; storage below clips to small fields regardless.
MAX_BODY_BYTES = 2 * 1024 * 1024

SESSIONS_MAX = 50      # persisted session records per workspace
DISPATCHES_MAX = 30    # pending dispatch records kept (FEAT-0025)
REQUESTS_MAX = 20      # CLI queue-requests awaiting desktop pickup
# A pending dispatch is stamped onto the next session that starts
# within this window; older ones are considered abandoned.
DISPATCH_STAMP_WINDOW_SECONDS = 900.0
PROMPTS_MAX = 50       # prompts kept per session
PROMPT_CLIP = 500      # chars kept per prompt
FILES_MAX = 200        # touched files kept per session
STATUS_TOUCHED_MAX = 60  # notes whose status changed, kept per session (TASK-0194)
MESSAGE_CLIP = 300     # chars kept for notification/stop messages
PERSIST_INTERVAL_SECONDS = 5.0
# A cockpit-terminal session with the opt-in external hook enabled fires
# BOTH capture paths, posting the same payload ~100ms apart. Identical
# (session, event, payload) within this window is that double-capture,
# not two real events — drop the second (TASK-0152).
DEDUP_WINDOW_SECONDS = 2.0

# Notification subtypes that mean "a human must act now" — the agent is
# blocked mid-work. idle_prompt is deliberately excluded (see below):
# a finished turn is `waiting` (review me), not blocked, and must not
# escalate to the red needs-input tier (TASK-0156, the never-ending
# red-blink report 2026-07-19).
_NEEDS_INPUT_NOTIFICATIONS = frozenset(
    {"permission_prompt", "elicitation_dialog"}
)
# Notification subtypes that mean "the agent finished and is idling,
# waiting for you" — the amber `waiting` tier, same as a Stop.
_WAITING_NOTIFICATIONS = frozenset({"idle_prompt"})
# Tool names whose tool_input.file_path counts as "touching a file".
_EDIT_TOOLS = frozenset(
    {"Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch"}
)
# Docs-note filename prefixes that satisfy the documentation contract
# for the undocumented-work rule (TASK-0125).
_DOC_NOTE_PREFIXES = ("TASK-", "ISS-", "CHG-")
# Broader set — every trackable note type — for the live-work views
# (FEAT-0036): "what items is this session touching", independent of the
# narrower undocumented-work contract above.
_WORK_NOTE_PREFIXES = (
    "TASK-", "ISS-", "FEAT-", "REQ-", "PHASE-", "RISK-", "CHG-", "ADR-", "TST-",
)


def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")


def _parse_iso(ts: str) -> float:
    try:
        return _dt.datetime.fromisoformat(ts).timestamp()
    except (ValueError, TypeError):
        return 0.0


def _normalize_reset(value: Any) -> str | None:
    """Normalise a rate-limit ``resets_at`` to an ISO-8601 string so every
    UI surface parses it the same way (review finding F2). Accepts an ISO
    string as-is, or a Unix epoch in seconds or milliseconds."""
    if isinstance(value, str) and value:
        return value
    if isinstance(value, (int, float)):
        secs = value / 1000.0 if value > 1e11 else float(value)
        try:
            return _dt.datetime.fromtimestamp(
                secs, _dt.timezone.utc
            ).isoformat(timespec="seconds")
        except (ValueError, OverflowError, OSError):
            return None
    return None


def _clip(value: Any, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


class AgentSessionTracker:
    """Accumulates hook events into per-session records for one workspace.

    Thread-safe: the HTTP server is multi-threaded and the watcher
    thread calls :meth:`on_file_event` concurrently with ingestion.
    """

    def __init__(
        self, *, docs_root: Path, sessions_path: Path | None = None
    ) -> None:
        self._lock = threading.Lock()
        self._docs_root = docs_root.resolve()
        self._sessions_path = sessions_path
        self._sessions: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []  # session ids, oldest first
        # Dispatch ledger (FEAT-0025 / TASK-0135): dispatches awaiting
        # a session to stamp, and CLI queue-requests awaiting the
        # desktop shell (TASK-0136).
        self._pending_dispatches: list[dict[str, Any]] = []
        self._dispatch_requests: list[dict[str, Any]] = []
        self._activity: dict[str, Any] | None = None
        self._last_persist = 0.0
        # Dedup window for the terminal+external double-capture
        # (TASK-0152): {(sid, event, digest): monotonic-ish ts}.
        self._recent_events: dict[tuple[str, str, int], float] = {}
        self._live_ttl = float(
            os.environ.get("COCKPIT_AGENT_SESSION_TTL_SECONDS", "600")
        )
        if sessions_path is not None:
            self._seed(sessions_path)

    # ---- persistence ----

    def _seed(self, path: Path) -> None:
        """Best-effort load of past sessions. Sessions that were live
        when the previous process died are marked ended so they can't
        ghost as live forever."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(data, dict) or not isinstance(
            data.get("sessions"), list
        ):
            return
        for rec in data["sessions"]:
            if not isinstance(rec, dict):
                continue
            sid = rec.get("session_id")
            if not isinstance(sid, str) or not sid:
                continue
            if rec.get("ended") is None:
                rec["ended"] = rec.get("last_event") or _utc_now_iso()
            self._sessions[sid] = rec
            self._order.append(sid)

    def _persist_locked(self, *, force: bool = False) -> None:
        """Atomic (temp+rename) mirror of the session index. Called
        under the instance lock; failures are logged, never raised."""
        if self._sessions_path is None:
            return
        now = _dt.datetime.now().timestamp()
        if not force and now - self._last_persist < PERSIST_INTERVAL_SECONDS:
            return
        self._last_persist = now
        # Retention: keep the most recent SESSIONS_MAX records.
        while len(self._order) > SESSIONS_MAX:
            dropped = self._order.pop(0)
            self._sessions.pop(dropped, None)
        payload = {"sessions": [self._sessions[sid] for sid in self._order]}
        try:
            self._sessions_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._sessions_path.with_name(
                self._sessions_path.name + ".tmp"
            )
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            os.replace(tmp, self._sessions_path)
        except OSError as exc:
            log.warning(
                "session index write failed for %s: %s",
                self._sessions_path, exc,
            )

    # ---- ingestion ----

    def _session_locked(self, sid: str, agent: str, ts: str) -> dict[str, Any]:
        sess = self._sessions.get(sid)
        if sess is None:
            sess = {
                "session_id": sid,
                "agent": agent,
                "started": ts,
                "ended": None,
                "last_event": ts,
                "cwd": None,
                "transcript_path": None,
                "prompts": [],
                "files": [],
                "docs_notes": [],
                "work_ts": {},
                "prompt_started": None,
                "status_touched": {},
                "cost": None,
                "chg_ids": [],
                "dispatches": [],
                "undocumented": False,
            }
            self._sessions[sid] = sess
            self._order.append(sid)
            # Stamp fresh pending dispatches onto the session they most
            # plausibly started (TASK-0135) — same correlation pattern
            # as CHG notes.
            now = _dt.datetime.now(_dt.timezone.utc).timestamp()
            fresh = [
                d for d in self._pending_dispatches
                if now - _parse_iso(d["ts"]) <= DISPATCH_STAMP_WINDOW_SECONDS
            ]
            if fresh:
                sess["dispatches"] = [dict(d) for d in fresh]
                self._pending_dispatches = [
                    d for d in self._pending_dispatches if d not in fresh
                ]
        return sess

    def _record_file_locked(self, sess: dict[str, Any], file_path: str) -> str | None:
        """Record a touched file; returns the docs-relative path when
        the file lives under the docs root, else None."""
        rel = relative_to_ci(Path(file_path), self._docs_root)
        entry = rel if rel is not None else file_path
        files = sess["files"]
        if entry in files:
            files.remove(entry)  # move to end = most recent
        files.append(entry)
        del files[:-FILES_MAX]
        if rel is not None:
            name = rel.rsplit("/", 1)[-1]
            if name.upper().startswith(_DOC_NOTE_PREFIXES):
                if rel not in sess["docs_notes"]:
                    sess["docs_notes"].append(rel)
            if name.upper().startswith(_WORK_NOTE_PREFIXES):
                work = sess.setdefault("work_notes", [])
                if rel not in work:
                    work.append(rel)
                # Last edit-touch per work note (TASK-0191) — drives the
                # prompt-scoped in-flight set and the active-item pulse.
                sess.setdefault("work_ts", {})[rel] = (
                    sess.get("last_event") or _utc_now_iso()
                )
        self._refresh_undocumented_locked(sess)
        return rel

    def _refresh_undocumented_locked(self, sess: dict[str, Any]) -> None:
        """TASK-0125 rule: source files edited (outside docs/) while no
        TASK/ISS/CHG note has been touched this session.

        Files under the docs root are stored docs-relative by
        ``_record_file_locked``; everything else keeps its absolute
        path — so "absolute path present" ⇔ "source file touched".
        """
        has_src = any(
            f.startswith("/") or (len(f) > 1 and f[1] == ":")
            for f in sess["files"]
        )
        sess["undocumented"] = has_src and not (
            sess["docs_notes"] or sess["chg_ids"]
        )

    def ingest(self, body: dict[str, Any]) -> dict[str, Any]:
        """Fold one hook payload into the tracker.

        Returns an outcome dict: ``{"ok": bool, "state": str | None,
        "message": str | None, "activity": dict | None,
        "ignored": bool}``. ``state`` is the headline agent-state the
        caller should record + fan out (None = no state change).
        """
        event = body.get("hook_event_name")
        if not isinstance(event, str) or not event:
            return {"ok": False, "error": "missing 'hook_event_name'"}
        sid = body.get("session_id")
        if not isinstance(sid, str) or not sid:
            # Codex notify payloads carry `thread-id` instead.
            sid = body.get("thread-id")
        sid = sid if isinstance(sid, str) and sid else "unknown"
        agent = body.get("agent")
        agent = agent if isinstance(agent, str) and agent else "claude"
        ts = _utc_now_iso()

        state: str | None = None
        message: str | None = None
        ignored = False

        with self._lock:
            # Drop the terminal+external double-capture (TASK-0152):
            # identical payload for the same session/event within the
            # dedup window. Never persisted, no state/activity fan-out.
            now_ts = _parse_iso(ts)
            try:
                digest = hash(json.dumps(body, sort_keys=True, default=str))
            except (TypeError, ValueError):
                digest = None
            if digest is not None:
                dk = (sid, event, digest)
                seen = self._recent_events.get(dk)
                if seen is not None and now_ts - seen <= DEDUP_WINDOW_SECONDS:
                    return {"ok": True, "state": None, "message": None,
                            "activity": None, "ignored": True,
                            "duplicate": True}
                self._recent_events[dk] = now_ts
                if len(self._recent_events) > 256:
                    cutoff = now_ts - DEDUP_WINDOW_SECONDS
                    self._recent_events = {
                        k: v for k, v in self._recent_events.items()
                        if v > cutoff
                    }
            sess = self._session_locked(sid, agent, ts)
            sess["last_event"] = ts
            # A session receiving fresh activity is alive again — clear a
            # stale `ended` marker (ISS-0014). `_seed` stamps `ended` on
            # every persisted-live session at startup so a dead one can't
            # ghost as live; but the soft live-reload (TASK-0014) restarts
            # the sidecar under a still-running terminal, so its live
            # session would otherwise stay `ended` forever and never show
            # its cost/ctx. `SessionEnd` is the only event that ends a
            # session; a truly dead one gets no further events and still
            # ages out via `_live_ttl`. (A late event buffered after a
            # legitimate SessionEnd would briefly re-live the session, but
            # the CLI has already exited so no more arrive and it ages out
            # via the TTL — tolerated as purely cosmetic.)
            if event != "SessionEnd" and sess.get("ended") is not None:
                sess["ended"] = None
            for key in ("cwd", "transcript_path"):
                val = body.get(key)
                if isinstance(val, str) and val:
                    sess[key] = val

            activity: dict[str, Any] = {
                "event": event, "session_id": sid, "agent": agent, "ts": ts,
            }

            if event == "SessionStart":
                sess["ended"] = None
            elif event == "UserPromptSubmit":
                prompt = body.get("prompt")
                if isinstance(prompt, str) and prompt.strip():
                    clipped = _clip(prompt.strip(), PROMPT_CLIP)
                    sess["prompts"].append({"ts": ts, "text": clipped})
                    del sess["prompts"][:-PROMPTS_MAX]
                    activity["prompt"] = clipped
                # Prompt boundary (TASK-0191): work-note touches at/after
                # this stamp are "in flight for the current prompt".
                sess["prompt_started"] = ts
                state = "busy"
            elif event in ("PreToolUse", "PostToolUse"):
                tool = body.get("tool_name")
                if isinstance(tool, str) and tool:
                    activity["tool"] = tool
                tool_input = body.get("tool_input")
                if (
                    isinstance(tool, str)
                    and tool in _EDIT_TOOLS
                    and isinstance(tool_input, dict)
                ):
                    file_path = tool_input.get("file_path") or tool_input.get(
                        "path"
                    )
                    if isinstance(file_path, str) and file_path:
                        rel = self._record_file_locked(sess, file_path)
                        activity["file"] = file_path
                        if rel is not None:
                            activity["rel"] = rel
                # A tool event means the agent is actively working —
                # refresh busy so long tasks don't decay mid-flight.
                state = "busy"
            elif event == "PermissionRequest":
                tool = body.get("tool_name")
                message = (
                    f"wants to use {tool}" if isinstance(tool, str) and tool
                    else "needs permission"
                )
                state = "needs-input"
            elif event == "Notification":
                ntype = body.get("notification_type")
                raw_msg = body.get("message")
                if isinstance(raw_msg, str) and raw_msg.strip():
                    message = _clip(raw_msg.strip(), MESSAGE_CLIP)
                if isinstance(ntype, str) and ntype in _NEEDS_INPUT_NOTIFICATIONS:
                    state = "needs-input"
                    message = message or "needs your input"
                elif isinstance(ntype, str) and ntype in _WAITING_NOTIFICATIONS:
                    # Idle prompt = turn finished, agent waiting — amber,
                    # not the red blocked tier (TASK-0156).
                    state = "waiting"
                    message = message or "waiting for your input"
            elif event == "Stop":
                raw_msg = body.get("message")
                if isinstance(raw_msg, str) and raw_msg.strip():
                    message = _clip(raw_msg.strip(), MESSAGE_CLIP)
                state = "waiting"
            elif event == "SessionEnd":
                sess["ended"] = ts
                state = "idle"
            elif event == "Statusline":
                cost = body.get("cost")
                ctx = body.get("context_window")
                snap: dict[str, Any] = {}
                if isinstance(cost, dict):
                    for k in (
                        "total_cost_usd", "total_lines_added",
                        "total_lines_removed", "total_duration_ms",
                    ):
                        if isinstance(cost.get(k), (int, float)):
                            snap[k] = cost[k]
                if isinstance(ctx, dict):
                    for k in ("used_percentage", "context_window_size"):
                        if isinstance(ctx.get(k), (int, float)):
                            snap[k] = ctx[k]
                rl = body.get("rate_limits")
                if isinstance(rl, dict):
                    slim_rl: dict[str, Any] = {}
                    for window in ("five_hour", "seven_day"):
                        w = rl.get(window)
                        if isinstance(w, dict) and isinstance(
                            w.get("used_percentage"), (int, float)
                        ):
                            slim_rl[window] = {
                                "used_percentage": w["used_percentage"],
                                "resets_at": _normalize_reset(
                                    w.get("resets_at")
                                ),
                            }
                    if slim_rl:
                        snap["rate_limits"] = slim_rl
                if snap:
                    # When this reading was captured — lets the UI keep
                    # the freshest account-global usage across workspaces
                    # (TASK-0169).
                    snap["captured_at"] = ts
                    sess["cost"] = snap
                    activity["cost"] = snap
                else:
                    ignored = True
            elif event in ("SubagentStart", "SubagentStop"):
                agent_type = body.get("agent_type")
                if isinstance(agent_type, str) and agent_type:
                    activity["subagent"] = agent_type
            else:
                # Unknown / future event: log-and-drop (RISK-0004 —
                # schema drift must never break ingestion).
                log.debug("agent-hook: ignoring unknown event %r", event)
                ignored = True

            self._refresh_undocumented_locked(sess)
            activity["undocumented"] = sess["undocumented"]
            if state is not None:
                activity["state"] = state
            if not ignored:
                self._activity = activity
            self._persist_locked(
                force=event in ("SessionStart", "SessionEnd")
            )

        return {
            "ok": True,
            "state": state,
            "message": message,
            "activity": None if ignored else activity,
            "ignored": ignored,
        }

    # ---- dispatch ledger (FEAT-0025 / TASK-0135 + TASK-0136) ----

    def record_dispatch(
        self, note_id: str, verb: str | None = None,
        agent: str | None = None, *, enqueue: bool = False,
    ) -> dict[str, Any]:
        rec: dict[str, Any] = {"id": note_id, "ts": _utc_now_iso()}
        if verb:
            rec["verb"] = str(verb)
        if agent:
            rec["agent"] = str(agent)
        with self._lock:
            live = self._live_session_locked()
            if live is not None:
                # Agent already running: this dispatch belongs to the
                # live session (queued delivery lands there).
                live.setdefault("dispatches", []).append(dict(rec))
                del live["dispatches"][:-DISPATCHES_MAX]
                self._persist_locked(force=True)
            else:
                self._pending_dispatches.append(dict(rec))
                del self._pending_dispatches[:-DISPATCHES_MAX]
            if enqueue:
                self._dispatch_requests.append(dict(rec))
                del self._dispatch_requests[:-REQUESTS_MAX]
        return rec

    def take_dispatch_requests(self) -> list[dict[str, Any]]:
        """Hand queued CLI requests to the desktop shell exactly once."""
        with self._lock:
            out = list(self._dispatch_requests)
            self._dispatch_requests = []
            return out

    def dispatch_history(self, note_id: str) -> list[dict[str, Any]]:
        """Newest-first dispatch records for one note, with the session
        each landed in (TASK-0135). Pending records carry no session."""
        out: list[dict[str, Any]] = []
        with self._lock:
            now = _dt.datetime.now(_dt.timezone.utc).timestamp()
            for d in reversed(self._pending_dispatches):
                if d["id"] == note_id:
                    out.append({**d, "session_id": None, "live": False,
                                "pending": True})
            for sid in reversed(self._order):
                sess = self._sessions[sid]
                is_live = sess.get("ended") is None and (
                    now - _parse_iso(sess["last_event"]) <= self._live_ttl
                )
                for d in reversed(sess.get("dispatches") or []):
                    if d["id"] == note_id:
                        entry = {**d, "session_id": sid, "live": is_live}
                        cost = sess.get("cost")
                        if isinstance(cost, dict) and isinstance(
                            cost.get("total_cost_usd"), (int, float)
                        ):
                            entry["total_cost_usd"] = cost["total_cost_usd"]
                        out.append(entry)
        return out

    # ---- file-event correlation (TASK-0126) ----

    def on_file_event(self, kind: str, rel_path: str) -> None:
        """Watcher callback: attach CHG notes created/modified during a
        live session to that session, and count them for the
        undocumented-work rule."""
        if kind not in ("created", "modified"):
            return
        name = rel_path.rsplit("/", 1)[-1]
        if not name.upper().startswith("CHG-") or not name.endswith(".md"):
            return
        chg_id = name[: -len(".md")]
        with self._lock:
            sess = self._live_session_locked()
            if sess is None:
                return
            if chg_id not in sess["chg_ids"]:
                sess["chg_ids"].append(chg_id)
            if rel_path not in sess["docs_notes"]:
                sess["docs_notes"].append(rel_path)
            self._refresh_undocumented_locked(sess)
            self._persist_locked(force=True)

    def record_status_change(self, payload: dict[str, Any]) -> None:
        """Stamp a note whose status changed onto the live session
        (TASK-0194). Fed from the watcher's ``cockpit:status-change`` events,
        so it captures shell-tool writes the PostToolUse touch-tracker misses,
        and — being persisted on the session — survives a sidecar restart.
        Bounded; created-but-unchanged notes emit no transition so the
        untouched backlog never lands here.
        """
        rel = payload.get("rel")
        nid = payload.get("id")
        if not isinstance(rel, str) or not rel:
            return
        with self._lock:
            sess = self._live_session_locked()
            if sess is None:
                return
            touched = sess.setdefault("status_touched", {})
            touched[rel] = {
                "id": nid if isinstance(nid, str) else None,
                "status": payload.get("to"),
                "ts": payload.get("ts") or sess.get("last_event") or _utc_now_iso(),
                "title": payload.get("title"),
            }
            # Bound to the most recent changes by timestamp.
            if len(touched) > STATUS_TOUCHED_MAX:
                for k in sorted(touched, key=lambda r: str(touched[r].get("ts") or ""))[
                    : len(touched) - STATUS_TOUCHED_MAX
                ]:
                    touched.pop(k, None)
            self._persist_locked()

    def chg_provenance(self, chg_id: str) -> dict[str, Any] | None:
        """Which session produced this CHG note (if known)?"""
        with self._lock:
            for sid in reversed(self._order):
                sess = self._sessions[sid]
                if chg_id in sess.get("chg_ids", ()):
                    prov: dict[str, Any] = {
                        "session_id": sid,
                        "agent": sess.get("agent"),
                        "started": sess.get("started"),
                    }
                    cost = sess.get("cost")
                    if isinstance(cost, dict) and isinstance(
                        cost.get("total_cost_usd"), (int, float)
                    ):
                        prov["total_cost_usd"] = cost["total_cost_usd"]
                    return prov
        return None

    # ---- read paths ----

    def _live_session_locked(
        self, now: float | None = None
    ) -> dict[str, Any] | None:
        if now is None:
            now = _dt.datetime.now(_dt.timezone.utc).timestamp()
        for sid in reversed(self._order):
            sess = self._sessions[sid]
            if sess.get("ended") is None and (
                now - _parse_iso(sess["last_event"]) <= self._live_ttl
            ):
                return sess
        return None

    def has_live_session(self, now: float | None = None) -> bool:
        with self._lock:
            return self._live_session_locked(now) is not None

    @staticmethod
    def _slim(sess: dict[str, Any], *, live: bool) -> dict[str, Any]:
        prompts = sess.get("prompts") or []
        return {
            "session_id": sess["session_id"],
            "agent": sess.get("agent"),
            "started": sess.get("started"),
            "ended": sess.get("ended"),
            "live": live,
            "prompt_count": len(prompts),
            "last_prompt": prompts[-1]["text"] if prompts else None,
            "files": list(sess.get("files") or []),
            "docs_notes": list(sess.get("docs_notes") or []),
            "work_notes": list(sess.get("work_notes") or []),
            # Per-note last-touch timestamps + the current prompt boundary
            # (TASK-0191) — the server enriches these into work_items.
            "work_ts": dict(sess.get("work_ts") or {}),
            "prompt_started": sess.get("prompt_started"),
            # Notes whose status changed this session (TASK-0194).
            "status_touched": dict(sess.get("status_touched") or {}),
            "cost": sess.get("cost"),
            "chg_ids": list(sess.get("chg_ids") or []),
            "dispatches": [dict(d) for d in sess.get("dispatches") or []],
            "undocumented": bool(sess.get("undocumented")),
            "transcript_path": sess.get("transcript_path"),
        }

    def _latest_rate_limits_locked(self) -> dict[str, Any] | None:
        """Freshest account-global rate-limit reading across every
        session, by ``captured_at`` (TASK-0171). Rate limits are
        account-global, so the most recently captured reading wins
        regardless of which session recorded it; readings without a
        ``captured_at`` (freshness unknown) are ignored."""
        best: tuple[float, dict[str, Any], str] | None = None
        for sess in self._sessions.values():
            cost = sess.get("cost") or {}
            rl = cost.get("rate_limits")
            cap = cost.get("captured_at")
            if not isinstance(rl, dict) or not isinstance(cap, str):
                continue
            ts = _parse_iso(cap)
            if ts <= 0:
                continue
            if best is None or ts > best[0]:
                best = (ts, rl, cap)
        if best is None:
            return None
        return {"rate_limits": best[1], "rate_limits_at": best[2]}

    def latest_rate_limits(self) -> dict[str, Any] | None:
        with self._lock:
            return self._latest_rate_limits_locked()

    def snapshot(self) -> dict[str, Any]:
        """Live-activity block merged into ``/api/cockpit/state``.

        ``last_session`` carries the most recent session when none is
        live, so the agent strip can keep showing what the agent last
        did here — including the files it touched — between runs
        instead of vanishing the moment a session ends.

        ``rate_limits`` / ``rate_limits_at`` carry the freshest
        account-global usage reading across ALL sessions (TASK-0171).
        """
        with self._lock:
            live = self._live_session_locked()
            last = None
            if live is None and self._order:
                last = self._sessions[self._order[-1]]
            out: dict[str, Any] = {
                "activity": self._activity,
                "session": self._slim(live, live=True) if live else None,
                "last_session": (
                    self._slim(last, live=False) if last is not None else None
                ),
            }
            lrl = self._latest_rate_limits_locked()
            if lrl:
                out["rate_limits"] = lrl["rate_limits"]
                out["rate_limits_at"] = lrl["rate_limits_at"]
            return out

    def sessions_payload(self) -> list[dict[str, Any]]:
        """Newest-first slim session list for ``/api/cockpit/sessions``
        (TASK-0123). Prompts are included in full (clipped at ingest)."""
        with self._lock:
            now = _dt.datetime.now(_dt.timezone.utc).timestamp()
            out: list[dict[str, Any]] = []
            for sid in reversed(self._order):
                sess = self._sessions[sid]
                is_live = sess.get("ended") is None and (
                    now - _parse_iso(sess["last_event"]) <= self._live_ttl
                )
                slim = self._slim(sess, live=is_live)
                slim["prompts"] = [dict(p) for p in sess.get("prompts") or []]
                out.append(slim)
            return out
