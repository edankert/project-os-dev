"""The publication ladder — how far this project's work has travelled.

**Publication is the third phase** ([[ADR-0028]]), and it is the one the tool
has never had a surface for. Its obligations lived on `overview` — a view named
for *everything* — because there was nowhere else to put them.

Edwin asked for a release view and attached the question that decides its
shape: *"there are probably multiple types of releases, from committing,
pushing, deploying and actual versioned releases … should they all be shown in
this release view together with a history?"*

The fleet answers it. Measured across the twelve repos the cockpit renders on
2026-08-16:

===================  ==========================  =====  ==============================
rung                 who acts                    repos  live that day
===================  ==========================  =====  ==============================
``commit``           the agent, at close-out     12/12  --
``push``             the human, from the cockpit  8     7 commits across 4 repos
``deploy``           the human, elsewhere         2     your-applications.com at 34
``release``          the human, gated             3     your-trainer: 11 notes, 12 tags
===================  ==========================  =====  ==============================

So a ``Releases`` view would be **empty in 9 of 12 repos** — a permanent blank
button, the failure this project's `CLAUDE.md` records twice. The *ladder* is
universal: every repo commits.

**Three of the four rungs already existed.** `history_payload` returns
``remote_kind``, ``unpublished_count``, ``publication_known`` and a per-commit
``unpublished`` flag; since ISS-0168 the Push button sits with the commits it
publishes. What was missing is the fourth — ``git_state.py`` mentions "tag"
once, in a comment — and a home.

**Absent is not zero.** A rung the repo cannot reach is *omitted*, not rendered
empty: this project's standing rule, and the reason a repo with no remote reads
as complete rather than broken. A rung it *can* reach whose count is unknown
(`edankert.com`: a deploy remote with no upstream, so ``ahead`` is None) is a
row saying so — never a zero, which is the coercion ADR-0027's fourth admission
test exists to refuse and which shipped wrong once already.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import git_state

if TYPE_CHECKING:  # pragma: no cover
    from .index import Index

#: The ladder, in order. A rung's position is its meaning — work climbs.
RUNGS: tuple[str, ...] = ("commit", "push", "deploy", "release")

#: What each rung asks of a person, in the registry's vocabulary. `deploy` is
#: **named and refused** (Edwin, 2026-08-16): one fleet repo's only remote is a
#: server path, and pushing it publishes a live website. ADR-0027's third
#: admission test asks for an action the cockpit can offer **or name**; this is
#: the case that clause was written for.
RUNG_VERBS: dict[str, str] = {
    "commit": "Commit", "push": "Push", "deploy": "Deploy", "release": "Release",
}

_VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)?)")


@dataclass
class Rung:
    """One rung, and what stands at it."""

    name: str
    #: False when this repo cannot reach it — the rung is then omitted
    #: entirely rather than rendered at zero.
    reachable: bool = True
    count: int = 0
    #: True when the rung is reachable but its count cannot be taken. Never
    #: collapses to `count == 0`.
    unknown: bool = False
    #: An action the cockpit offers here, or "" when it only names one.
    verb: str = ""
    #: Why nothing is offered, when nothing is.
    refused: str = ""
    detail: str = ""
    rows: list[dict[str, Any]] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        return {
            "rung": self.name, "count": self.count, "unknown": self.unknown,
            "verb": self.verb, "refused": self.refused, "detail": self.detail,
            "rows": self.rows,
        }


def _tags(project_root: Path) -> list[dict[str, str]]:
    """Tags newest-first, or an empty list when git cannot say.

    Wrapped rather than trusted: a repo with no tags, a detached HEAD and an
    unreadable git dir must each yield nothing and take nothing down with them
    — one bad repo must not kill the fleet pass.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(project_root), "tag", "--sort=-creatordate",
             "--format=%(refname:short)%09%(creatordate:short)"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return []
    if out.returncode != 0:
        return []
    tags: list[dict[str, str]] = []
    for line in out.stdout.splitlines():
        name, _, when = line.partition("\t")
        if name.strip():
            tags.append({"name": name.strip(), "when": when.strip()})
    return tags


def baseline_ref(project_root: Path, index: "Index") -> str:
    """The tag the gate's delta is measured against — the last shipped release.

    Preference order, and each fallback is a real corpus state rather than
    defensive padding:

    1. The newest `released` note's **version**, matched to a tag by name. This
       is the honest baseline: *"since the thing I last shipped."*
    2. The newest tag by creation date, when no release note is `released` but
       tags exist — three of the twelve repos are in exactly this state, with a
       tag history and no `REL-*` notes at all.
    3. `""` — no tags. **Eleven of twelve repos.** The caller renders the
       census, not a delta.
    """
    tags = _tags(project_root)
    if not tags:
        return ""
    names = {t["name"] for t in tags}
    shipped = [
        r for r in _releases(index)
        if r["status"] == "released" and r["version"]
    ]
    shipped.sort(key=lambda r: _version_key(str(r["version"])), reverse=True)
    for release in shipped:
        version = str(release["version"]).lstrip("vV")
        for candidate in (f"v{version}", version):
            if candidate in names:
                return candidate
    return str(tags[0]["name"])


def _sealed_for(docs_root: Path, release_id: str) -> list:
    """The sealed ledgers belonging to one release, or `[]`."""
    from . import ledger as _ledger

    if not release_id:
        return []
    return [l for l in _ledger.load(docs_root) if l.release == release_id]


def _verified_for(docs_root: Path, release_id: str,
                  authored: list[str]) -> list[str]:
    """What a release verified — computed, with the authored list as fallback.

    Every check with a clearing entry in that release's ledger. `na` and
    `excused` are in it and that is not a lie: they are recorded decisions
    about this release, and a list of *what we verified* that hid them would
    be the hand-maintained excerpt this replaces.
    """
    sealed = _sealed_for(docs_root, release_id)
    if not sealed:
        return authored
    from . import ledger as _ledger

    return sorted({c for c, v in _ledger.resolve(sealed).items() if v.clears})


def _verified_platform(docs_root: Path, release_id: str) -> str:
    """Which platform's ledger the list came from."""
    return ", ".join(sorted({l.platform for l in _sealed_for(docs_root, release_id)
                             if l.platform}))


def _releases(index: "Index") -> list[dict[str, Any]]:
    """`REL-*` notes, newest id first."""
    out: list[dict[str, Any]] = []
    for record in index.notes_by_type("release"):
        if record.rel_path.startswith("__templates__/"):
            continue
        out.append({
            "id": record.note_id or "",
            "title": record.title or "",
            "status": (record.status or "").strip().lower(),
            "version": str(record.frontmatter.get("version") or "").strip(),
            # When it shipped. Empty on a draft, which is the point — `date:`
            # records when it went live and a drafted note has not.
            "date": str(record.frontmatter.get("date") or "").strip(),
            #: **Which platform this release ships** ([[TASK-0557]]). Empty
            #: means all of them — the opt-in rule [[DES-0012]] D4 gives
            #: release contents and [[ADR-0037]] gives the gate. Ten of
            #: `your-trainer`'s releases carry `android`; this repo's carry
            #: nothing, so it is one release for one platform-less world.
            "platform": str(record.frontmatter.get("platform") or "").strip().lower(),
            #: **Derived from the sealed ledger where there is one**
            #: ([[TASK-0546]], [[ADR-0037]]). A release note listing by hand
            #: what its ledger computes is two encodings of one fact — what
            #: [[ADR-0032]] spent a decision removing — and the argument does
            #: not weaken because the second encoding is short: it drifts, and
            #: the drift is silent.
            #:
            #: **The field is the fallback, not the source.** [[REL-0001]]
            #: predates the ledger and has nothing to derive from, so its 13
            #: entries stay as the record of what that release was measured
            #: against — the same two-shapes-split-by-time pattern `suite_at`
            #: uses, and for the same reason: a shipped release is immutable,
            #: so what it holds is a permanent fact about the past.
            "tests_verified": _verified_for(
                index.docs_root, str(record.note_id or ""),
                [str(v) for v in
                 (record.frontmatter.get("tests_verified") or [])]),
            #: **A release page that lists verified checks without naming the
            #: platform is this decision's own defect one level up**, so the
            #: platform travels with the list rather than being remembered by
            #: whoever renders it.
            "tests_verified_platform": _verified_platform(
                index.docs_root, str(record.note_id or "")),
            # `preparing:` is FRONTMATTER, not a status (FEAT-0105 /
            # TASK-0438). STATUSES.md allows a release only draft / released /
            # reverted and is template-owned, so adding vocabulary there would
            # report as divergence on the next sync. DES-0006 established this
            # exact pattern and obligations.py already documents it for
            # features: *"`acceptance: requested` in frontmatter, not a
            # status."* One precedent, applied again.
            "features": [
                str(f) for f in (record.frontmatter.get("features") or [])
            ],
            "preparing": bool(str(
                record.frontmatter.get("preparing") or "",
            ).strip()),
            "rel": record.rel_path,
        })
    out.sort(key=lambda r: str(r["id"]), reverse=True)
    return out


