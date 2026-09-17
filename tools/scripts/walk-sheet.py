#!/usr/bin/env python3
"""Generate a release walk sheet: the owed acceptance checks as a procedure.

A walk sheet is what a person reads while walking a release. It opens with the
screens the release changed, then lists every check the platform still owes, in
the order the project authored, with each check's setup, steps and expected
result printed on the page. The rules it implements are stated once in
`tools/instructions/TESTING.md`, "The walk" (project-os-dev ADR-0029); this
file restates none of them and is the only code that computes a walk.

WHY A GENERATOR AND NOT A NOTE
------------------------------
Every consumer with a large suite has written this document by hand, once per
release, and thrown it away. `your-trainer`'s is 719 lines, headed TEMPORARY,
written three times. It could never be generated because nothing in the system
held the order -- so this reads the order from one authored file that survives
releases, and everything else from the ledger.

WHAT IT READS, AND NOTHING ELSE
-------------------------------
  * the acceptance notes -- `level: acceptance`, their `area:`, `after:`,
    `covers:`, `command:` and their Setup / Steps / Expect sections;
  * `docs/releases/ledgers/{WORKING,REL-####}-<platform>.json`, sealed and open;
  * `docs/tests/acceptance/WALK.md`, the project's authored sitting order;
  * `docs/tests/acceptance/walk/*.md`, one written procedure per sitting;
  * the `SUR-*` notes, for their titles, their `parent:` and their `gallery:`;
  * `docs/changes/CHG-*.md` added since the last release tag, for the `##
    Impact` list that says which screens each one altered;
  * `git`, to find that tag and to date the change notes against it. This is
    the only subprocess it runs, and a checkout without the tag loses the
    survey and nothing else.

--check
-------
`--check` walks the procedures instead of printing a sheet: it fails when a
procedure and the release's owed set disagree ("The walk", rule 9). Exit 1 =
at least one procedure is wrong, 0 = nothing to fix. `validate-docs.sh` runs
it for every platform that has a ledger.

It writes markdown and never reads a sheet back. A generated sheet may be kept
as a record of what was walked; it is never edited by hand and nothing parses
it ("The walk", rule 1). `--out` is therefore optional: the sheet goes to
stdout unless a path is named.

THE OWED PREDICATE IS THE GATE'S
--------------------------------
A row is a manual check (feature or regression section, so no `command:`) with
no surviving clearing verdict for this platform. That is `ledger.owed()` in
`project-os-cockpit`, reproduced here entry for entry, because two
implementations of one predicate is how a badge and a gate come to disagree
about one corpus. The cockpit bundles this module rather than writing a second
one ("The walk", rule 7).

Exit codes: 0 = a sheet was produced, 2 = usage error or no ledger in this repo.

Stdlib only. Usage:
    walk-sheet.py --release REL-0017 --platform android [--out PATH] [--repo-root DIR]
    walk-sheet.py --check [--platform android] [--repo-root DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# --------------------------------------------------------------- note reading

#: Loaded lazily, so a host that already has a note index (the cockpit) can
#: import `build_walk` and `render` without dragging the validator in.
_VD = None


def _validator():
    """The validator's frontmatter reader, shared rather than rewritten.

    Two frontmatter parsers that disagree is a class of drift, not a bug, and
    `sync-snapshot.py` reuses this one for the same reason.
    """
    global _VD
    if _VD is None:
        import importlib.util as ilu
        here = Path(__file__).resolve().parent / "validate-docs.py"
        spec = ilu.spec_from_file_location("_vd_walk", here)
        module = ilu.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        _VD = module
    return _VD


#: `TASK-0825`, and `CHG-20260913` out of `CHG-20260913-The-Banner-Moves`.
#: **Two or more digits, not three or four**: a change note's id carries an
#: eight-digit date, so the narrower pattern matched every task and no change
#: at all -- and an invalidation naming a change then produced a survey entry
#: with no id, no title and no quoted section. Found by independent review,
#: 2026-09-13; your-trainer's ledger happens to hold only `TASK-*` ids, which
#: is why generating a real sheet did not show it. The index a change note is
#: filed under is `CHG-20260913`, which is what this must return.
ID_RE = re.compile(r"\b([A-Z]{2,6})-(\d{2,})\b")
#: The status that takes a check off the list without deleting it. **`retired`
#: alone**, and the narrowness is the point: `superseded` is not a legal status
#: for a `[[test]]` (`STATUSES.md` `[[test]]`), and adding it here made this
#: generator report one fewer owed row than the cockpit's page on the same
#: corpus -- a second disagreement introduced while fixing the first, which is
#: precisely what ISS-0303 is about. The predicate is `acceptance._is_retired`,
#: reproduced.
RETIRED = frozenset({"retired"})
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def _ids(value) -> list[str]:
    items = value if isinstance(value, list) else [value]
    out = []
    for item in items:
        if not isinstance(item, str):
            continue
        for m in ID_RE.finditer(item):
            out.append("%s-%s" % (m.group(1), m.group(2)))
    return out


def _text(value) -> str:
    return str(value or "").strip().strip("\"'")


def body_of(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text


def section(body: str, *names: str) -> str:
    """The text under the first of ``names`` that the note has, verbatim.

    Verbatim is the rule, not a convenience: a walker follows these words, and
    a generator that reflowed or summarised them would be putting words a
    nobody wrote in front of the person recording the verdict.

    Fenced blocks are skipped when looking for the heading that ends a section,
    so a `# comment` inside a shell example does not truncate the steps.
    """
    lines = body.splitlines()
    for want in names:
        depth, start = 0, -1
        in_fence = False
        for i, line in enumerate(lines):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            found = HEADING_RE.match(line)
            if not found:
                continue
            if start == -1:
                if found.group(2).strip().lower().rstrip(":") == want.lower():
                    depth, start = len(found.group(1)), i + 1
                continue
            if len(found.group(1)) <= depth:
                return "\n".join(lines[start:i]).strip("\n").rstrip()
        if start != -1:
            return "\n".join(lines[start:]).strip("\n").rstrip()
    return ""


def lead_paragraph(body: str) -> str:
    """The prose between a note's title and its first sub-heading.

    **A concession to the corpus that exists, not a fifth heading.** Measured
    on `your-trainer` 2026-09-13: of 61 owed rows, 53 had no `## Steps` and no
    `## Procedure`, because the pre-ADR-0027 shape put the whole procedure in
    an unheaded paragraph under the title. Printing nothing for those rows
    would make the sheet useless on the one corpus large enough to need it,
    which is the opposite of rule 5. The row says the heading is missing and
    prints the prose anyway, so it stays a worklist entry.
    """
    lines, out, seen_title = body.splitlines(), [], False
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        found = HEADING_RE.match(line)
        if found:
            if len(found.group(1)) == 1 and not seen_title:
                seen_title, out = True, []
                continue
            break
        #: **Nothing is collected before the title.** An HTML comment or a
        #: provenance line above the `# ` heading used to become the row's
        #: steps, and a markdown comment renders as nothing at all -- so the
        #: row said "the note's description is below" and showed a blank.
        #: Found by independent review, 2026-09-13.
        if seen_title:
            out.append(line)
    return "\n".join(out).strip("\n").rstrip()


@dataclass
class Check:
    """One acceptance check, as much of it as a sheet row needs."""

    id: str
    title: str
    path: str
    area: str = ""
    after: list[str] = field(default_factory=list)
    covers: list[str] = field(default_factory=list)
    command: str = ""
    setup: str = ""
    steps: str = ""
    expect: str = ""
    #: The note's unheaded description, printed only when it states no steps.
    lead: str = ""
    #: Declared only on checks without a usable authored procedure. A platform
    #: can owe a check even when its action is not currently possible there.
    readiness_for: dict[str, dict[str, str]] = field(default_factory=dict)
    readiness_problems: list[str] = field(default_factory=list)

    @property
    def section(self) -> str:
        """feature / regression / automated -- derived, never filed.

        `TESTING.md`, "The three sections": a `command:` makes it automated; a
        `covers:` naming an `ISS-*` makes it a claim about a past defect, so a
        regression; everything else is a standing claim about behaviour. A
        check naming no issue reads as a behaviour claim, which is the safe
        direction -- it stays on the list rather than settling forever.
        """
        if self.command:
            return "automated"
        #: **Only the automated branch changes a sheet**, because both of the
        #: others are manual and a row does not say which it is. The split is
        #: kept so this module and the cockpit name the same three sections
        #: from the same two fields; its regression/feature boundary is
        #: asserted there, on a surface that renders it, and cannot be
        #: asserted here. Said rather than left for the next reader to find
        #: (independent review, 2026-09-13).
        if any(ref.startswith("ISS-") for ref in self.covers):
            return "regression"
        return "feature"


def load_checks(docs_root: Path, index=None, repo_root: Path | None = None) -> dict[str, Check]:
    """Every `level: acceptance` note, with its procedure sections read.

    `path` is recorded relative to ``repo_root`` so a row's link works from a
    checkout rather than from the machine the sheet was generated on.
    """
    vd = _validator()
    if index is None:
        index, _ = vd.build_note_index(docs_root)
    out: dict[str, Check] = {}
    for note_id, (path, fm) in index.items():
        if not isinstance(fm, dict):
            continue
        if vd.note_type(fm) != "test":
            continue
        if _text(fm.get("level")) != "acceptance":
            continue
        #: **Retiring a check means kept, and no longer asked.** The verdict
        #: and its date survive as the record that a behaviour was once
        #: walked; what stops is the asking. A sheet that printed a retired
        #: check would ask it, undoing the one thing retirement does -- and it
        #: made this generator report five owed rows where the cockpit's page
        #: reported four on the same corpus, which is exactly the disagreement
        #: bundling one implementation was meant to prevent. Filed downstream
        #: as project-os-cockpit ISS-0303, 2026-09-13.
        if _text(fm.get("status")) in RETIRED:
            continue
        body = body_of(path)
        shown = path
        if repo_root is not None:
            try:
                shown = path.relative_to(repo_root)
            except ValueError:
                pass
        readiness, readiness_problems = parse_check_readiness(
            fm.get("walk_readiness_for"), str(shown))
        out[note_id] = Check(
            id=note_id,
            title=_text(fm.get("title")),
            path=str(shown),
            area=_text(fm.get("area")),
            after=_ids(fm.get("after")),
            covers=_ids(fm.get("covers")),
            command=_text(fm.get("command")),
            setup=section(body, "Setup"),
            #: Procedure and Expected results are the pre-ADR-0027 headings.
            #: Read as fallbacks so a corpus nobody has rewritten yet still
            #: yields a walkable row. Setup has no fallback, and that absence
            #: is the point of the "not stated" label.
            steps=section(body, "Steps", "Procedure"),
            expect=section(body, "Expect", "Expected results"),
            lead=lead_paragraph(body),
            readiness_for=readiness,
            readiness_problems=readiness_problems,
        )
    return out


def parse_check_readiness(raw, path: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Read a check's explicit per-platform readiness for fallback rows."""
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `walk_readiness_for` must map platforms to kind and reason" % path]
    out: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    for platform, value in raw.items():
        if (not isinstance(platform, str)
                or not re.fullmatch(r"[a-z][a-z0-9_-]*", platform)
                or not isinstance(value, dict)
                or value.get("kind") not in ("preparation", "decision")
                or not isinstance(value.get("reason"), str)
                or not value["reason"].strip()
                or ("issue" in value and not isinstance(value["issue"], str))):
            problems.append("%s: `walk_readiness_for` entry %r needs a platform, "
                            "kind preparation or decision, and a plain reason" % (path, platform))
            continue
        out[platform] = {"kind": value["kind"],
                         "reason": value["reason"].strip(),
                         "issue": value.get("issue", "").strip()}
    return out, problems


