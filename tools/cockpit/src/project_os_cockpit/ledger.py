"""The acceptance ledger — a verdict is an event, not a field ([[ADR-0037]]).

An acceptance verdict is a fact about **(check × platform × release)**. It was
stored as a scalar `mark:` in the check note's frontmatter, and a scalar cannot
hold a three-tuple: 579 of `../your-trainer`'s 581 acceptance notes carried no
platform at all while every one of its 513 passes was earned on Android.

This module is the container with the right arity.

**One file per release per platform.** Because releases are per-platform in any
repo shipping independent cadences (`your-trainer`: `v2.1.6` against
`ios/v0.1.0`, separate tag namespaces), each ledger is single-platform *by
construction* — there is no cross-platform release object to hang a shared one
on. The cross-platform view is a query across ledgers, not a document.

**JSON, not YAML** (decision 9, Edwin's call). Measured before adopting it:
`yaml.dump`/`yaml.safe_dump` occur **zero** times in `src/` and
`tools/scripts/`. PyYAML is a read-only dependency here — every YAML file in
the corpus is authored by a person or edited line by line — so a YAML ledger
would introduce this project's first hand-rolled YAML writer, on the one file a
CI runner appends to on every green build. `json` is stdlib and total, and
YAML's implicit typing (`no` → `False`, a bare date → `date`) is a live hazard
on a file of ids, dates and short words.

This is **not** the JSON [[ADR-0030]] rejected, and the reason has nothing to do
with the format: [[FEAT-0112]]'s was a *projection* of state the notes already
held, which is what made the tool mandatory to edit a check. This holds state
that exists nowhere else. The line [[project-os-dev#ADR-0009]] draws is
*derived versus authored*.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

#: Where a ledger lives — with its subject ([[ADR-0020]]: obligations live with
#: their subject, and a ledger's subject is a release).
LEDGERS_REL = "releases/ledgers"
#: The open ledger for a platform. There is always exactly one, and **sealing
#: is what assigns its events to a release** — which is [[ISS-0206]]'s "where do
#: invalidation events live before a release exists" answered without adding a
#: field to anything.
WORKING_PREFIX = "WORKING"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_date(raw: str) -> bool:
    """A real date, not a date-SHAPED string.

    `2026-13-45` matched the regex and was accepted — and a ledger is sorted by
    this field, so a nonsense date does not merely look wrong, it reorders the
    resolution. Found by independent review, 2026-08-19.
    """
    if not _DATE_RE.match(raw or ""):
        return False
    try:
        date.fromisoformat(raw)
    except ValueError:
        return False
    return True
#: A platform is a filename component, so it may not contain a separator or a
#: dot. Checked rather than trusted: the platform comes from a note field and a
#: `../` in it would write outside the ledger directory.
_PLATFORM_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
#: The other half of a sealed ledger's filename, guarded for the same reason.
_RELEASE_RE = re.compile(r"^[A-Z]{2,6}-\d{3,4}$")


# ---------------------------------------------------------------- vocabulary

#: **Clears the gate.** Four values, and they are not interchangeable — see
#: `PERSISTS` for the property that separates `na` from `excused`.
CLEARING: frozenset[str] = frozenset({"pass", "partial", "na", "excused"})
#: **Blocks.** `fail` — walked, it failed. `question` — walked, and the *check*
#: is not understood, which is a different piece of work from a broken
#: behaviour and routes to a different person ([[ADR-0029]] kept the
#: distinction; [[ADR-0037]] decision 6 keeps it again against a source
#: proposal that dropped it by omission). `blocked` — could not be run right
#: now, and it blocks **deliberately**: `na` and `excused` are decisions
#: somebody made about this release, `blocked` is an accident that will be gone
#: next week, and a gate that clears because the rig was down clears on
#: whatever happens to be broken that day.
BLOCKING: frozenset[str] = frozenset({"fail", "blocked", "question"})
MARKS: frozenset[str] = CLEARING | BLOCKING

#: **Survives the seal.** [[ADR-0037]] decision 7, and the sharpest single
#: property in that decision.
#:
#: `na` is a statement about the check and the platform — *there is no
#: OS-level auto-backup surface on iOS* — so re-asking it every release is the
#: maintained-matrix failure the whole design exists to remove. It persists
#: until an invalidation supersedes it.
#:
#: **`excused` does not.** It is a statement about the check, the platform
#: **and this release**: *not done this cycle, by decision*. If it persisted, a
#: check excused once would be excused forever.
#:
#: *That is what the code did before this module existed.* `Item.excepted` was
#: `mark in {canceled, -}` read from frontmatter and scoped to nothing, while
#: the comment directly above that set still described the per-release property
#: [[ADR-0029]] removed when it moved the release exception from `[!]` to
#: `[-]`. A field on a note cannot hold *"expires with its release"* at any
#: price; an event in a per-release ledger gets it by construction, because the
#: ledger it sits in **is** the release it applies to.
PERSISTS: frozenset[str] = frozenset({"pass", "partial", "na"})
#: Everything but `pass` carries its justification. [[ADR-0029]] made this rule
#: and it was never enforced against anything: measured 2026-08-19,
#: `verdict_reason:` is non-empty on **0 of 671** notes, because nobody ever
#: wrote one of the marks that demanded it. On an event it is checked at write
#: time, against something that exists.
NEEDS_REASON: frozenset[str] = MARKS - {"pass"}

#: How the result arrived. One field for two things that used to be two
#: mechanisms: a CI exit code and a person's verdict are two answers to one
#: question ([[ADR-0037]] decision 3).
METHODS: frozenset[str] = frozenset({"manual", "automated", "migration"})


class LedgerError(ValueError):
    """A ledger that cannot be trusted. Never raised for an absent file — a
    repo with no ledger is a repo that has not started, not a broken one."""


# ------------------------------------------------------------------- records

@dataclass(frozen=True)
class Entry:
    """One event. Either a verdict or an invalidation, never both."""

    check: str
    date: str
    mark: str = ""
    by: str = ""
    method: str = ""
    reason: str = ""
    #: The change that made an existing verdict untrustworthy. An invalidation
    #: is an **event with a date** sitting after the verdict it overtakes,
    #: which is why `mark: rerun` is not a value in this vocabulary: the two
    #: states [[ADR-0034]] minted `rerun` to tell apart are distinguishable by
    #: construction here.
    invalidated_by: str = ""

    @property
    def is_invalidation(self) -> bool:
        return bool(self.invalidated_by)

    @property
    def clears(self) -> bool:
        return self.mark in CLEARING


@dataclass(frozen=True)
class Evidence:
    """What backs a verdict — a screenshot, a log, a path.

    **A sibling of `entries`, not a field on one** ([[ADR-0037]] decision 1,
    Edwin's call). It is bulky, it arrives late, and one artefact often covers
    several checks, so it joins by `check` + `date` and an entry stays one line.

    It is not on the *note* for the reason the whole decision runs on: a
    screenshot proves one walk happened on one platform on one date, and on a
    permanent check that is a standing claim of exactly the kind decision 3
    rejects for `automation:`. Measured before removing it: `evidence:` was
    non-empty on **0 of 671** acceptance notes — it never held anything
    precisely because a walk's evidence has no home on a permanent check.
    """

    check: str
    date: str
    ref: str
    note: str = ""


@dataclass
class Ledger:
    """One release, one platform, append-only."""

    platform: str
    path: Path | None = None
    release: str = ""
    version: str = ""
    #: The date this ledger was sealed. Empty means it is the working one.
    sealed: str = ""
    entries: list[Entry] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def is_working(self) -> bool:
        return not self.sealed

    def to_json(self) -> str:
        """One entry per line, so a diff reads as *what was added* — which is
        what an append-only file is for. `json.dumps` with an indent puts every
        scalar on its own line and turns a one-event append into a
        forty-line diff, so the entries are composed rather than dumped."""
        head: dict[str, Any] = {"platform": self.platform}
        if self.release:
            head["release"] = self.release
        if self.version:
            head["version"] = self.version
        if self.sealed:
            head["sealed"] = self.sealed
        lines = [f'  "{k}": {json.dumps(v)},' for k, v in head.items()]

        def block(name: str, rows: list[str], last: bool) -> list[str]:
            if not rows:
                return [f'  "{name}": []' + ("" if last else ",")]
            out = [f'  "{name}": [']
            for i, row in enumerate(rows):
                out.append(f"    {row}" + ("" if i == len(rows) - 1 else ","))
            out.append("  ]" + ("" if last else ","))
            return out

        lines += block("entries", [_entry_json(e) for e in self.entries],
                       last=False)
        lines += block("evidence", [_evidence_json(v) for v in self.evidence],
                       last=True)
        return "{\n" + "\n".join(lines) + "\n}\n"


def _entry_json(entry: Entry) -> str:
    row: dict[str, Any] = {"check": entry.check}
    if entry.invalidated_by:
        row["invalidated_by"] = entry.invalidated_by
    else:
        row["mark"] = entry.mark
    row["date"] = entry.date
    for name in ("method", "by", "reason"):
        value = getattr(entry, name)
        if value:
            row[name] = value
    return json.dumps(row, ensure_ascii=False)


def _evidence_json(item: Evidence) -> str:
    row: dict[str, Any] = {"check": item.check, "date": item.date,
                           "ref": item.ref}
    if item.note:
        row["note"] = item.note
    return json.dumps(row, ensure_ascii=False)


# -------------------------------------------------------------------- verify

def check_entry(raw: dict[str, Any], *, where: str) -> Entry:
    """One entry, or a `LedgerError` naming the file and what is missing.

    Refused rather than coerced. A ledger is what a release gate reads, and an
    entry missing its author or its date is a verdict nobody can stand behind —
    which is the state all 671 notes were already in, with `verdict_date` and
    `verdict_reason` empty on every one of them.
    """
    check = str(raw.get("check", "") or "").strip()
    if not check:
        raise LedgerError(f"{where}: an entry names no check")
    when = str(raw.get("date", "") or "").strip()
    if not _is_date(when):
        raise LedgerError(f"{where}: {check} has no usable date ({when!r})")
    if "platform" in raw:
        raise LedgerError(
            f"{where}: {check} carries its own `platform` — the platform is "
            f"the ledger's, and an entry that could contradict its file is a "
            f"second encoding of one fact")

    invalidated = str(raw.get("invalidated_by", "") or "").strip()
    if invalidated:
        if raw.get("mark"):
            raise LedgerError(
                f"{where}: {check} carries both a mark and an invalidation — "
                f"they are two events and belong on two lines")
        return Entry(check=check, date=when, invalidated_by=invalidated,
                     reason=str(raw.get("reason", "") or "").strip())

    mark = str(raw.get("mark", "") or "").strip()
    if mark not in MARKS:
        raise LedgerError(
            f"{where}: {check} has mark {mark!r}; expected one of "
            f"{', '.join(sorted(MARKS))}")
    method = str(raw.get("method", "") or "").strip()
    if method not in METHODS:
        raise LedgerError(
            f"{where}: {check} has method {method!r}; expected one of "
            f"{', '.join(sorted(METHODS))}")
    by = str(raw.get("by", "") or "").strip()
    if not by:
        raise LedgerError(f"{where}: {check} names nobody in `by`")
    reason = str(raw.get("reason", "") or "").strip()
    if mark in NEEDS_REASON and not reason:
        raise LedgerError(
            f"{where}: a {mark} verdict on {check} needs a reason — the mark "
            f"and its justification are one event, so a check cannot leave "
            f"the gate without saying why")
    return Entry(check=check, date=when, mark=mark, by=by, method=method,
                 reason=reason)


def check_evidence(raw: dict[str, Any], *, where: str) -> Evidence:
    check = str(raw.get("check", "") or "").strip()
    ref = str(raw.get("ref", "") or "").strip()
    when = str(raw.get("date", "") or "").strip()
    if not check or not ref:
        raise LedgerError(f"{where}: an evidence item needs a check and a ref")
    if not _is_date(when):
        raise LedgerError(f"{where}: evidence for {check} has no usable date")
    return Evidence(check=check, date=when, ref=ref,
                    note=str(raw.get("note", "") or "").strip())


def orphan_evidence(ledger: Ledger) -> list[Evidence]:
    """Evidence for a walk nobody recorded.

    **A claim pointing at nothing reads as backed and is not** ([[ISS-0198]]).
    Evidence joins by `check` + `date`, so an item whose pair matches no entry
    is either a typo or proof of a walk that was never written down, and both
    want a person.

    *(This used to say "the same guard `cover_check` applies to `covered_by:`
    and for the same reason". Both are gone — [[REQ-0057]], 2026-08-21: a note
    no longer declares that a machine covers it, because a standing claim rots
    silently and an observed one cannot. The reason survives the function and
    is stated directly above rather than by reference to a deletion.)*
    """
    pairs = {(e.check, e.date) for e in ledger.entries}
    return [v for v in ledger.evidence if (v.check, v.date) not in pairs]


# ---------------------------------------------------------------------- read

def _parse(text: str, *, where: str, platform: str) -> Ledger:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LedgerError(f"{where}: not readable as JSON — {exc}") from None
    if not isinstance(raw, dict):
        raise LedgerError(f"{where}: the ledger is not an object")
    stated = str(raw.get("platform", "") or "").strip()
    if stated and platform and stated != platform:
        raise LedgerError(
            f"{where}: says platform {stated!r} and is filed under "
            f"{platform!r} — the filename and the field must agree")
    return Ledger(
        platform=stated or platform,
        release=str(raw.get("release", "") or "").strip(),
        version=str(raw.get("version", "") or "").strip(),
        sealed=str(raw.get("sealed", "") or "").strip(),
        entries=[check_entry(e, where=where)
                 for e in (raw.get("entries") or [])],
        evidence=[check_evidence(v, where=where)
                  for v in (raw.get("evidence") or [])],
    )


#: `REL-0012-android` / `WORKING-android` -> `android`. **Anchored on the
#: prefix, not on the first hyphen**, and that is not pedantry: splitting on
#: the first hyphen read `REL-0012-android` as platform `0012-android`, which
#: matched no filter — so a ledger disappeared from its own platform the moment
#: it was sealed, and every verdict in it silently stopped counting. Found by
#: sealing one, which is the argument for exercising a format rather than
#: reading it.
_LEDGER_NAME_RE = re.compile(r"^(?:WORKING|[A-Z]{2,6}-\d{3,4})-(?P<platform>.+)$")


def _platform_of(path: Path) -> str:
    found = _LEDGER_NAME_RE.match(path.stem)
    return found.group("platform") if found else ""


def ledgers_dir(docs_root: Path) -> Path:
    return docs_root / LEDGERS_REL


def load(docs_root: Path, platform: str | None = None) -> list[Ledger]:
    """Every ledger, oldest first, the working one last.

    Ordering is the resolution order — a later event supersedes an earlier one
    — so it is a property of this function rather than of each caller. Sealed
    ledgers sort by their seal date; the working ledger is always newest,
    because everything in it happened after the last seal by definition.
    """
    root = ledgers_dir(docs_root)
    if not root.is_dir():
        return []
    out: list[Ledger] = []
    for path in sorted(root.glob("*.json")):
        found = _platform_of(path)
        if not found:
            #: **Refused, not skipped.** `REL-12-ios.json`, `working-ios.json`
            #: and `ios.json` all miss the naming rule, and skipping them is
            #: the same failure the first-hyphen bug had — a ledger that
            #: disappears from its own platform while `platforms()` still
            #: reports the platform — reached through a different door. Found
            #: by independent review, 2026-08-19.
            raise LedgerError(
                f"{LEDGERS_REL}/{path.name}: the filename does not name a "
                f"platform. It must be `WORKING-<platform>.json` or "
                f"`REL-####-<platform>.json`, or its verdicts are invisible "
                f"to every query while the file sits there looking read")
        if platform and found != platform:
            continue
        ledger = _parse(path.read_text(encoding="utf-8"),
                        where=f"{LEDGERS_REL}/{path.name}", platform=found)
        ledger.path = path
        out.append(ledger)
    out.sort(key=lambda l: (l.is_working, l.sealed))
    return out


def has_ledger(docs_root: Path) -> bool:
    """Whether this repo keeps verdicts in ledgers.

    **A ledger FILE, not a directory.** `write()` creates the directory before
    writing, and an empty one used to mean *"every check is owed"* — so an
    interrupted first write turned a whole suite to `todo`. Fail-closed, and
    still not the mechanism the docstring claimed. Found by independent
    review, 2026-08-19.
    """
    root = ledgers_dir(docs_root)
    return root.is_dir() and any(root.glob("*.json"))


def platforms(docs_root: Path) -> list[str]:
    """Every platform this repo has a ledger for. A repo with none is a repo
    that has not started, and its checks are owed everywhere."""
    return sorted({l.platform for l in load(docs_root) if l.platform})


def working_path(docs_root: Path, platform: str) -> Path:
    if not _PLATFORM_RE.match(platform or ""):
        raise LedgerError(
            f"{platform!r} is not a usable platform name — it becomes part of "
            f"a filename, so it must be lowercase alphanumerics, `-` or `_`")
    return ledgers_dir(docs_root) / f"{WORKING_PREFIX}-{platform}.json"


def working(docs_root: Path, platform: str) -> Ledger:
    """The open ledger for a platform, created in memory if it has none yet."""
    path = working_path(docs_root, platform)
    if path.exists():
        ledger = _parse(path.read_text(encoding="utf-8"),
                        where=f"{LEDGERS_REL}/{path.name}", platform=platform)
        ledger.path = path
        return ledger
    return Ledger(platform=platform, path=path)


# ------------------------------------------------------------------ resolve

@dataclass(frozen=True)
class Verdict:
    """What a platform currently says about one check."""

    check: str
    mark: str
    date: str
    by: str
    method: str
    reason: str
    #: Which ledger it came from — `""` for the working one.
    release: str

    @property
    def clears(self) -> bool:
        return self.mark in CLEARING


def resolve(ledgers: Iterable[Ledger]) -> dict[str, Verdict]:
    """The current verdict per check, from a platform's ledgers in order.

    Three rules, and each is a decision rather than a mechanic:

    * a later terminal entry **supersedes** an earlier one;
    * an invalidation **clears** the standing verdict — the check is owed
      again, and `mark: rerun` is not needed to say so because the invalidation
      is itself a dated event sitting after the verdict it overtakes;
    * **an `excused` expires when its ledger seals** ([[ADR-0037]] decision 7).
      It was true of one release. Everything else that clears — `pass`,
      `partial`, `na` — persists until invalidated.

    A check with no surviving verdict simply has no key, and *that absence is
    the answer*: no entry for a platform means owed on that platform, with no
    field anywhere declaring applicability ([[REQ-0054]]).
    """
    #: **Two layers, because an expiring mark must not destroy the verdict
    #: underneath it.** `standing` holds the last PERSISTING verdict — a
    #: `pass`, a `partial`, an `na`. `transient` holds a non-persisting one and
    #: outranks it only while its own ledger is open.
    #:
    #: The first version kept one layer and *popped* on expiry, which meant a
    #: `pass` in REL-0001 followed by an `excused` in REL-0002 resolved to
    #: NOTHING once REL-0002 sealed. That contradicts decision 7 in as many
    #: words — `pass` persists *"until an invalidation event supersedes"* it,
    #: and an excuse is not an invalidation. The gate consequence was benign
    #: (owed rather than cleared) and the **burndown** consequence was not:
    #: `burndown` selects A-`pass` rows, so excusing a check on Android
    #: silently removed a real iOS parity gap from the report built to replace
    #: `PARITY_MATRIX`. Found by independent review, 2026-08-19.
    standing: dict[str, Verdict] = {}
    transient: dict[str, Verdict] = {}
    for ledger in ledgers:
        #: **By date, ties by file order.** Append-only means file order is
        #: usually chronological, and *usually* is not a property — a backfill,
        #: a hand-edit or a merge can put an older event last, and then a 2020
        #: `fail` supersedes a 2026 `pass`. A stable sort keeps the append
        #: order for same-day events, which is the only ordering the file
        #: itself can claim to know. Found by independent review, 2026-08-19.
        for entry in sorted(ledger.entries, key=lambda e: e.date):
            if entry.is_invalidation:
                #: An invalidation clears BOTH layers. It is the one event that
                #: says *the evidence is untrustworthy*, and evidence beneath a
                #: superseded excuse is no more trustworthy than evidence above
                #: it.
                standing.pop(entry.check, None)
                transient.pop(entry.check, None)
                continue
            found = Verdict(
                check=entry.check, mark=entry.mark, date=entry.date,
                by=entry.by, method=entry.method, reason=entry.reason,
                release=ledger.release if not ledger.is_working else "",
            )
            if entry.mark in PERSISTS:
                standing[entry.check] = found
                #: A new persisting verdict retires any transient one over it:
                #: walking a check settles it outright, and leaving a stale
                #: `blocked` on top would report the rig as still down.
                transient.pop(entry.check, None)
            elif ledger.is_working:
                transient[entry.check] = found
            else:
                #: Expired with its release, and it takes nothing with it.
                continue
    return {**standing, **transient}


def verdicts(docs_root: Path, platform: str) -> dict[str, Verdict]:
    """The resolved state of one platform. The join every surface reads."""
    return resolve(load(docs_root, platform))


# ------------------------------------------------------------------- append

def _today() -> str:
    return date.today().isoformat()


def append(
    docs_root: Path,
    platform: str,
    *,
    check: str,
    mark: str = "",
    by: str = "",
    method: str = "manual",
    reason: str = "",
    invalidated_by: str = "",
    when: str | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> Entry:
    """One event onto the working ledger, validated before it is written.

    **It never touches a note.** That is the property [[REQ-0055]] exists for,
    and it is guarded rather than reviewed: the read path spans 87 sites in the
    renderer alone, and a surviving frontmatter write does not raise — it puts
    a scalar back where the migration removed one.
    """
    ledger = working(docs_root, platform)
    if not ledger.is_working:                        # pragma: no cover
        raise LedgerError(f"{ledger.path} is sealed and cannot be appended to")
    raw: dict[str, Any] = {"check": check, "date": when or _today()}
    if invalidated_by:
        raw["invalidated_by"] = invalidated_by
        if reason:
            raw["reason"] = reason
    else:
        raw.update({"mark": mark, "by": by, "method": method})
        if reason:
            raw["reason"] = reason
    entry = check_entry(raw, where=f"append to {platform}")
    ledger.entries.append(entry)
    for item in evidence or []:
        ledger.evidence.append(check_evidence(
            {**item, "check": check, "date": entry.date},
            where=f"append to {platform}"))
    write(ledger)
    return entry


def blob_sha(text: str) -> str:
    """Git's blob hash for ``text`` — `sha1("blob <len>\\0" + bytes)`.

    **Computed, not shelled out.** It is the same value `git hash-object`
    prints, and computing it here means `seal()` can record the hash of a file
    it is about to write — which is what makes sealing ONE commit instead of
    two ([[ADR-0037]] decision 9a).

    A blob hash rather than a commit sha because it verifies the **bytes**
    rather than the history: an edit is caught whether it was committed,
    rebased, cherry-picked or restored from a backup.
    """
    import hashlib

    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def write(ledger: Ledger) -> None:
    if ledger.path is None:                          # pragma: no cover
        raise LedgerError("a ledger with no path cannot be written")
    ledger.path.parent.mkdir(parents=True, exist_ok=True)
    ledger.path.write_text(ledger.to_json(), encoding="utf-8")


def seal(
    docs_root: Path, platform: str, *, release: str, version: str,
    when: str | None = None,
) -> Path:
    """Close a platform's working ledger against a release.

    Sealing does two things and only one of them is bookkeeping. It assigns
    every event in the file to a release — [[ISS-0206]]'s question answered
    without a field on anything — and it is **when `excused` expires**: from
    the next resolution onward those checks are owed again, with nobody having
    to remember.
    """
    ledger = working(docs_root, platform)
    if ledger.path is None or not ledger.path.exists():
        raise LedgerError(
            f"no working ledger for {platform} — sealing an empty cycle would "
            f"record a release nobody verified anything for")
    if not _RELEASE_RE.match(release or ""):
        raise LedgerError(
            f"{release!r} is not a usable release id — it becomes part of a "
            f"filename, so it must look like `REL-0012`. `platform` was "
            f"guarded and this was not, which is the asymmetry that lets one "
            f"of two filename components escape the directory")
    ledger.release = release
    ledger.version = version
    ledger.sealed = when or _today()
    target = ledgers_dir(docs_root) / f"{release}-{platform}.json"
    if target.exists():
        raise LedgerError(f"{target.name} already exists and is sealed")
    ledger.path = target
    write(ledger)
    working_path(docs_root, platform).unlink()
    return target


def seal_record(docs_root: Path, platform: str, *, release: str, version: str,
                when: str | None = None) -> dict[str, str]:
    """Seal, and return what the release note must record to vouch for it.

    `{file, sha}` — the sealed ledger's name and its content hash. The caller
    writes it into the release note **in the same commit**, which is the whole
    point of hashing content rather than history ([[ADR-0037]] decision 9a):
    a commit sha does not exist until after the commit, so recording one would
    leave a window where the seal is unprotected and a reader cannot tell a
    half-sealed release from a tampered one.
    """
    target = seal(docs_root, platform, release=release, version=version,
                  when=when)
    return {"file": target.name,
            "sha": blob_sha(target.read_text(encoding="utf-8"))}


# ------------------------------------------------------------------ queries

@dataclass(frozen=True)
class Gap:
    """One check that holds on A and has said nothing on B."""

    check: str
    since: str
    by: str
    method: str


def burndown(docs_root: Path, a: str, b: str) -> list[Gap]:
    """Where platform B stands against platform A.

    *A-`pass` with no surviving verdict on B.* The question
    `PARITY_MATRIX.md` was hand-maintained to answer, as a query that cannot
    rot — and the first time this repo can ask it at all, because until the
    ledger there was one scalar per check and no way to say *which platform*.

    **`na` drops out by construction**: a check ruled inapplicable on B has a
    surviving verdict on B, so it is not a gap. **`excused` does not** — it
    expired with its release, so the check is owed again and appears here,
    which is exactly right: *not done this cycle* is a gap, and saying so is
    the difference between a burndown and a wish.

    The payoff [[ADR-0037]] names: an Android fix invalidates **the check**, so
    both platforms' verdicts re-arm at once. That is the structural fix for the
    `ISS-0365`/`ISS-0366` class — an iOS twin of an Android fix that never
    crossed, invisible because the matrix row already said DONE.
    """
    held = verdicts(docs_root, a)
    other = verdicts(docs_root, b)
    return [
        Gap(check=check, since=v.date, by=v.by, method=v.method)
        for check, v in sorted(held.items())
        if v.mark == "pass" and check not in other
    ]


def owed(docs_root: Path, platform: str, checks: Iterable[str]) -> list[str]:
    """Which of ``checks`` this platform still owes — the run list.

    No surviving verdict, or one that blocks. It is the same predicate the
    gate reads, which is deliberate: *"what must a person run"* and *"can we
    ship"* are the same question at two zoom levels ([[DES-0012]]), and two
    implementations of one predicate is how a badge and a gate come to
    disagree about the same corpus.
    """
    found = verdicts(docs_root, platform)
    return [c for c in checks
            if (v := found.get(c)) is None or not v.clears]