def _version_key(version: str) -> tuple[int, ...]:
    """`"2.1.6"` -> `(2, 1, 6)`; unparseable -> `()`, which sorts lowest."""
    found = _VERSION_RE.search(version or "")
    if not found:
        return ()
    return tuple(int(part) for part in found.group(1).split("."))


def preparing(index: "Index") -> dict[str, Any] | None:
    """The release a person has declared they intend to ship, or None.

    **Not merely a `draft`.** If a release is always open — which is what
    FEAT-0105 gives you — and the gate asked whenever one existed, the gate
    would ask **forever**: the self-re-arming badge ADR-0027 excludes
    staleness for, and the failure PHASE-034 was opened to avoid producing.
    Being *open* and being *prepared for ship* are different facts and only
    the second is a debt.

    `STATUSES.md` documents a release's ``draft`` as *"prepared and verified,
    not yet live"*. That is a release in preparation, it has been representable
    since the vocabulary was written, and **nothing has ever read it** — which
    is why the acceptance gate had no subject and mounted only on a note a
    reader had to already know to open.

    **A draft behind a shipped version is not in preparation.** Found by
    running this against the fleet rather than against a fixture: `your-trainer`
    carries `REL-0008` at `draft`, version **2.0.2**, while 2.0.5, 2.1.0 and
    2.1.6 have all shipped since. Gating on it would have said *"60 checks
    stand between 2.0.2 and shipping"* about a version three releases in the
    past — and, worse, it would have said it **forever**, which is precisely
    the self-re-arming badge ADR-0027 refuses and that this whole phase exists
    to avoid producing.

    Such a draft is stale record-keeping in the repo that owns it. It is
    reported by :func:`stale_drafts` so it stays visible, and it does not gate.
    """
    by_platform = preparing_by_platform(index)
    if not by_platform:
        return None
    #: **The thin wrapper the task asked for.** Six call sites read this, and
    #: a rename touching every consumer in one commit is how the last three
    #: regressions in this phase were introduced -- so they move one at a
    #: time. Where exactly one release is preparing, *the* release and *a*
    #: release are the same thing and every existing caller is correct.
    #:
    #: Where more than one is, this returns the first by the order
    #: `open_releases` already establishes (newest version first). That is a
    #: state `RELEASE-PREPARING` reports as an ERROR rather than a warning --
    #: it is what the ledger cannot represent ([[ADR-0037]]: one working
    #: ledger per platform, and sealing assigns it to a release) -- so the
    #: arbitrary pick is a stopgap over a corpus the validator refuses,
    #: never a silent choice a reader could mistake for a decision.
    ordered = [r for r in open_releases(index) if r["preparing"]]
    return ordered[0] if ordered else None


def preparing_by_platform(index: "Index") -> dict[str, dict[str, Any]]:
    """The release in preparation **for each platform** ([[TASK-0557]]).

    Edwin, 2026-08-19: *"Let's consider one release at the time only, multiple
    releases should use git branches anyway. We can potentially have multiple
    releases going on at the same time for different platforms."*

    **Two concurrent releases on one platform are a branch, not a schema
    problem**, and that is what keeps [[ADR-0037]]'s ledger intact: one working
    ledger per platform, and sealing assigns it to a release. If two releases
    were preparing on one platform, a verdict recorded today would belong to
    neither by construction.

    A release with **no** `platform:` takes them all -- the same opt-in rule
    [[DES-0012]] D4 gives release contents. It is keyed under `""`, which is
    the platform-less world every repo but `your-trainer` lives in.

    Ordered by the `open_releases` order (newest version first), so where a
    platform has more than one -- the state the validator refuses -- the entry
    is at least deterministic rather than dict-order.
    """
    out: dict[str, dict[str, Any]] = {}
    for release in open_releases(index):
        if not release["preparing"]:
            continue
        out.setdefault(release["platform"], release)
    return out


def preparing_conflicts(index: "Index") -> dict[str, list[str]]:
    """Platforms with **more than one** release in preparation ([[TASK-0557]]).

    Returned rather than raised: the validator turns it into an error, and a
    library that raised here would take down every surface that merely wanted
    to render a page.
    """
    seen: dict[str, list[str]] = {}
    for release in open_releases(index):
        if release["preparing"]:
            seen.setdefault(release["platform"], []).append(release["id"])
    return {p: ids for p, ids in seen.items() if len(ids) > 1}


def open_releases(index: "Index") -> list[dict[str, Any]]:
    """Drafts a shipped version has not overtaken — open or preparing."""
    releases = _releases(index)
    shipped = max(
        (_version_key(r["version"]) for r in releases if r["status"] == "released"),
        default=(),
    )
    live = [
        r for r in releases
        if r["status"] == "draft" and _version_key(r["version"]) > shipped
    ]
    live.sort(key=lambda r: _version_key(r["version"]), reverse=True)
    return live


def stale_drafts(index: "Index") -> list[dict[str, Any]]:
    """Drafts a later release has already overtaken.

    Named rather than dropped: a `draft` note that a shipped version passed is
    a real thing to fix, and silently ignoring it would replace one wrong
    signal with no signal.
    """
    releases = _releases(index)
    shipped = max(
        (_version_key(r["version"]) for r in releases if r["status"] == "released"),
        default=(),
    )
    return [
        r for r in releases
        if r["status"] == "draft" and _version_key(r["version"]) <= shipped
    ]


