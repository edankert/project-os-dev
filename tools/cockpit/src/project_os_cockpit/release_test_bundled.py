#!/usr/bin/env python3
"""Generate a release test sheet: the owed acceptance checks as a procedure.

A release test sheet is what a person reads while testing a release by hand. It opens with the
screens the release changed, then lists every check the platform still owes, in
the order the project authored, with each check's setup, steps and expected
result printed on the page. The rules it implements are stated once in
`tools/instructions/TESTING.md`, "The release test" (project-os-dev ADR-0029); this
file restates none of them and is the only code that computes a release test.

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
  * `docs/tests/acceptance/RELEASE-TEST.md`, the project's authored section order;
  * `docs/tests/acceptance/release-test/*.md`, one written procedure per section;
  * the `SUR-*` notes, for their titles, their `parent:` and their `gallery:`;
  * `docs/changes/CHG-*.md` added since the last release tag, for the `##
    Impact` list that says which screens each one altered;
  * `git`, to find that tag and to date the change notes against it. This is
    the only subprocess it runs, and a checkout without the tag loses the
    what-changed list and nothing else.

--check
-------
`--check` reads the procedures instead of printing a sheet: it fails when a
procedure and the release's owed set disagree ("The release test", rule 9). Exit 1 =
at least one procedure is wrong, 0 = nothing to fix. `validate-docs.sh` runs
it for every platform that has a ledger.

It writes markdown and never reads a sheet back. A generated sheet may be kept
as a record of what was tested; it is never edited by hand and nothing parses
it ("The release test", rule 1). `--out` is therefore optional: the sheet goes to
stdout unless a path is named.

THE OWED PREDICATE IS THE GATE'S
--------------------------------
A row is a manual check (a feature or regression test, so no `command:`) with
no surviving clearing verdict for this platform. That is `ledger.owed()` in
`project-os-cockpit`, reproduced here entry for entry, because two
implementations of one predicate is how a badge and a gate come to disagree
about one corpus. The cockpit bundles this module rather than writing a second
one ("The release test", rule 7).

Exit codes: 0 = a sheet was produced, 2 = usage error or no ledger in this repo.

Stdlib only. Usage:
    release-test.py --release REL-0017 --platform android [--out PATH] [--repo-root DIR]
    release-test.py --check [--platform android] [--repo-root DIR]
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
#: import `build_release_test` and `render` without dragging the validator in.
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
        spec = ilu.spec_from_file_location("_vd_release_test", here)
        module = ilu.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        _VD = module
    return _VD


#: `TASK-0825`, and `CHG-20260913` out of `CHG-20260913-The-Banner-Moves`.
#: **Two or more digits, not three or four**: a change note's id carries an
#: eight-digit date, so the narrower pattern matched every task and no change
#: at all -- and an invalidation naming a change then produced a what-changed entry
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


def under_heading(body: str, *names: str) -> str:
    """The text under the first of ``names`` that the note has, verbatim.

    Verbatim is the rule, not a convenience: a tester follows these words, and
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
    #: An Expect line marked for a platform this repo keeps no ledger for
    #: (project-os-dev REQ-0034). The line prints on no platform, so it is
    #: refused rather than lost.
    expect_problems: list[str] = field(default_factory=list)

    @property
    def kind(self) -> str:
        """feature / regression / automated -- derived, never filed.

        `TESTING.md`, "The three test kinds": a `command:` makes it automated; a
        `covers:` naming an `ISS-*` makes it a claim about a past defect, so a
        regression; everything else is a standing claim about behaviour. A
        check naming no issue reads as a behaviour claim, which is the safe
        direction -- it stays on the list rather than settling forever.
        """
        if self.command:
            return "automated"
        #: **Only the automated branch changes a sheet**, because both of the
        #: others are manual and a row does not say which it is. The split is
        #: kept so this module and the cockpit name the same three test kinds
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
    known_platforms = platforms(docs_root)
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
        #: tested; what stops is the asking. A sheet that printed a retired
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
            fm.get("readiness_for"), str(shown))
        if "walk_readiness_for" in fm:
            readiness_problems.append(
                "%s: `walk_readiness_for` is the old name; it is now `readiness_for`. %s"
                % (shown, MIGRATE_HINT))
        #: A misspelt platform hid the notice on every platform without a word
        #: (FEAT-0033 review, 2026-09-24); procedures already refuse one.
        readiness_problems += ["%s: `readiness_for` names platform %s, and this repo "
                               "keeps ledgers only for %s" % (shown, name, ", ".join(known_platforms))
                               for name in sorted(readiness) if known_platforms and name not in known_platforms]
        expect = under_heading(body, "Expect", "Expected results")
        expect_problems = [
            "%s: an Expect line is marked [%s], and this repo keeps ledgers only for %s: %s"
            % (note_id, name, ", ".join(known_platforms), line.strip())
            for name, line in expect_marks(expect)
            if known_platforms and name not in known_platforms]
        out[note_id] = Check(
            id=note_id,
            title=_text(fm.get("title")),
            path=str(shown),
            area=_text(fm.get("area")),
            after=_ids(fm.get("after")),
            covers=_ids(fm.get("covers")),
            command=_text(fm.get("command")),
            setup=under_heading(body, "Setup"),
            #: Procedure and Expected results are the pre-ADR-0027 headings.
            #: Read as fallbacks so a corpus nobody has rewritten yet still
            #: yields a row a person can test. Setup has no fallback, and that absence
            #: is the point of the "not stated" label.
            steps=under_heading(body, "Steps", "Procedure"),
            expect=expect,
            lead=lead_paragraph(body),
            readiness_for=readiness,
            readiness_problems=readiness_problems,
            expect_problems=expect_problems,
        )
    return out


