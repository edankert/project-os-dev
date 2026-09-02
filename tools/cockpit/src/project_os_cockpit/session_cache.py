"""Prompt-cache economics for a session, read from its transcript
(FEAT-0081 / TASK-0343).

The agent strip has shown ``ctx %`` and a running dollar total since
FEAT-0020. Neither answers the question that actually drives the next
turn's bill: **what does the conversation weigh, and is the cache behind
it still warm?** ``ctx %`` is fill against the context window; the dollar
figure is spend to date. The next turn's input cost is the prefix weight
multiplied by either the cache-read rate (0.1x) or the cache-write rate
(2x on the 1-hour TTL these sessions use) — a 20x swing that nothing
surfaces.

The data is already on disk. Claude Code writes a JSONL transcript whose
assistant entries carry a ``usage`` block with exact
``cache_read_input_tokens`` / ``cache_creation_input_tokens`` and the
``ephemeral_1h`` / ``ephemeral_5m`` split, and ``AgentTracker`` has
stored ``transcript_path`` per session since FEAT-0019. This module is a
**pure reader** over that file.

Two entry points, deliberately separate:

* :func:`live_state` — bounded **tail** read for the strip. Transcripts
  in this repo's own history reach 34MB and the strip re-renders on
  every snapshot, so reading the whole file here would be a performance
  regression shipped inside a cost feature.
* :func:`history` — full streaming scan for the retrospective figure,
  memoised hard against ``(path, mtime, size)``.

Two correctness notes that are easy to get wrong:

* **Deduplicate by ``message.id``.** Claude Code writes one transcript
  entry per content block, so consecutive entries repeat the same
  ``usage`` verbatim. A naive scan double-counts every multi-block turn.
* **A cost figure here is an estimate.** Token counts are exact; the
  dollars are derived from a hard-coded per-family price table that
  drifts. Callers render them with a ``~`` and round hard.

This module never issues an API request and must never gain one. A
keep-warm ping costs 2x the full prefix *every ping*, against 2x *once*
for letting the cache expire — so background re-warming is strictly more
expensive than doing nothing. See FEAT-0081, "The automation that must
not be built".
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Iterator

log = logging.getLogger("project_os_cockpit.session_cache")

# Tail budget for the live read. Big enough to hold several assistant
# turns (an entry carries one content block, but a block holding a large
# tool result can run to hundreds of KB), small enough that reading it on
# every snapshot is free. FALLBACK is one retry for a session whose last
# turns are unusually fat; beyond that the live read gives up rather than
# creeping toward a full read of a 34MB file.
TAIL_BYTES = 512 * 1024
TAIL_BYTES_FALLBACK = 4 * 1024 * 1024

# A full-prefix re-write is `cache_read == 0` with a substantial write on
# a turn that is not the session's first. The floor keeps small
# early-session turns out of the count.
FULL_REWRITE_MIN = 5_000

# Below this, a model switch discarded too little to be worth naming.
# Measured events run 252k-986k tokens, so this is two orders of
# magnitude clear of the real cases (ISS-0104).
MODEL_SWITCH_MIN_DISCARD = 50_000

# `model` on the assistant entry Claude Code writes when a request fails.
# Not a turn — see `_turn_from_entry` (ISS-0106).
SYNTHETIC_MODEL = "<synthetic>"

# How long a model switch stays the freshest thing the badge can say
# (ISS-0107). Past this the standing warm/cooling/cold state renders
# again. A switch is a recent EVENT; leaving it up for the life of the
# transcript suppressed the cold warning this module exists to give.
MODEL_SWITCH_NOTICE_SECONDS = 15 * 60

TTL_1H = 3600
TTL_5M = 300

# Cache-write premium over base input, by TTL, and the read discount.
WRITE_MULT_1H = 2.0
WRITE_MULT_5M = 1.25
READ_MULT = 0.1

# Base input $/MTok by model family. Drifts — every figure derived from
# it is an estimate and must be rendered as one.
_PRICE_PER_MTOK: tuple[tuple[str, float], ...] = (
    ("fable", 10.0),
    ("mythos", 10.0),
    ("opus", 5.0),
    ("sonnet", 3.0),
    ("haiku", 1.0),
)
_PRICE_DEFAULT = 5.0

CAUSE_SESSION_START = "session-start"
CAUSE_TTL_EXPIRY = "ttl-expiry"
CAUSE_MODEL_SWITCH = "model-switch"
CAUSE_OTHER = "other"

_HISTORY_CACHE: dict[str, tuple[float, int, "CacheHistory"]] = {}
_LIVE_CACHE: dict[str, tuple[float, int, "LiveCacheState | None"]] = {}
_CACHE_MAX = 64


def price_per_mtok(model: str | None) -> float:
    """Base input price for a model id, by family substring."""
    name = (model or "").lower()
    for key, price in _PRICE_PER_MTOK:
        if key in name:
            return price
    return _PRICE_DEFAULT


def _parse_iso(ts: Any) -> float:
    if not isinstance(ts, str) or not ts:
        return 0.0
    try:
        return _dt.datetime.fromisoformat(
            ts.replace("Z", "+00:00")
        ).timestamp()
    except ValueError:
        return 0.0


@dataclass
class TurnUsage:
    """One deduplicated assistant turn's cache accounting."""

    ts: str
    epoch: float
    model: str | None
    read: int
    write: int
    write_1h: int
    write_5m: int

    @property
    def prefix_tokens(self) -> int:
        """What the conversation weighs after this turn — everything the
        next turn either reads from cache or re-writes."""
        return self.read + self.write

    @property
    def ttl_seconds(self) -> int:
        """TTL the cache was written under. These sessions write 1h
        exclusively (measured: 129.0M tokens 1h against 0.0M 5m); the 5m
        branch is defensive."""
        return TTL_5M if self.write_5m > self.write_1h else TTL_1H

    @property
    def write_multiplier(self) -> float:
        return WRITE_MULT_5M if self.ttl_seconds == TTL_5M else WRITE_MULT_1H

    def rewrite_cost_usd(self) -> float:
        """What re-writing this prefix from cold would cost."""
        return (
            self.prefix_tokens / 1e6
            * price_per_mtok(self.model)
            * self.write_multiplier
        )

    def read_cost_usd(self) -> float:
        """What reading this prefix from a warm cache would cost."""
        return self.prefix_tokens / 1e6 * price_per_mtok(self.model) * READ_MULT