def ladder(project_root: Path, index: "Index") -> list[Rung]:
    """Every rung this repo reaches, in order."""
    try:
        state = git_state.read(project_root)
    except OSError:                       # pragma: no cover — unreadable repo
        state = git_state.GitState(
            remote=None, kind="none", ahead=None, commits=(), dirty=0,
        )

    rungs: list[Rung] = []

    # ---- commit: every repo reaches it -----------------------------------
    # **No verb, deliberately.** ADR-0027's first admission test is that a
    # PERSON must discharge it, and committing is the agent's — `close-out
    # commits its own work` (FEAT-0055). The rung is shown because it is the
    # bottom of the ladder and the only one every repo reaches; it is state,
    # not a debt.
    rungs.append(Rung(
        name="commit", count=state.dirty, verb="",
        detail=(
            f"{state.dirty} uncommitted note(s) — the agent commits these at "
            "close-out" if state.dirty else "nothing uncommitted"
        ),
    ))

    # ---- push / deploy: whichever remote this repo has --------------------
    # A repo has exactly one remote kind, so exactly one of these is reachable
    # — and merging them would put two things a person must treat differently
    # behind one number.
    for name, kind in (("push", "backup"), ("deploy", "deploy")):
        if state.kind != kind:
            rungs.append(Rung(name=name, reachable=False))
            continue
        rung = Rung(name=name, verb=RUNG_VERBS[name], detail=state.remote or "")
        if name == "deploy":
            rung.verb = ""
            rung.refused = (
                "this remote is a deployment target, not a backup — publishing "
                "it puts work live, so the cockpit names it and never sends it"
            )
        if state.ahead is None:
            rung.unknown = True
            rung.detail = "no upstream is set, so nothing can say what is unpublished"
        else:
            rung.count = len(state.commits)
            rung.rows = [
                {"id": c.sha, "title": c.subject, "detail": c.when}
                for c in state.commits
            ]
            # Absent at zero applies to the ASK as well as to the row: a rung
            # with nothing at it is still shown — that is the answer — but it
            # does not claim to need a person. A permanent `To push` on a repo
            # with nothing to push is the badge that re-arms itself.
            if not rung.count:
                rung.verb = ""
        rungs.append(rung)

    # ---- release: notes and tags -----------------------------------------
    releases = _releases(index)
    tags = _tags(project_root)
    if not releases and not tags:
        rungs.append(Rung(name="release", reachable=False))
    else:
        versions = {r["version"] for r in releases if r["version"]}
        rows: list[dict[str, Any]] = [
            {
                "id": r["id"], "title": r["title"], "status": r["status"],
                "detail": r["version"], "rel": r["rel"],
                # A tag naming the same version, so a release note and the tag
                # that shipped it read as one thing rather than two lists.
                "tagged": any(
                    _VERSION_RE.search(t["name"])
                    and _VERSION_RE.search(t["name"]).group(1) == r["version"]
                    for t in tags
                ),
            }
            for r in releases
        ]
        # A tag with no note is shown as itself rather than hidden — the note
        # is the record, but the tag is what actually shipped.
        for tag in tags:
            found = _VERSION_RE.search(tag["name"])
            if found and found.group(1) in versions:
                continue
            rows.append({
                "id": tag["name"], "title": "tag with no release note",
                # `released` rather than blank: a tag IS a thing that shipped,
                # and an empty status made the whole rung read as open work,
                # so the record never folded away (Edwin: *"the other views
                # hide completed items, so you can only see the next/current
                # items to work on"*).
                "status": "released", "detail": tag["when"], "rel": "",
                "tagged": True,
            })
        draft = preparing(index)
        rungs.append(Rung(
            name="release", count=len(releases), verb="",
            detail=(
                f"{draft['id']} in preparation" if draft
                else f"{len(tags)} tag(s)"
            ),
            rows=rows,
        ))
    return rungs


def payload(project_root: Path, index: "Index") -> dict[str, Any]:
    """The ladder as data, for the Publication view."""
    rungs = ladder(project_root, index)
    draft = preparing(index)
    return {
        "rungs": [r.payload() for r in rungs if r.reachable],
        # Named so a surface can say "this repo does not deploy" rather than
        # leaving the reader to infer it from an absence.
        "unreachable": [r.name for r in rungs if not r.reachable],
        "preparing": draft,
        # Visible, and not gating.
        "stale_drafts": stale_drafts(index),
    }


#: A release's artifacts sit beside its note and are named for it — measured
#: across `your-trainer`'s seven: `REL-0007-v2.0.0-play-store-listing.xml`,
#: `REL-0012-v2.1.6-play-store-listing.xml`, and so on. The convention has
#: held for every platform text the project has ever shipped and lives nowhere
#: but in Edwin's habit, so ADR-0028 blesses it rather than this regex
#: inferring it (FEAT-0107 / TASK-0444).
#:
#: The release NOTE itself is excluded — it is the record, not an artifact of
#: it.
def artifacts_for(docs_root: Path, release_id: str) -> list[dict[str, str]]:
    """Files in `docs/releases/` named for this release, other than its note."""
    folder = docs_root / "releases"
    if not folder.is_dir() or not release_id:
        return []
    out: list[dict[str, str]] = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or not path.name.startswith(f"{release_id}-"):
            continue
        if path.suffix.lower() == ".md":
            continue                       # the note itself
        entry: dict[str, Any] = {
            "name": path.name,
            # The kind, from the convention's trailing segment:
            # `REL-0012-v2.1.6-play-store-listing.xml` -> `play store listing`
            "kind": re.sub(
                r"^REL-\d+-v[\d.]+-", "", path.stem,
            ).replace("-", " ") or path.suffix.lstrip("."),
            "rel": f"releases/{path.name}",
        }
        entry.update(_check_artifact(path))
        out.append(entry)
    return out


#: The ceiling the store copy declares in its own header comment — *"500-char
#: ceiling per locale"*, *"Char counts asserted < 500"* — and which nothing has
#: ever checked.
_STORE_CEILING = 500
#: `en-GB`, `zh-TW`, `pt-BR`, and bare `de`. Anchored so a `<release-notes>`
#: or `<content>` wrapper is never mistaken for a locale.
_LOCALE_TAG_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,4})?$")


def _check_artifact(path: Path) -> dict[str, Any]:
    """A verdict on a published artifact, or nothing for a kind we do not know.

    **Two of `your-trainer`'s seven store XMLs do not parse.** Both end with
    leaked tool-call closing tags after the root element —
    `</release-notes></content></invoke>` — a class of corruption from the
    authoring path sitting in the declared source of truth for store copy in
    ten locales, one of them the file the public 2.0 announcement was cut from.
    Four lines of stdlib parsing turns a file-open into a verdict.

    An unknown kind is returned **without** a verdict rather than flagged: this
    knows about XML, and implying judgement over a file it does not understand
    would be the same overreach as a gate that counts what it cannot read.
    """
    if path.suffix.lower() != ".xml":
        return {"checked": False}
    import xml.etree.ElementTree as ET

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        line = getattr(exc, "position", (0, 0))[0]
        return {
            "checked": True, "ok": False,
            "problem": f"does not parse (line {line})" if line
                       else "does not parse",
        }
    except OSError:
        return {"checked": False}
    # Locale-bearing store copy. The corpus names locales as ELEMENTS —
    # `<en-GB>`, `<zh-TW>`, `<ja-JP>` under `<release-notes version="2.1.6">`
    # — not as `lang=` attributes, which is what a first pass assumed and what
    # made this return no locale count at all against real files.
    entries = [el for el in root if _LOCALE_TAG_RE.match(el.tag or "")]
    longest = max(
        (len("".join(el.itertext()).strip()) for el in entries), default=0,
    )
    out: dict[str, Any] = {"checked": True, "ok": True, "problem": ""}
    if entries:
        out["locales"] = len(entries)
        out["longest"] = longest
        if longest > _STORE_CEILING:
            out["ok"] = False
            out["problem"] = f"{longest} chars exceeds the {_STORE_CEILING} ceiling"
    return out


# ----- what a release actually verified (FEAT-0109 / TASK-0450) -------------
#
# The shipped-release page renders `tests_verified:` as links under the heading
# **Acceptance tests as executed**. Follow REL-0012's: it names TST-0011, which
# has 18 checkboxes — all unticked — and 18 `- Evidence: ___` slots, all blank,
# at `status: ready`.
#
# And the field is inert rather than merely stale: `last_verified` equals
# `created` in **15 of the 16** `TST-*` notes in `your-trainer` that carry it.
# It is written by the template at authoring time and has never once recorded a
# verification. The heading is a claim; this makes the row report instead.

_BOX_RE = re.compile(r"^\s*[-*+]\s+\[([^\]]*)\]\s", re.MULTILINE)
#: Evidence that a check was actually observed, in the three forms the corpus
#: uses — measured rather than guessed:
#:
#: * `- Evidence: <something>` — the template's slot, filled. **A blank
#:   `Evidence: ___` must not count**, which is the mutation this exists to
#:   fail; `TST-0011` has 18 of them and would otherwise grade 18/18.
#: * `✅ (Claude, tablet: address rotated …)` — the witness, 22 times in
#:   `ACCEPTANCE_CHECKLIST_v2.1.1.md`.
#: * `**Verified 2026-06-07**` / `**Partial pass …**` / `**FAILS …**` — the
#:   dated verdict, in `ACCEPTANCE_TESTS_v2.1.0.md`. Its trailing `.` and its
#:   `:` variant both appear, so the date is what anchors it, not the closing
#:   punctuation.
_EVIDENCE_RE = re.compile(
    r"Evidence:\s*(?!_+\s*$)\S"
    r"|✅\s*\("
    r"|\*\*(?:Verified|Partial pass|Open|Not reproduced|FAILS|Blocked)\s+"
    r"\d{4}-\d{2}-\d{2}",
    re.MULTILINE,
)