def check_readiness(check: Check, platform: str) -> dict[str, str]:
    """A malformed declaration is a visible decision, never a ready card."""
    if check.readiness_problems:
        return {"kind": "decision", "reason":
                "This check's walk readiness declaration is invalid. Fix its note "
                "before recording a verdict.", "issue": ""}
    return check.readiness_for.get(platform, {})


CHANGES_REL = "changes"
RELEASES_REL = "releases"
GALLERY_REL = "tests/acceptance/gallery"
PROCEDURES_REL = "tests/acceptance/walk"
#: The folder holding the pictures of the build being walked. Every other
#: folder under the gallery is named after the tag it was captured at.
CANDIDATE_DIR = "candidate"
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".svg")
IMPACT_HEADING = "Impact"
#: A release note is a candidate for "the last release tag" only at this
#: status. `draft` has not shipped; `reverted` and `abandoned` shipped and
#: were taken back, so the screens at that tag are not what anyone is
#: comparing against.
RELEASED = frozenset({"released"})

#: A screen **the item is about**, not one it happens to mention. The id has to
#: start the list item, after whatever emphasis or link punctuation is in the
#: way. Anchoring matters on a corpus written before this rule existed: one of
#: your-trainer's twelve change notes since v2.1.8 says "intervals.icu got its
#: own, SUR-0016" in the middle of a sentence about `area:` values, and an
#: unanchored search read that as a screen the release changed. Measured
#: 2026-09-14 while landing this rule.
#: Matched, never searched: `^` here would be redundant with `.match` and
#: would quietly make a `.search` behave the same, so the anchoring rule would
#: have no way to be got wrong and no way to be tested.
_SUR_RE = re.compile(r"[\s*_`\[]*SUR-(\d{2,})\b")
_LIST_ITEM_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
#: "No screen changed", however it is emphasised. A change note says this
#: instead of naming screens, and a parser that did not recognise it would
#: read the note as one that simply forgot.
_NO_SCREEN_RE = re.compile(r"^[\s*_`]*no screen changed\b", re.I)
#: What separates a screen's id from its sentence: a colon, an em or en dash,
#: or a hyphen with a space after it. A hyphen without one is part of a slug.
_SEP_RE = re.compile(r"^[\s*_`\]]*(?:[:\u2014\u2013]|-\s)\s*")


@dataclass
class Surface:
    """One `SUR-*` note: what it is called, what it sits under, its pictures."""

    id: str
    title: str
    parent: str = ""
    #: `(key, state)` pairs from `gallery:`; `state` is "" for a plain key.
    gallery: list[tuple[str, str]] = field(default_factory=list)


def load_surfaces(index) -> dict[str, Surface]:
    """Every `SUR-*` note, with `parent:` resolved to an id.

    `parent:` is written three ways in the fleet -- a bare id, a wikilink, and
    the parent's title -- so all three are resolved here and a caller never
    has to ask which one it got. A `parent:` naming nothing resolvable is
    dropped rather than kept as a string: the survey nests by id, and a
    dangling parent would put a child under a heading that does not exist.
    """
    vd = _validator()
    out: dict[str, Surface] = {}
    by_title: dict[str, str] = {}
    for note_id, (path, fm) in index.items():
        if not isinstance(fm, dict) or vd.note_type(fm) != "surface":
            continue
        title = _text(fm.get("title"))
        raw = fm.get("gallery")
        gallery: list[tuple[str, str]] = []
        for item in (raw if isinstance(raw, list) else [raw]):
            entry = _text(item)
            if not entry:
                continue
            key, _, state = entry.partition(":")
            if key.strip():
                gallery.append((key.strip(), state.strip()))
        out[note_id] = Surface(id=note_id, title=title,
                               parent=_text(fm.get("parent")), gallery=gallery)
        if title:
            by_title.setdefault(title, note_id)
    for surface in out.values():
        if not surface.parent:
            continue
        found = [i for i in _ids(surface.parent) if i in out]
        resolved = found[0] if found else by_title.get(surface.parent, "")
        surface.parent = resolved if resolved and resolved != surface.id else ""
    return out


def surfaces_by_title(index) -> dict[str, str]:
    """`area:` string -> `SUR-*` id, for repos that keep surface notes.

    A repo with no `SUR-*` notes groups by the `area:` string alone, which is
    why this may legitimately be empty.
    """
    vd = _validator()
    out = {}
    for note_id, (path, fm) in index.items():
        if isinstance(fm, dict) and vd.note_type(fm) == "surface":
            title = _text(fm.get("title"))
            if title:
                out.setdefault(title, note_id)
    return out


def top_screen(surface_id: str, surfaces: dict[str, Surface]) -> str:
    """The top-level screen a surface sits under, or itself.

    Walks `parent:` upwards with a seen-set, because a pair of notes naming
    each other is a thing an author can write and is not worth a crash.
    """
    seen, at = {surface_id}, surface_id
    while True:
        parent = surfaces[at].parent if at in surfaces else ""
        if not parent or parent in seen:
            return at
        seen.add(parent)
        at = parent


@dataclass
class Change:
    """One change note, and the screens its `## Impact` list names."""

    id: str
    title: str
    path: str
    #: `(SUR-* id, the sentence written for it)`, in the note's own order.
    screens: list[tuple[str, str]] = field(default_factory=list)
    #: The note said, in as many words, that it altered no screen.
    no_screen: bool = False

    @property
    def silent(self) -> bool:
        """Neither a screen nor "No screen changed" -- nobody answered."""
        return not self.screens and not self.no_screen


def parse_impact(body: str) -> tuple[list[tuple[str, str]], bool]:
    """`## Impact` -> the screens it names with their sentences, and "none".

    The sentence is everything after the id and its separator, printed
    verbatim on the sheet. A line naming a screen and saying nothing about it
    keeps an empty sentence rather than being dropped: the screen still has
    to be looked at, and the silence is visible on the sheet.
    """
    screens: list[tuple[str, str]] = []
    none = False
    in_fence = False
    for line in section(body, IMPACT_HEADING).splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        #: **A fenced block is an example, not a claim.** A template or a
        #: change note showing the shape inside ``` would otherwise put a
        #: screen on the survey that nothing altered. Found by independent
        #: review, 2026-09-14.
        if in_fence:
            continue
        item = _LIST_ITEM_RE.match(line)
        if not item:
            continue
        text = item.group(1).strip()
        if _NO_SCREEN_RE.match(text):
            none = True
            continue
        #: **Every screen the item names, not just the first.** One line
        #: reading `[[SUR-0001]] and [[SUR-0002]]: both gained a lap counter`
        #: used to drop the second screen and print the first one's sentence
        #: as `and [[SUR-0002]]: both gained…`, raw markup and all. The label
        #: is the run of ids and links at the head of the item; the sentence
        #: is what follows the last of them, and each screen gets it. Found by
        #: independent review, 2026-09-14.
        found: list[str] = []
        rest = text
        while True:
            match = _SUR_RE.match(rest)
            if not match:
                break
            found.append("SUR-%s" % match.group(1))
            rest = rest[match.end():]
            close = rest.find("]]")
            if 0 <= close <= 80:
                rest = rest[close + 2:]
            else:
                rest = re.sub(r"^[-\w]*", "", rest)
            #: `and`, `,` or `+` between two ids keeps the label going; a
            #: separator ends it and the sentence starts.
            joined = re.match(r"^[\s*_`]*(?:and|,|&|\+)[\s*_`]*", rest)
            if not joined:
                break
            rest = rest[joined.end():]
        if not found:
            continue
        sentence = _SEP_RE.sub("", rest, count=1).strip()
        for surface_id in found:
            screens.append((surface_id, sentence))
    return screens, none


def load_changes(docs_root: Path, repo_root: Path | None = None,
                 only: set[str] | None = None) -> list[Change]:
    """The change notes, in filename order, with their Impact lists read.

    ``only`` is a set of repo-relative paths -- the notes git says were added
    since the release tag. Without it every change note is read, which is what
    `--check` wants when it is auditing the corpus rather than one release.
    """
    out: list[Change] = []
    root = docs_root / CHANGES_REL
    if not root.is_dir():
        return out
    vd = _validator()
    for path in sorted(root.glob("*.md")):
        shown = path
        if repo_root is not None:
            try:
                shown = path.relative_to(repo_root)
            except ValueError:
                pass
        if only is not None and str(shown) not in only:
            continue
        fm = vd.parse_frontmatter(path)
        if not isinstance(fm, dict):
            continue
        screens, none = parse_impact(body_of(path))
        out.append(Change(id=_text(fm.get("id")) or path.stem,
                          title=_text(fm.get("title")), path=str(shown),
                          screens=screens, no_screen=none))
    return out


# ------------------------------------------------- the last release, and git

def _git(root: Path, *args: str) -> tuple[int, str]:
    """`git` in ``root``. A missing git is a return code, never an exception.

    The survey is the only thing that needs git, so a machine without it, or
    a checkout that is not a repository, loses the survey and keeps the sheet.
    """
    try:
        done = subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return 127, ""
    return done.returncode, done.stdout.strip()


def last_release(docs_root: Path, platform: str) -> tuple[str, str, str]:
    """(release id, tag, why not) -- the newest released `REL-*` for a platform.

    Read from the release NOTES rather than from `git tag`, because a tag
    pattern is a guess and a note says which tag was the release. A project
    shipping more than one platform tags them differently -- `v2.1.8` for
    Android and `ios/v0.1.0` for iOS -- and the note carries `platform:`, so
    the per-platform answer falls out instead of needing a second convention.
    A note with no `platform:` counts for every platform, the same opt-in rule
    release contents use.
    """
    root = docs_root / RELEASES_REL
    if not root.is_dir():
        return "", "", "this project keeps no release notes in docs/%s" % RELEASES_REL
    vd = _validator()
    found = []
    for path in sorted(root.glob("*.md")):
        fm = vd.parse_frontmatter(path)
        if not isinstance(fm, dict) or vd.note_type(fm) != "release":
            continue
        if _text(fm.get("status")) not in RELEASED:
            continue
        theirs = _text(fm.get("platform"))
        if theirs and theirs != platform:
            continue
        found.append((_text(fm.get("date")), _text(fm.get("id")) or path.stem,
                      _text(fm.get("tag"))))
    if not found:
        return "", "", ("this project has no released REL-* note for %s, so there "
                        "is no last release to compare against" % platform)
    found.sort()
    release_id, tag = found[-1][1], found[-1][2]
    if not tag:
        return release_id, "", ("%s is the newest released note for %s and it "
                                "carries no `tag:`, so nothing says where the "
                                "last release is in git" % (release_id, platform))
    return release_id, tag, ""


def changes_since(repo_root: Path, tag: str) -> tuple[set[str], str]:
    """Change notes added between ``tag`` and HEAD, as repo-relative paths."""
    rel = "docs/%s" % CHANGES_REL
    code, _ = _git(repo_root, "rev-parse", "--git-dir")
    if code != 0:
        return set(), ("this is not a git checkout, so no change note can be "
                       "dated against the tag `%s`" % tag)
    code, _ = _git(repo_root, "rev-parse", "--verify", "--quiet",
                   "%s^{commit}" % tag)
    if code != 0:
        return set(), ("the tag `%s` is not in this checkout -- a shallow clone "
                       "does not carry it" % tag)
    code, out = _git(repo_root, "diff", "--diff-filter=A", "--name-only",
                     "%s..HEAD" % tag, "--", rel)
    if code != 0:
        return set(), "git could not list what `%s..HEAD` added under %s" % (tag, rel)
    return {line.strip() for line in out.splitlines() if line.strip()}, ""