@dataclass
class RewriteEvent:
    """A turn that re-wrote the whole prefix instead of reading it."""

    ts: str
    cause: str
    tokens: int
    cost_usd: float
    gap_seconds: float | None
    model: str | None
    prev_model: str | None


@dataclass
class LiveCacheState:
    """Cache standing of the most recent turn, for the strip."""

    prefix_tokens: int
    last_turn_at: str
    age_seconds: float
    ttl_seconds: int
    model: str | None
    state: str                       # warm | cooling | cold
    resume_cost_usd: float           # next turn cold
    warm_cost_usd: float             # next turn warm
    model_switch: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "prefix_tokens": self.prefix_tokens,
            "last_turn_at": self.last_turn_at,
            "age_seconds": round(self.age_seconds),
            "ttl_seconds": self.ttl_seconds,
            "model": self.model,
            "state": self.state,
            "resume_cost_usd": round(self.resume_cost_usd, 2),
            "warm_cost_usd": round(self.warm_cost_usd, 2),
        }
        if self.state == "cooling":
            out["cooling_minutes_left"] = max(
                0, int((self.ttl_seconds - self.age_seconds) // 60)
            )
        if self.model_switch:
            out["model_switch"] = self.model_switch
        return out


@dataclass
class CacheHistory:
    """Retrospective accounting over a whole transcript."""

    turns: int = 0
    read_tokens: int = 0
    write_tokens: int = 0
    read_cost_usd: float = 0.0
    write_cost_usd: float = 0.0
    events: list[RewriteEvent] = field(default_factory=list)

    def buckets(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for ev in self.events:
            b = out.setdefault(
                ev.cause, {"count": 0, "tokens": 0, "cost_usd": 0.0}
            )
            b["count"] += 1
            b["tokens"] += ev.tokens
            b["cost_usd"] += ev.cost_usd
        for b in out.values():
            b["cost_usd"] = round(b["cost_usd"], 2)
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "turns": self.turns,
            "read_tokens": self.read_tokens,
            "write_tokens": self.write_tokens,
            "read_cost_usd": round(self.read_cost_usd, 2),
            "write_cost_usd": round(self.write_cost_usd, 2),
            "rewrites": self.buckets(),
            # Avoidable = everything except the session's unavoidable
            # first cold write.
            "avoidable_cost_usd": round(
                sum(
                    ev.cost_usd
                    for ev in self.events
                    if ev.cause != CAUSE_SESSION_START
                ),
                2,
            ),
        }


#: The token counters that decide whether an entry did any work.
TOKEN_FIELDS = (
    "cache_read_input_tokens", "cache_creation_input_tokens",
    "input_tokens", "output_tokens",
)


def _effective_usage(usage: dict[str, Any]) -> dict[str, Any]:
    """The usage block that actually carries this turn's numbers.

    Normally that is the block itself. When every top-level counter is
    zero but ``usage.iterations`` holds real figures, the numbers live
    one level down and this returns the serving attempt instead
    (ISS-0114).

    The **last** iteration, not the sum: `prefix_tokens` answers "what
    will the next turn read or re-write", which is the attempt that
    produced this message. Summing would double-count a turn that fell
    back between models. Every entry observed in this corpus has exactly
    one iteration, so the two agree there — the distinction only bites
    on a server-side fallback, and then last-attempt is the correct
    answer for weight even though sum is the correct answer for billing.
    """
    def _int(source: dict[str, Any], key: str) -> int:
        val = source.get(key)
        return int(val) if isinstance(val, (int, float)) else 0

    if any(_int(usage, k) for k in TOKEN_FIELDS):
        return usage
    iterations = usage.get("iterations")
    if not isinstance(iterations, list):
        return usage
    for entry in reversed(iterations):
        if isinstance(entry, dict) and any(_int(entry, k) for k in TOKEN_FIELDS):
            return entry
    return usage


def _turn_from_entry(entry: dict[str, Any]) -> TurnUsage | None:
    """A deduplicatable assistant turn, or ``None`` for anything else.

    **An API-error placeholder is not a turn** (ISS-0106). When a request
    fails, Claude Code writes an assistant entry carrying a real
    ``message.id``, ``model: "<synthetic>"``, an all-zero ``usage``, and
    text like ``API Error: Unable to connect to API (ECONNRESET)``. There
    are 33 across this machine's transcripts.

    Letting one through does more than inflate a count: it becomes the
    *previous* turn, so a retry seconds after a reset makes a 151-hour
    idle gap read as 52 seconds, and the event is then filed as a model
    switch with ``prev_model: "<synthetic>"`` — corrupting the exact
    statistic this module was written to produce.

    The rejection is on the **shape of the data** rather than the
    sentinel alone — no tokens *anywhere* in the entry — so a future
    placeholder under a different name cannot reintroduce the defect.

    "Anywhere" is load-bearing (ISS-0114). A first version of this test
    read only the top-level `usage` totals and argued that an entry
    consuming nothing did no work. Five entries in the corpus it was
    derived from falsify that: their top-level totals are all zero and
    the real accounting sits in ``usage.iterations`` — one of them a
    ``stop_reason: tool_use`` turn that read 461,787 cached tokens. They
    are turns, and both dropping them and counting them as zero are
    wrong, so the totals are taken from wherever they actually are.
    """
    if entry.get("type") != "assistant":
        return None
    msg = entry.get("message")
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    model = msg.get("model")
    if model == SYNTHETIC_MODEL:
        return None

    usage = _effective_usage(usage)
    creation = usage.get("cache_creation")
    creation = creation if isinstance(creation, dict) else {}

    def _int(source: dict[str, Any], key: str) -> int:
        val = source.get(key)
        return int(val) if isinstance(val, (int, float)) else 0

    if not any(_int(usage, k) for k in TOKEN_FIELDS):
        return None

    ts = entry.get("timestamp")
    ts = ts if isinstance(ts, str) else ""
    return TurnUsage(
        ts=ts,
        epoch=_parse_iso(ts),
        model=model if isinstance(model, str) else None,
        read=_int(usage, "cache_read_input_tokens"),
        write=_int(usage, "cache_creation_input_tokens"),
        write_1h=_int(creation, "ephemeral_1h_input_tokens"),
        write_5m=_int(creation, "ephemeral_5m_input_tokens"),
    )


def _iter_turns(lines: Iterator[bytes | str]) -> Iterator[TurnUsage]:
    """Deduplicated assistant turns, in file order.

    Claude Code emits one entry per content block, repeating ``usage``
    verbatim across them — so this drops any turn whose ``message.id``
    was already seen. Without it every multi-block turn is counted
    once per block.
    """
    seen: set[str] = set()
    for raw in lines:
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except (ValueError, TypeError):
            continue          # truncated tail line, or a partial write
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message")
        mid = msg.get("id") if isinstance(msg, dict) else None
        if not isinstance(mid, str) or mid in seen:
            continue
        turn = _turn_from_entry(entry)
        if turn is None:
            continue
        seen.add(mid)
        yield turn


def _read_tail(path: str, budget: int) -> list[str]:
    """Last ``budget`` bytes as complete lines.

    The first line of a mid-file seek is almost always partial, so it is
    dropped unless the read covered the whole file.
    """
    size = os.path.getsize(path)
    start = max(0, size - budget)
    with open(path, "rb") as fh:
        fh.seek(start)
        blob = fh.read()
    lines = blob.split(b"\n")
    if start > 0 and lines:
        lines = lines[1:]
    out: list[str] = []
    for line in lines:
        try:
            out.append(line.decode("utf-8"))
        except UnicodeDecodeError:
            continue
    return out


def _prune(cache: dict[str, Any]) -> None:
    while len(cache) > _CACHE_MAX:
        cache.pop(next(iter(cache)))


def _stat(path: str | None) -> tuple[float, int] | None:
    if not path:
        return None
    try:
        st = os.stat(path)
    except OSError:
        return None
    return st.st_mtime, st.st_size


def live_state(
    transcript_path: str | None, now: float | None = None
) -> LiveCacheState | None:
    """Cache standing of the last turn, from a bounded tail read.

    Returns ``None`` for a missing, unreadable, empty, or usage-free
    transcript. This runs inside the snapshot path, so every failure is
    an absent badge rather than an exception.
    """
    stat = _stat(transcript_path)
    if stat is None:
        return None
    assert transcript_path is not None
    mtime, size = stat
    hit = _LIVE_CACHE.get(transcript_path)
    if hit is not None and hit[0] == mtime and hit[1] == size:
        cached = hit[2]
        if cached is None:
            return None
        # Age is wall-clock, so recompute it even on a cache hit —
        # otherwise a warm badge never cools while the file is idle,
        # which is exactly when it needs to.
        return _with_age(cached, now)

    turns: list[TurnUsage] = []
    try:
        for budget in (TAIL_BYTES, TAIL_BYTES_FALLBACK):
            turns = list(_iter_turns(iter(_read_tail(transcript_path, budget))))
            if turns or budget >= size:
                break
    except OSError as exc:
        log.debug("session_cache: tail read failed for %s: %s",
                  transcript_path, exc)
        return None

    state: LiveCacheState | None = None
    if turns and turns[-1].epoch > 0:
        # A turn with no usable timestamp yields no badge (ISS-0108).
        # `_with_age` would otherwise measure from epoch 0 and report
        # `cold` with an age of 56 years — the module's most alarming
        # state, asserted from the absence of data. The TypeScript half
        # of this feature states the principle explicitly; this is it
        # honoured on the Python side, and it matches the contract every
        # other failure here follows: an absent badge, never a confident
        # one.
        last = turns[-1]
        prev = turns[-2] if len(turns) > 1 else None
        switch = None
        if (
            prev is not None
            and last.model
            and prev.model
            and last.model != prev.model
            and last.read == 0
            and last.write >= MODEL_SWITCH_MIN_DISCARD
        ):
            # ISS-0104: the switch discarded a warm prefix. Report it;
            # never try to prevent it — the cockpit does not own the
            # session.
            switch = {
                "from": prev.model,
                "to": last.model,
                "discarded_tokens": prev.prefix_tokens or last.write,
                "cost_usd": round(last.rewrite_cost_usd(), 2),
            }
        state = LiveCacheState(
            prefix_tokens=last.prefix_tokens,
            last_turn_at=last.ts,
            age_seconds=0.0,
            ttl_seconds=last.ttl_seconds,
            model=last.model,
            state="warm",
            resume_cost_usd=last.rewrite_cost_usd(),
            warm_cost_usd=last.read_cost_usd(),
            model_switch=switch,
        )

    _LIVE_CACHE[transcript_path] = (mtime, size, state)
    _prune(_LIVE_CACHE)
    return _with_age(state, now) if state is not None else None


def _with_age(state: LiveCacheState, now: float | None) -> LiveCacheState:
    """Re-derive age and warm/cooling/cold against the clock.

    ``warm`` is a claim this reader cannot actually prove — a cache entry
    can be evicted before its TTL, and 6 of the 14 measured sub-hour
    re-writes had no model change to explain them. So the state is a
    statement about *elapsed time against the known TTL*, and the UI
    words it that way.
    """
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc).timestamp()
    age = max(0.0, now - _parse_iso(state.last_turn_at))
    if age >= state.ttl_seconds:
        label = "cold"
    elif age >= state.ttl_seconds * 0.75:
        label = "cooling"
    else:
        label = "warm"
    # The switch announcement expires with the same clock (ISS-0107).
    # It was derived from the last turn and never decayed, so a session
    # left alone after a switch never rendered warm, cooling or cold
    # again — the badge kept reporting a cost already paid instead of
    # the one about to be.
    switch = (
        state.model_switch
        if state.model_switch and age < MODEL_SWITCH_NOTICE_SECONDS
        else None
    )
    return LiveCacheState(
        prefix_tokens=state.prefix_tokens,
        last_turn_at=state.last_turn_at,
        age_seconds=age,
        ttl_seconds=state.ttl_seconds,
        model=state.model,
        state=label,
        resume_cost_usd=state.resume_cost_usd,
        warm_cost_usd=state.warm_cost_usd,
        model_switch=switch,
    )