def _grade(record: Any) -> dict[str, Any]:
    """How much of a test note was actually walked, and with what evidence."""
    body = record.body or ""
    marks = _BOX_RE.findall(body)
    walked = sum(1 for m in marks if m.strip().lower() == "x")
    front = record.frontmatter or {}
    created = str(front.get("created") or "").strip()
    verified = str(front.get("last_verified") or "").strip()
    return {
        "total": len(marks),
        "walked": walked,
        "evidence": len(_EVIDENCE_RE.findall(body)),
        "last_verified": verified,
        # The whole point. `last_verified == created` means the field was
        # stamped by the template and never touched, which is true of 15 of 16
        # notes in the corpus — so the honest word is "never", not "stale".
        "never_verified": bool(verified) and verified == created,
    }


def release_item_payload(
    index: "Index", release_id: str, item_id: str,
) -> dict[str, Any]:
    """*What about this item, in this release* (FEAT-0117 / TASK-0472).

    Edwin: *"having features defined as they are now, makes them selectable in
    this view but instead you would like to have one view per item."* Selecting
    a feature inside a release used to `navigateTo('/docs/features/…')` — the
    plain note, with no release context at all. The thing selected and the
    thing received were mismatched.

    **The three lists are the coupling Edwin corrected the design to.** Not
    *"the checks this feature names"* — that would be the naming model he
    rejected — but originated, invalidated, and in-its-areas, which only exist
    as questions once `covers:` and `invalidated_by:` are fields.

    **The empty state is the point, not a failure.** A feature with all three
    empty is the normal case — Edwin: *"not all features might need acceptance
    tests"* — and the surface says so in words rather than rendering an empty
    page. It also shows any authored `acceptance_impact:` line, which since
    [[ADR-0036]] is a record of a question somebody answered rather than one
    anybody is being asked.
    """
    from . import acceptance as _acc

    releases = _releases(index)
    held = next((r for r in releases if r["id"] == release_id), None)
    if held is None and (release_id or "next").lower() == "next":
        live = open_releases(index)
        held = live[0] if live else None

    path = index.by_id(item_id)
    record = index.get(path) if path is not None else None
    if record is None:
        return {"exists": False, "id": item_id,
                "release": held["id"] if held else ""}

    out: dict[str, Any] = {
        "exists": True,
        "id": record.note_id or item_id,
        "title": record.title or "",
        "type": record.note_type or "",
        "status": record.status or "",
        "rel": record.rel_path,
        "release": held["id"] if held else "",
        "release_version": held["version"] if held else "",
        "release_status": held["status"] if held else "",
    }
    if (record.note_type or "") != "feature":
        # An issue selected inside a release is a real row and has no sweep.
        # Answering with the three lists anyway would invent a relationship
        # the record does not carry.
        out["acceptance_impact"] = ""
        out["impact_state"] = ""
        out["originated"] = []
        out["invalidated"] = []
        out["in_areas"] = []
        return out

    # **A read over the suite, not a sweep** (ADR-0036). This called
    # `sweep.candidates`, which computed these three lists *and* the offer of
    # what to write. The write half is withdrawn; the read half is what this
    # page has always been for — *which checks does this feature answer for* —
    # so it is inlined rather than lost with the module that hosted it.
    fid = record.note_id or item_id
    suite = _acc.load(index.docs_root, index)
    originated = [i for i in suite.items if fid in (i.refs or ())]
    # `invalidated_by:` naming this feature. Empty in every repo today — the
    # population the sweep existed to create — and kept because a note written
    # before the withdrawal still says what overtook it.
    invalidated = [
        i for i in suite.items
        if i.invalidated.change and i.invalidated.change == fid
        and i not in originated
    ]
    areas = {i.area for i in originated if i.area}
    seen = {id(i) for i in originated} | {id(i) for i in invalidated}
    in_areas = [i for i in suite.items if i.area in areas and id(i) not in seen]
    out.update({
        "acceptance_impact": str(
            record.frontmatter.get("acceptance_impact") or "").strip(),
        # No `impact_state`: nothing is owed, so there is no state to be in.
        "impact_state": "",
        "originated": [_acc._row(i) for i in originated],
        "invalidated": [_acc._row(i) for i in invalidated],
        "in_areas": [_acc._row(i) for i in in_areas],
        "subjects": [fid],
    })
    # The issues this feature closed — from the record, never inferred. A
    # feature's `fixes:`/`issues:` is what it says it closed; a heuristic over
    # dates would be a guess presented as a fact.
    closed: list[dict[str, str]] = []
    for field in ("fixes", "issues"):
        raw = record.frontmatter.get(field) or []
        values = raw if isinstance(raw, (list, tuple)) else [raw]
        for value in values:
            for found in re.findall(r"\b(ISS-\d{3,4})\b", str(value)):
                hit = index.by_id(found)
                issue = index.get(hit) if hit is not None else None
                if issue is None or any(c["id"] == found for c in closed):
                    continue
                closed.append({
                    "id": found, "title": issue.title or "",
                    "status": issue.status or "", "rel": issue.rel_path,
                })
    out["closed_issues"] = closed
    return out


def _resolve_feature_row(index: "Index", feature_id: str) -> dict[str, Any]:
    """One chosen row, resolved to a title and a link.

    The frozen branch already did this by hand because emitting the raw
    frontmatter string rendered `[[FEAT-0085-BleHardening]]` as bracket-wrapped
    slugs with no titles ([[ISS-0180]]). Chosen contents are the same
    frontmatter read the same way, so they get the same resolver rather than a
    second one.
    """
    path = index.by_id(feature_id)
    record = index.get(path) if path is not None else None
    return {
        "id": (record.note_id if record else feature_id) or feature_id,
        "title": (record.title if record else feature_id) or feature_id,
        "rel": (record.rel_path if record else ""),
    }


def _held_back_reasons(record: "Any | None") -> dict[str, dict[str, str]]:
    """`held_back:` off the release note, keyed by feature id.

    Written by `note_writes.release_contents` when somebody takes a feature
    out ([[TASK-0576]]). A hand-edited `features:` list produces held-back
    features with **no** entry here, which is a real state and is reported as
    such rather than papered over -- see :func:`_held_back_rows`.
    """
    out: dict[str, dict[str, str]] = {}
    for raw in ((record.frontmatter.get("held_back") if record else None) or []):
        if not isinstance(raw, dict):
            continue
        fid = str(raw.get("id") or "").strip()
        if not fid:
            continue
        out[fid] = {"reason": str(raw.get("reason") or ""),
                    "date": str(raw.get("date") or "")}
    return out


