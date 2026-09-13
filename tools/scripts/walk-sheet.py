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
  * `docs/tests/acceptance/WALK.md`, the project's authored sitting order.

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
"""

from __future__ import annotations

import argparse
import json
import re
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
        )
    return out


CHANGES_REL = "changes"
#: `"TASK-0862, TASK-0863"` -> two tokens. Kept as written rather than
#: canonicalised, because a change note's id IS its full slug.
_CAUSE_SPLIT = re.compile(r"[,;\s]+")


def causes(raw: str) -> list[str]:
    return [tok.strip().strip("[]") for tok in _CAUSE_SPLIT.split(raw or "")
            if tok.strip()]


def change_notes(docs_root: Path) -> dict[str, tuple[str, Path]]:
    """Change notes, keyed by their full id and by their filename stem.

    **A second index, because the first one deliberately excludes them.**
    `CHG` is not in the validator's `ID_PREFIXES`, so `build_note_index` holds
    no change note at all, and a survey resolving an invalidation that named
    one printed the id with an empty title and quoted nothing. Keying on the
    full id rather than on `CHG-<date>` is not fussiness either: two change
    notes dated the same day is ordinary, and `CHG-<date>` would pick one of
    them arbitrarily. Found by independent review, 2026-09-13.
    """
    out: dict[str, tuple[str, Path]] = {}
    root = docs_root / CHANGES_REL
    if not root.is_dir():
        return out
    vd = _validator()
    for path in sorted(root.glob("*.md")):
        fm = vd.parse_frontmatter(path)
        if not isinstance(fm, dict):
            continue
        title = _text(fm.get("title"))
        for key in (_text(fm.get("id")), path.stem):
            if key:
                out.setdefault(key, (title, path))
    #: A ledger may also name a change by its canonical id, `CHG-20260913`,
    #: rather than by its full slug. That resolves only while the date picks
    #: out one note: two change notes dated the same day is ordinary, and
    #: answering with either of them would be a guess.
    seen: dict[str, list[str]] = {}
    for key in list(out):
        for canonical in _ids(key):
            seen.setdefault(canonical, []).append(key)
    for canonical, owners in seen.items():
        if len(set(owners)) == 1 and canonical not in out:
            out[canonical] = out[owners[0]]
    return out


def note_titles(index) -> dict[str, tuple[str, Path]]:
    return {i: (_text(fm.get("title")), path) for i, (path, fm) in index.items()
            if isinstance(fm, dict)}


def surfaces_by_title(index) -> dict[str, str]:
    """`area:` string -> `SUR-*` id, for repos that keep surface notes.

    A repo with no `SUR-*` notes groups the survey by the `area:` string
    alone, which is why this may legitimately be empty.
    """
    vd = _validator()
    out = {}
    for note_id, (path, fm) in index.items():
        if isinstance(fm, dict) and vd.note_type(fm) == "surface":
            title = _text(fm.get("title"))
            if title:
                out.setdefault(title, note_id)
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
class SurveyEntry:
    surface: str
    surface_id: str
    checks: list[str]
    causes: list[tuple[str, str, str]]   # (id, title, quoted reopened section)


@dataclass
class Placed:
    sitting: Sitting
    rows: list[Check]


@dataclass
class Walk:
    release: str
    platform: str
    generated: str
    survey: list[SurveyEntry]
    sittings: list[Placed]
    unplaced: list[Check]
    gallery: str = ""
    #: Something to fix in `WALK.md`.
    warnings: list[str] = field(default_factory=list)
    #: Something true about this sheet that is nobody's mistake.
    notices: list[str] = field(default_factory=list)
    authored_order: bool = True

    @property
    def rows(self) -> int:
        return sum(len(p.rows) for p in self.sittings) + len(self.unplaced)


REOPENED_HEADING = "Acceptance checks reopened"


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


def build_walk(checks: dict[str, Check], events: list[Event], sittings: list[Sitting],
               *, release: str, platform: str, titles=None, surfaces=None,
               gallery: str = "", generated: str = "", warnings=None,
               notices=None, changes=None,
               authored_order: bool = True) -> Walk:
    """The sheet as data: the survey, the sittings and the unplaced rows.

    Takes plain values rather than a repo path, so a host with its own note
    index (the cockpit's `walk_payload`) computes the same walk from the same
    rules without a second implementation of any of them.
    """
    titles = titles or {}
    surfaces = surfaces or {}
    changes = changes or {}
    warnings = list(warnings or [])
    verdicts = resolve(events)
    latest = latest_events(events)

    owed = [c for c in checks.values()
            if c.section != "automated"
            and ((v := verdicts.get(c.id)) is None or not v.clears)]
    owed.sort(key=lambda c: c.id)

    # --- the survey: owed checks whose last word from the ledger was "redo this"
    grouped: dict[str, list[Check]] = {}
    reopened: dict[str, dict[str, str]] = {}
    for check in owed:
        event = latest.get(check.id)
        if event is None or not event.is_invalidation:
            continue
        surface = check.area or "(no area on the check)"
        grouped.setdefault(surface, []).append(check)
        for cause in causes(event.invalidated_by):
            reopened.setdefault(surface, {})[cause] = ""
    survey = []
    for surface in sorted(grouped):
        rows = []
        for cause in sorted(reopened.get(surface, {})):
            #: A change note resolves by its full id; everything else through
            #: the canonical id the note index is keyed on.
            title, path = changes.get(cause, ("", None))
            if path is None:
                canonical = _ids(cause)
                if canonical:
                    title, path = titles.get(canonical[0], ("", None))
            quoted = section(body_of(Path(path)), REOPENED_HEADING) if path else ""
            rows.append((cause, title, quoted))
        survey.append(SurveyEntry(surface=surface,
                                  surface_id=surfaces.get(surface, ""),
                                  checks=[c.id for c in grouped[surface]],
                                  causes=rows))

    # --- placement: the first sitting that claims a check keeps it
    placed: list[Placed] = []
    taken: set[str] = set()
    for sitting in sittings:
        claimed = [c for c in owed
                   if c.id not in taken
                   and (c.id in sitting.checks
                        or c.area in sitting.surfaces
                        or surfaces.get(c.area, "") in sitting.surfaces)]
        taken.update(c.id for c in claimed)
        if claimed:
            placed.append(Placed(sitting=sitting,
                                 rows=order_rows(claimed, warnings, sitting.name)))
    unplaced = order_rows([c for c in owed if c.id not in taken],
                          warnings, "Unplaced")
    return Walk(release=release, platform=platform,
                generated=generated or date.today().isoformat(),
                survey=survey, sittings=placed, unplaced=unplaced,
                gallery=gallery, warnings=warnings, notices=list(notices or []),
                authored_order=authored_order)


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


def render(walk: Walk) -> str:
    """The sheet a person reads. Counts of rows are the only numbers on it."""
    out: list[str] = []
    out.append("# Walk sheet — %s, %s" % (walk.release, walk.platform))
    out.append("")
    out.append("Generated %s by `tools/scripts/walk-sheet.py` from the release "
               "ledger, the check notes and `docs/tests/acceptance/WALK.md`. "
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

    out.append("## Survey — the surfaces this release changed")
    out.append("")
    if walk.gallery:
        out.append("Regenerate and compare before walking anything: `%s`" % walk.gallery)
        out.append("")
    if not walk.survey:
        out.append("Nothing on the owed list was reopened by a change in this "
                   "release. Every row below is owed because it has never been "
                   "walked on this platform, or because its last verdict did "
                   "not clear.")
        out.append("")
    else:
        out.append("Open these screens first and look at them, before walking a "
                   "single scripted check. Each one has an owed check that a "
                   "change in this release reopened.")
        out.append("")
        for entry in walk.survey:
            label = entry.surface
            if entry.surface_id:
                label = "%s (%s)" % (entry.surface, entry.surface_id)
            out.append("### %s — %d owed" % (label, len(entry.checks)))
            out.append("")
            out.append("Reopened by:")
            out.append("")
            for cause, title, quoted in entry.causes:
                out.append("- **%s**%s" % (cause, " — %s" % title if title else ""))
                if quoted:
                    out.append("")
                    out.append(_quote(quoted))
                    out.append("")
            out.append("")
            out.append("Checks under this surface: %s" % ", ".join(entry.checks))
            out.append("")

    def rows_of(title: str, sitting: Sitting | None, rows: list[Check]) -> None:
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
        out.append("%d %s." % (len(rows), "row" if len(rows) == 1 else "rows"))
        out.append("")
        for check in rows:
            head = "### [%s](%s)" % (check.id, check.path)
            if check.title:
                head += " — %s" % check.title
            out.append(head)
            out.append("")
            out.append("- [ ] walked, and the verdict recorded in the ledger")
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

    for i, placed in enumerate(walk.sittings, start=1):
        rows_of("Sitting %d — %s" % (i, placed.sitting.name), placed.sitting,
                placed.rows)
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

def generate(repo_root: Path, release: str, platform: str) -> Walk:
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
        raise WalkError(
            "no acceptance checks in %s. A walk sheet lists `[[test]]` notes at "
            "`level: acceptance`; this repo has none." % docs_root)
    known = platforms(docs_root)
    if platform not in known:
        raise WalkError(
            "no ledger for platform %r. This repo keeps one for: %s. A walk "
            "asked for by an unknown name would read no verdicts at all and "
            "report every check in the repo as owed, so it is refused instead."
            % (platform, ", ".join(known) or "(none)"))
    events = load_events(docs_root, platform)
    walk_path = docs_root / WALK_REL
    authored = walk_path.is_file()
    warnings: list[str] = []
    if authored:
        gallery, sittings, warnings = parse_walk_order(
            walk_path.read_text(encoding="utf-8"))
    else:
        gallery, sittings = "", unordered_sittings(list(checks.values()))
    notices: list[str] = []
    sealed = sealed_releases(docs_root).get(release, "")
    if sealed:
        notices.append(
            "%s is already sealed (its ledger is %s-%s.json). This sheet is "
            "what the platform owes NOW, not what that release owed when it "
            "was sealed, because a ledger resolves forward."
            % (release, release, sealed))
    return build_walk(
        checks, events, sittings, release=release, platform=platform,
        titles=note_titles(index), surfaces=surfaces_by_title(index),
        changes=change_notes(docs_root), gallery=gallery, warnings=warnings,
        notices=notices, authored_order=authored)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a release walk sheet: the owed acceptance checks "
                    "as a procedure, the changed screens first.",
        epilog="The rules are stated once in tools/instructions/TESTING.md, "
               '"The walk"; this script restates none of them. The survey groups '
               "by the SUR-* note whose title matches a check's area:, and by "
               "the area: string alone in a repo that keeps no surface notes. "
               "Without --out the sheet goes to stdout; a sheet kept as a record "
               "of what was walked is never edited by hand and never read back.")
    ap.add_argument("--release", required=True,
                    help="the release this walk is for, e.g. REL-0017")
    ap.add_argument("--platform", required=True,
                    help="the platform whose ledger is read, e.g. android")
    ap.add_argument("--out", default="",
                    help="write the sheet here instead of stdout")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not (root / "SNAPSHOT.yaml").is_file():
        print("walk-sheet: no SNAPSHOT.yaml at %s" % root, file=sys.stderr)
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