def history(transcript_path: str | None) -> CacheHistory | None:
    """Full-transcript accounting, memoised against mtime and size.

    Streams the file — transcripts here reach 34MB and must never be
    loaded whole.
    """
    stat = _stat(transcript_path)
    if stat is None:
        return None
    assert transcript_path is not None
    mtime, size = stat
    hit = _HISTORY_CACHE.get(transcript_path)
    if hit is not None and hit[0] == mtime and hit[1] == size:
        return hit[2]

    out = CacheHistory()
    prev: TurnUsage | None = None
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as fh:
            for index, turn in enumerate(_iter_turns(fh)):
                out.turns += 1
                out.read_tokens += turn.read
                out.write_tokens += turn.write
                price = price_per_mtok(turn.model)
                out.read_cost_usd += turn.read / 1e6 * price * READ_MULT
                out.write_cost_usd += (
                    turn.write / 1e6 * price * turn.write_multiplier
                )
                if turn.read == 0 and turn.write > FULL_REWRITE_MIN:
                    out.events.append(
                        _classify(turn, prev, index, price)
                    )
                prev = turn
    except OSError as exc:
        log.debug("session_cache: scan failed for %s: %s",
                  transcript_path, exc)
        return None

    _HISTORY_CACHE[transcript_path] = (mtime, size, out)
    _prune(_HISTORY_CACHE)
    return out


def _classify(
    turn: TurnUsage, prev: TurnUsage | None, index: int, price: float
) -> RewriteEvent:
    """Why this turn re-wrote the whole prefix.

    ``other`` is a real answer, not a classification failure: a cache
    entry can be evicted before its TTL, so some sub-hour re-writes have
    no discoverable cause. Forcing them into a bucket would overstate
    what the data supports.
    """
    cost = turn.write / 1e6 * price * turn.write_multiplier
    gap: float | None = None
    if prev is not None and prev.epoch and turn.epoch:
        gap = turn.epoch - prev.epoch

    if index == 0 or prev is None:
        cause = CAUSE_SESSION_START
    elif gap is not None and gap > turn.ttl_seconds:
        cause = CAUSE_TTL_EXPIRY
    elif (
        prev.model
        and turn.model
        and prev.model != turn.model
        and turn.write >= MODEL_SWITCH_MIN_DISCARD
    ):
        cause = CAUSE_MODEL_SWITCH
    else:
        cause = CAUSE_OTHER

    return RewriteEvent(
        ts=turn.ts,
        cause=cause,
        tokens=turn.write,
        cost_usd=cost,
        gap_seconds=gap,
        model=turn.model,
        prev_model=prev.model if prev is not None else None,
    )