def _held_back_rows(
    index: "Index",
    held_ids: "set[str] | None",
    derived_rows: list[dict[str, Any]],
    record: "Any | None",
) -> list[dict[str, Any]]:
    """What this release is NOT carrying, and why ([[TASK-0576]]).

    **A count that shrinks with no cause beside it is the defect this phase
    exists to remove** -- [[ISS-0241]]'s *"89 executed by CI"* and
    [[ISS-0243]]'s *"90% complete"* are the same sentence about a different
    number. [[ADR-0040]] chose subtraction over division partly so the gate
    would stay conservative; this is the other half of that argument, which is
    that the subtraction must also be **visible**.

    `held_ids` `None` reads the record alone -- the shipped case, where the
    derived set has moved on and the frontmatter is the only record left.

    **An exclusion with no recorded reason is reported, not hidden.** The
    write path refuses a removal without one, so an empty `reason` means the
    `features:` list was hand-edited; saying so is the whole point of the
    field, and defaulting it to a plausible sentence would be the lie again.
    """
    reasons = _held_back_reasons(record)
    by_id = {str(r.get("id") or ""): r for r in derived_rows}
    ids = sorted(reasons) if held_ids is None else sorted(held_ids)
    out: list[dict[str, Any]] = []
    for fid in ids:
        row = by_id.get(fid) or _resolve_feature_row(index, fid)
        entry = reasons.get(fid) or {}
        out.append({
            "id": fid,
            "title": str(row.get("title") or fid),
            "rel": str(row.get("rel") or ""),
            "reason": entry.get("reason", ""),
            "date": entry.get("date", ""),
        })
    return out


def contents_candidates(
    index: "Index", release_id: str, platform: str = "",
) -> list[dict[str, Any]]:
    """Features a person could add to this release ([[TASK-0511]]/[[TASK-0558]]).

    **Without a candidate list the control is a text box, and a text box for an
    id is how [[ISS-0142]] happened.** The server owns the list because the
    rule it encodes -- what is already claimed elsewhere -- is the same one
    `note_writes.release_contents` refuses on, and two implementations of one
    question is [[REQ-0059]]'s forbidden shape (three instances found in this
    phase already).

    Done-but-unshipped, minus what this release already names, minus anything
    claimed by **another open release on the same platform**. Across platforms
    is not a conflict: a feature is *"more than likely delivered to multiple
    platforms"* (Edwin), and 25 of `your-trainer`'s features are cross-platform
    against 45 android-only and 9 ios-only.
    """
    here = str(platform or "").strip().lower()
    claimed: set[str] = set()
    for other in open_releases(index):
        if other["id"] == release_id or other["platform"] != here:
            continue
        path = index.by_id(other["id"])
        record = index.get(path) if path is not None else None
        for ref in ((record.frontmatter.get("features") if record else None) or []):
            for match in re.finditer(r"FEAT-\d+", str(ref)):
                claimed.add(match.group(0))

    mine: set[str] = set()
    path = index.by_id(release_id)
    record = index.get(path) if path is not None else None
    for ref in ((record.frontmatter.get("features") if record else None) or []):
        for match in re.finditer(r"FEAT-\d+", str(ref)):
            mine.add(match.group(0))

    out: list[dict[str, Any]] = []
    for row in shipping_in(index, release_id):
        fid = str(row.get("id") or "")
        if not fid or fid in mine or fid in claimed:
            continue
        out.append({"id": fid, "title": row.get("title") or fid,
                    "rel": row.get("rel") or ""})
    out.sort(key=lambda r: str(r["id"]))
    return out


#: Platform values that mean **every** platform, so a release on any one of
#: them would carry the feature.
#:
#: `cockpit._platform_match` knows `shared` and nothing else. Measured on
#: `../your-trainer` before this was written: the corpus holds 818 `android`,
#: 288 empty, 284 `ios`, 15 `cross`, 12 `web`, 10 `marketing`, 3 `all`, 1
#: `docs`, 1 `both` -- and **zero** `shared`. A rule that knows one spelling of
#: cross-platform and meets four would drop `cross`, `all` and `both` from
#: every release that named a platform, which is a silent narrowing in the one
#: direction a release surface must never move quietly.
_EVERY_PLATFORM = frozenset({"", "shared", "cross", "all", "both"})


def _ships_on(feature_platform: str, release_platform: str) -> bool:
    """Would a release on ``release_platform`` carry this feature?

    **A foreign platform is excluded; nothing else is.** The predicate is
    written as an exclusion rather than a match, and the direction is the
    point: an unset, `cross` or unrecognised platform stays in, so a feature
    leaves a release's contents only when it says, in so many words, that it
    belongs to a different one. That is the same conservative direction
    [[ADR-0040]] chose for check subtraction -- selection may only ever remove
    what somebody can point at.

    A release that has not said what it ships takes everything, which is the
    opt-in rule [[DES-0012]] D4 already gives release contents and the
    acceptance gate.
    """
    f = str(feature_platform or "").strip().lower()
    r = str(release_platform or "").strip().lower()
    if r in _EVERY_PLATFORM:
        return True
    return f in _EVERY_PLATFORM or f == r


def _platform_of_release(index: "Index", release_id: str) -> str:
    path = index.by_id(release_id) if release_id else None
    record = index.get(path) if path is not None else None
    if record is None:
        return ""
    return str(record.frontmatter.get("platform") or "").strip().lower()


def shipping_in(index: "Index", release_id: str = "") -> list[dict[str, Any]]:
    """The features a release would freeze — the derived done-but-unshipped set,
    **on this release's platform**.

    Exposed for `mark_released` (TASK-0469), which has to write this list down
    at the moment of shipping. `../your-trainer`'s REL-0013 is the reason: it
    was prepared by the cockpit with `features: []`, so the moment its status
    flips its page reads *"What shipped — 0 feature(s)"* — the list was always
    derived and never frozen, and shipping is exactly when there stops being
    anything to derive it from.

    **`release_id` is no longer decorative** ([[ISS-0261]]). It used to be
    accepted and unused, on the reasoning that only one release is open at a
    time so the derived set is the same for all of them. That is true of
    *which* releases are open and false of *what they ship*: `your-trainer`'s
    REL-0013 declares `platform: android` and was offered nine iOS features and
    an iOS-parity feature, none of which any Android build can contain. There
    is not one `ios/*` tag in that repo, so they could never leave the list by
    shipping either — they would have sat on every Android release forever.

    **`unreleased_payload` is deliberately left alone.** Those features *are*
    unreleased and the fleet card is right to say so; what is wrong is offering
    them to a release that cannot carry them. Filtering the card instead would
    hide genuinely unshipped work, which is the opposite defect.
    """
    from .cockpit import unreleased_payload, _record_platform

    rows = list(unreleased_payload(index).get("items") or [])
    release_platform = _platform_of_release(index, release_id)
    if release_platform in _EVERY_PLATFORM:
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        path = index.by_id(str(row.get("id") or ""))
        record = index.get(path) if path is not None else None
        #: A row whose note cannot be resolved stays: the fail-closed
        #: direction here is to keep offering it, not to drop it silently.
        if record is None or _ships_on(_record_platform(record), release_platform):
            out.append(row)
    return out


def _acc_module() -> Any:
    """Imported lazily, the way every other acceptance reader here does it —
    `publication` and `acceptance` would otherwise import each other."""
    from . import acceptance as _acc
    return _acc


def _open_tests_for_contents(
    index: "Index", content_ids: set[str], suite: Any,
) -> list[dict[str, Any]]:
    """The checks still owed **for the features this release actually carries**
    ([[TASK-0504]]).

    Edwin: *"these should either show a list of open tsts or suggest something
    else."*

    **The predicate is settledness, not `status:`.** An acceptance check sits
    at `status: active` for its whole life -- the verdict lives in `mark:` and
    the ledger ([[ADR-0037]]) -- so filtering on status returns every check
    that covers a release feature, settled or not. Measured on `your-trainer`'s
    working tree, 2026-08-20: **94 by status, 3 by settledness.** The first
    number is an inventory; only the second is work.

    That 3-of-66 is also [[ADR-0040]]'s argument arriving from the other end:
    the gate is dominated by checks for features this release does not carry.
    """
    if not content_ids:
        return []
    rows: list[dict[str, Any]] = []
    for item in suite.items:
        if item.settled:
            continue
        hit = sorted({
            m.group(0)
            for ref in item.refs
            for m in re.finditer(r"FEAT-\d+", str(ref))
        } & content_ids)
        if not hit:
            continue
        rows.append({
            "id": item.note_id, "number": item.number, "name": item.name,
            "area": item.area, "rel": item.rel, "mark": item.mark,
            "features": hit,
        })
    #: Grouped by the feature a reader is thinking about, then by id so the
    #: order is stable between renders.
    rows.sort(key=lambda r: (r["features"][0], str(r["id"] or "")))
    return rows