def capture_finder(docs_root: Path, repo_root: Path | None, tag: str):
    """`key -> (before, after)`, as repo-relative paths, "" where absent.

    The convention is `TESTING.md`, "The walk", rule 2: one folder per tag,
    plus `candidate/` for the build being walked.
    """
    base = docs_root / GALLERY_REL

    def find(folder: str, key: str) -> str:
        if not folder:
            return ""
        for ext in IMAGE_EXT:
            path = base / folder / (key + ext)
            if path.is_file():
                if repo_root is not None:
                    try:
                        return str(path.relative_to(repo_root))
                    except ValueError:
                        pass
                return str(path)
        return ""

    def captures(key: str) -> tuple[str, str]:
        return find(tag, key), find(CANDIDATE_DIR, key)

    return captures


# ------------------------------------------------------ a sitting's procedure

#: `1. ` or `1) ` at the start of a line, indented no more than three spaces --
#: deeper than that is a continuation inside the previous item, not a new one.
_STEP_RE = re.compile(r"^ {0,3}(\d+)[.)]\s+(.*)$")
#: `TST-0648.4` or `TST-0648`, in backticks. ASCII, because a tag is typed by
#: an LLM into a markdown file and read back by a regular expression; an
#: en dash or a smart quote in one would be a tag nobody can find.
_TAG_RE = re.compile(r"`(TST-\d{2,})(?:\.(\d+))?`")
#: A malformed backticked check reference must be reported even when another
#: valid tag on the same line satisfies coverage. Otherwise the unparsed text
#: becomes prose and an observation can disappear from the owed walk.
_TAG_LIKE_RE = re.compile(r"`TST-[^`]*`")
_ACTION_HEAD_RE = re.compile(r"^(\*\*.+?\.\*\*)\s*(.*)$")
_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_WS_RE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """One line of markdown, reduced to the words it asserts.

    The list marker goes, runs of whitespace collapse, and emphasis at either
    end goes -- `- **The banner reads DONE.**` and `The banner reads DONE.`
    say the same thing to a walker. Nothing inside the line is touched, so a
    code symbol in backticks still has to match.
    """
    return _WS_RE.sub(" ", _MARKER_RE.sub("", text or "")).strip().strip("*_ ")


def parse_tags(line: str) -> list[tuple[str, str]]:
    """Every expectation tag on a line, as `(check id, step number or "")`."""
    return [(m.group(1), m.group(2) or "") for m in _TAG_RE.finditer(line)]


def quote_of(line: str) -> str:
    """What a tagged line claims, with its tags removed."""
    return normalise(_TAG_RE.sub("", line))


@dataclass
class Expectation:
    """One line of a procedure step that says what should be observed."""

    quote: str
    raw: str
    tags: list[tuple[str, str]] = field(default_factory=list)
    #: Filled by `build_walk`: which of this line's tags the release owes.
    owed: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class Step:
    #: Its position in the list, which is what a tag's `.N` names and what the
    #: sheet prints. Markdown renumbers an ordered list and so does this.
    number: int
    head: str
    authored_head: str = ""
    #: The digit actually written, kept only so the validator can report a
    #: note whose own numbering will not match what the sheet prints.
    written: int = 0
    body: list[str] = field(default_factory=list)
    #: The `SUR-*` id this step happens on, when one could be resolved.
    surface_id: str = ""
    #: What the step actually wrote, id or title, for the message when it did
    #: not resolve.
    surface_said: str = ""
    expectations: list[Expectation] = field(default_factory=list)
    #: Empty means every platform; otherwise the authored platforms for this action.
    platforms: set[str] = field(default_factory=set)
    #: State to confirm before this action; authored, never inferred from prose.
    #: A declaration on this source step; carried to later applicable steps
    #: when the walk is built for one platform.
    state_declared: str = ""
    required_state: str = ""
    #: A later retained step may ask the walker to keep evidence from here.
    capture_prompt: str = ""
    capture_needed: bool = False
    uses_capture: list[int] = field(default_factory=list)
    #: A wait the author declared for this action, never a session estimate.
    timer_seconds: int = 0
    #: A known fixture, control or product decision needed before execution.
    readiness: dict[str, object] = field(default_factory=dict)
    readiness_declared: dict[str, object] = field(default_factory=dict)
    #: Platform-specific action prose after the unchanged bold surface name.
    action_for: dict[str, str] = field(default_factory=dict)

    @property
    def parts(self) -> set[tuple[str, str]]:
        return {tag for e in self.expectations for tag in e.tags}


@dataclass
class SetupItem:
    id: str
    text: str
    #: Empty means every step; annotated procedures name the steps explicitly.
    steps: set[int] = field(default_factory=set)
    platforms: set[str] = field(default_factory=set)


@dataclass
class Procedure:
    """One sitting's written script."""

    path: str
    sitting: str
    setup: str
    steps: list[Step] = field(default_factory=list)
    setup_items: list[SetupItem] = field(default_factory=list)
    requires: dict[int, list[int]] = field(default_factory=dict)
    parse_problems: list[str] = field(default_factory=list)
    #: Why this procedure cannot be printed. Non-empty means the sitting falls
    #: back to per-check rows ("The walk", rule 9).
    problems: list[str] = field(default_factory=list)
    #: True about the procedure, nobody's mistake.
    remarks: list[str] = field(default_factory=list)


_SETUP_ITEM_RE = re.compile(r"^- \[([a-z][a-z0-9_-]*)\] (.+)$")


def _number_map(raw, label: str, path: str) -> tuple[dict[int, list[int]], list[str]]:
    """Read a frontmatter map of step positions to step positions."""
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `%s` must map step numbers to lists of step numbers" % (path, label)]
    out: dict[int, list[int]] = {}
    problems: list[str] = []
    for key, value in raw.items():
        number = 0
        try:
            number = int(key)
            targets = [int(item) for item in value] if isinstance(value, list) else None
        except (TypeError, ValueError):
            targets = None
        if number < 1 or targets is None or any(target < 1 for target in targets):
            problems.append("%s: `%s` entry %r needs positive step numbers" % (path, label, key))
        else:
            out[number] = targets
    return out, problems


def _platform_map(raw, label: str, path: str) -> tuple[dict[str, set[str]], list[str]]:
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `%s` must map ids to platform lists" % (path, label)]
    out: dict[str, set[str]] = {}
    problems: list[str] = []
    for key, value in raw.items():
        if not isinstance(value, list) or not value or any(
                not isinstance(item, str) or not item.strip() for item in value):
            problems.append("%s: `%s` entry %r needs a nonempty platform list" % (path, label, key))
        else:
            out[str(key)] = {item.strip() for item in value}
    return out, problems


def _text_map(raw, label: str, path: str) -> tuple[dict[str, str], list[str]]:
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `%s` must map step numbers to nonempty text" % (path, label)]
    out: dict[str, str] = {}
    problems: list[str] = []
    for key, value in raw.items():
        if not str(key).isdigit() or not isinstance(value, str) or not value.strip():
            problems.append("%s: `%s` entry %r needs a step number and nonempty text"
                            % (path, label, key))
        else:
            out[str(key)] = value.strip()
    return out, problems


def _duration_map(raw, path: str) -> tuple[dict[str, int], list[str]]:
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `timer_for` must map step numbers to positive seconds" % path]
    out: dict[str, int] = {}
    problems: list[str] = []
    for key, value in raw.items():
        try:
            seconds = int(value)
        except (TypeError, ValueError):
            seconds = 0
        if not str(key).isdigit() or seconds < 1:
            problems.append("%s: `timer_for` entry %r needs a step number and positive seconds"
                            % (path, key))
        else:
            out[str(key)] = seconds
    return out, problems


def _readiness_map(raw, path: str) -> tuple[dict[str, dict[str, object]], list[str]]:
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `readiness_for` must map step numbers to kind and reason" % path]
    out: dict[str, dict[str, object]] = {}
    problems: list[str] = []
    for key, value in raw.items():
        if (not str(key).isdigit() or not isinstance(value, dict)
                or value.get("kind") not in ("preparation", "decision")
                or not isinstance(value.get("reason"), str)
                or not value["reason"].strip()
                or ("issue" in value and not isinstance(value["issue"], str))
                or ("platforms" in value and (not isinstance(value["platforms"], list)
                    or not value["platforms"] or any(not isinstance(item, str)
                    or not re.fullmatch(r"[a-z][a-z0-9_-]*", item)
                    for item in value["platforms"])))):
            problems.append("%s: `readiness_for` entry %r needs a step number, "
                            "kind preparation or decision, and a plain reason" % (path, key))
        else:
            out[str(key)] = {"kind": value["kind"], "reason": value["reason"].strip(),
                             "issue": value.get("issue", "").strip(),
                             "platforms": list(value.get("platforms", []))}
    return out, problems