def parse_check_readiness(raw, path: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Read a check's explicit per-platform readiness for fallback rows."""
    if raw in (None, ""):
        return {}, []
    if not isinstance(raw, dict):
        return {}, ["%s: `readiness_for` must map platforms to kind and reason" % path]
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
            problems.append("%s: `readiness_for` entry %r needs a platform, "
                            "kind preparation or decision, and a plain reason" % (path, platform))
            continue
        if _result_problem(value):
            problems.append("%s: `readiness_for` entry %r %s"
                            % (path, platform, _result_problem(value)))
            continue
        out[platform] = {"kind": value["kind"],
                         "reason": value["reason"].strip(),
                         "issue": value.get("issue", "").strip(),
                         "result": value.get("result", "")}
    return out, problems


def check_readiness(check: Check, platform: str) -> dict[str, str]:
    """A malformed declaration is a visible decision, never a ready card."""
    if check.readiness_problems:
        return {"kind": "decision", "reason":
                "This check's readiness declaration is invalid. Fix its note "
                "before recording a verdict.", "issue": ""}
    return check.readiness_for.get(platform, {})


CHANGES_REL = "changes"
RELEASES_REL = "releases"
GALLERY_REL = "tests/acceptance/gallery"
PROCEDURES_REL = "tests/acceptance/release-test"
#: The folder holding the pictures of the build being tested. Every other
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
    dropped rather than kept as a string: the what-changed list nests by id, and a
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

    Follows `parent:` upwards with a seen-set, because a pair of notes naming
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
    #: `platforms:` from the frontmatter (project-os-dev REQ-0035). Empty
    #: means the note did not say, and it is then listed on every platform.
    platforms: list[str] = field(default_factory=list)
    #: The platform each entry of `screens` is marked for, "" for none: an
    #: Impact line may start `[ios]` where one note changed the platforms
    #: differently. Same length and order as `screens`.
    marks: list[str] = field(default_factory=list)
    #: `created:`, or the date in the file name, for the rule that a note
    #: written before `platforms:` existed is warned rather than refused.
    created: str = ""

    def on(self, platform: str) -> list[tuple[str, str]]:
        """The `(screen, sentence)` pairs this change made on ``platform``.

        An Impact line marked for a platform counts there only. An unmarked
        line counts where the note's `platforms:` says, and everywhere when
        the note declares none.
        """
        out = []
        for (surface_id, sentence), mark in zip(self.screens, self.marks or [""] * len(self.screens)):
            if mark:
                if not platform or mark == platform:
                    out.append((surface_id, sentence))
            elif not self.platforms or not platform or platform in self.platforms:
                out.append((surface_id, sentence))
        return out

    @property
    def silent(self) -> bool:
        """Neither a screen nor "No screen changed" -- nobody answered."""
        return not self.screens and not self.no_screen


def parse_impact(body: str) -> tuple[list[tuple[str, str]], bool]:
    """`## Impact` -> the screens it names with their sentences, and "none"."""
    entries, none = parse_impact_marked(body)
    return [(surface_id, sentence) for surface_id, sentence, _mark in entries], none


def parse_impact_marked(body: str) -> tuple[list[tuple[str, str, str]], bool]:
    """`## Impact` -> `(screen, sentence, platform or "")` per screen, and "none".

    The sentence is everything after the id and its separator, printed
    verbatim on the sheet. A line naming a screen and saying nothing about it
    keeps an empty sentence rather than being dropped: the screen still has
    to be looked at, and the silence is visible on the sheet.
    """
    return _screen_items(under_heading(body, IMPACT_HEADING).splitlines())


def _screen_items(lines: list[str]) -> tuple[list[tuple[str, str, str]], bool]:
    """List items that start with screen ids, as `(screen, sentence, platform)`.

    The shape of an Impact line, which the short what-changed lines reuse. A
    `[android]` or `[ios]` before the first id limits the line to that
    platform (project-os-dev REQ-0035).
    """
    screens: list[tuple[str, str, str]] = []
    none = False
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        #: **A fenced block is an example, not a claim.** A template or a
        #: change note showing the shape inside ``` would otherwise put a
        #: screen on the what-changed list that nothing altered. Found by independent
        #: review, 2026-09-14.
        if in_fence:
            continue
        item = _LIST_ITEM_RE.match(line)
        if not item:
            continue
        text = item.group(1).strip()
        mark, text = _split_mark(text)
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
            screens.append((surface_id, sentence, mark))
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
        entries, none = parse_impact_marked(body_of(path))
        raw = fm.get("platforms")
        declared = [_text(p) for p in (raw if isinstance(raw, list) else [raw]) if _text(p)]
        dated = re.match(r"CHG-(\d{4})(\d{2})(\d{2})", path.stem)
        created = _text(fm.get("created")) or ("%s-%s-%s" % dated.groups() if dated else "")
        out.append(Change(id=_text(fm.get("id")) or path.stem,
                          title=_text(fm.get("title")), path=str(shown),
                          screens=[(s, sentence) for s, sentence, _m in entries],
                          marks=[m for _s, _sentence, m in entries],
                          no_screen=none, platforms=declared, created=created))
    return out


# ------------------------------------------------ the short what-changed lines

#: One file per platform, `what-changed-<platform>.md`, beside the procedures
#: (project-os-dev REQ-0035). Its shape is SCHEMAS.md, "`what-changed.md`".
WHAT_CHANGED_PREFIX = "what-changed-"
#: A change note named on a short line: a wikilink, or the id in backticks.
_CHANGE_REF_RE = re.compile(r"\[\[(CHG-\d{8}[^\]|]*)(?:\|[^\]]*)?\]\]|`(CHG-\d{8}[^`]*)`")
_EMPTY_HOLDER_RE = re.compile(r"\s*\(\s*[,;]?\s*(?:[,;]\s*)*\)")


@dataclass
class ShortLines:
    """`what-changed-<platform>.md`: one short line per change and screen."""

    path: str
    tag: str
    #: `(change id, screen id) -> the short line`, in file order.
    lines: dict[tuple[str, str], str] = field(default_factory=dict)
    #: A line naming no change note, or no screen: nothing can be done with it.
    problems: list[str] = field(default_factory=list)


def what_changed_path(docs_root: Path, platform: str) -> Path:
    return docs_root / PROCEDURES_REL / ("%s%s.md" % (WHAT_CHANGED_PREFIX, platform))


def load_short_lines(docs_root: Path, platform: str,
                     repo_root: Path | None = None) -> ShortLines | None:
    """The platform's short what-changed lines, or None when there is no file.

    Written at release preparation, by an agent, against one release tag
    (project-os-dev ADR-0050 D3). Each line is an Impact-shaped item, a
    screen and a sentence, that also names the change note it summarises.
    """
    path = what_changed_path(docs_root, platform)
    if not path.is_file():
        return None
    shown = path
    if repo_root is not None:
        try:
            shown = path.relative_to(repo_root)
        except ValueError:
            pass
    fm = _validator().parse_frontmatter(path)
    fm = fm if isinstance(fm, dict) else {}
    out = ShortLines(path=str(shown), tag=_text(fm.get("tag")))
    body = body_of(path)
    entries, _none = _screen_items(body.splitlines())
    for surface_id, sentence, _mark in entries:
        refs = [a or b for a, b in _CHANGE_REF_RE.findall(sentence)]
        text = _WS_RE.sub(" ", _CHANGE_REF_RE.sub("", sentence))
        #: What held the reference: "()", "( , )" or a trailing dash.
        text = _EMPTY_HOLDER_RE.sub("", text).strip()
        text = re.sub(r"\s*[\u2014\u2013-]\s*$", "", text).strip()
        if not refs:
            out.problems.append("%s: the line for %s names no change note: %s"
                                % (out.path, surface_id, text))
            continue
        for ref in refs:
            out.lines.setdefault((ref.strip(), surface_id), text)
    in_fence = False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        item = _LIST_ITEM_RE.match(line)
        if in_fence or not item:
            continue
        _mark, text = _split_mark(item.group(1).strip())
        if not _SUR_RE.match(text) and _CHANGE_REF_RE.search(text):
            out.problems.append("%s: a line names a change note and no screen: %s"
                                % (out.path, text))
    return out


# ------------------------------------------------- the last release, and git

def _git(root: Path, *args: str) -> tuple[int, str]:
    """`git` in ``root``. A missing git is a return code, never an exception.

    The what-changed list is the only thing that needs git, so a machine
    without it, or a checkout that is not a repository, loses that list and
    keeps the sheet.
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

    The convention is `TESTING.md`, "The release test", rule 2: one folder per tag,
    plus `candidate/` for the build being tested.
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


# ------------------------------------------------------ a section's procedure

#: `1. ` or `1) ` at the start of a line, indented no more than three spaces --
#: deeper than that is a continuation inside the previous item, not a new one.
_STEP_RE = re.compile(r"^ {0,3}(\d+)[.)]\s+(.*)$")
#: `TST-0648.4` or `TST-0648`, in backticks. ASCII, because a tag is typed by
#: an LLM into a markdown file and read back by a regular expression; an
#: en dash or a smart quote in one would be a tag nobody can find.
_TAG_RE = re.compile(r"`(TST-\d{2,})(?:\.(\d+))?`")
#: A malformed backticked check reference must be reported even when another
#: valid tag on the same line satisfies coverage. Otherwise the unparsed text
#: becomes prose and an observation can disappear from the owed release test.
_TAG_LIKE_RE = re.compile(r"`TST-[^`]*`")
_ACTION_HEAD_RE = re.compile(r"^(\*\*.+?\.\*\*)\s*(.*)$")
_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_WS_RE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """One line of markdown, reduced to the words it asserts.

    The list marker goes, runs of whitespace collapse, and emphasis at either
    end goes -- `- **The banner reads DONE.**` and `The banner reads DONE.`
    say the same thing to a tester. Nothing inside the line is touched, so a
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
    #: Filled by `build_release_test`: which of this line's tags the release owes.
    owed: set[tuple[str, str]] = field(default_factory=set)
    #: Written by `expand_tag_only` from the check's own words, not by the
    #: procedure's author, so it is not a quote the author has to remove.
    expanded: bool = False


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
    #: when the release test is built for one platform.
    state_declared: str = ""
    required_state: str = ""
    #: A later retained step may ask the tester to keep evidence from here.
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
    #: The `### ` heading under `## Steps` this step sits under, "" before the
    #: first one (project-os-dev REQ-0033).
    group: str = ""

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
class Group:
    """A run of steps under one `### ` heading in `## Steps`.

    The heading names what the steps have in common, and the `Start:` line
    under it is the state the app and the bench must be in before the first
    of them (project-os-dev REQ-0033). It replaces `state_for:`.
    """

    title: str
    start: str = ""
    #: Step positions, in order.
    steps: list[int] = field(default_factory=list)


@dataclass
class Procedure:
    """One section's written script."""

    path: str
    section: str
    setup: str
    steps: list[Step] = field(default_factory=list)
    setup_items: list[SetupItem] = field(default_factory=list)
    requires: dict[int, list[int]] = field(default_factory=dict)
    #: The `### ` headings under `## Steps`, in order. Empty for a procedure
    #: written before groups existed.
    groups: list[Group] = field(default_factory=list)
    parse_problems: list[str] = field(default_factory=list)
    #: Why this procedure cannot be printed. Non-empty means the section falls
    #: back to per-check rows ("The release test", rule 9).
    problems: list[str] = field(default_factory=list)
    #: True about the procedure, nobody's mistake.
    remarks: list[str] = field(default_factory=list)
    #: The value of `sitting:`, the old name of `section:`, so the refusal
    #: can name what to change (project-os-dev ADR-0050).
    old_section: str = ""
    #: `(kind, message)` for a form this procedure should leave, found while
    #: reading it. Nobody's mistake yet, so it never fails `--check`.
    parse_warnings: list[tuple[str, str]] = field(default_factory=list)
    #: The same, plus what `audit_procedure` found on its last run.
    warnings: list[tuple[str, str]] = field(default_factory=list)


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


def _results() -> tuple[str, ...]:
    """The seven result values a ledger stores, read from the validator's list."""
    return tuple(_validator().LEDGER_MARKS)


def _result_problem(value) -> str:
    """Why a readiness `result:` is not usable, or "".

    `result:` is the result the tester is offered for a check that cannot be
    done yet (project-os-dev REQ-0033). It has to be one the ledger stores,
    or the page would offer a result nobody can record.
    """
    if "result" not in value or value["result"] in _results():
        return ""
    return ("has `result: %s`; a result is one of %s"
            % (value["result"], ", ".join(_results())))


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
        elif _result_problem(value):
            problems.append("%s: `readiness_for` entry %r %s" % (path, key, _result_problem(value)))
        else:
            out[str(key)] = {"kind": value["kind"], "reason": value["reason"].strip(),
                             "issue": value.get("issue", "").strip(),
                             "platforms": list(value.get("platforms", [])),
                             "result": value.get("result", "")}
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


_START_RE = re.compile(r"^\s*Start:\s*(.*?)\s*$")


def parse_steps(body: str) -> list[Step]:
    """`## Steps` -> its numbered items. `parse_groups` also returns the groups."""
    return parse_groups(body)[0]


def parse_groups(body: str) -> tuple[list[Step], list[Group]]:
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

    **A `### ` heading starts a group** (project-os-dev REQ-0033). The first
    line under it that is not blank may be `Start:` and the group's start
    state. Steps keep counting across groups, because a tag's `.N` and
    `requires:` name positions in the whole procedure.
    """
    steps: list[Step] = []
    groups: list[Group] = []
    current: Step | None = None
    in_fence = False
    #: The group whose heading was the last thing read, until its first
    #: non-blank line, which is the only place a `Start:` line counts.
    opened: Group | None = None
    for line in under_heading(body, "Steps").splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            if current is not None:
                current.body.append(line)
            continue
        heading = None if in_fence else HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 3:
            opened = Group(title=heading.group(2).strip())
            groups.append(opened)
            current = None
            continue
        if opened is not None and not in_fence and line.strip():
            start = _START_RE.match(line)
            waiting, opened = opened, None
            if start:
                waiting.start = start.group(1)
                continue
        found = None if in_fence else _STEP_RE.match(line)
        if found:
            current = Step(number=len(steps) + 1, head=found.group(2).strip(),
                           authored_head=found.group(2).strip(),
                           written=int(found.group(1)), body=[line],
                           group=groups[-1].title if groups else "")
            if groups:
                groups[-1].steps.append(current.number)
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
    return steps, groups


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


#: Every frontmatter map that declares something per step or per setup item.
_DECLARATION_MAPS = ("requires", "step_platforms", "state_for", "capture_for", "use_capture",
                     "timer_for", "readiness_for", "action_for", "setup_for", "setup_platforms")


def _flow_keys(text: str) -> list[str]:
    """The top-level keys of a one-line `{a: 1, b: [2, 3]}` map, quotes respected."""
    body = text.strip()
    if body.startswith("{"):
        body = body[1:]
    if body.endswith("}"):
        body = body[:-1]
    keys, depth, quote, start = [], 0, "", 0
    for i, ch in enumerate(body + ","):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            part = body[start:i]
            start = i + 1
            if ":" in part:
                keys.append(part.split(":", 1)[0].strip().strip("'\""))
    return keys


def duplicate_declarations(front: str, path: str) -> list[str]:
    """A step or setup id declared twice inside one declaration map.

    **Two instructions for one thing is the contradiction the validator can
    see** (project-os-dev TASK-0125). The frontmatter parser keeps the last
    value, so `state_for` with step 2 declared as both "Signed in as FREE"
    and "Signed in as PRO" printed PRO and dropped FREE without a word.
    Whether two different steps' prose disagrees ("any tier" against "PRO")
    is the author's to resolve (ADR-0046: nothing is inferred from prose).
    """
    problems: list[str] = []
    lines = front.splitlines()
    for i, line in enumerate(lines):
        found = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not found or found.group(1) not in _DECLARATION_MAPS:
            continue
        label, rest = found.group(1), found.group(2).strip()
        keys: list[str] = []
        if rest.startswith("{"):
            text, j = rest, i + 1
            while text.count("{") > text.count("}") and j < len(lines):
                text += " " + lines[j].strip()
                j += 1
            keys = _flow_keys(text)
        elif not rest or rest.startswith("#"):
            child = None
            for following in lines[i + 1:]:
                if not following.strip() or following.lstrip().startswith("#"):
                    continue
                indent = len(following) - len(following.lstrip(" "))
                if indent == 0:
                    break
                child = indent if child is None else child
                if indent != child or following.strip().startswith("- "):
                    continue
                key = re.match(r"\s*([^:#\s][^:]*?)\s*:", following)
                if key:
                    keys.append(key.group(1).strip("'\""))
        for key in sorted({k for k in keys if keys.count(k) > 1}):
            problems.append("%s: `%s` declares %s twice; the parser would keep one and "
                            "drop the other instruction without a word" % (path, label, key))
    return problems


def unknown_platforms(procedure: Procedure, known: list[str],
                      setup_platform_names: set[str]) -> list[str]:
    """Platform names this repo keeps no ledger for (rule 9, "Platform and state").

    `andriod` in `step_platforms` took the step off both real platforms, and
    nothing said so until one of its parts happened to be owed.
    """
    if not known:
        return []
    names: list[tuple[str, str]] = []
    for step in procedure.steps:
        names += [("step_platforms", name) for name in step.platforms]
        names += [("readiness_for", name) for name in step.readiness_declared.get("platforms", [])]
        names += [("action_for", name) for name in step.action_for]
    names += [("setup_platforms", name) for name in setup_platform_names]
    return ["%s: `%s` names platform %s, and this repo keeps ledgers only for %s"
            % (procedure.path, label, name, ", ".join(known))
            for label, name in sorted(set(names)) if name not in known]


def load_procedures(docs_root: Path, repo_root: Path | None = None) -> list[Procedure]:
    """Every procedure under `docs/tests/acceptance/release-test/`, parsed.

    The short what-changed lines live in the same folder and are not
    procedures (`load_short_lines`).
    """
    root = docs_root / PROCEDURES_REL
    if not root.is_dir():
        return []
    vd = _validator()
    known_platforms = platforms(docs_root)
    out: list[Procedure] = []
    for path in sorted(root.glob("*.md")):
        if path.name.startswith(WHAT_CHANGED_PREFIX):
            continue
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
        setup = under_heading(body, "Setup")
        steps, groups = parse_groups(body)
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
        #: Two start states for one step is the contradiction ADR-0046 says the
        #: validator can see: which one the tester reads would be an accident.
        for group in groups:
            if group.start and group.steps and str(group.steps[0]) in step_states:
                state_problems.append(
                    '%s: step %d has a start state twice, from the `Start:` line of "%s" '
                    "and from `state_for`; keep the `Start:` line"
                    % (shown_path, group.steps[0], group.title))
        warnings: list[tuple[str, str]] = []
        if step_states:
            warnings.append(("state_for", "%s: `state_for:` is replaced by a `Start:` line under "
                             "each group's `### ` heading in `## Steps` (project-os-dev "
                             "REQ-0033); it is still read" % shown_path))
        for label, mapping, target in (("capture_for", capture_prompts, capture_problems),
                                       ("timer_for", timers, timer_problems),
                                       ("readiness_for", readiness, readiness_problems),
                                       ("action_for", actions, action_problems)):
            for number in sorted(set(mapping) - {str(step.number) for step in steps}):
                target.append("%s: `%s` names absent step %s" % (shown_path, label, number))
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), 0)
        front = "\n".join(lines[1:end]) if lines and lines[0].strip() == "---" and end else ""
        procedure = Procedure(
            path=shown_path, section=_text(fm.get("section")),
            old_section=_text(fm.get("sitting")), setup=setup,
            steps=steps, setup_items=setup_items, requires=requires,
            groups=groups, parse_warnings=warnings,
            parse_problems=(require_problems + step_problems + state_problems
                            + capture_problems + use_problems + timer_problems
                            + setup_problems + readiness_problems + action_problems
                            + duplicate_declarations(front, shown_path)))
        procedure.parse_problems += unknown_platforms(
            procedure, known_platforms, {name for item in setup_items for name in item.platforms})
        out.append(procedure)
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
    that is what markdown renders and what a tester counts; counting distinct
    digits collapsed it to one owed part, so the release owed less than rule 9
    says it does. Found by independent review, 2026-09-14.

    A check whose procedure is an unheaded paragraph has none, and is one
    owed part cited by its bare id ("The release test", rule 9). Most of the corpus
    that needs this looks like that today (project-os-dev ISS-0064).
    """
    return list(range(1, len(written_steps(check)) + 1))


def parts_of(check: Check) -> list[tuple[str, str]]:
    """The owed parts a check contributes: one per numbered step, else one."""
    return [(check.id, str(n)) for n in numbered_steps(check)] or [(check.id, "")]


#: `[android] ` or `[ios] ` at the start of an Expect line, after its list
#: marker: the line holds on that platform only (project-os-dev REQ-0034,
#: ADR-0050 D2). Lower case, like a ledger's platform name, so a bracketed
#: word in ordinary prose, such as `[Save]`, is not read as a platform.
_PLATFORM_MARK_RE = re.compile(r"^\[([a-z][a-z0-9_-]*)\]\s+")


def _split_mark(display: str) -> tuple[str, str]:
    """(platform or "", the line without its platform mark)."""
    found = _PLATFORM_MARK_RE.match(display)
    if not found:
        return "", display
    return found.group(1), display[found.end():]


def expect_marks(expect: str) -> list[tuple[str, str]]:
    """Every `(platform, line)` an Expect section marks for one platform."""
    out = []
    for line in (expect or "").splitlines():
        platform, _rest = _split_mark(_MARKER_RE.sub("", line).strip())
        if platform:
            out.append((platform, line))
    return out


def expect_entries(check: Check) -> list[tuple[str, str, str]]:
    """Each Expect line as `(platform or "", normalised text, text as written)`.

    The platform mark is not part of what the line asserts, so it is removed
    from both texts; the list marker goes from the written text and nothing
    else does (`expect_display`).
    """
    out = []
    for line in (check.expect or "").splitlines():
        platform, display = _split_mark(_MARKER_RE.sub("", line).strip())
        text = normalise(display)
        if text:
            out.append((platform, text, display.strip()))
    return out


def _applies(mark: str, platform: str) -> bool:
    """An unmarked line holds everywhere; a marked one on its platform only.

    With no platform named, every line applies: that is a reader asking what
    the note says, not what one platform's page prints.
    """
    return not mark or not platform or mark == platform


def expect_lines(check: Check, platform: str = "") -> set[str]:
    """The check's `## Expect` lines on ``platform``, one normalised line per assertion."""
    return {text for mark, text, _shown in expect_entries(check) if _applies(mark, platform)}


def claims(section: Section, check: Check, surfaces: dict[str, str]) -> bool:
    """Whether a section claims a check ("The release test", rule 3)."""
    return (check.id in section.checks
            or check.area in section.surfaces
            or surfaces.get(check.area, "") in section.surfaces)


_PLACEMENTS: dict = {}


def placement(checks: list[Check], sections: list[Section],
              surfaces: dict[str, str]) -> dict[str, str]:
    """`check id -> section name`; the first section to claim a check keeps it.

    Memoised for the run (project-os-dev ISS-0093): `--check` asked the same
    question 475 times for one repo, 1.1 million `claims` calls. The key is the
    check ids with the identity of the section and surface objects, which a
    run never mutates; a copy returned per call keeps callers apart.
    """
    key = (tuple(c.id for c in checks), id(sections), id(surfaces))
    if key in _PLACEMENTS:
        return dict(_PLACEMENTS[key][0])
    out: dict[str, str] = {}
    for section in sections:
        for check in checks:
            if check.id not in out and claims(section, check, surfaces):
                out[check.id] = section.name
    #: The inputs are kept alive with the answer, so their ids cannot be
    #: reused by other objects while the entry exists.
    _PLACEMENTS[key] = (dict(out), sections, surfaces)
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


#: What a consumer runs once to move its own files to the release test names
#: (project-os-dev ADR-0050). Printed wherever an old name is refused.
MIGRATE_HINT = "Run `python3 tools/scripts/migrate-release-test-names.py --apply` (project-os-dev ADR-0050)."


def entry_result(entry: dict) -> str:
    """A ledger entry's result: `result`, or `mark` in an entry written before it.

    New entries write `result` (project-os-dev ADR-0050). Sealed ledgers are
    records and are never rewritten, so every reader accepts `mark` for good.
    """
    value = entry.get("result")
    if value in (None, ""):
        value = entry.get("mark")
    return _text(value)


class ReleaseTestError(Exception):
    """Something a person has to fix before a sheet can be produced."""


class NothingToTest(ReleaseTestError):
    """This repo has no release test to compute, which is not a fault.

    **Its own class, because `--check` runs on every commit and must be silent
    here without going quiet about a broken ledger.** The first version caught
    `ReleaseTestError` and swallowed all of it, so a ledger whose filename named no
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
    result: str = ""
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
        return self.result in CLEARING


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
    skipped: a ledger that silently drops out of its own platform while it
    still looks read is the worse failure.
    """
    root = docs_root / LEDGERS_REL
    if not root.is_dir():
        return []
    ledgers = []
    for path in sorted(root.glob("*.json")):
        found = _LEDGER_NAME_RE.match(path.stem)
        if not found:
            raise ReleaseTestError(
                "%s/%s: the filename does not name a platform. It must be "
                "`WORKING-<platform>.json` or `REL-####-<platform>.json`, or "
                "its verdicts are invisible to every query."
                % (LEDGERS_REL, path.name))
        if found.group("platform") != platform:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReleaseTestError("%s/%s: not readable as JSON -- %s"
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
                raise ReleaseTestError(
                    "%s: %s has no usable date (%r) -- a ledger is resolved in "
                    "date order, so a date-shaped string reorders the answer"
                    % (LEDGERS_REL, _text(entry.get("check")), when))
            out.append(Event(
                check=_text(entry.get("check")), date=when,
                result=entry_result(entry), reason=_text(entry.get("reason")),
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

    Two layers, because an expiring result must not destroy the verdict
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
        if event.result in PERSISTS:
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

    A release test is asked for by name, and a name is easy to mistype. Without this,
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


# ------------------------------------------------------------ the section order

@dataclass
class Section:
    name: str
    surfaces: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    state: str = ""
    bench: list[str] = field(default_factory=list)

    @property
    def claims_nothing(self) -> bool:
        return not self.surfaces and not self.checks


RELEASE_TEST_REL = "tests/acceptance/RELEASE-TEST.md"
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
    nothing warned, and a tester could not tell a split entry from two
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


def parse_section_order(text: str) -> tuple[str, list[Section], list[str]]:
    """`RELEASE-TEST.md` -> (gallery command, sections in file order, warnings).

    One `### ` heading per section, one fenced `yaml` block under it. That is
    the whole syntax and the generator parses no other, so a second way to
    write a section is a defect rather than a dialect (ADR-0029 acceptance 1).
    """
    gallery = ""
    sections: list[Section] = []
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

    current: Section | None = None
    in_block = False
    for line in lines[start:]:
        heading = HEADING_RE.match(line)
        if heading and not in_block:
            if len(heading.group(1)) == 3:
                current = Section(name=heading.group(2).strip())
                sections.append(current)
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
                #: lines -- but dropping them silently was worse: a section
                #: with a block-style `surfaces:` and an inline `checks:` still
                #: claims something, so it drew no "claims nothing" warning and
                #: its surfaces simply vanished. Found by independent review,
                #: 2026-09-13.
                warnings.append(
                    'the section "%s" writes `%s:` as a block list; the section '
                    "order is read as inline lists only, so write it "
                    '`%s: ["one", "two"]` or it is not read at all'
                    % (current.name, found.group(1), found.group(1)))
                continue
            setattr(current, found.group(1), _inline_list(value))
            continue
        found = _YAML_SCALAR_RE.match(line)
        if found and found.group(1) == "state":
            current.state = _strip_comment(found.group(2)).strip().strip("\"'")

    for section in sections:
        if section.claims_nothing:
            warnings.append(
                'the section "%s" names neither `surfaces` nor `checks`, so it '
                "can claim nothing and no row will appear under it"
                % section.name)
    return gallery, sections, warnings


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
    #: The date of the candidate picture's last commit, set only when that is
    #: before the change that altered its screen: the picture cannot show the
    #: change (project-os-dev REQ-0035).
    stale: str = ""
    #: The change the picture is older than.
    stale_against: str = ""

    @property
    def new(self) -> bool:
        """Captured now and not at the last release: a screen that is new."""
        return bool(self.after) and not self.before


@dataclass
class Screen:
    """One line of what changed: a screen, what changed on it, its pictures."""

    id: str
    title: str
    parent: str = ""
    #: `(change id, change title, the sentence that change wrote)`.
    sentences: list[tuple[str, str, str]] = field(default_factory=list)
    captures: list[Capture] = field(default_factory=list)
    #: Named by a change note and matched by no `SUR-*` note.
    unresolved: bool = False
    #: Per entry of `sentences`: True when the sentence is the short line from
    #: `what-changed-<platform>.md` rather than the Impact sentence.
    short: list[bool] = field(default_factory=list)


@dataclass
class Placed:
    section: Section
    rows: list[Check]
    #: The section's written procedure, when it has one and it holds up.
    procedure: Procedure | None = None
    #: Only setup that the retained actions use on this platform.
    setup: str = ""
    #: The steps of that procedure this release owes something from.
    steps: list[Step] = field(default_factory=list)
    #: How many steps were left out because everything they cite has passed.
    omitted: int = 0
    #: Owed checks the procedure covers, for the tick list under it.
    owed_checks: list[Check] = field(default_factory=list)
    #: The changed screens this section tests, on this platform
    #: (project-os-dev REQ-0035).
    what_changed: list[Screen] = field(default_factory=list)

    @property
    def tested_from_procedure(self) -> bool:
        return self.procedure is not None and not self.procedure.problems


@dataclass
class ReleaseTest:
    release: str
    platform: str
    generated: str
    what_changed: list[Screen]
    sections: list[Placed]
    unplaced: list[Check]
    gallery: str = ""
    #: Something to fix in `RELEASE-TEST.md`.
    warnings: list[str] = field(default_factory=list)
    #: Something true about this sheet that is nobody's mistake.
    notices: list[str] = field(default_factory=list)
    authored_order: bool = True
    #: The release note and tag the what-changed list compared against, and why it could
    #: not. Exactly one of `what_changed_tag` and `what_changed_problem` is set.
    what_changed_release: str = ""
    what_changed_tag: str = ""
    what_changed_problem: str = ""
    #: The changed screens no printed section tests. `what_changed` is every
    #: changed screen on this platform; each section carries its own share.
    what_changed_overview: list[Screen] = field(default_factory=list)
    #: Why the short what-changed lines were not used, "" when they were.
    short_lines_problem: str = ""
    #: Change notes in range that declare no `platforms:`, listed on every
    #: platform. Empty for a project with one platform.
    undeclared: list[str] = field(default_factory=list)

    @property
    def rows(self) -> int:
        return sum(len(p.rows) for p in self.sections) + len(self.unplaced)


def order_rows(rows: list[Check], warnings: list[str], where: str) -> list[Check]:
    """`after:` first, then id ("The release test", rule 4).

    A prerequisite in another section cannot be ordered here, so only edges
    inside this section count. A cycle is reported and the rows fall back to id
    order: nothing gates on `after:`, so failing the whole sheet over it would
    cost the tester their afternoon to save an ordering.
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
    (a feature or regression test) with no surviving clearing verdict.
    """
    verdicts = resolve(events)
    out = [c for c in checks.values()
           if c.kind != "automated"
           and ((v := verdicts.get(c.id)) is None or not v.clears)]
    out.sort(key=lambda c: c.id)
    return out


def build_what_changed(changes: list[Change], surfaces: dict[str, Surface],
                       captures=None, platform: str = "", keep=None,
                       short: dict[tuple[str, str], str] | None = None,
                       stale=None) -> list[Screen]:
    """The screens a release changed, from the change notes that named them.

    Order is the top-level screens by title, each followed by its children.
    That is the order a person navigates in, and it is why a dialog never
    appears above the screen it opens from ("The release test", rule 2).

    ``platform`` keeps what each change did on that platform (`Change.on`).
    ``keep`` is a predicate on a screen id, for one section's share. ``short``
    maps `(change id, screen id)` to the short line written at release
    preparation, used in place of the Impact sentence. ``stale`` is
    `(picture path, [change]) -> (date, change id)`, for a candidate picture
    older than the change it should show.
    """
    found: dict[str, Screen] = {}
    altered: dict[str, list[Change]] = {}
    #: **One short line per change and screen.** A change note with two Impact
    #: lines for one screen has one short line for both, since the short lines
    #: are keyed by (change, screen), and it printed twice. Two Impact lines
    #: with no short line are two sentences, and both print. Found by
    #: independent review, 2026-09-27.
    shortened: set[tuple[str, str]] = set()
    for change in changes:
        for surface_id, sentence in change.on(platform):
            if keep is not None and not keep(surface_id):
                continue
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
            line = (short or {}).get((change.id, surface_id), "")
            altered.setdefault(surface_id, []).append(change)
            if line:
                if (change.id, surface_id) in shortened:
                    continue
                shortened.add((change.id, surface_id))
            screen.sentences.append((change.id, change.title, line or sentence))
            screen.short.append(bool(line))
    # A changed dialog still needs its containing screen in the list, even
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
                    capture = Capture(key=key, state=state, before=before, after=after)
                    if stale is not None and after and altered.get(screen.id):
                        capture.stale, capture.stale_against = stale(after, altered[screen.id])
                    screen.captures.append(capture)
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


def screen_homes(sections: list[Section], surface_notes: dict[str, Surface],
                 surfaces: dict[str, str], checks: dict[str, Check]) -> dict[str, str]:
    """`screen id -> section name`: the section whose what-changed list shows it.

    A section tests the screens its `surfaces:` names and the screens of the
    checks its `checks:` names. A section that claims its checks by id alone,
    such as a bench section, would otherwise show no change at all. The first
    section in order that tests a screen keeps it. A child screen no section
    names goes with its top-level screen (project-os-dev REQ-0035).
    """
    def as_id(name: str) -> str:
        if name in surface_notes:
            return name
        return surfaces.get(name, "")

    tested: list[tuple[str, set[str]]] = []
    for section in sections:
        ids = {as_id(name) for name in section.surfaces}
        ids |= {as_id(checks[c].area) for c in section.checks if c in checks}
        tested.append((section.name, ids - {""}))
    homes: dict[str, str] = {}
    for surface_id in surface_notes:
        for candidate in (surface_id, top_screen(surface_id, surface_notes)):
            home = next((name for name, ids in tested if candidate in ids), "")
            if home:
                homes[surface_id] = home
                break
    return homes


def stale_finder(repo_root: Path | None):
    """`(picture, changes) -> (date, change id)` for a picture older than a change.

    A picture is older than a change when the commit that last touched it
    comes before the commit that added the change note. That is a question of
    commit order, not of clock time, so two commits in the same second still
    compare. A picture with uncommitted edits is new, and a change note not
    yet committed is newer than every committed picture. Without git nothing
    is flagged, because nothing can be dated.
    """
    if repo_root is None or _git(repo_root, "rev-parse", "--git-dir")[0] != 0:
        return None
    seen: dict[tuple, tuple[int, str]] = {}

    def run(*args: str) -> tuple[int, str]:
        if args not in seen:
            seen[args] = _git(repo_root, *args)
        return seen[args]

    def last_commit(path: str, *how: str) -> str:
        code, out = run("log", "-1", "--format=%H", *how, "--", path)
        return out.splitlines()[0] if code == 0 and out.strip() else ""

    def stale(picture: str, changes: list[Change]) -> tuple[str, str]:
        taken = last_commit(picture)
        code, dirty = run("status", "--porcelain", "--", picture)
        if not taken or (code == 0 and dirty.strip()):
            return "", ""
        for change in changes:
            added = last_commit(change.path, "--diff-filter=A")
            later = (not added
                     or (added != taken
                         and run("merge-base", "--is-ancestor", taken, added)[0] == 0))
            if later:
                _code, when = run("log", "-1", "--format=%cs", taken)
                return when, change.id
        return "", ""

    return stale


def build_release_test(checks: dict[str, Check], events: list[Event], sections: list[Section],
               *, release: str, platform: str, surfaces=None,
               surface_notes=None, changes=None, captures=None,
               procedures=None, known=None, retired=None,
               gallery: str = "", generated: str = "",
               warnings=None, notices=None, authored_order: bool = True,
               what_changed_release: str = "", what_changed_tag: str = "",
               what_changed_problem: str = "", short_lines: ShortLines | None = None,
               stale=None, known_platforms=None,
               quoted_refused: bool | None = None) -> ReleaseTest:
    """The sheet as data: what changed, the sections and the unplaced rows.

    Takes plain values rather than a repo path, so a host with its own note
    index (the cockpit's `release_test_payload`) computes the same release test from the same
    rules without a second implementation of any of them.

    ``short_lines`` is this platform's `what-changed-<platform>.md`, or None
    when there is none. ``known_platforms`` is every platform with a ledger;
    with more than one, a change note declaring no `platforms:` is named.
    """
    surfaces = surfaces or {}
    surface_notes = surface_notes or {}
    warnings = list(warnings or [])
    owed = owed_checks(checks, events)
    owed_ids = {c.id for c in owed}

    changes = list(changes or [])
    short, short_problem = short_lines_for(short_lines, what_changed_tag)
    if what_changed_problem or not any(c.on(platform) for c in changes):
        short_problem = ""
    undeclared = sorted(c.id for c in changes
                        if not c.platforms and c.screens and len(known_platforms or []) > 1)
    what_changed = build_what_changed(changes, surface_notes, captures, platform,
                                      short=short, stale=stale)
    homes = screen_homes(sections, surface_notes, surfaces, checks)

    # --- placement: the first section that claims a check keeps it
    placed: list[Placed] = []
    taken: set[str] = set()
    by_section = {p.section: p for p in (procedures or []) if p.section}
    for section in sections:
        claimed = [c for c in owed if c.id not in taken and claims(section, c, surfaces)]
        taken.update(c.id for c in claimed)
        if not claimed:
            continue
        rows = order_rows(claimed, warnings, section.name)
        entry = Placed(section=section, rows=rows)
        entry.what_changed = build_what_changed(
            changes, surface_notes, captures, platform, short=short, stale=stale,
            keep=lambda s, name=section.name: homes.get(s) == name)
        procedure = by_section.get(section.name)
        if procedure is not None:
            attach_procedure(entry, procedure, checks, owed_ids, sections,
                             surfaces, platform=platform, retired=retired, known=known,
                             quoted_refused=quoted_refused)
        placed.append(entry)
    unplaced = order_rows([c for c in owed if c.id not in taken],
                          warnings, "Unplaced")
    printed = {entry.section.name for entry in placed}
    overview = build_what_changed(
        changes, surface_notes, captures, platform, short=short, stale=stale,
        keep=lambda s: homes.get(s) not in printed)
    return ReleaseTest(release=release, platform=platform,
                generated=generated or date.today().isoformat(),
                what_changed=what_changed, sections=placed, unplaced=unplaced,
                gallery=gallery, warnings=warnings, notices=list(notices or []),
                authored_order=authored_order, what_changed_release=what_changed_release,
                what_changed_tag=what_changed_tag, what_changed_problem=what_changed_problem,
                what_changed_overview=overview, short_lines_problem=short_problem,
                undeclared=undeclared)


def short_lines_for(short_lines: ShortLines | None, tag: str
                    ) -> tuple[dict[tuple[str, str], str], str]:
    """(the short lines to use, why none are used) for the last release tag.

    The lines are used only when the file names the tag this sheet compared
    against. Otherwise every screen prints its Impact sentences, and one line
    says why (project-os-dev REQ-0035).
    """
    if short_lines is None:
        return {}, ("no short lines are written for this platform, so each "
                    "screen shows the change notes' Impact sentences; "
                    "`tools/skills/release-test-prep/SKILL.md` writes them")
    if not tag:
        #: **Said, not dropped.** The lines were written and are not used,
        #: and a sheet that shows the Impact sentences with no reason looks
        #: as if the file were ignored. Found by independent review, 2026-09-27.
        return {}, ("the short lines in `%s` are written against %s, and no "
                    "release has been tagged on this platform yet, so each "
                    "screen shows the change notes' Impact sentences instead"
                    % (short_lines.path,
                       "`%s`" % short_lines.tag if short_lines.tag else "no tag"))
    if short_lines.tag != tag:
        return {}, ("the short lines in `%s` were written against %s and the "
                    "last release is `%s`, so each screen shows the change "
                    "notes' Impact sentences instead"
                    % (short_lines.path,
                       "`%s`" % short_lines.tag if short_lines.tag else "no tag",
                       tag))
    return dict(short_lines.lines), ""


def attach_procedure(entry: Placed, procedure: Procedure, checks: dict[str, Check],
                     owed_ids: set[str], sections: list[Section],
                     surfaces: dict[str, str], platform: str = "",
                     retired: set[str] | None = None,
                     known: dict[str, Check] | None = None,
                     quoted_refused: bool | None = None) -> None:
    """Hold a procedure to what this section owes, then keep what prints.

    The judgement is `audit_procedure`; this decides what a sheet does with
    the answer. A procedure with a problem still reaches `entry.procedure`,
    because the renderer prints the problem above the per-check rows it falls
    back to -- a stale procedure that vanished silently would leave the tester
    reading rows and wondering where the script went.
    """
    entry.procedure = procedure
    for step in procedure.steps:
        step.head = step.authored_head or step.head
        step.readiness = step.readiness_declared
    procedure.problems, procedure.remarks = audit_procedure(
        procedure, entry.section, entry.rows, checks, owed_ids, sections, surfaces,
        platform=platform, retired=retired, known=known, quoted_refused=quoted_refused)
    if procedure.problems:
        return
    applicable = [step for step in procedure.steps
                  if not step.platforms or not platform or platform in step.platforms]
    current_state = ""
    for step in procedure.steps:
        step.required_state = ""
    #: A group's `Start:` line takes effect at the first of its steps this
    #: platform keeps, so a group whose first step runs on the other platform
    #: still states its start; `state_for` on a step then replaces it, as it
    #: replaced an earlier `state_for`.
    group_of = {number: i for i, group in enumerate(procedure.groups) for number in group.steps}
    in_group = None
    for step in applicable:
        here = group_of.get(step.number)
        if here is not None and here != in_group:
            in_group = here
            if procedure.groups[here].start:
                current_state = procedure.groups[here].start
        if step.state_declared:
            current_state = step.state_declared
        step.required_state = current_state
    for step in procedure.steps:
        action = step.action_for.get(platform)
        if action:
            #: A step no longer has to name its screen (project-os-dev
            #: REQ-0033), so without a bold heading to keep, the variant
            #: replaces the whole action line.
            prefix = _ACTION_HEAD_RE.match(step.authored_head)
            step.head = "%s %s" % (prefix.group(1), action) if prefix else action
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
        #: A declaration that can never apply contradicts another one
        #: (TASK-0125): the item is limited to platforms none of its steps run on.
        targets = [steps[n] for n in item.steps if n in steps] if item.steps else list(steps.values())
        if item.platforms and targets and not any(
                not step.platforms or step.platforms & item.platforms for step in targets):
            problems.append("%s: setup item %s is limited to %s, but none of its steps runs there"
                            % (procedure.path, item.id, ", ".join(sorted(item.platforms))))
    for step in procedure.steps:
        if not step.platforms:
            continue
        limited = set(step.readiness_declared.get("platforms", []))
        if limited and not limited & step.platforms:
            problems.append("%s: step %d's `readiness_for` is limited to %s, but the step runs only on %s"
                            % (procedure.path, step.number, ", ".join(sorted(limited)),
                               ", ".join(sorted(step.platforms))))
        for name in sorted(set(step.action_for) - step.platforms):
            problems.append("%s: step %d has an `action_for` variant for %s, but the step runs only on %s"
                            % (procedure.path, step.number, name, ", ".join(sorted(step.platforms))))
    for step in procedure.steps:
        if step.action_for and parse_tags(step.body[0]):
            problems.append("%s: step %d carries test tags on its action line, which `action_for` "
                            "would replace; put the tags on a line of their own"
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


def expect_text(check: Check, platform: str = "") -> list[str]:
    """The check's `## Expect` lines on ``platform``, normalised, in the note's order.

    A line marked for another platform is left out (project-os-dev REQ-0034).

    **Two identical lines are both kept.** A tag `.N` pairs with line N by
    position (`expect_for`), so dropping the second copy moved every later
    line up by one, and a tag named the line after the one it meant. A reader
    that lists the lines without pairing them removes the copy itself
    (`_unique`). Found by independent review, 2026-09-27.
    """
    return [text for mark, text, _shown in expect_entries(check) if _applies(mark, platform)]


def _unique(lines: list[str]) -> list[str]:
    """``lines`` with each repeat after the first removed, in order."""
    out: list[str] = []
    for line in lines:
        if line not in out:
            out.append(line)
    return out


def expect_display(check: Check) -> dict[str, str]:
    """Each Expect line as the note writes it, keyed by its normalised form.

    The sheet prints this: the list marker goes and nothing else changes, so
    emphasis stays whole and a code span keeps its spacing (`GRADE  N.N%`). `normalise` also strips emphasis at either end, which
    is right for comparing and wrong for printing: `Step 5: **the scorecard
    can still be submitted.**` lost its closing `**` (TASK-0186).
    """
    out: dict[str, str] = {}
    for _mark, key, shown in expect_entries(check):
        if key not in out:
            out[key] = shown
    return out


def expect_block(check: Check, platform: str = "") -> str:
    """The `## Expect` section as a per-check row prints it on ``platform``.

    Verbatim, except that a line marked for another platform is left out and
    a line marked for this one loses its mark (project-os-dev REQ-0034).
    """
    out = []
    for line in (check.expect or "").splitlines():
        found = _MARKER_RE.match(line)
        head, rest = (line[:found.end()], line[found.end():]) if found else ("", line)
        mark, text = _split_mark(rest.strip())
        if not mark:
            out.append(line)
        elif _applies(mark, platform):
            out.append(head + text)
    return "\n".join(out).strip("\n")


def expect_for(check: Check, number: str, platform: str = "") -> list[str]:
    """The Expect lines a tag names: line N for step N when the check pairs them.

    A check whose `## Expect` has exactly one line per numbered step pairs
    them by position, and a tag `.N` names line N. Procedures already read them so:
    on your-trainer, 204 of 211 quotes citing such a check quote line N for
    `.N` (2026-09-26). Any other check has no pairing, so a tag names all of
    its Expect lines. For a tag `.N` that is a problem `--check` reports
    (`_audit_tag`), because the tester would read lines meant for other steps.

    **Counted per platform** (project-os-dev REQ-0034): the lines are the ones
    that apply on ``platform``, so a check writing `[android]` and `[ios]`
    versions of line 2 still pairs step 2 with line 2 on each platform.
    """
    lines = expect_text(check, platform)
    if number and pairs_steps(check, platform) and 1 <= int(number) <= len(lines):
        return [lines[int(number) - 1]]
    return _unique(lines)


def pairs_steps(check: Check, platform: str = "") -> bool:
    """Whether the check's Expect lines on ``platform`` number one per numbered step."""
    lines = expect_text(check, platform)
    return bool(lines) and len(lines) == len(numbered_steps(check))


def expand_tag_only(procedure: Procedure, checks: dict[str, Check], platform: str = "") -> None:
    """Give each tag-only expectation line the check's current words.

    project-os-dev ISS-0088, ADR-0049. A line may be only its tags,
    `` - `TST-0480` ``, instead of quoting the check. It is replaced here, for
    the sheet and for the cockpit's payload alike, by one line per line of the
    check's own `## Expect`, each carrying that check's tags. So the tester
    still reads the check's own words, which is what lets a tick stand as a
    verdict on the check (ADR-0045), and editing the check no longer breaks
    the procedure: it only changes what the next sheet prints.

    A tag names the Expect lines `expect_for` gives on ``platform``: line N
    of a check that pairs its steps with its Expect lines, else all of them.
    A line marked for another platform never prints (project-os-dev
    REQ-0034). A check with no Expect text on this platform, or a tag naming
    no check, leaves the line as written; the audit reports the second.
    """
    for step in procedure.steps:
        replaced = False
        body: list[str] = []
        expectations: list[Expectation] = []
        pending = {id(e): e for e in step.expectations}
        by_raw: dict[str, list[Expectation]] = {}
        for e in step.expectations:
            by_raw.setdefault(e.raw, []).append(e)
        for i, line in enumerate(step.body):
            queue = by_raw.get(line) or []
            found = queue.pop(0) if queue else None
            if found is None:
                body.append(line)
                continue
            pending.pop(id(found), None)
            owners = []
            for check_id, _number in found.tags:
                if check_id not in owners:
                    owners.append(check_id)
            texts = {}
            for cid in owners:
                if cid in checks:
                    lines: list[str] = []
                    for c, n in found.tags:
                        if c == cid:
                            lines += [x for x in expect_for(checks[cid], n, platform) if x not in lines]
                    texts[cid] = lines
            if i == 0 or found.quote or not texts or not all(texts.get(cid) for cid in owners):
                body.append(line)
                expectations.append(found)
                continue
            prefix = line[:line.index("`")] if "`" in line else line
            for cid in owners:
                tags = [tag for tag in found.tags if tag[0] == cid]
                tag_text = " ".join("`%s%s`" % (c, "." + n if n else "") for c, n in tags)
                shown = expect_display(checks[cid])
                for text in texts[cid]:
                    raw = "%s%s %s" % (prefix, shown.get(text, text), tag_text)
                    body.append(raw)
                    expectations.append(Expectation(quote=text, raw=raw, tags=list(tags),
                                                    expanded=True))
            replaced = True
        if replaced:
            step.body = body
            step.expectations = expectations + list(pending.values())


#: Whether a quoted expectation line is refused, unless the section order
#: file says `quoted_lines: warning`. **A warning until the consumers had
#: moved to tags alone, then an error** (project-os-dev REQ-0034, ADR-0050 D2).
#: your-trainer's procedures held 724 quoted lines on 2026-09-27 and none by
#: the end of that day; `release-test-tags.py --all --apply` rewrites them.
#: A refused procedure's section falls back to per-check rows.
QUOTED_EXPECTATIONS_REFUSED = True

#: The values `quoted_lines:` may take in the section order file.
QUOTED_LINE_MODES = {"refused": True, "warning": False}


def quoted_expectations(procedure: Procedure) -> list[str]:
    """Each procedure line that states an expectation in its own words.

    ADR-0050 D2: a check's expected result is written once, in the check's
    `## Expect`, and a procedure line is its tags alone. A quote is a second
    copy that drifts, and an action line carrying tags makes the action stand
    in for the expected result.
    """
    out = []
    for step in procedure.steps:
        for expectation in step.expectations:
            if expectation.expanded or not expectation.quote:
                continue
            if step.body and expectation.raw == step.body[0]:
                out.append("step %d of %s carries tags on its action line; put them on a "
                           "line of their own under it, where the page prints the check's "
                           "own Expect line (project-os-dev ADR-0050 D2)"
                           % (step.number, procedure.path))
            else:
                out.append("step %d of %s quotes an expectation instead of giving its tags "
                           "alone: %r; the page prints the check's own Expect line for a tag "
                           "(project-os-dev ADR-0050 D2), and `python3 "
                           "tools/scripts/release-test-tags.py --all --apply` rewrites it"
                           % (step.number, procedure.path, expectation.quote))
    return out


def audit_procedure(procedure: Procedure, section: Section, owed: list[Check],
                    checks: dict[str, Check], owed_ids: set[str],
                    sections: list[Section], surfaces: dict[str, str],
                    platform: str = "",
                    retired: set[str] | None = None,
                    known: dict[str, Check] | None = None,
                    quoted_refused: bool | None = None) -> tuple[list[str], list[str]]:
    """(problems, remarks) for one procedure ("The release test", rule 9).

    A problem is a disagreement between the procedure and the release's owed
    set, or between a quoted expectation and the check it quotes. A remark is
    something true that is not a disagreement, such as a live check the
    procedure has not reached yet. A step that names no screen is no longer
    one: the action alone is enough (project-os-dev REQ-0033). Coverage of the owed
    parts is the requirement; coverage of everything live is the aim.

    A warning is a form the procedure should leave, such as a quoted
    expectation, and goes to ``procedure.warnings`` so the return shape stays
    the one the cockpit already calls.
    """
    problems: list[str] = validate_preparation(procedure, platform)
    remarks: list[str] = []
    retired = retired or set()
    procedure.warnings = list(procedure.parse_warnings)
    if quoted_refused is None:
        quoted_refused = QUOTED_EXPECTATIONS_REFUSED
    for message in quoted_expectations(procedure):
        if quoted_refused:
            problems.append(message)
        else:
            procedure.warnings.append(("quoted", message))
    #: **Every check a tag may legally name, not only the owed ones.** A
    #: procedure covers its whole section and prints the owed part of itself,
    #: so it cites checks that have already passed. A host that passed only
    #: the owed set -- which the cockpit's `release_test_payload` did -- reported
    #: every such tag as naming no check at all, and the two readers of one
    #: corpus disagreed about one procedure. That is exactly what rule 7 says
    #: bundling this module prevents. Found by independent review, 2026-09-14.
    known = known or checks
    expand_tag_only(procedure, known, platform)
    where = placement(sorted(known.values(), key=lambda c: c.id), sections, surfaces)
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
            % (procedure.path, ", ".join(str(s.written) for s in applicable),
               len(applicable)))
    for step in applicable:
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
                                           known, retired, where, section.name,
                                           platform))
    for part in sorted(want):
        if part not in cited:
            check = want[part]
            problems.append(
                "%s owes %s and no step cites it; the tester would not test it "
                "(%s)" % (section.name, _part_name(part), procedure.path))
    for part, steps in sorted(cited.items()):
        if part in want and len(steps) > 1:
            problems.append(
                "%s is cited by steps %s; one owed part is tested once, so the "
                "verdict has one place to come from (%s)"
                % (_part_name(part), ", ".join(str(n) for n in sorted(steps)),
                   procedure.path))
    live = [c for c in known.values()
            if c.kind != "automated" and where.get(c.id) == section.name]
    covered = {tag[0] for tag in cited}
    missing = sorted(c.id for c in live if c.id not in covered)
    if missing:
        remarks.append(
            "covers %d of %d live checks in \"%s\"; not yet reached: %s"
            % (len(live) - len(missing), len(live), section.name,
               ", ".join(missing)))
    return problems, remarks


def _part_name(part: tuple[str, str]) -> str:
    return "%s step %s" % part if part[1] else "%s (one part, its steps are not numbered)" % part[0]


def _audit_tag(procedure: Procedure, step: Step, expectation: Expectation,
               tag: tuple[str, str], checks: dict[str, Check], retired: set[str],
               where: dict[str, str], section_name: str,
               platform: str = "") -> list[str]:
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
    if claimed_by and claimed_by != section_name:
        return ['%s cites %s, which the section "%s" claims; a check is tested '
                "in one section" % (at, check_id, claimed_by)]
    numbers = numbered_steps(check)
    if number and int(number) not in numbers:
        return ["%s cites step %s of %s, which has %s"
                % (at, number, check_id,
                   "no numbered steps" if not numbers
                   else "steps %s" % ", ".join(str(n) for n in numbers))]
    if not number and numbers:
        return ["%s cites %s with no step number, and that check numbers %d "
                "steps; cite the step" % (at, check_id, len(numbers))]
    #: **A tag `.N` needs one Expect line per step.** Otherwise `expect_for`
    #: cannot pair them and prints every line for every tag, so the tester
    #: reads lines meant for other steps and nothing said so. A check with 3
    #: steps and the lines `A`, `B`, `[ios] C` printed A and B for each tag on
    #: Android. A check stating no Expect text is not reported: nothing
    #: prints, and silence is not a mismatch (below). Found by independent
    #: review, 2026-09-27.
    problems = []
    applying = expect_text(check, platform)
    if number and platform and applying and not pairs_steps(check, platform):
        problems.append(
            "%s cites step %s of %s, and on %s that check has %d numbered %s and "
            "%d Expect %s, so a step cannot be paired with its line and every tag "
            "prints all of them; write one Expect line per step, split per "
            "platform with `[%s]` where they differ"
            % (at, number, check_id, platform, len(numbers),
               _plural(len(numbers), "step"), len(applying),
               _plural(len(applying), "line"), platform))
    wanted = expect_lines(check, platform)
    if not wanted:
        #: **Silence is not a mismatch.** The check states no expected result,
        #: so there is nothing to compare the quote against and no evidence
        #: either way. Reporting a mismatch here would be a claim the
        #: validator cannot support, and 57 of 61 rows on the corpus that
        #: needs this look like that today (project-os-dev ISS-0064).
        return problems
    if expectation.quote not in wanted:
        return problems + ["%s quotes %s as %r, and that check's Expect says none of: %s; "
                "`python3 tools/scripts/release-test-tags.py --refresh` re-quotes a line whose "
                "check was reworded, or cite the step by its tag alone (ADR-0049)"
                % (at, check_id, expectation.quote,
                   "; ".join(repr(w) for w in sorted(wanted)))]
    return problems


def unordered_sections(checks: list[Check]) -> list[Section]:
    """The fallback for a project with no RELEASE-TEST.md: one section per area.

    Id order inside, area order outside, and the sheet says its order is
    nobody's. Better than one undifferentiated list, and visibly not a section
    order somebody authored ("The release test", rule 3).
    """
    areas = sorted({c.area for c in checks if c.area})
    out = [Section(name=area, surfaces=[area]) for area in areas]
    return out


# ------------------------------------------------------------ text helpers

def _quote(text: str) -> str:
    return "\n".join("> " + line if line.strip() else ">"
                     for line in text.splitlines())


def _plural(n: int, one: str, many: str = "") -> str:
    return one if n == 1 else (many or one + "s")


# ------------------------------------------------------------- the page model

#: What a readiness problem suggests when it names no `result:`: a missing
#: fixture blocks the check, and an open product question is a question
#: (project-os-dev REQ-0033).
DEFAULT_RESULT = {"preparation": "blocked", "decision": "question"}
#: "Step 3:" at the start of a check's Expect line: the check's own numbering,
#: which the page does not print (project-os-dev REQ-0033). The emphasis
#: around it may be double (`**`, `__`) or single (`*`, `_`); the double
#: form is tried first, so `**` is never read as two single markers.
_STEP_PREFIX_RE = re.compile(
    r"^(\*\*|__|\*|_)?\s*Step\s+\d+[a-z]?\s*[:.—–-]\s*(\*\*|__|\*|_)?\s*", re.I)
_TAG_SPAN_RE = re.compile(r"\s*`TST-\d{2,}(?:\.\d+)?`")


def _tag_name(tag: tuple[str, str]) -> str:
    """`TST-0657.1`, or `TST-0028` for a check whose steps are not numbered."""
    return "%s.%s" % tag if tag[1] else tag[0]


def shown_expected(text: str) -> str:
    """An Expect line as the page prints it: no list marker, no tags, no "Step N:"."""
    text = _TAG_SPAN_RE.sub("", _MARKER_RE.sub("", text.strip())).strip()
    found = _STEP_PREFIX_RE.match(text)
    if found:
        rest = text[found.end():]
        #: "**Step 3: the scorecard shows.**" opens its emphasis before the
        #: number and closes it at the end, so the opening marker goes back.
        #: "Step 1: **the panel.**" opens its emphasis after it. Either way
        #: one marker was taken without its partner, and it goes back.
        #: "*Step 2:* done" wraps the prefix alone, so both markers go.
        #: Two different markers, as in "*Step 2: **the panel** shows.*",
        #: are two openings, and both go back.
        opened, after = found.group(1) or "", found.group(2) or ""
        if opened != after:
            rest = opened + after + rest
        text = rest.strip()
        #: "Step 3: the slot reads ..." was the middle of a sentence; alone,
        #: it starts one.
        first = re.search(r"[A-Za-z]", text)
        if first and not re.match(r"[`\[]", text[:first.start()] or " "):
            text = text[:first.start()] + text[first.start()].upper() + text[first.start() + 1:]
    return text


def _readiness(readiness: dict | None) -> dict | None:
    """A readiness declaration as the page states it, with the result to offer."""
    if not readiness:
        return None
    kind = readiness.get("kind", "")
    return {"kind": kind, "reason": readiness.get("reason", ""),
            "issue": readiness.get("issue", "") or "",
            "result": readiness.get("result") or DEFAULT_RESULT.get(kind, "question")}


def _setup_entries(text: str) -> list[str]:
    """Setup prose as separate things to do: one per list item, else one per paragraph."""
    lines = text.strip().splitlines()
    if not lines:
        return []
    if any(_MARKER_RE.match(line) for line in lines):
        out: list[str] = []
        for line in lines:
            if _MARKER_RE.match(line):
                out.append(_MARKER_RE.sub("", line).strip())
            elif line.strip() and out:
                out[-1] += " " + line.strip()
            elif line.strip():
                out.append(line.strip())
        return out
    return [_WS_RE.sub(" ", para).strip() for para in re.split(r"\n\s*\n", text.strip()) if para.strip()]


def screen_payload(screen: Screen) -> dict:
    shorts = screen.short or [False] * len(screen.sentences)
    return {
        "id": screen.id, "title": screen.title, "parent": screen.parent,
        "unresolved": screen.unresolved,
        "lines": [{"change": change_id, "title": title, "text": sentence, "short": short}
                  for (change_id, title, sentence), short in zip(screen.sentences, shorts)],
        "captures": [{"key": c.key, "state": c.state, "before": c.before, "after": c.after,
                      "new": c.new, "stale": c.stale, "stale_against": c.stale_against}
                     for c in screen.captures],
    }


def _procedure_checks(placed: Placed, platform: str) -> tuple[list[dict], dict[int, int]]:
    """The printed checks of a section tested from its procedure, in groups.

    Numbers run from 1 over the steps this platform keeps. They are the only
    step numbers a tester sees, and every line the page writes about a step
    uses them (project-os-dev ISS-0086).
    """
    procedure = placed.procedure
    printed = {step.number: i for i, step in enumerate(placed.steps, start=1)}
    titles = {i: group.title for i, group in enumerate(procedure.groups)}
    starts = {i: group.start for i, group in enumerate(procedure.groups)}
    group_of = {n: i for i, group in enumerate(procedure.groups) for n in group.steps}
    applicable = [s.number for s in procedure.steps
                  if not s.platforms or not platform or platform in s.platforms]
    groups: list[dict] = []
    previous_state = None
    previous_number = None
    for step in placed.steps:
        here = group_of.get(step.number, -1)
        if not groups or groups[-1]["_index"] != here:
            groups.append({"_index": here, "title": titles.get(here, ""),
                           "start": step.required_state if here >= 0 and starts.get(here) else "",
                           "checks": []})
            if not groups[-1]["start"] and step.required_state != previous_state:
                groups[-1]["start"] = step.required_state
            restate, again = "", False
        else:
            skipped = previous_number is not None and any(
                previous_number < n < step.number for n in applicable)
            restate = step.required_state if step.required_state and (
                skipped or step.required_state != previous_state) else ""
            again = bool(restate) and step.required_state == previous_state
        previous_state, previous_number = step.required_state, step.number
        lines = []
        for expectation in step.expectations:
            text = shown_expected(expectation.raw)
            #: Only the tags this release owes are printed beside the line;
            #: the ones already passed are kept apart (project-os-dev REQ-0033).
            lines.append({"text": text,
                          "tags": [_tag_name(tag) for tag in expectation.tags if tag in expectation.owed],
                          "passed": [_tag_name(tag) for tag in expectation.tags if tag not in expectation.owed],
                          "owed": bool(expectation.owed)})
        action = [step.head.strip()]
        expectation_raws = {e.raw for e in step.expectations}
        for line in step.body[1:]:
            if line.strip() and line not in expectation_raws:
                action.append(line.strip())
        owed_lines = [line for line in lines if line["owed"]]
        tags = []
        for line in owed_lines:
            tags += [tag for tag in line["tags"] if tag not in tags]
        owed_tags = {tag for e in step.expectations for tag in e.owed}
        checks = []
        for check_id, _n in sorted(owed_tags):
            if check_id not in checks:
                checks.append(check_id)
        groups[-1]["checks"].append({
            "number": printed[step.number],
            "action": _WS_RE.sub(" ", " ".join(action)).strip(),
            "expected": [{"text": line["text"], "tags": line["tags"], "passed": line["passed"]}
                         for line in owed_lines],
            #: Lines whose checks have all passed: kept for a host that shows
            #: them, never printed as something to observe.
            "passed_lines": [{"text": line["text"], "tags": line["passed"]}
                             for line in lines if not line["owed"]],
            "tags": tags,
            "checks": checks,
            "passed": sorted({_tag_name(tag) for e in step.expectations
                              for tag in e.tags if tag not in e.owed}),
            "preparation": not owed_tags,
            "start": restate,
            "start_again": again,
            "readiness": _readiness(step.readiness),
            "timer": step.timer_seconds,
            "capture": step.capture_prompt if step.capture_needed else "",
            "compare_with": [printed[n] for n in step.uses_capture if n in printed],
            "path": "",
        })
    for group in groups:
        del group["_index"]
    return groups, printed


def _setup_payload(placed: Placed, printed: dict[int, int], platform: str) -> dict:
    """Setup in three parts: on the bench, before you start, and later.

    An item a procedure ties to particular steps belongs to the first printed
    check that needs it. When that is check 1 it is done before starting;
    otherwise it is done later, and the page names the check.
    """
    before: list[str] = []
    later: list[dict] = []
    procedure = placed.procedure
    if procedure is not None and placed.tested_from_procedure:
        for item in procedure.setup_items:
            if item.platforms and platform and platform not in item.platforms:
                continue
            texts = _setup_entries(item.text)
            if not item.steps:
                before += texts
                continue
            served = sorted(printed[n] for n in item.steps if n in printed)
            if not served:
                continue
            if served[0] == 1:
                before += texts
            else:
                later += [{"check": served[0], "text": text} for text in texts]
    elif placed.section.state:
        before.append(placed.section.state)
    later.sort(key=lambda item: item["check"])
    return {"bench": list(placed.section.bench), "before": before, "later": later}


def _row_checks(rows: list[Check], platform: str) -> list[dict]:
    """One printed check per owed check, for a section with no usable procedure."""
    out = []
    for number, check in enumerate(rows, start=1):
        out.append({
            "number": number, "action": check.title or check.id,
            "expected": [{"text": shown_expected(expect_display(check).get(key, key)), "tags": [],
                          "passed": []} for key in _unique(expect_text(check, platform))],
            "passed_lines": [],
            "tags": [check.id], "checks": [check.id], "passed": [],
            "preparation": False, "start": "",
            "readiness": _readiness(check_readiness(check, platform)),
            "timer": 0, "capture": "", "compare_with": [], "path": check.path,
            #: A check with no procedure is tested from its own note, so its
            #: setup and steps stay on the page (rule 5). The length check
            #: counts them, which is what makes writing a procedure pay.
            "setup": check.setup.strip(),
            "steps": check.steps.strip() or check.lead.strip(),
            "steps_heading": bool(check.steps.strip()),
            "expect_stated": bool(check.expect.strip()),
        })
    return out


def section_payload(number: int | None, placed: Placed | None, rows: list[Check],
                    sheet: ReleaseTest) -> dict:
    """One section of the page: what changed, setup, and its checks in groups."""
    section = placed.section if placed is not None else Section(name="Unplaced")
    from_procedure = placed is not None and placed.tested_from_procedure
    if from_procedure:
        groups, printed = _procedure_checks(placed, sheet.platform)
        omitted = placed.omitted
    else:
        groups, printed, omitted = [{"title": "", "start": "", "checks": _row_checks(rows, sheet.platform)}], {}, 0
    setup = (_setup_payload(placed, printed, sheet.platform) if placed is not None
             else {"bench": [], "before": [], "later": []})
    procedure = placed.procedure if placed is not None else None
    return {
        "number": number, "name": section.name, "unplaced": placed is None,
        #: `count` is the numbered checks a tester works through; `owed` is
        #: the test notes behind them. The approved example's "28 checks"
        #: is the first; its "4 test notes" the second.
        "count": sum(len(group["checks"]) for group in groups),
        "owed": len(rows), "tests": sorted({c.id for c in rows}),
        "bench_line": " · ".join(section.bench), "state": section.state,
        "procedure": procedure.path if procedure is not None else "",
        "problems": list(procedure.problems) if procedure is not None else [],
        "what_changed": [screen_payload(s) for s in (placed.what_changed if placed else [])],
        "nothing_changed": bool(placed is not None and not placed.what_changed
                                and sheet.what_changed_tag),
        "setup": setup,
        "groups": groups,
        "omitted": omitted,
    }


def payload(sheet: ReleaseTest) -> dict:
    """The page as data. The Markdown sheet is rendered from this, and the
    cockpit draws its page from the same dictionary (`--json`), so the two
    cannot disagree. Its shape is TESTING.md, "The release test", rule 10.
    """
    sections = [section_payload(i, placed, placed.rows, sheet)
                for i, placed in enumerate(sheet.sections, start=1)]
    if sheet.unplaced:
        sections.append(section_payload(None, None, sheet.unplaced, sheet))
    return {
        "release": sheet.release, "platform": sheet.platform, "generated": sheet.generated,
        "owed": sheet.rows, "authored_order": sheet.authored_order,
        "notices": list(sheet.notices), "warnings": list(sheet.warnings),
        "what_changed": {
            "release": sheet.what_changed_release, "tag": sheet.what_changed_tag,
            "problem": sheet.what_changed_problem, "gallery": sheet.gallery,
            "short_lines_problem": sheet.short_lines_problem,
            "undeclared": list(sheet.undeclared),
            "any": bool(sheet.what_changed),
            "screens": [screen_payload(s) for s in sheet.what_changed_overview],
        },
        "sections": sections,
    }


# --------------------------------------------------------------- the renderer

#: How the page writes a platform whose ledger name is not simply capitalised.
PLATFORM_NAMES = {"android": "Android", "ios": "iOS", "macos": "macOS"}


def platform_name(platform: str) -> str:
    """A ledger's platform name as a sentence writes it: `ios` is iOS, `android` Android."""
    return PLATFORM_NAMES.get(platform.lower(), platform[:1].upper() + platform[1:])


def _result_word(result: str) -> str:
    return {"na": "N/A"}.get(result, result.capitalize())


def render_what_changed(page: dict, out: list[str]) -> None:
    """What changed on this platform, before any section ("The release test", rule 2).

    Each section prints the changes to its own screens at its head. This part
    says what the list was compared against, and prints the changed screens
    no section on this sheet tests. No check id appears in any of it: the
    list is places to open and look at, not things to run.
    """
    changed = page["what_changed"]
    platform = platform_name(page["platform"])
    out.append("## What changed on %s" % platform)
    out.append("")
    if changed["gallery"]:
        out.append("Regenerate and compare before testing anything: `%s`" % changed["gallery"])
        out.append("")
    if changed["problem"]:
        out.append("**No release to compare against:** %s. Nothing is listed "
                   "below, because without a last release nothing says which "
                   "change notes are new." % changed["problem"])
        out.append("")
    elif changed["tag"]:
        out.append("Compared against **%s**, tagged `%s`. Every change note added "
                   "since that tag is read for the screens it says it altered on %s."
                   % (changed["release"] or "the last release", changed["tag"], platform))
        out.append("")
    if changed["short_lines_problem"]:
        out.append("**Short lines not used:** %s." % changed["short_lines_problem"])
        out.append("")
    undeclared = changed["undeclared"]
    if undeclared:
        out.append("**Listed on every platform:** %s %s no `platforms:`, so "
                   "nothing says which platform %s changed: %s."
                   % (len(undeclared),
                      _plural(len(undeclared), "change note declares", "change notes declare"),
                      _plural(len(undeclared), "it", "they"), ", ".join(undeclared)))
        out.append("")
    if not changed["any"]:
        if not changed["problem"]:
            out.append("No change note names a screen on %s. Either this release "
                       "altered no screen there, or its change notes have no "
                       "`## Impact` list — the close-out step that writes one is in "
                       '`tools/instructions/TESTING.md`, "The release test", rule 8.'
                       % platform)
            out.append("")
        return
    out.append("Each section starts with the changes to the screens it tests. "
               "Open those screens and look at them before its first check.")
    out.append("")
    if changed["screens"]:
        out.append("No section on this sheet tests these changed screens. Open "
                   "them and look at them too:")
        out.append("")
        render_screens(changed["screens"], out, "###")


def render_screens(screens: list[dict], out: list[str], depth: str) -> None:
    """Changed screens, each with its lines and pictures; a child one level down."""
    for screen in screens:
        level = depth + "#" if screen["parent"] else depth
        label = ("%s (%s)" % (screen["title"], screen["id"])
                 if screen["title"] != screen["id"] else screen["id"])
        out.append("%s %s" % (level, label))
        out.append("")
        if screen["unresolved"]:
            out.append("**No surface note carries this id.** A change note names "
                       "it, so something was altered, and nobody reading this "
                       "sheet can tell which screen to open.")
            out.append("")
        for line in screen["lines"]:
            if line["short"]:
                out.append("- %s" % line["text"])
                continue
            said = line["text"] or "_that change names this screen and says nothing about it_"
            out.append("- %s — %s" % (said, line["title"] or line["change"]))
        if screen["lines"]:
            out.append("")
        for capture in screen["captures"]:
            name = "`%s`" % capture["key"]
            if capture["state"]:
                name += " (%s)" % capture["state"]
            if capture["stale"]:
                out.append("%s — **this picture is older than the change**: it was "
                           "committed on %s, before %s, so it cannot show it. "
                           "Capture it again." % (name, capture["stale"], capture["stale_against"]))
                out.append("")
            if capture["new"]:
                out.append("%s — **new**, captured now and not at the last release:" % name)
                out.append("")
                out.append("![%s, now](%s)" % (capture["key"], capture["after"]))
            elif capture["after"]:
                out.append("%s — before, then now:" % name)
                out.append("")
                out.append("![%s, at the last release](%s)" % (capture["key"], capture["before"]))
                out.append("")
                out.append("![%s, now](%s)" % (capture["key"], capture["after"]))
            else:
                out.append("%s — captured at the last release and not since:" % name)
                out.append("")
                out.append("![%s, at the last release](%s)" % (capture["key"], capture["before"]))
            out.append("")


def readiness_line(readiness: dict) -> str:
    """One line: why the check cannot be tested as written, and which result fits."""
    issue = " (%s)" % readiness["issue"] if readiness["issue"] else ""
    return "%s%s Suggested: %s." % (readiness["reason"].rstrip(), issue,
                                     _result_word(readiness["result"]))


def render_note_parts(check: dict, out: list[str]) -> None:
    """A per-check row's Setup and Steps, indented under its action line."""
    if check["setup"]:
        out.append("  - Setup: %s" % _WS_RE.sub(" ", check["setup"]))
    else:
        out.append("  - **Setup: not stated.** This check has no Setup heading. Write "
                   'one while you test it (`tools/instructions/TESTING.md`, "A check '
                   'is testable by a stranger").')
    if check["steps"] and check["steps_heading"]:
        out.append("  - Steps:")
        out.extend(("    " + line) if line.strip() else "" for line in check["steps"].splitlines())
    elif check["steps"]:
        out.append("  - **Steps: no heading.** The note's own description is below; "
                   "give it numbered steps while you test it.")
        out.extend(("    " + line) if line.strip() else "" for line in check["steps"].splitlines())
    else:
        out.append("  - Steps: _The note states no steps._")
    out.append("  - Expect:" if check["expected"] else "")
    if not check["expected"]:
        out.pop()


def render_section(section: dict, platform: str, out: list[str]) -> None:
    """One section: what changed, setup in three parts, then its numbered checks."""
    if section["unplaced"]:
        out.append("## Unplaced")
    else:
        out.append("## Section %d — %s" % (section["number"], section["name"]))
    out.append("")
    out.append("%d %s · %d test %s: %s" % (section["count"], _plural(section["count"], "check"),
                                           section["owed"], _plural(section["owed"], "note"),
                                           ", ".join(section["tests"])))
    out.append("")
    if section["what_changed"]:
        out.append("### What changed on the screens this section tests")
        out.append("")
        render_screens(section["what_changed"], out, "####")
    elif section["nothing_changed"]:
        out.append("Nothing changed on the screens this section tests.")
        out.append("")
    setup = section["setup"]
    if setup["bench"] or setup["before"] or setup["later"]:
        out.append("### Setup")
        out.append("")
        if setup["bench"]:
            out.append("**On the bench:**")
            out.append("")
            out.extend("- %s" % item for item in setup["bench"])
            out.append("")
        if setup["before"]:
            out.append("**Before you start:**")
            out.append("")
            out.extend("%d. %s" % (i, item) for i, item in enumerate(setup["before"], start=1))
            out.append("")
        if setup["later"]:
            out.append("**Later:**")
            out.append("")
            out.extend("- Check %d needs: %s" % (item["check"], item["text"])
                       for item in setup["later"])
            out.append("")
    if section["problems"]:
        out.append("**This section has a procedure and it no longer matches "
                   "what the release owes.** Each owed check is printed on its "
                   "own below instead, so nothing owed is hidden. Rewrite it with "
                   "`tools/skills/release-test-procedure/SKILL.md`:")
        out.append("")
        out.extend("- %s" % problem for problem in section["problems"])
        out.append("")
    out.append("### Checks")
    out.append("")
    if section["procedure"] and not section["problems"]:
        out.append("From [%s](%s)." % (section["procedure"], section["procedure"]))
        if section["omitted"]:
            out.append("%d %s of it %s left out: %s already passed or %s another platform."
                       % (section["omitted"], _plural(section["omitted"], "step"),
                          _plural(section["omitted"], "is", "are"),
                          _plural(section["omitted"], "it has", "they have"),
                          _plural(section["omitted"], "is for", "are for")))
        out.append("")
    for group in section["groups"]:
        if group["title"]:
            out.append("#### %s" % group["title"])
            out.append("")
        if group["start"]:
            out.append("Start: %s" % group["start"])
            out.append("")
        for check in group["checks"]:
            if check["start"]:
                if out[-1] != "":
                    out.append("")
                out.append("%s: %s" % ("Start again" if check.get("start_again") else "Start",
                                       check["start"]))
                out.append("")
            action = ("[%s](%s)" % (check["action"], check["path"]) if check["path"]
                      else check["action"])
            if check["timer"]:
                action += " ⏱ %d s" % check["timer"]
            out.append("- [ ] **%d.** %s" % (check["number"], action))
            if check["preparation"]:
                out.append("  - _Preparation for a later check. Nothing to record._")
            if "setup" in check:
                render_note_parts(check, out)
            tags = " ".join("`%s`" % tag for tag in check["tags"])
            for i, line in enumerate(check["expected"]):
                #: A line carries its own tags; a per-check row's lines all
                #: belong to its one check, whose tag goes on the last.
                own = line["tags"] or (check["tags"] if i == len(check["expected"]) - 1 else [])
                shown = " ".join("`%s`" % tag for tag in own)
                indent = "    - " if "setup" in check else "  - "
                out.append("%s%s%s" % (indent, line["text"], " " + shown if shown else ""))
            if not check["expected"] and not check["preparation"]:
                said = ("_The note states no expected result for %s._" % platform_name(platform)
                        if check.get("expect_stated", True) else "_The note states no expected result._")
                out.append("  - %s %s" % (said, tags))
            if check["readiness"]:
                out.append("  - _%s_" % readiness_line(check["readiness"]))
            if check["capture"]:
                out.append("  - _Keep what you see: %s_" % check["capture"])
            if check["compare_with"]:
                out.append("  - _Compare with what you kept at check %s._"
                           % ", ".join(str(n) for n in check["compare_with"]))
        out.append("")


def render(sheet: ReleaseTest) -> str:
    """The sheet a person reads, rendered from `payload`."""
    return render_page(payload(sheet))


def render_page(page: dict) -> str:
    out: list[str] = []
    out.append("# Release test — %s, %s" % (page["release"], page["platform"]))
    out.append("")
    out.append("Generated %s by `tools/scripts/release-test.py` from the release "
               "ledger, the check notes, the change notes and "
               "`docs/tests/acceptance/RELEASE-TEST.md`. "
               "Do not edit it: record every result in the ledger and generate "
               "it again. The rules are in `tools/instructions/TESTING.md`, "
               '"The release test".' % page["generated"])
    out.append("")
    sections = page["sections"]
    count = sum(section["count"] for section in sections)
    out.append("**%d %s in %d %s, from %d owed test %s.**"
               % (count, _plural(count, "check"), len(sections), _plural(len(sections), "section"),
                  page["owed"], _plural(page["owed"], "note")))
    out.append("")
    out.append("The validator counts from `mark:` on the note; this sheet counts "
               "from the ledger (project-os-dev ISS-0060).")
    if not page["authored_order"]:
        out.append("")
        out.append("**This project has authored no section order.** The sections "
                   "below are one per `area:` in id order, which is a grouping "
                   "and not a section order. Copy `docs/__templates__/release-test.md` to "
                   "`docs/tests/acceptance/RELEASE-TEST.md` and write the real one.")
    for notice in page["notices"]:
        out.append("")
        out.append("**Note:** %s" % notice)
    for warning in page["warnings"]:
        out.append("")
        out.append("**Check the section order:** %s" % warning)
    out.append("")
    out.append("## Sections")
    out.append("")
    out.append("| # | Section | Checks | On the bench |")
    out.append("|---|---|---|---|")
    for section in sections:
        out.append("| %s | %s | %d | %s |" % (
            section["number"] if section["number"] is not None else "–",
            section["name"].replace("|", "\\|"), section["count"],
            section["bench_line"].replace("|", "\\|") or "Nothing extra"))
    out.append("")
    render_what_changed(page, out)
    for section in sections:
        render_section(section, page["platform"], out)
    if any(s["unplaced"] for s in sections):
        out.append("The Unplaced checks are owed and no section in "
                   "`docs/tests/acceptance/RELEASE-TEST.md` claims their `area:`. "
                   "Add a section that claims them, or add the area to one that exists.")
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
    """Everything one platform's release test is computed from, read once."""

    repo_root: Path
    docs_root: Path
    index: dict
    checks: dict[str, Check]
    retired: set[str]
    surfaces: dict[str, str]
    surface_notes: dict[str, Surface]
    events: list[Event]
    sections: list[Section]
    procedures: list[Procedure]
    gallery: str = ""
    warnings: list[str] = field(default_factory=list)
    authored: bool = True
    what_changed_release: str = ""
    what_changed_tag: str = ""
    what_changed_problem: str = ""
    changes: list[Change] = field(default_factory=list)
    short_lines: ShortLines | None = None
    platforms: list[str] = field(default_factory=list)
    limits: LengthLimits = field(default_factory=lambda: LengthLimits())
    limit_problems: list[str] = field(default_factory=list)
    #: `quoted_lines:` from the section order file: whether a quoted
    #: expectation line refuses its procedure (the default) or only warns.
    quoted_refused: bool = True


def read_repo(repo_root: Path, platform: str) -> Reading:
    """Read a repo once, for either the sheet or the check."""
    docs_root = repo_root / "docs"
    if not has_ledger(docs_root):
        raise ReleaseTestError(
            "no release ledger in %s. A release test sheet is the ledger's owed set, so "
            "there is nothing to generate until the first verdict is written "
            "through the ledger path, which creates "
            "docs/releases/ledgers/WORKING-<platform>.json. A new project "
            "starting with no ledger is project-os-dev ISS-0059."
            % (docs_root / LEDGERS_REL))
    vd = _validator()
    index, _ = vd.build_note_index(docs_root)
    checks = load_checks(docs_root, index, repo_root=repo_root)
    if not checks:
        raise NothingToTest(
            "no acceptance checks in %s. A release test sheet lists `[[test]]` notes at "
            "`level: acceptance`; this repo has none." % docs_root)
    known = platforms(docs_root)
    if platform not in known:
        raise ReleaseTestError(
            "no ledger for platform %r. This repo keeps one for: %s. A release test "
            "asked for by an unknown name would read no verdicts at all and "
            "report every check in the repo as owed, so it is refused instead."
            % (platform, ", ".join(known) or "(none)"))
    release_test_path = docs_root / RELEASE_TEST_REL
    authored = release_test_path.is_file()
    limits, limit_problems = LengthLimits(), []
    quoted_refused = QUOTED_EXPECTATIONS_REFUSED
    if authored:
        gallery, sections, warnings = parse_section_order(
            release_test_path.read_text(encoding="utf-8"))
        front = vd.parse_frontmatter(release_test_path)
        limits, limit_problems = parse_limits(
            front.get("length_limits") if isinstance(front, dict) else None,
            "docs/%s" % RELEASE_TEST_REL)
        mode = front.get("quoted_lines") if isinstance(front, dict) else None
        if mode not in (None, ""):
            if mode in QUOTED_LINE_MODES:
                quoted_refused = QUOTED_LINE_MODES[mode]
            else:
                limit_problems.append(
                    "docs/%s: `quoted_lines` is %r; it is refused (the default) or warning"
                    % (RELEASE_TEST_REL, mode))
    else:
        gallery, sections, warnings = "", unordered_sections(list(checks.values())), []
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
        events=load_events(docs_root, platform), sections=sections,
        procedures=procedures, gallery=gallery, warnings=warnings,
        authored=authored, what_changed_release=release_id,
        what_changed_tag="" if problem else tag, what_changed_problem=problem, changes=changes,
        short_lines=load_short_lines(docs_root, platform, repo_root), platforms=known,
        limits=limits, limit_problems=limit_problems, quoted_refused=quoted_refused)


def generate(repo_root: Path, release: str, platform: str) -> ReleaseTest:
    read = read_repo(repo_root, platform)
    notices: list[str] = []
    sealed = sealed_releases(read.docs_root).get(release, "")
    if sealed:
        notices.append(
            "%s is already sealed (its ledger is %s-%s.json). This sheet is "
            "what the platform owes NOW, not what that release owed when it "
            "was sealed, because a ledger resolves forward."
            % (release, release, sealed))
    return sheet_from(read, release, platform, notices=notices)


def sheet_from(read: Reading, release: str, platform: str, notices=None,
               pictures: bool = True) -> ReleaseTest:
    """The sheet for one platform from what `read_repo` read.

    ``pictures`` off skips looking for screenshots and dating them, which
    the length check does not need.
    """
    return build_release_test(
        read.checks, read.events, read.sections, release=release, platform=platform,
        surfaces=read.surfaces, surface_notes=read.surface_notes,
        changes=read.changes, procedures=read.procedures, retired=read.retired,
        captures=capture_finder(read.docs_root, read.repo_root, read.what_changed_tag) if pictures else None,
        gallery=read.gallery, warnings=read.warnings, notices=notices,
        authored_order=read.authored, what_changed_release=read.what_changed_release,
        what_changed_tag=read.what_changed_tag, what_changed_problem=read.what_changed_problem,
        short_lines=read.short_lines, stale=stale_finder(read.repo_root) if pictures else None,
        known_platforms=read.platforms, quoted_refused=read.quoted_refused)


def check_repo(repo_root: Path, platform: str) -> tuple[list[str], list[str]]:
    """(problems, remarks) for every procedure in a repo, on one platform."""
    problems, _warnings, remarks = check_repo_findings(repo_root, platform)
    return problems, remarks


def check_repo_findings(repo_root: Path, platform: str
                        ) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """(problems, warnings, remarks) for a repo on one platform.

    A warning is `(kind, message)`: a form the notes should leave, which does
    not fail `--check` (`run_check` prints it, summarised under `--quiet`).
    """
    read = read_repo(repo_root, platform)
    problems: list[str] = []
    warnings: list[tuple[str, str]] = []
    for check in read.checks.values():
        problems.extend(check.readiness_problems)
        problems.extend(check.expect_problems)
    remarks: list[str] = []
    owed = owed_checks(read.checks, read.events)
    owed_ids = {c.id for c in owed}
    by_name = {s.name: s for s in read.sections}
    seen: set[str] = set()
    for procedure in read.procedures:
        if not procedure.section:
            if procedure.old_section:
                problems.append("%s: `sitting:` is the old name; it is now `section:`. %s"
                                % (procedure.path, MIGRATE_HINT))
                continue
            problems.append("%s: no `section:` in its frontmatter, so nothing "
                            "says which section it tests" % procedure.path)
            continue
        if procedure.section not in by_name:
            problems.append(
                '%s: `section: "%s"` matches no `### ` heading in docs/%s'
                % (procedure.path, procedure.section, RELEASE_TEST_REL))
            continue
        if procedure.section in seen:
            problems.append('%s: a second procedure for "%s"; one section is '
                            "tested from one script" % (procedure.path, procedure.section))
            continue
        seen.add(procedure.section)
        section = by_name[procedure.section]
        mine = [c for c in owed if claims(section, c, read.surfaces)]
        placed = placement(owed, read.sections, read.surfaces)
        mine = [c for c in mine if placed.get(c.id) == section.name]
        found, said = audit_procedure(procedure, section, mine, read.checks,
                                      owed_ids, read.sections, read.surfaces,
                                      platform=platform,
                                      retired=read.retired,
                                      quoted_refused=read.quoted_refused)
        problems.extend(found)
        warnings.extend(procedure.warnings)
        remarks.extend(said)
    if read.procedures:
        placed_all = placement(owed, read.sections, read.surfaces)
        uncovered = sorted({placed_all.get(c.id, "") for c in owed} - seen - {""})
        if uncovered:
            remarks.append("no procedure yet for: %s" % ", ".join(uncovered))
    #: **Every change note, not only the ones this release lists.** The
    #: what-changed list is restricted to what git says is new since the tag; the
    #: worklist is not, and a repo with no released note would otherwise be
    #: told nothing at all about its Impact lists. Found by independent
    #: review, 2026-09-14.
    for change in load_changes(read.docs_root, repo_root):
        for surface_id, _ in change.screens:
            if surface_id not in read.surface_notes:
                remarks.append("%s names %s in its Impact list and no surface "
                               "note carries that id" % (change.path, surface_id))
        if change.silent:
            remarks.append("%s has no `## Impact` list, so it tells the what-changed list "
                           "nothing; write the screens it altered, or "
                           '"No screen changed" and why' % change.path)
        found, warned = platform_findings(change, read.platforms)
        problems.extend(found)
        warnings.extend(warned)
    warnings.extend(short_line_findings(read, platform))
    problems.extend(read.limit_problems)
    if read.authored:
        page = payload(sheet_from(read, "", platform, pictures=False))
        for message in length_findings(page, read.limits):
            if read.limits.error:
                problems.append(message)
            else:
                warnings.append(("length", message))
    return problems, warnings, remarks


# ----------------------------------------------------------- the length check

@dataclass
class LengthLimits:
    """How long a printed line and a section may be (project-os-dev REQ-0036).

    The defaults are the one place the limits are set. A project overrides
    them in its section order file's frontmatter, `length_limits:`, with the
    same keys. The reports are errors; `error: false` turns them back into
    warnings, for a project still shortening its sections.

    The section budget is `section_base` words plus `section_per_check` words
    for each owed check. Measured on your-trainer's 27 rewritten sections on
    2026-09-27 (project-os-dev TASK-0195): every one fits these defaults,
    and 300 plus 30 would fail 17 of them.
    """

    action: int = 20
    expected: int = 25
    section_base: int = 300
    section_per_check: int = 40
    error: bool = True


_LIMIT_KEYS = {"action", "expected", "section_base", "section_per_check", "error"}


def parse_limits(raw, path: str) -> tuple[LengthLimits, list[str]]:
    """`length_limits:` from the section order file, or the defaults."""
    limits = LengthLimits()
    if raw in (None, ""):
        return limits, []
    if not isinstance(raw, dict):
        return limits, ["%s: `length_limits` must be a map of %s"
                        % (path, ", ".join(sorted(_LIMIT_KEYS)))]
    problems = []
    for key, value in raw.items():
        if key not in _LIMIT_KEYS:
            problems.append("%s: `length_limits` has `%s`; the keys are %s"
                            % (path, key, ", ".join(sorted(_LIMIT_KEYS))))
        elif key == "error":
            if not isinstance(value, bool):
                problems.append("%s: `length_limits.error` must be true or false" % path)
            else:
                limits.error = value
        elif isinstance(value, bool) or not isinstance(value, int) or value < 1:
            problems.append("%s: `length_limits.%s` must be a whole number of words above 0"
                            % (path, key))
        else:
            setattr(limits, key, value)
    return limits, problems


_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")


def printed_words(text: str) -> int:
    """The words a tester reads: no tags, no link targets, no pictures, no markup."""
    count = 0
    for line in text.splitlines():
        if line.lstrip().startswith("!["):
            continue
        line = _TAG_SPAN_RE.sub("", line)
        line = _LINK_RE.sub(lambda m: m.group(1), line)
        line = re.sub(r"[`*_#|>]+", " ", line)
        count += len([w for w in line.split() if re.search(r"\w", w)])
    return count


def length_findings(page: dict, limits: LengthLimits) -> list[str]:
    """Every action line, expected line and section over its limit, on one page."""
    out = []
    for section in page["sections"]:
        where = ("Unplaced" if section["unplaced"]
                 else 'section %d, "%s"' % (section["number"], section["name"]))
        for group in section["groups"]:
            for check in group["checks"]:
                tag = " ".join("`%s`" % tag for tag in check["tags"])
                words = printed_words(check["action"])
                if words > limits.action:
                    out.append("%s, check %d (%s): the action is %d words, over the limit "
                               "of %d: %s" % (where, check["number"], tag, words,
                                              limits.action, _clip(check["action"])))
                for line in check["expected"]:
                    words = printed_words(line["text"])
                    if words > limits.expected:
                        out.append("%s, check %d (%s): an expected line is %d words, over "
                                   "the limit of %d: %s" % (where, check["number"],
                                                             " ".join("`%s`" % t for t in line["tags"]) or tag,
                                                             words, limits.expected,
                                                             _clip(line["text"])))
        printed: list[str] = []
        render_section(section, page["platform"], printed)
        words = printed_words("\n".join(printed))
        budget = limits.section_base + limits.section_per_check * section["count"]
        if words > budget:
            out.append("%s prints %d words, over its budget of %d (%d + %d for each of "
                       "its %d checks)" % (where[0].upper() + where[1:], words, budget,
                                           limits.section_base, limits.section_per_check,
                                           section["count"]))
    return out


def _clip(text: str, words: int = 8) -> str:
    parts = text.split()
    return '"%s%s"' % (" ".join(parts[:words]), " ..." if len(parts) > words else "")


#: A change note created on or after this date that names a screen must say
#: which platforms it changed, in a project with more than one. Earlier notes
#: are warned: they were written before `platforms:` existed
#: (project-os-dev REQ-0035, TASK-0191).
PLATFORMS_REQUIRED_FROM = "2026-09-28"


def platform_findings(change: Change, known: list[str]
                      ) -> tuple[list[str], list[tuple[str, str]]]:
    """(problems, warnings) for one change note's `platforms:` and Impact marks."""
    problems: list[str] = []
    warnings: list[tuple[str, str]] = []
    named = set(change.platforms) | {m for m in change.marks if m}
    for name in sorted(named - set(known)):
        if known:
            problems.append("%s names the platform `%s`, and this project keeps a "
                            "ledger only for: %s" % (change.path, name, ", ".join(known)))
    if len(known) > 1 and change.screens and not change.platforms:
        message = ("%s names a screen in its Impact list and declares no "
                   "`platforms:`, so it is listed on every platform" % change.path)
        if change.created and change.created >= PLATFORMS_REQUIRED_FROM:
            problems.append(message + "; add `platforms: [%s]` with the ones it "
                            "changed" % ", ".join(known))
        else:
            warnings.append(("platforms", message))
    return problems, warnings


def short_line_findings(read: Reading, platform: str) -> list[tuple[str, str]]:
    """Warnings for `what-changed-<platform>.md` when it names the last release tag.

    A file written against an older tag is not checked line by line: the
    sheet already says it is out of date and does not use it.
    """
    short = read.short_lines
    if short is None or not read.what_changed_tag or short.tag != read.what_changed_tag:
        return []
    out = [("short_lines", problem) for problem in short.problems]
    for change in read.changes:
        for surface_id, _sentence in change.on(platform):
            if (change.id, surface_id) not in short.lines:
                out.append(("short_lines", "%s has no short line for %s on %s, "
                            "which %s changed" % (short.path, surface_id,
                                                   platform, change.id)))
    return out


def run_check(repo_root: Path, platform: str, quiet: bool = False) -> int:
    """`--check` over one platform or all of them. 0 = nothing to fix.

    **Nothing to check is not a failure, and a broken ledger still is.** No
    ledger and no live acceptance check are both repos with no procedure to
    hold to anything, and `validate-docs.sh` runs this on every commit --
    letting those through made a repo whose checks had all been retired fail
    its own pre-commit hook forever. But the first fix caught every
    `ReleaseTestError`, which took a malformed ledger with it; `NothingToTest` is the
    narrow one. Both halves found by independent review, 2026-09-14, rounds
    one and two.
    """
    docs_root = repo_root / "docs"
    if not has_ledger(docs_root):
        return 0
    wanted = [platform] if platform else platforms(docs_root)
    status = 0
    printed: set[str] = set()
    #: A warning holds for the file, whichever platform found it, so it prints
    #: once. Under `--quiet`, which is how `validate-docs.sh` runs this on
    #: every commit, each kind prints as one line with its count: 724 quoted
    #: lines on your-trainer (2026-09-27) would otherwise bury everything else.
    seen_warnings: set[tuple[str, str]] = set()
    warned: dict[str, int] = {}
    for name in wanted:
        try:
            problems, warnings, remarks = check_repo_findings(repo_root, name)
        except NothingToTest as exc:
            #: No live acceptance check means no procedure to hold to anything.
            if not quiet:
                print("release-test --check (%s): nothing to check -- %s"
                      % (name, exc), file=sys.stderr)
            continue
        except ReleaseTestError as exc:
            #: Everything else `read_repo` refuses is a broken ledger, and
            #: `--check` is the only thing that reads one on every commit.
            print("ERROR [RELEASE-TEST] release-test --check (%s): %s" % (name, exc), file=sys.stderr)
            status = 2
            continue
        for problem in problems:
            #: A check's own readiness problem is the same on every platform;
            #: printing it once per platform read as two findings (FEAT-0033 review).
            if problem in printed:
                continue
            printed.add(problem)
            #: `ERROR [RELEASE-TEST]`: the validator's line shape, so a reader
            #: filtering for ERROR finds it (project-os-dev ISS-0089).
            print("ERROR [RELEASE-TEST] release-test --check (%s): %s" % (name, problem), file=sys.stderr)
        for kind, warning in warnings:
            if (kind, warning) in seen_warnings:
                continue
            seen_warnings.add((kind, warning))
            if quiet:
                warned[kind] = warned.get(kind, 0) + 1
            else:
                print("WARN  [RELEASE-TEST] release-test --check (%s): %s" % (name, warning),
                      file=sys.stderr)
        #: Remarks are printed when something is wrong, or when a person
        #: asked. `validate-docs.sh` runs this on every commit, and a repo
        #: with procedures would otherwise print its coverage shortfall to
        #: everybody, every time, until it stopped being read.
        if problems or not quiet:
            for remark in remarks:
                print("release-test --check (%s): note: %s" % (name, remark))
        if problems:
            status = 1
    for kind in sorted(warned):
        print("WARN  [RELEASE-TEST] release-test --check: %d %s; `python3 "
              "tools/scripts/release-test.py --check` lists them"
              % (warned[kind], WARNING_KINDS.get(kind, "warning(s) of kind " + kind)),
              file=sys.stderr)
    return status


#: What each kind of warning is, for the one-line count `--quiet` prints.
WARNING_KINDS = {
    "quoted": "procedure line(s) state an expectation in their own words instead of "
              "giving tags alone (project-os-dev ADR-0050 D2)",
    "state_for": "procedure(s) still declare `state_for:`, which a `Start:` line under a "
                 "group heading replaces (project-os-dev REQ-0033)",
    "platforms": "change note(s) name a screen and declare no `platforms:`, so they "
                 "are listed on every platform (project-os-dev REQ-0035)",
    "short_lines": "change(s) since the last release have no short what-changed line, "
                   "or a line names no change or no screen (project-os-dev REQ-0035)",
    "length": "line(s) or section(s) are longer than their word limit "
              "(project-os-dev REQ-0036)",
}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a release test sheet: the owed acceptance checks "
                    "as a procedure, the changed screens first.",
        epilog="The rules are stated once in tools/instructions/TESTING.md, "
               '"The release test"; this script restates none of them. What changed lists '
               "the screens the change notes added since the last release tag "
               "say they altered. Without --out the sheet goes to stdout; a "
               "sheet kept as a record of what was tested is never edited by "
               "hand and never read back. --check reads the procedures instead "
               "and exits 1 when one no longer matches what the release owes.")
    ap.add_argument("--release", default="",
                    help="the release this release test is for, e.g. REL-0017")
    ap.add_argument("--platform", default="",
                    help="the platform whose ledger is read, e.g. android; with "
                         "--check, every platform when omitted")
    ap.add_argument("--check", action="store_true",
                    help="hold each section's procedure to what the release "
                         "owes, print nothing else, and exit 1 on a disagreement")
    ap.add_argument("--out", default="",
                    help="write the sheet here instead of stdout")
    ap.add_argument("--json", action="store_true",
                    help="write the page as JSON, the data the Markdown sheet is "
                         "rendered from and the cockpit draws its page from")
    ap.add_argument("--quiet", action="store_true",
                    help="with --check, print remarks only when something is "
                         "also wrong")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not (root / "SNAPSHOT.yaml").is_file():
        print("release-test: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
        return 2
    if args.check:
        return run_check(root, args.platform, quiet=args.quiet)
    missing = [name for name, value in (("--release", args.release),
                                        ("--platform", args.platform)) if not value]
    if missing:
        print("release-test: %s required to generate a sheet"
              % " and ".join(missing), file=sys.stderr)
        return 2
    try:
        sheet = generate(root, args.release, args.platform)
    except ReleaseTestError as exc:
        print("release-test: %s" % exc, file=sys.stderr)
        return 2
    text = (json.dumps(payload(sheet), indent=2, ensure_ascii=False) + "\n"
            if args.json else render(sheet))
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print("release-test: %d owed rows -> %s" % (sheet.rows, target))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