def release_payload(
    project_root: Path, index: "Index", release_id: str = "next",
) -> dict[str, Any]:
    """One answer for the release page (FEAT-0106 / TASK-0440).

    What is in this release, what state it is in, and what stands between it
    and shipping — assembled from the computations that already exist rather
    than from new ones. `unreleased_payload` for what has not shipped,
    `acceptance.gate_payload` for the gate.

    ``next`` answers **even when no release note exists**, which is the
    ordinary case: the open release is derived and nothing is written until a
    person declares one.
    """
    from . import acceptance
    from .cockpit import unreleased_payload

    wanted = (release_id or "next").strip()
    releases = _releases(index)
    held: dict[str, Any] | None = None
    if wanted.lower() == "next":
        live = open_releases(index)
        held = live[0] if live else None
    else:
        held = next((r for r in releases if r["id"] == wanted), None)

    shipped = held is not None and held["status"] == "released"
    if shipped:
        # A shipped release names what it carried; the derived set has moved
        # on. The frozen list is the record and must not be recomputed.
        # **Resolved, not raw** (ISS-0180). This emitted the frontmatter
        # strings verbatim — `[[FEAT-0085-BleHardening]]` — so a shipped
        # release's page listed bracket-wrapped slugs with no titles and no
        # links, while the NEXT release's rows were fully resolved. Edwin:
        # *"you didn't fix any of the actual page issues like the table and
        # the feature links, for the completed features."*
        rows = []
        for raw in held.get("features") or []:
            found = re.search(r"\[\[([^\]|]+)", str(raw))
            target = found.group(1) if found else str(raw).strip()
            path = index.by_id(target)
            record = index.get(path) if path is not None else None
            rows.append({
                "id": (record.note_id if record else target),
                "title": (record.title if record else target),
                "rel": (record.rel_path if record else ""),
            })
        contents = {
            "kind": "frozen",
            "ids": [r["id"] for r in rows],
            "rows": rows,
            "count": len(rows),
            "since": "",
            #: **The seal freezes the exclusions too** ([[TASK-0576]]). What a
            #: release held back, and why, is part of what it was measured
            #: against -- a shipped release whose gate was smaller than the
            #: repo's must still say what made it smaller.
            "held_back": _held_back_rows(
                index, None, [],
                index.get(index.by_id(held["id"]))
                if held and index.by_id(held["id"]) is not None else None),
        }
    else:
        # `unreleased_payload`'s own keys: `items` and `since` (FEAT-0072).
        # Read them rather than inventing near-misses — a second vocabulary
        # for one computation is how two surfaces come to disagree.
        unshipped = unreleased_payload(index)
        since = unshipped.get("since") or {}
        since_id = since.get("id", "") if isinstance(since, dict) else str(since)

        #: **`held["id"]`, not `release_id`.** The argument is `"next"` on the
        #: page a person actually lands on, and `index.by_id("next")` is
        #: `None` — so `named` came back empty and the subtraction below could
        #: not fire for the one release anybody is preparing. The resolved id
        #: is the release; the argument is how it was asked for.
        _rel_id = held["id"] if held else ""
        #: **The derived set is this release's platform's** ([[ISS-0261]]).
        #: `unreleased_payload` answers *what has not shipped anywhere*; a
        #: release page asks *what could this release carry*, and the two are
        #: the same question only in a single-platform repo.
        derived_rows = shipping_in(index, _rel_id)
        _rel_path = index.by_id(_rel_id) if _rel_id else None
        _rel_rec = index.get(_rel_path) if _rel_path is not None else None
        named_order: list[str] = []
        for raw in ((_rel_rec.frontmatter.get("features") if _rel_rec else None) or []):
            for m in re.finditer(r"FEAT-\d+", str(raw)):
                if m.group(0) not in named_order:
                    named_order.append(m.group(0))
        named = set(named_order)

        #: **CHOSEN is a different kind from DERIVED, and the page has always
        #: known it** ([[FEAT-0142]] scope: *"the page distinguishes derived
        #: rows from chosen rows"*). The renderer offers `Remove` only on
        #: `c.kind !== 'derived'` and has a test pinning that guard — but
        #: nothing ever emitted a third kind, so the control was unreachable
        #: and a feature could be added through the front door and never taken
        #: back out through it. Naming one feature is the semantic jump the
        #: compose warning announces; this is that jump arriving in the
        #: payload.
        if named:
            rows = [_resolve_feature_row(index, fid) for fid in named_order]
            contents = {
                "kind": "chosen",
                "count": len(rows),
                "since": since_id,
                "rows": rows,
            }
        else:
            rows = derived_rows
            contents = {
                "kind": "derived",
                #: `len(derived_rows)`, not `unshipped["count"]` — the card's
                #: count is fleet-wide and this list is platform-scoped, and a
                #: heading that disagrees with the rows under it is worse than
                #: either number alone.
                "count": len(derived_rows),
                "since": since_id,
                "rows": rows,
            }

    # A SHIPPED release shows the record as it stood, not today's gate. It
    # verified a snapshot — `ACCEPTANCE_CHECKLIST_v2.1.1` for REL-0012 — and
    # recomputing the live suite for it would answer a question nobody asked
    # about a release that shipped in July.
    if shipped:
        gate: dict[str, Any] = {}
    else:
        # Oldest-first for `ages`, which wants the FIRST tag a row was already
        # unsettled at; `_tags` returns newest-first for the ladder.
        ordered = [t["name"] for t in reversed(_tags(project_root))]
        #: **What this release held back** ([[FEAT-0129]] / [[TASK-0512]]).
        #: A release that NAMES contents has, by naming them, deselected every
        #: derived feature it did not name -- and [[ADR-0040]] says selection
        #: subtracts: a check drops only when every feature it covers was held
        #: back. A release naming nothing deselects nothing, which is the
        #: derived behaviour eleven historical releases depend on.
        #: **From the NOTE's frontmatter, not from `held`.** `_releases()`
        #: builds id/title/status/version/date/platform and no `features` key,
        #: so the first cut of this read `held.get("features")`, got `None`
        #: every time, and the subtraction could never fire -- caught only by
        #: testing the POSITIVE case (a release that names three of its
        #: thirty-two) rather than the invariant, which passed either way.
        #:
        #: **Held back is measured against the DERIVED set**, which is what
        #: the release would have carried had nobody chosen. `contents.rows`
        #: is no longer that set once a release names its contents, so reading
        #: it here would make the held-back set empty exactly when it matters.
        held_back = (
            {str(r.get("id") or "") for r in derived_rows} - named
            if named else set()
        )
        contents["held_back"] = _held_back_rows(
            index, held_back, derived_rows, _rel_rec)
        gate = acceptance.gate_payload(
            index.docs_root,
            index=index,
            project_root=project_root,
            baseline_ref=baseline_ref(project_root, index),
            tags=ordered,
            deselected=held_back,
        )
    verified: list[dict[str, Any]] = []
    known_issues = ""
    owed: list[dict[str, Any]] = []
    if held is not None:
        path = index.by_id(held["id"])
        record = index.get(path) if path is not None else None
        if record is not None:
            for raw in record.frontmatter.get("tests_verified") or []:
                note_id = str(raw)
                found = re.search(r"\[\[([^\]|]+)", note_id)
                target = found.group(1) if found else note_id
                hit = index.by_id(target)
                named = index.get(hit) if hit else None
                row: dict[str, Any] = {
                    "id": target,
                    "rel": named.rel_path if named else "",
                    # An entry naming a note the corpus does not carry is said
                    # so, rather than rendered as a link that goes nowhere.
                    "resolved": named is not None,
                    "title": named.title if named else "",
                }
                if named is not None:
                    row["grade"] = _grade(named)
                else:
                    # **A claim is not a broken link** (TASK-0471). 11 of the
                    # corpus's 15 `tests_verified` entries are recorded
                    # sentences — *"Unit tests: 614 tests, all passing"* — and
                    # every one rendered as *"not in this corpus"*, which reads
                    # as a defect in the record rather than as the record.
                    # An entry that does not look like an id never was one.
                    row["claim"] = not bool(
                        re.fullmatch(r"[A-Z]{2,6}-\d{2,}", target.strip()))
                verified.append(row)
            owed = still_owed(record, index, project_root,
                              shipped_on=str(held.get('date') or ''))
            raw_issues = _known_issues(record.body)
            if raw_issues:
                from . import renderer as _renderer

                # Rendered, not printed. This came back as raw markdown and
                # the page showed it with `white-space: pre-wrap`, so a
                # known-issues TABLE displayed as a column of pipe characters
                # (ISS-0180). Rendering it here rather than in the client
                # keeps one markdown pipeline — wikilinks in those cells
                # resolve through the same index as everywhere else.
                known_issues = _renderer.render_markdown_text(
                    raw_issues,
                    source_path=index.docs_root / (record.rel_path or "x.md"),
                    resolver=index.resolve,
                    asset_resolver=index.resolve_asset,
                )
    return {
        "id": held["id"] if held else "",
        "version": held["version"] if held else "",
        "status": held["status"] if held else "",
        "preparing": bool(held and held["preparing"]),
        "exists": held is not None,
        "title": held["title"] if held else "Next release",
        "rel": held["rel"] if held else "",
        "contents": contents,
        # **What could be added** (TASK-0511). Server-owned because the rule it
        # encodes — what another open release on this platform already claims —
        # is the one `release_contents` refuses on, and two implementations of
        # one question is REQ-0059's forbidden shape.
        "contents_candidates": (
            [] if shipped else contents_candidates(
                index, held["id"] if held else "",
                str((held or {}).get("platform") or ""))
        ),
        # **What is still owed for what this release carries**
        # (TASK-0504). Distinct from `gate`, which counts every
        # unsettled check in the repo: this one is scoped to the
        # contents above, which is the question a release asks.
        "open_tests": _open_tests_for_contents(
            index,
            {str(r.get("id") or "") for r in (contents.get("rows") or [])},
            _acc_module().load(index.docs_root, index=index),
        ),
        "gate": gate,
        # What this release verified, and what it shipped with unfixed — the
        # two halves Edwin described, both already in the record and read by
        # nothing until now.
        "tests_verified": verified,
        # HTML, rendered through the one markdown pipeline.
        "known_issues_html": known_issues,
        "artifacts": artifacts_for(index.docs_root, held["id"] if held else ""),
        # What the release asked for after shipping and nobody came back to.
        # Reads the same note the known-issues section comes from.
        "still_owed": owed,
        # **Counted honestly** (TASK-0471). REL-0010's heading says 11; the
        # truth is 1 open + 2 done + 8 unknowable. One number over three
        # populations is a number nobody can act on, and the eight unknowable
        # ones are why: nothing outside the repo can tell whether a store
        # listing was updated.
        "still_owed_split": _owed_split(owed),
        # **Confidence, rolled up** (TASK-0471). Edwin asked *"is this a
        # feature stat"* — it is not. It is a CHECK property (`automation:`)
        # summed over the checks touching what shipped, so the page reports it
        # without anybody authoring the same fact twice.
        "confidence": _confidence(index, contents.get("rows") or []),
        "stale_drafts": stale_drafts(index),
    }