def _action_map(raw, path: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `action_for` must map step numbers to platform actions" % path]
    out: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    for key, value in raw.items():
        if (not str(key).isdigit() or not isinstance(value, dict) or not value
                or any(not isinstance(platform, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", platform)
                       or not isinstance(action, str) or not action.strip()
                       or _TAG_RE.search(action) for platform, action in value.items())):
            problems.append("%s: `action_for` entry %r needs platform names and nonempty actions without test tags"
                            % (path, key))
        else:
            out[str(key)] = {platform: action.strip() for platform, action in value.items()}
    return out, problems


def parse_setup_items(setup: str, scope, platforms, path: str) -> tuple[list[SetupItem], list[str]]:
    """A scoped setup is a list of named bullets; legacy setup remains whole."""
    if scope in (None, "") and platforms in (None, ""):
        return ([SetupItem(id="", text=setup)] if setup else []), []
    problems: list[str] = []
    if not isinstance(scope, dict):
        return [], ["%s: `setup_for` must map each setup id to step numbers" % path]
    if platforms in (None, ""):
        platforms = {}
    if not isinstance(platforms, dict):
        return [], ["%s: `setup_platforms` must map setup ids to platforms" % path]
    items: list[SetupItem] = []
    current: list[str] = []
    current_id = ""
    for line in setup.splitlines():
        found = _SETUP_ITEM_RE.match(line)
        if found:
            if current_id:
                items.append(SetupItem(id=current_id, text="\n".join(current).strip()))
            current_id, current = found.group(1), ["- " + found.group(2)]
        elif current_id:
            current.append(line)
        elif line.strip():
            problems.append("%s: scoped setup has text before its first named item" % path)
    if current_id:
        items.append(SetupItem(id=current_id, text="\n".join(current).strip()))
    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        problems.append("%s: setup ids must be unique" % path)
    for item in items:
        raw_steps = scope.get(item.id)
        if raw_steps == "all":
            item.steps = set()
        elif not isinstance(raw_steps, list) or not raw_steps:
            problems.append("%s: setup item %s needs `all` or a nonempty `setup_for` step list"
                            % (path, item.id))
            continue
        else:
            try:
                item.steps = {int(value) for value in raw_steps}
            except (TypeError, ValueError):
                problems.append("%s: setup item %s names an invalid step" % (path, item.id))
        if any(value < 1 for value in item.steps):
            problems.append("%s: setup item %s names an invalid step" % (path, item.id))
        raw_platforms = platforms.get(item.id, [])
        if not isinstance(raw_platforms, list) or any(
                not isinstance(value, str) or not value.strip() for value in raw_platforms):
            problems.append("%s: setup item %s has invalid platforms" % (path, item.id))
        else:
            item.platforms = {value.strip() for value in raw_platforms}
    for key in set(scope) | set(platforms):
        if key not in ids:
            problems.append("%s: setup metadata names absent item %s" % (path, key))
    return items, problems


def parse_steps(body: str) -> list[Step]:
    """`## Steps` -> the numbered items under it, each with its own lines.

    **A step's number is its position, not the digit written.** Markdown
    renumbers an ordered list, so `1.` on every item renders as 1, 2, 3 and is
    the style most people write. Keying on the written digit made two steps
    share a number, which defeated the rule that an owed part may be cited by
    only one step -- the citation count was a set of numbers. Found by
    independent review, 2026-09-14. `written` keeps the digit so the validator
    can say when a note's own numbering will not match the sheet.

    **A tag inside a fenced block is not a citation.** Fences were skipped when
    finding where a step begins and not when collecting what it claims, so a
    worked example in ``` satisfied coverage on its own, and could equally
    refuse a correct procedure for citing one part twice. Same review.
    """
    steps: list[Step] = []
    current: Step | None = None
    in_fence = False
    for line in section(body, "Steps").splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            if current is not None:
                current.body.append(line)
            continue
        found = None if in_fence else _STEP_RE.match(line)
        if found:
            current = Step(number=len(steps) + 1, head=found.group(2).strip(),
                           authored_head=found.group(2).strip(),
                           written=int(found.group(1)), body=[line])
            steps.append(current)
            tags = parse_tags(line)
            if tags:
                current.expectations.append(
                    Expectation(quote=quote_of(line), raw=line, tags=tags))
            continue
        if current is None:
            continue
        current.body.append(line)
        if in_fence:
            continue
        tags = parse_tags(line)
        if tags:
            current.expectations.append(
                Expectation(quote=quote_of(line), raw=line, tags=tags))
    return steps


def name_surfaces(steps: list[Step], surfaces: dict[str, Surface]) -> None:
    """Resolve each step's screen from its first line, by id or by title."""
    titles = {s.title: s.id for s in surfaces.values() if s.title}
    for step in steps:
        found = [i for i in _ids(step.head) if i.startswith("SUR-")]
        if found:
            step.surface_id = found[0]
            known = surfaces.get(step.surface_id)
            step.surface_said = known.title if known and known.title else step.surface_id
            continue
        for title, sid in sorted(titles.items(), key=lambda kv: -len(kv[0])):
            if title and title in step.head:
                step.surface_id, step.surface_said = sid, title
                break


def load_procedures(docs_root: Path, repo_root: Path | None = None) -> list[Procedure]:
    """Every file under `docs/tests/acceptance/walk/`, parsed."""
    root = docs_root / PROCEDURES_REL
    if not root.is_dir():
        return []
    vd = _validator()
    out: list[Procedure] = []
    for path in sorted(root.glob("*.md")):
        fm = vd.parse_frontmatter(path)
        fm = fm if isinstance(fm, dict) else {}
        body = body_of(path)
        shown = path
        if repo_root is not None:
            try:
                shown = path.relative_to(repo_root)
            except ValueError:
                pass
        shown_path = str(shown)
        setup = section(body, "Setup")
        steps = parse_steps(body)
        requires, require_problems = _number_map(fm.get("requires"), "requires", shown_path)
        step_platforms, step_problems = _platform_map(
            fm.get("step_platforms"), "step_platforms", shown_path)
        step_states, state_problems = _text_map(
            fm.get("state_for"), "state_for", shown_path)
        capture_prompts, capture_problems = _text_map(
            fm.get("capture_for"), "capture_for", shown_path)
        capture_sources, use_problems = _number_map(
            fm.get("use_capture"), "use_capture", shown_path)
        timers, timer_problems = _duration_map(fm.get("timer_for"), shown_path)
        readiness, readiness_problems = _readiness_map(fm.get("readiness_for"), shown_path)
        actions, action_problems = _action_map(fm.get("action_for"), shown_path)
        setup_items, setup_problems = parse_setup_items(
            setup, fm.get("setup_for"), fm.get("setup_platforms"), shown_path)
        for step in steps:
            step.platforms = step_platforms.get(str(step.number), set())
            step.state_declared = step_states.get(str(step.number), "")
            step.required_state = step.state_declared
            step.capture_prompt = capture_prompts.get(str(step.number), "")
            step.uses_capture = capture_sources.get(step.number, [])
            step.timer_seconds = timers.get(str(step.number), 0)
            step.readiness = readiness.get(str(step.number), {})
            step.readiness_declared = readiness.get(str(step.number), {})
            step.action_for = actions.get(str(step.number), {})
        unknown = set(step_platforms) - {str(step.number) for step in steps}
        for number in sorted(unknown):
            step_problems.append("%s: `step_platforms` names absent step %s" % (shown_path, number))
        for number in sorted(set(step_states) - {str(step.number) for step in steps}):
            state_problems.append("%s: `state_for` names absent step %s" % (shown_path, number))
        for label, mapping, target in (("capture_for", capture_prompts, capture_problems),
                                       ("timer_for", timers, timer_problems),
                                       ("readiness_for", readiness, readiness_problems),
                                       ("action_for", actions, action_problems)):
            for number in sorted(set(mapping) - {str(step.number) for step in steps}):
                target.append("%s: `%s` names absent step %s" % (shown_path, label, number))
        out.append(Procedure(
            path=shown_path, sitting=_text(fm.get("sitting")), setup=setup,
            steps=steps, setup_items=setup_items, requires=requires,
            parse_problems=(require_problems + step_problems + state_problems
                            + capture_problems + use_problems + timer_problems
                            + setup_problems + readiness_problems + action_problems)))
    return out


def written_steps(check: Check) -> list[int]:
    """The digits a check note writes on the numbered items under `## Steps`."""
    out: list[int] = []
    in_fence = False
    for line in (check.steps or "").splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        found = _STEP_RE.match(line)
        if found:
            out.append(int(found.group(1)))
    return out


def numbered_steps(check: Check) -> list[int]:
    """The step positions a check note has: 1..n, or empty.

    **Position, not the digit written**, for the reason `parse_steps` gives.
    A note whose `## Steps` read `1.` three times has three steps, because
    that is what markdown renders and what a walker counts; counting distinct
    digits collapsed it to one owed part, so the release owed less than rule 9
    says it does. Found by independent review, 2026-09-14.

    A check whose procedure is an unheaded paragraph has none, and is one
    owed part cited by its bare id ("The walk", rule 9). Most of the corpus
    that needs this looks like that today (project-os-dev ISS-0064).
    """
    return list(range(1, len(written_steps(check)) + 1))


def parts_of(check: Check) -> list[tuple[str, str]]:
    """The owed parts a check contributes: one per numbered step, else one."""
    return [(check.id, str(n)) for n in numbered_steps(check)] or [(check.id, "")]


def expect_lines(check: Check) -> set[str]:
    """The check's `## Expect` section, one normalised line per assertion."""
    return {q for q in (normalise(l) for l in (check.expect or "").splitlines()) if q}


def claims(sitting: Sitting, check: Check, surfaces: dict[str, str]) -> bool:
    """Whether a sitting claims a check ("The walk", rule 3)."""
    return (check.id in sitting.checks
            or check.area in sitting.surfaces
            or surfaces.get(check.area, "") in sitting.surfaces)


def placement(checks: list[Check], sittings: list[Sitting],
              surfaces: dict[str, str]) -> dict[str, str]:
    """`check id -> sitting name`; the first sitting to claim a check keeps it."""
    out: dict[str, str] = {}
    for sitting in sittings:
        for check in checks:
            if check.id not in out and claims(sitting, check, surfaces):
                out[check.id] = sitting.name
    return out


# ------------------------------------------------------------- ledger reading

LEDGERS_REL = "releases/ledgers"
#: Clears the gate. The four values and the reason they differ are
#: `TAXONOMY.md`, "Acceptance outcomes (the ledger's vocabulary)".
CLEARING = frozenset({"pass", "partial", "na", "excused"})
#: Survives the seal. `excused` does not: it is a statement about one release.
PERSISTS = frozenset({"pass", "partial", "na"})
_LEDGER_NAME_RE = re.compile(r"^(?:WORKING|[A-Z]{2,6}-\d{3,4})-(?P<platform>.+)$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class WalkError(Exception):
    """Something a person has to fix before a sheet can be produced."""


class NothingToWalk(WalkError):
    """This repo has no walk to compute, which is not a fault.

    **Its own class, because `--check` runs on every commit and must be silent
    here without going quiet about a broken ledger.** The first version caught
    `WalkError` and swallowed all of it, so a ledger whose filename named no
    platform, and a ledger entry dated `2026-13-45`, both stopped being
    reported anywhere: the generator still refused them and nothing in
    `validate-docs.sh` did. Found by independent review, round two,
    2026-09-14 -- a defect introduced by the fix to round one's eighth
    finding.
    """


@dataclass
class Event:
    check: str
    date: str
    mark: str = ""
    reason: str = ""
    invalidated_by: str = ""
    release: str = ""
    #: Whether it came from the open ledger. **Derived from `sealed:`, never
    #: from `release:`.** The two are written at the same moment and can still
    #: disagree in a hand-edited file, and keying the sort on one and the
    #: expiry on the other made this generator and the cockpit report different
    #: owed sets for one corpus: a ledger with `sealed` and no `release` lost an
    #: owed row here and kept it there. Found by independent review, 2026-09-13.
    working: bool = True

    @property
    def is_invalidation(self) -> bool:
        return bool(self.invalidated_by)

    @property
    def clears(self) -> bool:
        return self.mark in CLEARING


def _usable_date(raw: str) -> bool:
    if not _DATE_RE.match(raw or ""):
        return False
    try:
        date.fromisoformat(raw)
    except ValueError:
        return False
    return True


def load_events(docs_root: Path, platform: str) -> list[Event]:
    """Every event for a platform, oldest ledger first, the open one last.

    Ordering is resolution order, so it belongs here rather than in each
    caller. A file whose name does not name a platform is refused rather than
    skipped: a ledger that silently disappears from its own platform while
    sitting there looking read is the worse failure.
    """
    root = docs_root / LEDGERS_REL
    if not root.is_dir():
        return []
    ledgers = []
    for path in sorted(root.glob("*.json")):
        found = _LEDGER_NAME_RE.match(path.stem)
        if not found:
            raise WalkError(
                "%s/%s: the filename does not name a platform. It must be "
                "`WORKING-<platform>.json` or `REL-####-<platform>.json`, or "
                "its verdicts are invisible to every query."
                % (LEDGERS_REL, path.name))
        if found.group("platform") != platform:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WalkError("%s/%s: not readable as JSON -- %s"
                            % (LEDGERS_REL, path.name, exc)) from None
        sealed = _text(raw.get("sealed"))
        ledgers.append((bool(sealed), sealed, _text(raw.get("release")),
                        raw.get("entries") or []))
    ledgers.sort(key=lambda l: (not l[0], l[1]))
    out: list[Event] = []
    for is_sealed, _, release, entries in ledgers:
        rows = [e for e in entries if isinstance(e, dict)]
        for entry in sorted(rows, key=lambda e: _text(e.get("date"))):
            when = _text(entry.get("date"))
            if not _usable_date(when):
                raise WalkError(
                    "%s: %s has no usable date (%r) -- a ledger is resolved in "
                    "date order, so a date-shaped string reorders the answer"
                    % (LEDGERS_REL, _text(entry.get("check")), when))
            out.append(Event(
                check=_text(entry.get("check")), date=when,
                mark=_text(entry.get("mark")), reason=_text(entry.get("reason")),
                invalidated_by=_text(entry.get("invalidated_by")),
                release=release, working=not is_sealed))
    return out


def resolve(events: list[Event]) -> dict[str, Event]:
    """What a platform currently says about each check.

    Three rules, each a decision rather than a mechanic: a later verdict
    supersedes an earlier one; an invalidation clears the standing verdict, so
    the check is owed again; and an `excused` expires when its ledger seals,
    because it was a statement about one release. A check with no surviving
    verdict simply has no key, and that absence is the answer.

    Two layers, because an expiring mark must not destroy the verdict
    underneath it: a `pass` followed by an `excused` in a sealed ledger
    resolves back to the `pass`, not to nothing.
    """
    standing: dict[str, Event] = {}
    transient: dict[str, Event] = {}
    for event in events:
        if event.is_invalidation:
            standing.pop(event.check, None)
            transient.pop(event.check, None)
            continue
        if event.mark in PERSISTS:
            standing[event.check] = event
            transient.pop(event.check, None)
        elif event.working:              # still in the open ledger
            transient[event.check] = event
    return {**standing, **transient}


def latest_events(events: list[Event]) -> dict[str, Event]:
    """The last thing recorded about each check, superseded or not."""
    out: dict[str, Event] = {}
    for event in events:
        out[event.check] = event
    return out


def platforms(docs_root: Path) -> list[str]:
    """Every platform this repo keeps a ledger for.

    A walk is asked for by name, and a name is easy to mistype. Without this,
    `--platform andriod` read no ledger, found no verdict for anything, and
    printed a confident sheet of every check in the repo -- 545 rows on
    your-trainer, with no warning. Found by independent review, 2026-09-13.
    """
    root = docs_root / LEDGERS_REL
    if not root.is_dir():
        return []
    found = set()
    for path in sorted(root.glob("*.json")):
        name = _LEDGER_NAME_RE.match(path.stem)
        if name:
            found.add(name.group("platform"))
    return sorted(found)


def sealed_releases(docs_root: Path) -> dict[str, str]:
    """`REL-####` -> the platform whose sealed ledger claims it."""
    root = docs_root / LEDGERS_REL
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _text(raw.get("sealed")) and _text(raw.get("release")):
            out[_text(raw.get("release"))] = _text(raw.get("platform"))
    return out


def has_ledger(docs_root: Path) -> bool:
    """Whether this repo keeps verdicts in ledgers at all.

    A ledger FILE, not a directory: `ensure_working` creates the directory
    before writing, and an empty one must not read as "this repo has started".
    """
    root = docs_root / LEDGERS_REL
    return root.is_dir() and any(root.glob("*.json"))


# ------------------------------------------------------------ the walk order

@dataclass
class Sitting:
    name: str
    surfaces: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    state: str = ""
    bench: list[str] = field(default_factory=list)

    @property
    def claims_nothing(self) -> bool:
        return not self.surfaces and not self.checks


WALK_REL = "tests/acceptance/WALK.md"
_YAML_LIST_RE = re.compile(r"^\s*(surfaces|checks|bench)\s*:\s*(.*)$")
_YAML_SCALAR_RE = re.compile(r"^\s*(state|gallery)\s*:\s*(.*)$")


def _inline_list(raw: str) -> list[str]:
    """`["a, b", "c"]` -> two entries, not three.

    **Split respecting quotes.** The first version split on every comma and
    stripped quotes afterwards, so the quotes protected nothing and a bench
    entry written as a sentence came apart: `"A second device on the same
    Wi-Fi, for the tablet row"` printed as two items, the second of which,
    *"for the tablet row"*, is an instruction to fetch nothing. `bench:` is
    the field people write as prose, so it is where this shows. Quiet, too:
    nothing warned, and a walker could not tell a split entry from two
    somebody wrote. Filed downstream as project-os-cockpit ISS-0304,
    2026-09-13.
    """
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    out, item, quote = [], [], None
    for ch in raw:
        if quote:
            if ch == quote:
                quote = None
            else:
                item.append(ch)
        elif ch in "\"'":
            quote = ch
        elif ch == ",":
            out.append("".join(item).strip())
            item = []
        else:
            item.append(ch)
    out.append("".join(item).strip())
    return [p for p in out if p]


def parse_walk_order(text: str) -> tuple[str, list[Sitting], list[str]]:
    """`WALK.md` -> (gallery command, sittings in file order, warnings).

    One `### ` heading per sitting, one fenced `yaml` block under it. That is
    the whole syntax and the generator parses no other, so a second way to
    write a sitting is a defect rather than a dialect (ADR-0029 acceptance 1).
    """
    gallery = ""
    sittings: list[Sitting] = []
    warnings: list[str] = []
    lines = text.splitlines()

    # frontmatter: only `gallery:` is read here.
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
            found = _YAML_SCALAR_RE.match(lines[i])
            if found and found.group(1) == "gallery":
                gallery = _strip_comment(found.group(2)).strip().strip("\"'")

    current: Sitting | None = None
    in_block = False
    for line in lines[start:]:
        heading = HEADING_RE.match(line)
        if heading and not in_block:
            if len(heading.group(1)) == 3:
                current = Sitting(name=heading.group(2).strip())
                sittings.append(current)
            elif len(heading.group(1)) <= 2:
                current = None
            continue
        if FENCE_RE.match(line):
            in_block = not in_block
            continue
        if not in_block or current is None:
            continue
        found = _YAML_LIST_RE.match(line)
        if found:
            value = _strip_comment(found.group(2)).strip()
            if not value:
                #: **Block-style is refused loudly rather than read.** ADR-0029
                #: acceptance box 1 fixes one syntax and calls a second one a
                #: defect, so this does not quietly learn to parse `- item`
                #: lines -- but dropping them silently was worse: a sitting
                #: with a block-style `surfaces:` and an inline `checks:` still
                #: claims something, so it drew no "claims nothing" warning and
                #: its surfaces simply vanished. Found by independent review,
                #: 2026-09-13.
                warnings.append(
                    'the sitting "%s" writes `%s:` as a block list; the walk '
                    "order is read as inline lists only, so write it "
                    '`%s: ["one", "two"]` or it is not read at all'
                    % (current.name, found.group(1), found.group(1)))
                continue
            setattr(current, found.group(1), _inline_list(value))
            continue
        found = _YAML_SCALAR_RE.match(line)
        if found and found.group(1) == "state":
            current.state = _strip_comment(found.group(2)).strip().strip("\"'")

    for sitting in sittings:
        if sitting.claims_nothing:
            warnings.append(
                'the sitting "%s" names neither `surfaces` nor `checks`, so it '
                "can claim nothing and no row will appear under it"
                % sitting.name)
    return gallery, sittings, warnings


def _strip_comment(raw: str) -> str:
    out, quote = [], None
    for ch in raw:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


# -------------------------------------------------------------- the payload

@dataclass
class Capture:
    """One screenshot key, and the two pictures of it."""

    key: str
    state: str = ""
    before: str = ""
    after: str = ""

    @property
    def new(self) -> bool:
        """Captured now and not at the last release: a screen that is new."""
        return bool(self.after) and not self.before


@dataclass
class Screen:
    """One line of the survey: a screen, what changed on it, its pictures."""

    id: str
    title: str
    parent: str = ""
    #: `(change id, change title, the sentence that change wrote)`.
    sentences: list[tuple[str, str, str]] = field(default_factory=list)
    captures: list[Capture] = field(default_factory=list)
    #: Named by a change note and matched by no `SUR-*` note.
    unresolved: bool = False


@dataclass
class Placed:
    sitting: Sitting
    rows: list[Check]
    #: The sitting's written procedure, when it has one and it holds up.
    procedure: Procedure | None = None
    #: Only setup that the retained actions use on this platform.
    setup: str = ""
    #: The steps of that procedure this release owes something from.
    steps: list[Step] = field(default_factory=list)
    #: How many steps were left out because everything they cite has passed.
    omitted: int = 0
    #: Owed checks the procedure covers, for the tick list under it.
    owed_checks: list[Check] = field(default_factory=list)

    @property
    def walked_from_procedure(self) -> bool:
        return self.procedure is not None and not self.procedure.problems


@dataclass
class Walk:
    release: str
    platform: str
    generated: str
    survey: list[Screen]
    sittings: list[Placed]
    unplaced: list[Check]
    gallery: str = ""
    #: Something to fix in `WALK.md`.
    warnings: list[str] = field(default_factory=list)
    #: Something true about this sheet that is nobody's mistake.
    notices: list[str] = field(default_factory=list)
    authored_order: bool = True
    #: The release note and tag the survey compared against, and why it could
    #: not. Exactly one of `survey_tag` and `survey_problem` is set.
    survey_release: str = ""
    survey_tag: str = ""
    survey_problem: str = ""

    @property
    def rows(self) -> int:
        return sum(len(p.rows) for p in self.sittings) + len(self.unplaced)


def order_rows(rows: list[Check], warnings: list[str], where: str) -> list[Check]:
    """`after:` first, then id ("The walk", rule 4).

    A prerequisite in another sitting cannot be ordered here, so only edges
    inside this sitting count. A cycle is reported and the rows fall back to id
    order: nothing gates on `after:`, so failing the whole sheet over it would
    cost the walker their afternoon to save an ordering.
    """
    here = {c.id: c for c in rows}
    pending = {c.id: [a for a in c.after if a in here and a != c.id] for c in rows}
    out: list[Check] = []
    while pending:
        ready = sorted(i for i, deps in pending.items()
                       if not [d for d in deps if d in pending])
        if not ready:
            warnings.append(
                "%s: `after:` forms a cycle over %s -- the rows are in id order "
                "and nothing is gated on it" % (where, ", ".join(sorted(pending))))
            out.extend(here[i] for i in sorted(pending))
            break
        for check_id in ready:
            out.append(here[check_id])
            del pending[check_id]
    return out


def owed_checks(checks: dict[str, Check], events: list[Event]) -> list[Check]:
    """The manual checks this platform still owes, in id order.

    `ledger.owed()` in `project-os-cockpit`, entry for entry: a manual check
    (feature or regression section) with no surviving clearing verdict.
    """
    verdicts = resolve(events)
    out = [c for c in checks.values()
           if c.section != "automated"
           and ((v := verdicts.get(c.id)) is None or not v.clears)]
    out.sort(key=lambda c: c.id)
    return out


def build_survey(changes: list[Change], surfaces: dict[str, Surface],
                 captures=None) -> list[Screen]:
    """The screens a release changed, from the change notes that named them.

    Order is the top-level screens by title, each followed by its children.
    That is the order a person navigates in, and it is why a dialog never
    appears above the screen it opens from ("The walk", rule 2).
    """
    found: dict[str, Screen] = {}
    for change in changes:
        for surface_id, sentence in change.screens:
            screen = found.get(surface_id)
            if screen is None:
                known = surfaces.get(surface_id)
                screen = Screen(
                    id=surface_id,
                    title=known.title if known and known.title else surface_id,
                    parent=top_screen(surface_id, surfaces) if known else "",
                    unresolved=known is None)
                if screen.parent == surface_id:
                    screen.parent = ""
                found[surface_id] = screen
            screen.sentences.append((change.id, change.title, sentence))
    # A changed dialog still needs its containing screen in the survey, even
    # when no change note names that screen directly.
    for screen in list(found.values()):
        if screen.parent and screen.parent not in found:
            parent = surfaces.get(screen.parent)
            found[screen.parent] = Screen(
                id=screen.parent,
                title=parent.title if parent and parent.title else screen.parent,
                parent="",
                unresolved=parent is None)
    if captures is not None:
        for screen in found.values():
            known = surfaces.get(screen.id)
            for key, state in (known.gallery if known else []):
                before, after = captures(key)
                if before or after:
                    screen.captures.append(
                        Capture(key=key, state=state, before=before, after=after))
    tops = sorted((s for s in found.values() if not s.parent),
                  key=lambda s: (s.title.lower(), s.id))
    out: list[Screen] = []
    for top in tops:
        out.append(top)
        out.extend(sorted((s for s in found.values() if s.parent == top.id),
                          key=lambda s: (s.title.lower(), s.id)))
    #: A child whose parent no change note named still has to be looked at, so
    #: it prints after the screens that do have a parent on the sheet rather
    #: than being dropped for having nowhere to nest.
    shown = {s.id for s in out}
    out.extend(sorted((s for s in found.values() if s.id not in shown),
                      key=lambda s: (s.title.lower(), s.id)))
    return out


def build_walk(checks: dict[str, Check], events: list[Event], sittings: list[Sitting],
               *, release: str, platform: str, surfaces=None,
               surface_notes=None, changes=None, captures=None,
               procedures=None, known=None, retired=None,
               gallery: str = "", generated: str = "",
               warnings=None, notices=None, authored_order: bool = True,
               survey_release: str = "", survey_tag: str = "",
               survey_problem: str = "") -> Walk:
    """The sheet as data: the survey, the sittings and the unplaced rows.

    Takes plain values rather than a repo path, so a host with its own note
    index (the cockpit's `walk_payload`) computes the same walk from the same
    rules without a second implementation of any of them.
    """
    surfaces = surfaces or {}
    surface_notes = surface_notes or {}
    warnings = list(warnings or [])
    owed = owed_checks(checks, events)
    owed_ids = {c.id for c in owed}

    survey = build_survey(list(changes or []), surface_notes, captures)

    # --- placement: the first sitting that claims a check keeps it
    placed: list[Placed] = []
    taken: set[str] = set()
    by_sitting = {p.sitting: p for p in (procedures or []) if p.sitting}
    for sitting in sittings:
        claimed = [c for c in owed if c.id not in taken and claims(sitting, c, surfaces)]
        taken.update(c.id for c in claimed)
        if not claimed:
            continue
        rows = order_rows(claimed, warnings, sitting.name)
        entry = Placed(sitting=sitting, rows=rows)
        procedure = by_sitting.get(sitting.name)
        if procedure is not None:
            attach_procedure(entry, procedure, checks, owed_ids, sittings,
                             surfaces, platform=platform, retired=retired, known=known)
        placed.append(entry)
    unplaced = order_rows([c for c in owed if c.id not in taken],
                          warnings, "Unplaced")
    return Walk(release=release, platform=platform,
                generated=generated or date.today().isoformat(),
                survey=survey, sittings=placed, unplaced=unplaced,
                gallery=gallery, warnings=warnings, notices=list(notices or []),
                authored_order=authored_order, survey_release=survey_release,
                survey_tag=survey_tag, survey_problem=survey_problem)


def attach_procedure(entry: Placed, procedure: Procedure, checks: dict[str, Check],
                     owed_ids: set[str], sittings: list[Sitting],
                     surfaces: dict[str, str], platform: str = "",
                     retired: set[str] | None = None,
                     known: dict[str, Check] | None = None) -> None:
    """Hold a procedure to what this sitting owes, then keep what prints.

    The judgement is `audit_procedure`; this decides what a sheet does with
    the answer. A procedure with a problem still reaches `entry.procedure`,
    because the renderer prints the problem above the per-check rows it falls
    back to -- a stale procedure that vanished silently would leave the walker
    reading rows and wondering where the script went.
    """
    entry.procedure = procedure
    for step in procedure.steps:
        step.head = step.authored_head or step.head
        step.readiness = step.readiness_declared
    procedure.problems, procedure.remarks = audit_procedure(
        procedure, entry.sitting, entry.rows, checks, owed_ids, sittings, surfaces,
        platform=platform, retired=retired, known=known)
    if procedure.problems:
        return
    applicable = [step for step in procedure.steps
                  if not step.platforms or not platform or platform in step.platforms]
    current_state = ""
    for step in procedure.steps:
        step.required_state = ""
    for step in applicable:
        if step.state_declared:
            current_state = step.state_declared
        step.required_state = current_state
    for step in procedure.steps:
        action = step.action_for.get(platform)
        if action:
            prefix = _ACTION_HEAD_RE.match(step.authored_head)
            if prefix:
                step.head = "%s %s" % (prefix.group(1), action)
        if step.readiness and step.readiness.get("platforms") and platform not in step.readiness["platforms"]:
            step.readiness = {}
    owed_parts = {part for c in entry.rows for part in parts_of(c)}
    direct: set[int] = set()
    for step in procedure.steps:
        for expectation in step.expectations:
            expectation.owed.clear()
    for step in applicable:
        for expectation in step.expectations:
            expectation.owed = {tag for tag in expectation.tags if tag in owed_parts}
        if any(e.owed for e in step.expectations):
            direct.add(step.number)
    needed = set(direct)
    pending = list(direct)
    while pending:
        for prerequisite in procedure.requires.get(pending.pop(), []):
            if prerequisite not in needed:
                needed.add(prerequisite)
                pending.append(prerequisite)
    kept = [step for step in applicable if step.number in needed]
    by_number = {step.number: step for step in procedure.steps}
    for step in procedure.steps:
        step.capture_needed = False
    for step in kept:
        for source in step.uses_capture:
            by_number[source].capture_needed = True
    entry.steps = kept
    entry.omitted = len(procedure.steps) - len(kept)
    entry.owed_checks = list(entry.rows)
    entry.setup = "\n\n".join(item.text for item in procedure.setup_items
                              if (not item.platforms or not platform or platform in item.platforms)
                              and (not item.steps or item.steps & needed))


def validate_preparation(procedure: Procedure, platform: str = "") -> list[str]:
    """Reject broken declarations before they can drop an owed observation."""
    problems = list(procedure.parse_problems)
    steps = {step.number: step for step in procedure.steps}
    graph = procedure.requires
    for number, targets in graph.items():
        if number not in steps:
            problems.append("%s: `requires` names absent step %d" % (procedure.path, number))
        for target in targets:
            if target not in steps:
                problems.append("%s: step %d requires absent step %d"
                                % (procedure.path, number, target))
            elif number in steps and platform and (
                    not steps[number].platforms or platform in steps[number].platforms) and (
                    steps[target].platforms and platform not in steps[target].platforms):
                problems.append("%s: step %d requires step %d, which is unavailable on %s"
                                % (procedure.path, number, target, platform))
            if target >= number:
                problems.append("%s: step %d requires step %d, but a prerequisite must come earlier"
                                % (procedure.path, number, target))
    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(number: int) -> None:
        if number in visiting:
            problems.append("%s: `requires` has a cycle through step %d"
                            % (procedure.path, number))
            return
        if number in visited or number not in steps:
            return
        visiting.add(number)
        for target in graph.get(number, []):
            visit(target)
        visiting.remove(number)
        visited.add(number)

    for number in graph:
        visit(number)
    for item in procedure.setup_items:
        for number in item.steps:
            if number not in steps:
                problems.append("%s: setup item %s names absent step %d"
                                % (procedure.path, item.id, number))
    for step in procedure.steps:
        if step.action_for and (not _ACTION_HEAD_RE.match(step.authored_head)
                                or parse_tags(step.body[0])):
            problems.append("%s: step %d needs a bold surface heading without test tags for `action_for`"
                            % (procedure.path, step.number))
        for source in step.uses_capture:
            if source not in steps:
                problems.append("%s: step %d uses evidence from absent step %d"
                                % (procedure.path, step.number, source))
            elif source >= step.number:
                problems.append("%s: step %d must use evidence from an earlier step"
                                % (procedure.path, step.number))
            elif not steps[source].capture_prompt:
                problems.append("%s: step %d uses step %d but it declares no capture prompt"
                                % (procedure.path, step.number, source))
            elif source not in graph.get(step.number, []):
                problems.append("%s: step %d must require evidence source step %d"
                                % (procedure.path, step.number, source))
    return problems


def audit_procedure(procedure: Procedure, sitting: Sitting, owed: list[Check],
                    checks: dict[str, Check], owed_ids: set[str],
                    sittings: list[Sitting], surfaces: dict[str, str],
                    platform: str = "",
                    retired: set[str] | None = None,
                    known: dict[str, Check] | None = None) -> tuple[list[str], list[str]]:
    """(problems, remarks) for one procedure ("The walk", rule 9).

    A problem is a disagreement between the procedure and the release's owed
    set, or between a quoted expectation and the check it quotes. A remark is
    something true that is not a disagreement -- a step that names no screen,
    or a live check the procedure has not reached yet. Coverage of the owed
    parts is the requirement; coverage of everything live is the aim.
    """
    problems: list[str] = validate_preparation(procedure, platform)
    remarks: list[str] = []
    retired = retired or set()
    #: **Every check a tag may legally name, not only the owed ones.** A
    #: procedure covers its whole sitting and prints the owed part of itself,
    #: so it cites checks that have already passed. A host that passed only
    #: the owed set -- which the cockpit's `walk_payload` did -- reported
    #: every such tag as naming no check at all, and the two readers of one
    #: corpus disagreed about one procedure. That is exactly what rule 7 says
    #: bundling this module prevents. Found by independent review, 2026-09-14.
    known = known or checks
    where = placement(sorted(known.values(), key=lambda c: c.id), sittings, surfaces)
    want: dict[tuple[str, str], Check] = {}
    for check in owed:
        for part in parts_of(check):
            want[part] = check
    cited: dict[tuple[str, str], set[int]] = {}
    applicable = [step for step in procedure.steps
                  if not step.platforms or not platform or platform in step.platforms]
    off = [s for s in applicable if s.written and s.written != s.number]
    if off:
        remarks.append(
            "%s numbers its steps %s and the sheet prints them 1 to %d; a "
            "part is counted by position, so cite the position"
            % (procedure.path, ", ".join(str(s.written) for s in procedure.steps),
               len(procedure.steps)))
    for step in applicable:
        if not step.surface_id:
            remarks.append("step %d names no screen; a step says where it "
                           "happens (%s)" % (step.number, procedure.path))
        in_fence = False
        for line in step.body:
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for candidate in _TAG_LIKE_RE.finditer(line):
                if not _TAG_RE.fullmatch(candidate.group()):
                    problems.append(
                        "step %d of %s has malformed expectation tag %s; "
                        "use a numeric `TST-####.N` tag or a bare check id"
                        % (step.number, procedure.path, candidate.group()))
        for expectation in step.expectations:
            for tag in expectation.tags:
                cited.setdefault(tag, set()).add(step.number)
                problems.extend(_audit_tag(procedure, step, expectation, tag,
                                           known, retired, where, sitting.name))
    for part in sorted(want):
        if part not in cited:
            check = want[part]
            problems.append(
                "%s owes %s and no step cites it; the walker would not walk it "
                "(%s)" % (sitting.name, _part_name(part), procedure.path))
    for part, steps in sorted(cited.items()):
        if part in want and len(steps) > 1:
            problems.append(
                "%s is cited by steps %s; one owed part is walked once, so the "
                "verdict has one place to come from (%s)"
                % (_part_name(part), ", ".join(str(n) for n in sorted(steps)),
                   procedure.path))
    live = [c for c in known.values()
            if c.section != "automated" and where.get(c.id) == sitting.name]
    covered = {tag[0] for tag in cited}
    missing = sorted(c.id for c in live if c.id not in covered)
    if missing:
        remarks.append(
            "covers %d of %d live checks in \"%s\"; not yet reached: %s"
            % (len(live) - len(missing), len(live), sitting.name,
               ", ".join(missing)))
    return problems, remarks


def _part_name(part: tuple[str, str]) -> str:
    return "%s step %s" % part if part[1] else "%s (one part, its steps are not numbered)" % part[0]


def _audit_tag(procedure: Procedure, step: Step, expectation: Expectation,
               tag: tuple[str, str], checks: dict[str, Check], retired: set[str],
               where: dict[str, str], sitting_name: str) -> list[str]:
    """Everything wrong with one tag on one line."""
    check_id, number = tag
    at = "step %d of %s" % (step.number, procedure.path)
    if check_id in retired:
        return ["%s cites %s, which is retired; a retired check is kept and no "
                "longer asked" % (at, check_id)]
    check = checks.get(check_id)
    if check is None:
        return ["%s cites %s, which matches no acceptance check in this repo"
                % (at, check_id)]
    claimed_by = where.get(check_id, "")
    if claimed_by and claimed_by != sitting_name:
        return ['%s cites %s, which the sitting "%s" claims; a check is walked '
                "in one sitting" % (at, check_id, claimed_by)]
    numbers = numbered_steps(check)
    if number and int(number) not in numbers:
        return ["%s cites step %s of %s, which has %s"
                % (at, number, check_id,
                   "no numbered steps" if not numbers
                   else "steps %s" % ", ".join(str(n) for n in numbers))]
    if not number and numbers:
        return ["%s cites %s with no step number, and that check numbers %d "
                "steps; cite the step" % (at, check_id, len(numbers))]
    wanted = expect_lines(check)
    if not wanted:
        #: **Silence is not a mismatch.** The check states no expected result,
        #: so there is nothing to compare the quote against and no evidence
        #: either way. Reporting a mismatch here would be a claim the
        #: validator cannot support, and 57 of 61 rows on the corpus that
        #: needs this look like that today (project-os-dev ISS-0064).
        return []
    if expectation.quote not in wanted:
        return ["%s quotes %s as %r, and that check's Expect says none of: %s"
                % (at, check_id, expectation.quote,
                   "; ".join(repr(w) for w in sorted(wanted)))]
    return []


def unordered_sittings(checks: list[Check]) -> list[Sitting]:
    """The fallback for a project with no WALK.md: one sitting per area.

    Id order inside, area order outside, and the sheet says its order is
    nobody's. Better than one undifferentiated list, and visibly not a walk
    order somebody authored ("The walk", rule 3).
    """
    areas = sorted({c.area for c in checks if c.area})
    out = [Sitting(name=area, surfaces=[area]) for area in areas]
    return out


# --------------------------------------------------------------- the renderer

def _quote(text: str) -> str:
    return "\n".join("> " + line if line.strip() else ">"
                     for line in text.splitlines())


def _plural(n: int, one: str, many: str = "") -> str:
    return one if n == 1 else (many or one + "s")


def render_survey(walk: Walk, out: list[str]) -> None:
    """The screens this release changed ("The walk", rule 2).

    No check id appears here, and that is the rule rather than an oversight:
    the survey is a list of places to open and look at. The previous version
    printed the checks an invalidation reopened, which is a list of things to
    run, and a person read it as the start of the walk instead of as the look
    around before it.
    """
    out.append("## Survey — the screens this release changed")
    out.append("")
    if walk.gallery:
        out.append("Regenerate and compare before walking anything: `%s`" % walk.gallery)
        out.append("")
    if walk.survey_problem:
        out.append("**No release to compare against:** %s. Nothing is listed "
                   "below, because without a last release nothing says which "
                   "change notes are new." % walk.survey_problem)
        out.append("")
    elif walk.survey_tag:
        out.append("Compared against **%s**, tagged `%s`. Every change note added "
                   "since that tag is read for the screens it says it altered."
                   % (walk.survey_release or "the last release", walk.survey_tag))
        out.append("")
    if not walk.survey:
        out.append("No change note names a screen. Either this release altered no "
                   "screen, or its change notes have no `## Impact` list — the "
                   "close-out step that writes one is in "
                   '`tools/instructions/TESTING.md`, "The walk", rule 8.')
        out.append("")
        return
    out.append("Open these screens and look at them before walking a single "
               "scripted step. Each line under a screen is what one change says "
               "it altered there.")
    out.append("")
    for screen in walk.survey:
        depth = "####" if screen.parent else "###"
        label = "%s (%s)" % (screen.title, screen.id) if screen.title != screen.id else screen.id
        out.append("%s %s" % (depth, label))
        out.append("")
        if screen.unresolved:
            out.append("**No surface note carries this id.** A change note names "
                       "it, so something was altered, and nobody reading this "
                       "sheet can tell which screen to open.")
            out.append("")
        for change_id, title, sentence in screen.sentences:
            said = sentence or "_that change names this screen and says nothing about it_"
            out.append("- %s — %s" % (said, title or change_id))
        out.append("")
        for capture in screen.captures:
            name = "`%s`" % capture.key
            if capture.state:
                name += " (%s)" % capture.state
            if capture.new:
                out.append("%s — **new**, captured now and not at the last release:"
                           % name)
                out.append("")
                out.append("![%s, now](%s)" % (capture.key, capture.after))
            elif capture.after:
                out.append("%s — before, then now:" % name)
                out.append("")
                out.append("![%s, at the last release](%s)" % (capture.key, capture.before))
                out.append("")
                out.append("![%s, now](%s)" % (capture.key, capture.after))
            else:
                out.append("%s — captured at the last release and not since:" % name)
                out.append("")
                out.append("![%s, at the last release](%s)" % (capture.key, capture.before))
            out.append("")


def render_check(check: Check, out: list[str], platform: str = "") -> None:
    """One per-check row, walkable without leaving the sheet (rule 5)."""
    head = "### [%s](%s)" % (check.id, check.path)
    if check.title:
        head += " — %s" % check.title
    out.append(head)
    out.append("")
    readiness = check_readiness(check, platform)
    if readiness:
        label = "Needs preparation" if readiness["kind"] == "preparation" else "Needs a decision"
        out.append("**%s:** %s" % (label, readiness["reason"]))
        if readiness.get("issue"):
            out.append("Related issue: %s." % readiness["issue"])
        out.append("")
    out.append("- [ ] walked, and the verdict recorded in the ledger" if not readiness
               else "- [ ] readiness resolved, then walked or a decision recorded in the ledger")
    out.append("")
    if check.setup:
        out.append("**Setup:** %s" % check.setup.strip())
    else:
        out.append("**Setup: not stated.** This check has no Setup "
                   "heading. Write one while you walk it "
                   '(`tools/instructions/TESTING.md`, "A check is '
                   'walkable by a stranger").')
    out.append("")
    if check.steps:
        out.append("**Steps:**")
        out.append("")
        out.append(check.steps)
    elif check.lead:
        out.append("**Steps: no heading.** The note's own description "
                   "is below; give it numbered steps while you walk it.")
        out.append("")
        out.append(check.lead)
    else:
        out.append("**Steps:**")
        out.append("")
        out.append("_The note states no steps._")
    out.append("")
    out.append("**Expect:**")
    out.append("")
    out.append(check.expect if check.expect
               else "_The note states no expected result._")
    out.append("")


def render_procedure(placed: Placed, out: list[str]) -> None:
    """One sitting walked from its written script ("The walk", rule 9)."""
    procedure = placed.procedure
    out.append("Walked from a procedure: [%s](%s). The setup below is stated once "
               "and every step assumes it." % (procedure.path, procedure.path))
    out.append("")
    if placed.setup:
        out.append("**Setup:**")
        out.append("")
        out.append(placed.setup)
    else:
        out.append("**Setup: not stated.** The procedure has no Setup heading, so "
                   "every step below assumes a state nobody wrote down.")
    out.append("")
    out.append("%d %s to walk." % (len(placed.steps), _plural(len(placed.steps), "step")))
    if placed.omitted:
        out.append("")
        out.append("%d further %s in this procedure %s left out because %s "
                   "not needed for this platform's owed observations."
                   % (placed.omitted, _plural(placed.omitted, "step"),
                      _plural(placed.omitted, "is", "are"),
                      _plural(placed.omitted, "it is", "they are")))
    out.append("")
    for position, step in enumerate(placed.steps, start=1):
        preparation = not any(expectation.owed for expectation in step.expectations)
        out.append("#### Step %d%s%s" % (
            position,
            " — %s" % step.surface_said if step.surface_said else "",
            " (preparation; source step %d)" % step.number if preparation else
            " (source step %d)" % step.number if position != step.number else ""))
        out.append("")
        if step.required_state:
            out.append("**Required state:** %s" % step.required_state)
            out.append("")
        if step.readiness:
            label = "Needs preparation" if step.readiness["kind"] == "preparation" else "Needs a decision"
            out.append("**%s:** %s%s" % (label, step.readiness["reason"],
                       " (%s)" % step.readiness["issue"] if step.readiness["issue"] else ""))
            out.append("")
        if step.capture_needed:
            out.append("**Capture here for a later comparison:** %s" % step.capture_prompt)
            out.append("")
        if step.uses_capture:
            out.append("**Compare with evidence from source %s.**" % ", ".join(
                "step %d" % source for source in step.uses_capture))
            out.append("")
        if step.timer_seconds:
            out.append("**Optional timer:** %d seconds. Ending it records no verdict."
                       % step.timer_seconds)
            out.append("")
        if preparation:
            out.append("_Prepare the next observation. Continue without recording a test verdict._")
            out.append("")
        for i, line in enumerate(step.body):
            #: The step's number is already in the heading above, so the first
            #: line prints without it. Everything else prints as written: a
            #: walker follows these words and a generator that reflowed them
            #: would be putting words nobody wrote in front of the person
            #: recording the verdict.
            text = step.head if i == 0 else line
            if not text.strip():
                out.append("")
                continue
            found = next((e for e in step.expectations if e.raw == line), None)
            if found is None:
                out.append(text)
                continue
            if preparation:
                continue
            passed = [tag for tag in found.tags if tag not in found.owed]
            suffix = ""
            if passed:
                suffix = "  _(already walked: %s)_" % ", ".join(
                    _part_name(tag) for tag in passed)
            out.append(text.rstrip() + suffix)
        out.append("")
    out.append("**Record a verdict for each of these when the procedure is done:**")
    out.append("")
    for check in placed.owed_checks:
        out.append("- [ ] [%s](%s)%s" % (check.id, check.path,
                                         " — %s" % check.title if check.title else ""))
    out.append("")


def render(walk: Walk) -> str:
    """The sheet a person reads. Counts of rows are the only numbers on it."""
    out: list[str] = []
    out.append("# Walk sheet — %s, %s" % (walk.release, walk.platform))
    out.append("")
    out.append("Generated %s by `tools/scripts/walk-sheet.py` from the release "
               "ledger, the check notes, the change notes and "
               "`docs/tests/acceptance/WALK.md`. "
               "Do not edit it: record every verdict in the ledger and generate "
               "it again. The rules are in `tools/instructions/TESTING.md`, "
               '"The walk".' % walk.generated)
    out.append("")
    out.append("**%d owed %s in %d %s.**"
               % (walk.rows, "row" if walk.rows == 1 else "rows",
                  len(walk.sittings) + (1 if walk.unplaced else 0),
                  "sitting" if len(walk.sittings) + (1 if walk.unplaced else 0) == 1
                  else "sittings"))
    out.append("")
    out.append("The validator counts from `mark:` on the note; this sheet counts "
               "from the ledger (project-os-dev ISS-0060).")
    if not walk.authored_order:
        out.append("")
        out.append("**This project has authored no walk order.** The sittings "
                   "below are one per `area:` in id order, which is a grouping "
                   "and not a walk. Copy `docs/__templates__/walk.md` to "
                   "`docs/tests/acceptance/WALK.md` and write the real one.")
    for notice in walk.notices:
        out.append("")
        out.append("**Note:** %s" % notice)
    for warning in walk.warnings:
        out.append("")
        out.append("**Check the walk order:** %s" % warning)
    out.append("")

    render_survey(walk, out)

    def rows_of(title: str, placed: Placed | None, rows: list[Check]) -> None:
        sitting = placed.sitting if placed is not None else None
        out.append("## %s" % title)
        out.append("")
        if sitting is not None and sitting.state:
            out.append("**State this sitting needs:** %s" % sitting.state)
            out.append("")
        if sitting is not None and sitting.bench:
            out.append("**On the bench:**")
            out.append("")
            for item in sitting.bench:
                out.append("- %s" % item)
            out.append("")
        if placed is not None and placed.procedure is not None and placed.procedure.problems:
            out.append("**This sitting has a procedure and it no longer matches "
                       "what the release owes.** The checks are printed one by "
                       "one below instead, so nothing owed is hidden. Rewrite it "
                       "with `tools/skills/walk-procedure/SKILL.md`:")
            out.append("")
            for problem in placed.procedure.problems:
                out.append("- %s" % problem)
            out.append("")
        if placed is not None and placed.walked_from_procedure:
            out.append("%d owed %s, walked as one script."
                       % (len(rows), _plural(len(rows), "check")))
            out.append("")
            render_procedure(placed, out)
            return
        out.append("%d %s." % (len(rows), "row" if len(rows) == 1 else "rows"))
        out.append("")
        for check in rows:
            render_check(check, out, walk.platform)

    for i, placed in enumerate(walk.sittings, start=1):
        rows_of("Sitting %d — %s" % (i, placed.sitting.name), placed, placed.rows)
    if walk.unplaced:
        rows_of("Unplaced", None, walk.unplaced)
        out.append("These rows are owed and no sitting in "
                   "`docs/tests/acceptance/WALK.md` claims their `area:`. That "
                   "is the walk order's worklist, not a defect in the sheet: "
                   "add a sitting that claims them, or add the area to one that "
                   "exists.")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------- main

def retired_checks(docs_root: Path, index=None) -> set[str]:
    """The acceptance checks that are kept and no longer asked.

    `load_checks` drops them, which is right for a sheet and wrong for the
    validator: a procedure citing a retired check must be told that is what it
    did, and a check that is simply absent gets a different message.
    """
    vd = _validator()
    if index is None:
        index, _ = vd.build_note_index(docs_root)
    return {note_id for note_id, (path, fm) in index.items()
            if isinstance(fm, dict) and vd.note_type(fm) == "test"
            and _text(fm.get("level")) == "acceptance"
            and _text(fm.get("status")) in RETIRED}


@dataclass
class Reading:
    """Everything one platform's walk is computed from, read once."""

    repo_root: Path
    docs_root: Path
    index: dict
    checks: dict[str, Check]
    retired: set[str]
    surfaces: dict[str, str]
    surface_notes: dict[str, Surface]
    events: list[Event]
    sittings: list[Sitting]
    procedures: list[Procedure]
    gallery: str = ""
    warnings: list[str] = field(default_factory=list)
    authored: bool = True
    survey_release: str = ""
    survey_tag: str = ""
    survey_problem: str = ""
    changes: list[Change] = field(default_factory=list)


def read_repo(repo_root: Path, platform: str) -> Reading:
    """Read a repo once, for either the sheet or the check."""
    docs_root = repo_root / "docs"
    if not has_ledger(docs_root):
        raise WalkError(
            "no release ledger in %s. A walk sheet is the ledger's owed set, so "
            "there is nothing to generate until the first verdict is written "
            "through the ledger path, which creates "
            "docs/releases/ledgers/WORKING-<platform>.json. A new project "
            "starting with no ledger is project-os-dev ISS-0059."
            % (docs_root / LEDGERS_REL))
    vd = _validator()
    index, _ = vd.build_note_index(docs_root)
    checks = load_checks(docs_root, index, repo_root=repo_root)
    if not checks:
        raise NothingToWalk(
            "no acceptance checks in %s. A walk sheet lists `[[test]]` notes at "
            "`level: acceptance`; this repo has none." % docs_root)
    known = platforms(docs_root)
    if platform not in known:
        raise WalkError(
            "no ledger for platform %r. This repo keeps one for: %s. A walk "
            "asked for by an unknown name would read no verdicts at all and "
            "report every check in the repo as owed, so it is refused instead."
            % (platform, ", ".join(known) or "(none)"))
    walk_path = docs_root / WALK_REL
    authored = walk_path.is_file()
    if authored:
        gallery, sittings, warnings = parse_walk_order(
            walk_path.read_text(encoding="utf-8"))
    else:
        gallery, sittings, warnings = "", unordered_sittings(list(checks.values())), []
    surface_notes = load_surfaces(index)
    procedures = load_procedures(docs_root, repo_root)
    for procedure in procedures:
        name_surfaces(procedure.steps, surface_notes)
    release_id, tag, problem = last_release(docs_root, platform)
    added: set[str] = set()
    if tag:
        added, problem = changes_since(repo_root, tag)
    changes = load_changes(docs_root, repo_root, only=added if tag and not problem else set())
    return Reading(
        repo_root=repo_root, docs_root=docs_root, index=index, checks=checks,
        retired=retired_checks(docs_root, index),
        surfaces=surfaces_by_title(index), surface_notes=surface_notes,
        events=load_events(docs_root, platform), sittings=sittings,
        procedures=procedures, gallery=gallery, warnings=warnings,
        authored=authored, survey_release=release_id,
        survey_tag="" if problem else tag, survey_problem=problem, changes=changes)


def generate(repo_root: Path, release: str, platform: str) -> Walk:
    read = read_repo(repo_root, platform)
    notices: list[str] = []
    sealed = sealed_releases(read.docs_root).get(release, "")
    if sealed:
        notices.append(
            "%s is already sealed (its ledger is %s-%s.json). This sheet is "
            "what the platform owes NOW, not what that release owed when it "
            "was sealed, because a ledger resolves forward."
            % (release, release, sealed))
    return build_walk(
        read.checks, read.events, read.sittings, release=release, platform=platform,
        surfaces=read.surfaces, surface_notes=read.surface_notes,
        changes=read.changes, procedures=read.procedures, retired=read.retired,
        captures=capture_finder(read.docs_root, repo_root, read.survey_tag),
        gallery=read.gallery, warnings=read.warnings, notices=notices,
        authored_order=read.authored, survey_release=read.survey_release,
        survey_tag=read.survey_tag, survey_problem=read.survey_problem)


def check_repo(repo_root: Path, platform: str) -> tuple[list[str], list[str]]:
    """(problems, remarks) for every procedure in a repo, on one platform."""
    read = read_repo(repo_root, platform)
    problems: list[str] = []
    for check in read.checks.values():
        problems.extend(check.readiness_problems)
    remarks: list[str] = []
    owed = owed_checks(read.checks, read.events)
    owed_ids = {c.id for c in owed}
    by_name = {s.name: s for s in read.sittings}
    seen: set[str] = set()
    for procedure in read.procedures:
        if not procedure.sitting:
            problems.append("%s: no `sitting:` in its frontmatter, so nothing "
                            "says which sitting it walks" % procedure.path)
            continue
        if procedure.sitting not in by_name:
            problems.append(
                '%s: `sitting: "%s"` matches no `### ` heading in docs/%s'
                % (procedure.path, procedure.sitting, WALK_REL))
            continue
        if procedure.sitting in seen:
            problems.append('%s: a second procedure for "%s"; one sitting is '
                            "walked from one script" % (procedure.path, procedure.sitting))
            continue
        seen.add(procedure.sitting)
        sitting = by_name[procedure.sitting]
        mine = [c for c in owed if claims(sitting, c, read.surfaces)]
        placed = placement(owed, read.sittings, read.surfaces)
        mine = [c for c in mine if placed.get(c.id) == sitting.name]
        found, said = audit_procedure(procedure, sitting, mine, read.checks,
                                      owed_ids, read.sittings, read.surfaces,
                                      platform=platform,
                                      retired=read.retired)
        problems.extend(found)
        remarks.extend(said)
    if read.procedures:
        uncovered = sorted({placement(owed, read.sittings, read.surfaces).get(c.id, "")
                            for c in owed} - seen - {""})
        if uncovered:
            remarks.append("no procedure yet for: %s" % ", ".join(uncovered))
    #: **Every change note, not only the ones this release surveys.** The
    #: survey is restricted to what git says is new since the tag; the
    #: worklist is not, and a repo with no released note would otherwise be
    #: told nothing at all about its Impact lists. Found by independent
    #: review, 2026-09-14.
    for change in load_changes(read.docs_root, repo_root):
        for surface_id, _ in change.screens:
            if surface_id not in read.surface_notes:
                remarks.append("%s names %s in its Impact list and no surface "
                               "note carries that id" % (change.path, surface_id))
        if change.silent:
            remarks.append("%s has no `## Impact` list, so it tells the survey "
                           "nothing; write the screens it altered, or "
                           '"No screen changed" and why' % change.path)
    return problems, remarks


def run_check(repo_root: Path, platform: str, quiet: bool = False) -> int:
    """`--check` over one platform or all of them. 0 = nothing to fix.

    **Nothing to check is not a failure, and a broken ledger still is.** No
    ledger and no live acceptance check are both repos with no procedure to
    hold to anything, and `validate-docs.sh` runs this on every commit --
    letting those through made a repo whose checks had all been retired fail
    its own pre-commit hook forever. But the first fix caught every
    `WalkError`, which took a malformed ledger with it; `NothingToWalk` is the
    narrow one. Both halves found by independent review, 2026-09-14, rounds
    one and two.
    """
    docs_root = repo_root / "docs"
    if not has_ledger(docs_root):
        return 0
    wanted = [platform] if platform else platforms(docs_root)
    status = 0
    for name in wanted:
        try:
            problems, remarks = check_repo(repo_root, name)
        except NothingToWalk as exc:
            #: No live acceptance check means no procedure to hold to anything.
            if not quiet:
                print("walk-sheet --check (%s): nothing to check -- %s"
                      % (name, exc), file=sys.stderr)
            continue
        except WalkError as exc:
            #: Everything else `read_repo` refuses is a broken ledger, and
            #: `--check` is the only thing that reads one on every commit.
            print("walk-sheet --check (%s): %s" % (name, exc), file=sys.stderr)
            status = 2
            continue
        for problem in problems:
            print("walk-sheet --check (%s): %s" % (name, problem), file=sys.stderr)
        #: Remarks are printed when something is wrong, or when a person
        #: asked. `validate-docs.sh` runs this on every commit, and a repo
        #: with procedures would otherwise print its coverage shortfall to
        #: everybody, every time, until it stopped being read.
        if problems or not quiet:
            for remark in remarks:
                print("walk-sheet --check (%s): note: %s" % (name, remark))
        if problems:
            status = 1
    return status


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a release walk sheet: the owed acceptance checks "
                    "as a procedure, the changed screens first.",
        epilog="The rules are stated once in tools/instructions/TESTING.md, "
               '"The walk"; this script restates none of them. The survey lists '
               "the screens the change notes added since the last release tag "
               "say they altered. Without --out the sheet goes to stdout; a "
               "sheet kept as a record of what was walked is never edited by "
               "hand and never read back. --check walks the procedures instead "
               "and exits 1 when one no longer matches what the release owes.")
    ap.add_argument("--release", default="",
                    help="the release this walk is for, e.g. REL-0017")
    ap.add_argument("--platform", default="",
                    help="the platform whose ledger is read, e.g. android; with "
                         "--check, every platform when omitted")
    ap.add_argument("--check", action="store_true",
                    help="hold each sitting's procedure to what the release "
                         "owes, print nothing else, and exit 1 on a disagreement")
    ap.add_argument("--out", default="",
                    help="write the sheet here instead of stdout")
    ap.add_argument("--quiet", action="store_true",
                    help="with --check, print remarks only when something is "
                         "also wrong")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not (root / "SNAPSHOT.yaml").is_file():
        print("walk-sheet: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 2
    if args.check:
        return run_check(root, args.platform, quiet=args.quiet)
    missing = [name for name, value in (("--release", args.release),
                                        ("--platform", args.platform)) if not value]
    if missing:
        print("walk-sheet: %s required to generate a sheet"
              % " and ".join(missing), file=sys.stderr)
        return 2
    try:
        walk = generate(root, args.release, args.platform)
    except WalkError as exc:
        print("walk-sheet: %s" % exc, file=sys.stderr)
        return 2
    text = render(walk)
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print("walk-sheet: %d owed rows -> %s" % (walk.rows, target))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
