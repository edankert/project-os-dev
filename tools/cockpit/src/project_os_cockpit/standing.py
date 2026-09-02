"""The project's standing documents: one per project, no lifecycle, human-facing.

`ISS-0125` measured the class: `README`, `INDEX`, `ARCHITECTURE`, `GLOSSARY`,
`OWNERSHIP`, `DESIGN`, `STYLEGUIDE`, `PHASES` — present in **90 of 96** possible
slots across the fleet, and **85 of those 90 stale or undated**. Not missing.
Unnamed as a set, unchecked, and unreachable — and a document nobody is ever
asked about is a document nobody updates.

**A manifest, not a type** (REQ-0033). A type models an open population: there
will be a ninth feature, a fortieth issue. There will never be a second
glossary. So the set is data, and `ISS-0124`'s question — whether these types
need status tables — is answered the other way: they carry no lifecycle status
at all, and `updated:` is the field that means something.

**Where the base set lives, and why it is not in `tools/`.** TASK-0380 assumed
the base would be template-owned and synced. It is better here: `sync-project-os.sh`
copies `tools/` wholesale, so anything a project added there would be destroyed
by the next sync — and the cockpit is never installed into a downstream repo at
all (CLAUDE.md: *"Repos are consumed by discovery, not by a shim"*). One
declaration in the app applies to every repo it renders, which is the property
"template-owned" was reaching for, without the sync hazard.

A project extends the set through its own `SNAPSHOT.yaml`, which is never
synced. That is the half that must survive an update, and it is the half that
lives in the repo being described.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StandingDocument:
    """One entry in the manifest."""

    name: str
    #: What question a reader opens it to answer. Not a description of the
    #: file — the reason it is in the set at all.
    question: str
    required: bool = True

    @property
    def filename(self) -> str:
        return f"{self.name}.md"


#: The base set, applying to every repo the cockpit renders.
BASE_STANDING: tuple[StandingDocument, ...] = (
    StandingDocument("README", "what is this project?"),
    StandingDocument("INDEX", "where do I find things?"),
    StandingDocument("ARCHITECTURE", "how is it built?"),
    StandingDocument("GLOSSARY", "what do the words mean?"),
    StandingDocument("OWNERSHIP", "who decides what?"),
    StandingDocument("DESIGN", "what should it look like?"),
    StandingDocument("STYLEGUIDE", "how is it written?"),
    StandingDocument("PHASES", "what order is it being built in?"),
)


@dataclass(frozen=True)
class Resolution:
    """How one manifest entry resolved against a real docs tree.

    `paths` carries **every** match, not the first. An entry resolving to two
    files means the set has quietly become a type, which is the drift REQ-0033
    exists to catch — and a resolver that returned the first match would hide
    it forever.
    """

    document: StandingDocument
    paths: tuple[Path, ...]

    @property
    def state(self) -> str:
        if len(self.paths) == 1:
            return "present"
        if not self.paths:
            return "missing" if self.document.required else "absent"
        return "ambiguous"

    @property
    def path(self) -> Path | None:
        return self.paths[0] if len(self.paths) == 1 else None


def _extensions_from_snapshot(project_root: Path) -> list[StandingDocument]:
    """Project-specific entries from `SNAPSHOT.yaml`'s `docs_system.standing`.

    That block exists today and **nothing reads it** — `source_of_truth`,
    `instructions`, `references`, no consumer anywhere. This gives a dead field
    its first one rather than inventing a place beside it.

    Parsed leniently: a malformed snapshot must not take the manifest with it,
    because the base set is the part that matters and it needs no snapshot.
    """
    snapshot = project_root / "SNAPSHOT.yaml"
    if not snapshot.is_file():
        return []
    try:
        import yaml

        data = yaml.safe_load(snapshot.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    block = (data.get("docs_system") or {}).get("standing") or []
    if not isinstance(block, list):
        return []
    out: list[StandingDocument] = []
    for entry in block:
        if isinstance(entry, str):
            out.append(StandingDocument(entry.strip(), "", required=True))
        elif isinstance(entry, dict):
            name = str(entry.get("name") or "").strip()
            if not name:
                continue
            out.append(StandingDocument(
                name,
                str(entry.get("question") or ""),
                required=bool(entry.get("required", True)),
            ))
    return out


#: Parsed manifests, keyed by project root and stamped with a digest of the
#: snapshot's bytes — see :func:`manifest`.
_manifest_cache: dict[str, tuple[str | None, tuple[StandingDocument, ...]]] = {}


def _snapshot_stamp(project_root: Path) -> str | None:
    """A digest of this project's snapshot, or None if it is absent.

    **Content, not `(mtime_ns, size)`**, which was the first version: two
    writes inside one filesystem timestamp tick, to the same length, would
    have served the older parse — rare, silent, and impossible to reason about
    from a wrong answer. Measured on this repo's 204 KB snapshot, the read and
    digest cost **0.114 ms against a 117 ms parse**, so the exact answer is a
    tenth of a percent of what caching it saves.
    """
    try:
        return hashlib.sha1(
            (project_root / "SNAPSHOT.yaml").read_bytes(),
            usedforsecurity=False,
        ).hexdigest()
    except OSError:
        return None


def manifest(project_root: Path) -> tuple[StandingDocument, ...]:
    """The base set plus this project's extensions, deduplicated by name.

    One function, so no consumer can read half the manifest — which is how a
    check ends up disagreeing with the surface it is meant to guard.

    **Memoised on the snapshot's own `(mtime_ns, size)`** ([[ISS-0166]]). This
    parsed a 204 KB `SNAPSHOT.yaml` on **every call**, for one field holding
    two entries — and since [[ADR-0025]] put *what needs a person* on every
    view, "every call" means up to seven times per view selection: 0.9s of
    Intent's 1.25s, against 0.03s for the one mode that never resolves the
    manifest.

    A stat rather than a TTL, so there is no staleness question to answer: the
    snapshot changing is exactly the event that invalidates this, and it is
    the only one — the base set is a module constant.
    """
    key = str(project_root)
    stamp = _snapshot_stamp(project_root)
    hit = _manifest_cache.get(key)
    if hit is not None and hit[0] == stamp:
        return hit[1]

    seen = {d.name.upper(): d for d in BASE_STANDING}
    for extra in _extensions_from_snapshot(project_root):
        seen.setdefault(extra.name.upper(), extra)
    built = tuple(seen.values())
    _manifest_cache[key] = (stamp, built)
    return built


def clear_manifest_cache() -> None:
    """Drop every memoised manifest — for tests, and for a moved workspace."""
    _manifest_cache.clear()


#: Names that also occur as container-directory signposts. `docs/issues/README.md`
#: and its eight siblings are boilerplate, not the project's README — the third
#: of the three jobs `reference` does (ISS-0125). A recursive search for
#: `README.md` finds nine of them and reports the entry ambiguous, which is a
#: sentence about the *search*, not about the corpus.
_ROOT_ONLY: frozenset[str] = frozenset({"README"})


def resolve(docs_root: Path, project_root: Path | None = None) -> list[Resolution]:
    """Resolve every manifest entry against a docs tree, in manifest order.

    The canonical location is the **docs root** — every member of this class
    sits there, which is what ISS-0125 measured. A copy deeper in the tree is a
    *rival*, and reporting it is the whole point of `Resolution.paths` carrying
    more than one path: an entry with two files has quietly become a type,
    which is the drift REQ-0033 exists to catch.

    `README` is root-only, because eight container directories carry one and
    none of them is the project's.

    **A member may live at the repo root instead**, and three of this project's
    do: `LLM_BRIEF.md`, `SECURITY.md` and `CONTEXT.md` are read before anything
    in `docs/` and ship beside it, not inside it. The docs root is still tried
    first — an entry that exists in both is the rival case, reported as
    ambiguous exactly as a deep copy would be.
    """
    root = project_root or docs_root.parent
    docs = manifest(root)

    # ONE walk for the whole manifest (ISS-0166). This was `docs_root.glob(
    # f"**/{doc.filename}")` inside the loop below — ten recursive walks of
    # ~900 notes per resolve, and Intent resolves seven times per view
    # selection. The rivals are the same question asked of one tree, so they
    # are answered by reading it once and bucketing by filename.
    # Keyed on the exact filename, not a lowercased one: `glob` is
    # case-sensitive where the filesystem is, and matching loosely here would
    # find rivals on Linux that macOS never reported — turning `present` into
    # `ambiguous` on one platform only.
    wanted = {
        doc.filename for doc in docs
        if doc.name.upper() not in _ROOT_ONLY
    }
    rivals: dict[str, list[Path]] = {name: [] for name in wanted}
    if wanted:
        for path in docs_root.rglob("*"):
            name = path.name
            if name not in rivals:
                continue
            if "__templates__" in path.parts or "__bases__" in path.parts:
                continue
            if path.is_file():
                rivals[name].append(path)

    out: list[Resolution] = []
    for doc in docs:
        canonical = docs_root / doc.filename
        matches: list[Path] = [canonical] if canonical.is_file() else []
        # The repo root is a **fallback**, never an additional match: this
        # repo has both `docs/README.md` (the docs signpost) and `README.md`
        # (the project's), and treating the root as a rival reported the entry
        # ambiguous when nothing was wrong. An entry the docs tree answers is
        # answered; only an unanswered one looks outward.
        if not matches:
            at_root = root / doc.filename
            if at_root.is_file():
                matches.append(at_root)
        if doc.name.upper() not in _ROOT_ONLY:
            matches.extend(sorted(
                p for p in rivals.get(doc.filename, ())
                if p != canonical
            ))
        out.append(Resolution(doc, tuple(matches)))
    return out


# ----- freshness, which is the only state these documents have --------------

#: Days after which a standing document is reported stale.
#:
#: 180, and the number has a reason rather than being round. These do not decay
#: like a manual test does (`MANUAL_TEST_STALE_DAYS = 60`, where "it passed
#: once" stops being an answer) — a glossary can be right for a year. What is
#: worth catching is *abandonment*, and ISS-0125 measured what that looks like:
#: `DESIGN.md` and `STYLEGUIDE.md` untouched since the day they were created,
#: six and a half months. 180 flags those and leaves a document someone revisits
#: twice a year alone.
#:
#: A parameter, not a constant of nature. Raise it if it nags; lower it if the
#: fleet's 94% does not move.
STALE_AFTER_DAYS = 180

#: Placeholder shapes that mark a document as still a template. The same
#: counting `brief_payload` does for `LLM_BRIEF.md` — one implementation of
#: "this was never filled in", not two.
_PLACEHOLDER_RE = re.compile(r"<[A-Za-z][^>\n]{2,40}>|TODO|FIXME|replace_me|YYYY-MM-DD")

#: Code is not template (ISS-0153). `<[A-Za-z]…>` matches an angle-bracket
#: token, and technical prose is full of legitimate ones — `GET /index/<type>`,
#: `user:<handle>`, `python -m project_os_cockpit <repo>/docs`. All of them are
#: correctly written inside backticks, and all of them were being counted:
#: `ARCHITECTURE.md` was reported as still holding its template while carrying
#: a full architecture diagram, because it explains a path convention.
#:
#: A real placeholder is prose in angle brackets — `<What is wrong?>`,
#: `<Change Title>` — and is never inside code. So code comes out first.
_FENCE_BLOCK_RE = re.compile(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _without_code(text: str) -> str:
    """Body with fenced blocks and inline spans removed."""
    return _INLINE_CODE_RE.sub("", _FENCE_BLOCK_RE.sub("", text))
_PLACEHOLDER_THRESHOLD = 3

_UPDATED_RE = re.compile(r'^updated:\s*"?(\d{4}-\d{2}-\d{2})', re.M)
_STATUS_RE = re.compile(r'^status:\s*\S', re.M)


@dataclass(frozen=True)
class Finding:
    """One thing wrong with one standing document.

    Four kinds, reported **distinctly**: a missing document, an entry claimed
    by two files, a document still holding its template, and one nobody has
    touched. Collapsing them into "problem" would lose the only useful part —
    what to do about it differs completely.
    """

    document: str
    kind: str      # missing | ambiguous | stub | stale | has_status
    detail: str
    severity: str  # error | warning


def check(docs_root: Path, project_root: Path | None = None,
          today: _dt.date | None = None) -> list[Finding]:
    """Every finding for this project's standing set.

    **Staleness warns and never errors.** A stale glossary is worth knowing
    about and worth nobody's build failing over — the pattern upstream ADR-0011
    established for independent review. A blocking gate on documentation nobody
    is currently reading gets disabled within a week, which is worse than a
    warning that is occasionally skipped.

    Lives here rather than in `validate_docs_bundled.py` because that file is
    template-owned and held byte-identical (ISS-0026). The rule is guarded
    locally and proposed upstream — the same split ISS-0069 and the PHASE-999
    rule took before it.
    """
    now = today or _dt.date.today()
    findings: list[Finding] = []
    for res in resolve(docs_root, project_root):
        name = res.document.name
        if res.state == "missing":
            findings.append(Finding(
                name, "missing",
                f"{res.document.filename} is absent; it answers "
                f"{res.document.question!r}",
                "error" if res.document.required else "warning",
            ))
            continue
        if res.state == "ambiguous":
            findings.append(Finding(
                name, "ambiguous",
                "two files claim this entry: "
                + ", ".join(str(p) for p in res.paths),
                "error",
            ))
            continue
        if res.path is None:
            continue
        text = res.path.read_text(encoding="utf-8", errors="replace")

        # A lifecycle status on a document with no lifecycle can only say
        # something false or say nothing (ISS-0125). `active` is in the
        # work-in-flight band, so it says the first.
        if _STATUS_RE.search(text.split("---")[1] if text.startswith("---") else ""):
            findings.append(Finding(
                name, "has_status",
                "carries a lifecycle `status:`, which for a standing document "
                "is either false or meaningless — `updated:` is its only state",
                "warning",
            ))

        body = _without_code(text.split("---", 2)[-1])
        if len(_PLACEHOLDER_RE.findall(body)) >= _PLACEHOLDER_THRESHOLD:
            findings.append(Finding(
                name, "stub", "still holds its template", "warning",
            ))

        m = _UPDATED_RE.search(text)
        if not m:
            findings.append(Finding(
                name, "stale", "carries no `updated:` date", "warning",
            ))
        else:
            age = (now - _dt.date.fromisoformat(m.group(1))).days
            if age > STALE_AFTER_DAYS:
                findings.append(Finding(
                    name, "stale",
                    f"last confirmed {age} days ago", "warning",
                ))
    return findings


@dataclass(frozen=True)
class Entry:
    """One manifest entry, resolved and judged — the shape both the Intent
    group and the obligation registry render from (TASK-0416).

    Two surfaces used to derive this independently: `cockpit._standing_group`
    resolved paths and picked a route, and `obligations` counted findings. They
    agreed by coincidence, and when they stopped, *"Intent's group came out 3
    against a badge of 5"*. One walk, two readers, is the repair.

    `kind` is the worst finding for this document, or `""` when nothing is
    wrong. Whether that kind is **owed** is deliberately not decided here —
    that is the registry's judgment, and this module must not grow a second
    opinion about it.
    """

    name: str
    question: str
    #: `/docs/<rel>` for a document under the docs root, `~root/<file>` for one
    #: beside it (LLM_BRIEF, SECURITY), `None` when it does not exist at all.
    url: str | None
    detail: str
    kind: str


def entries(docs_root: Path, project_root: Path | None = None) -> list[Entry]:
    """Every manifest entry, in manifest order, resolved and judged.

    Present or absent: a manifest of eight that yielded six would answer
    *"which of these exist"* with silence, and a missing ARCHITECTURE is the
    most interesting row in the set.
    """
    resolutions = resolve(docs_root, project_root)
    if not resolutions:
        return []
    by_doc: dict[str, list[Finding]] = {}
    for finding in check(docs_root, project_root):
        by_doc.setdefault(finding.document, []).append(finding)

    out: list[Entry] = []
    for res in resolutions:
        name = res.document.name
        own = by_doc.get(name, [])
        worst = own[0] if own else None
        # A member may live at the repo root rather than under `docs/`
        # (LLM_BRIEF, SECURITY) — three of this project's most-read documents
        # ship beside the docs tree. `~root/<file>` is the route that already
        # serves those (ISS-0037); `relative_to(docs_root)` raises on them,
        # which is how the extension announced itself.
        url: str | None = None
        if res.paths:
            try:
                url = f"/docs/{res.paths[0].relative_to(docs_root).as_posix()}"
            except ValueError:
                url = f"~root/{res.paths[0].name}"
        out.append(Entry(
            name=name,
            question=res.document.question,
            url=url,
            detail=worst.detail if worst else "current",
            kind=worst.kind if worst else "",
        ))
    return out