def _owed_split(owed: list[dict[str, Any]]) -> dict[str, int]:
    """`N open · M done · K unknowable`, open first."""
    out = {"open": 0, "done": 0, "unknowable": 0}
    for row in owed:
        verdict = str(row.get("verdict") or "")
        if verdict in out:
            out[verdict] += 1
        elif row.get("done") or verdict == "settled":
            out["done"] += 1
        else:
            out["open"] += 1
    return out


def _confidence(index: "Index", rows: list[dict[str, Any]]) -> dict[str, Any]:
    """How much of what shipped is covered mechanically, from `automation:`.

    Scoped to the checks that name a shipped item in `covers:` — a roll-up over
    the whole suite would answer a question about the project rather than about
    this release. A release whose features originated no checks reports zero of
    each and says so, which is a true sentence and not an empty one.
    """
    from . import acceptance

    ids = {str(row.get("id") or "") for row in rows
           if isinstance(row, dict) and row.get("id")}
    if not ids:
        return {"total": 0, "full": 0, "partial": 0, "manual": 0, "scoped": False}
    suite = acceptance.load(index.docs_root, index)
    touching = [i for i in suite.items if ids & set(i.refs)]
    out = {"total": len(touching), "full": 0, "partial": 0, "manual": 0,
           "scoped": True}
    for item in touching:
        key = (item.automation or "manual").strip().lower()
        if key in out:
            out[key] += 1
        else:
            out["manual"] += 1
    return out


# ----- still owed by a shipped release (FEAT-0110) --------------------------
#
# Eight of `your-trainer`'s twelve release notes carry a post-release checklist
# and **37 boxes are unticked**. The release page already reads `## Known
# issues` out of the same note and walks straight past the only section that
# contains outstanding work.
#
# The sharpest one, checked 2026-08-16: REL-0010 (v2.0.5, shipped 2026-05-23)
# says to flip `investigation_status` in `compatibility.json` on
# `your-applications.com`. It still reads `investigating`. Riders have seen a
# warning for 85 days after the fix shipped, and the only thing that remembers
# is an unticked checkbox in a Markdown file nothing reads.

#: Matched at `##`, `###` or `####` — **five of the eight use `###`**, and a
#: reader anchored on `##` finds 12 boxes where the corpus holds 37. Measured,
#: not assumed.
#:
#: `## Post-Release Review — PHASE-010 findings` is deliberately NOT matched:
#: it is a retrospective, not a list of actions, and sweeping it in would put
#: prose bullets under a heading that offers to tick them.
_POST_RELEASE_RE = re.compile(
    r"^(#{2,4})\s+.*\b(?:post[-\s]?release\s+actions?|follow[-\s]?up)\b.*$",
    re.IGNORECASE,
)
_CHECK_RE = re.compile(r"^\s*[-*+]\s+\[([^\]]*)\]\s+(.*)$")


def post_release_actions(body: str) -> list[dict[str, Any]]:
    """Unticked boxes under the note's post-release heading, with their lines.

    The section ends at a heading **at or above** its own level, so a `####`
    subsection inside a `###` checklist stays part of it — the ISS-0172 rule,
    which this project has already had to learn once on a different parser.
    """
    out: list[dict[str, Any]] = []
    inside = False
    level = 0
    previous = ""
    for number, line in enumerate(body.splitlines()):
        heading = re.match(r"^(#{1,6})\s", line)
        if heading and inside and len(heading.group(1)) <= level:
            inside = False
        found = _POST_RELEASE_RE.match(line)
        if found:
            inside, level = True, len(found.group(1))
            previous = ""
            continue
        if not inside:
            previous = line
            continue
        box = _CHECK_RE.match(line)
        if box and not box.group(1).strip():
            if not _renders_as_a_box(previous, line):
                previous = line
                continue
            out.append({"text": box.group(2).strip(), "line": number})
        previous = line
    return out


def _renders_as_a_box(previous: str, line: str) -> bool:
    """Whether this source line actually becomes a checkbox on screen.

    ISS-0175's trap, which this project has already paid for once. A task list
    opening immediately after a **paragraph** line, with no blank line between
    them, is absorbed into that paragraph by Markdown's lazy continuation: it
    renders **zero** checkboxes while a line-based reader counts every one.
    That mismatch left 285 of 542 rows carrying another row's text.

    **Asked of the renderer rather than guessed**, which is the whole lesson.
    A first attempt used the obvious heuristic — *"refuse when the previous
    line is not itself a checkbox"* — and it was wrong on the corpus: after a
    numbered list item, `- [ ] x` becomes a **sibling list item** and renders
    fine. Markdown's rules here are not reconstructible by eye, so the two
    lines are handed to the same markdown pipeline the page uses and the
    answer is read off the output.

    Refusing is the safe direction: an unread box is one somebody still has to
    find, while a mis-addressed tick is a record nobody can recover.
    """
    if not previous.strip():
        return True                      # a blank line always opens a list
    import markdown

    from .renderer import MARKDOWN_EXTENSIONS_BASE

    html = markdown.markdown(
        f"{previous}\n{line}\n", extensions=list(MARKDOWN_EXTENSIONS_BASE),
    )
    return 'type="checkbox"' in html


_TAG_RE = re.compile(r"git\s+tag\s+`?([A-Za-z0-9._-]+)`?")
#: Two shapes, both in the corpus and neither reducible to the other:
#:
#:   Set `status: fixed` on ISS-0268 + ISS-0269 …
#:   Update REL-0010 status to `published`
#:
#: The first names the status then the notes; the second names the note then
#: the status. A pattern for one silently returns "unknowable, no evidence" for
#: the other, which is how four boxes instructing an impossible status went
#: unexplained on the first pass.
_STATUS_RE = re.compile(
    r"`?status:\s*`?\s*`?(?P<want>[a-z]+)`?(?P<tail>[^.]*)", re.IGNORECASE,
)
_STATUS_TO_RE = re.compile(
    r"(?P<tail>.*?)\bstatus\s+to\s+`?(?P<want>[a-z]+)`?", re.IGNORECASE,
)
_ID_IN_TEXT_RE = re.compile(r"\b([A-Z]{2,6}-\d{3,4})\b")

#: Verdicts. Exactly three, and the third is load-bearing: an unknowable box is
#: honest, a silently-carried one is not.
DONE, OPEN, UNKNOWABLE = "done", "open", "unknowable"

#: Per-type status vocabularies, for judging whether a box asks for something
#: achievable. Imported from the validator's table rather than restated — that
#: table is the one the pre-commit gate enforces, and a second copy here would
#: let this page bless a status the validator rejects.
try:                                              # pragma: no cover
    from .validate_docs_bundled import ALLOWED_STATUS as _ALLOWED_STATUS
except Exception:                                 # pragma: no cover
    _ALLOWED_STATUS: dict[str, set[str]] = {}


def verdict_for(
    text: str, index: "Index", tags: "set[str] | None" = None,
) -> dict[str, str]:
    """What the record says about one unticked post-release box.

    Only lookups that already exist: does a tag exist, and does a note carry a
    named status. **Everything else is `unknowable`**, including every box that
    names a file in another workspace — inferring from prose that a sibling
    repo's JSON field has the right value would be a guess, and a wrong
    `done` here is the one outcome that destroys a record rather than
    preserving it.
    """
    tag = _TAG_RE.search(text)
    if tag:
        # `git push origin v2.0.5` is NOT this: a local tag existing says
        # nothing about whether it was pushed, and the box asks about pushing.
        if "push" in text.lower().split("git tag")[0]:
            return {"verdict": UNKNOWABLE, "evidence": "asks about pushing"}
        name = tag.group(1)
        if tags is None:
            return {"verdict": UNKNOWABLE, "evidence": "tags unavailable"}
        if name in tags:
            return {"verdict": DONE, "evidence": f"tag {name} exists"}
        return {"verdict": OPEN, "evidence": f"tag {name} does not exist"}

    status = _STATUS_RE.search(text) or _STATUS_TO_RE.search(text)
    if status:
        wanted = status.group("want").strip().lower()
        ids = _ID_IN_TEXT_RE.findall(status.group("tail"))
        if not ids:
            return {"verdict": UNKNOWABLE, "evidence": "names no note"}
        seen: list[str] = []
        for note_id in ids:
            path = index.by_id(note_id)
            record = index.get(path) if path is not None else None
            if record is None:
                return {"verdict": UNKNOWABLE,
                        "evidence": f"{note_id} is not in the record"}
            # `published` is instructed by FOUR release notes and is not a
            # release status — STATUSES.md allows draft / released / reverted.
            # Checked against the note's OWN type rather than the global
            # vocabulary, because `published` is a perfectly good status for
            # other types and the global check therefore never fires.
            #
            # `unknowable`, not `open`: the box asks for something that cannot
            # be done, and reporting it as open would invite someone to write
            # an invalid status to satisfy it. A template defect, owed
            # upstream, not fixable from this page.
            got = (record.status or "").strip().lower()
            allowed = _ALLOWED_STATUS.get(record.note_type or "")
            if allowed and wanted not in allowed:
                from . import statuses as _statuses

                note = (f"`{wanted}` is not a valid "
                        f"{record.note_type} status")
                # Two very different situations wear the same wording, and
                # collapsing them hides the one that matters:
                #
                #   `published` on REL-0010, which IS `released` — stale
                #   phrasing for something already terminal.
                #   `passing` on REQ-0183, which is still `draft` — nothing
                #   has moved in 85 days and the 30-day window closed in June.
                #
                # Calling both unknowable would bury a live obligation behind
                # a wording complaint. The instruction is still reported as
                # unachievable either way; what changes is whether the row
                # says anyone needs to look.
                if got in _statuses.COMPLETED_STATUSES:
                    return {"verdict": UNKNOWABLE,
                            "evidence": f"{note}; {note_id} is {got}"}
                return {"verdict": OPEN,
                        "evidence": f"{note}; {note_id} is {got or 'unset'}"}
            seen.append(f"{note_id} is {got or 'unset'}")
            if got != wanted:
                return {"verdict": OPEN, "evidence": ", ".join(seen)}
        return {"verdict": DONE, "evidence": ", ".join(seen)}

    return {"verdict": UNKNOWABLE, "evidence": ""}


def _age_days(since: str) -> int:
    """Days from an ISO date to today, or ``0`` when it cannot be read.

    ``0`` rather than a guess: a release note with no `date:` is a draft, and
    inventing an age for one would put a number on the page that nothing in
    the record supports.
    """
    from datetime import date

    try:
        year, month, day = (int(part) for part in since.split("-")[:3])
        return max(0, (date.today() - date(year, month, day)).days)
    except (TypeError, ValueError):
        return 0


def still_owed(
    record: Any, index: "Index", project_root: Path, shipped_on: str = "",
) -> list[dict[str, Any]]:
    """Every unticked post-release box on a release note, with its verdict.

    An **open** box carries an age in days from the release date. That is the
    difference between *"this is outstanding"* and *"this has been outstanding
    for 85 days and four releases have shipped over it"*, and the second is
    the one that makes anybody act.
    """
    tags = {t["name"] for t in _tags(project_root)}
    age = _age_days(shipped_on)
    out: list[dict[str, Any]] = []
    for box in post_release_actions(record.body or ""):
        row = {**box, **verdict_for(box["text"], index, tags)}
        # Only on `open`. An age on a done box is noise, and an age on an
        # unknowable one implies the tool knows it is outstanding.
        row["age_days"] = age if row["verdict"] == OPEN else 0
        out.append(row)
    return out


#: The section a release note uses for what it shipped with unfixed. Six of
#: `your-trainer`'s twelve carry one, under this heading or a near variant, so
#: the match is on the WORDS rather than on an exact string.
_KNOWN_ISSUES_RE = re.compile(
    r"^##\s+.*\b(known issues|shipping with|shipped with)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


def _known_issues(body: str) -> str:
    """The release note's own known-issues section, verbatim, or ``""``."""
    match = _KNOWN_ISSUES_RE.search(body or "")
    if match is None:
        return ""
    rest = body[match.end():]
    end = re.search(r"^##\s", rest, re.MULTILINE)
    return (rest[: end.start()] if end else rest).strip()
