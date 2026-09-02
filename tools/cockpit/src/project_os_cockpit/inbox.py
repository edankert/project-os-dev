"""The project inbox — external material staged for triage (FEAT-0045).

`inbox/` at the repo root holds things that have arrived but have not been
decided about: a screenshot, an export, a page of notes. An LLM reads each item
and files it, splits it, or discards it, and **the success condition is that the
directory ends up empty** (`tools/skills/inbox-triage/SKILL.md`).

Deliberately outside `docs/`: that directory is the curated record, walked by
the validator and read as the truth, and untriaged material does not belong in
it. Gitignored, because an item is either filed — at which point the *filed*
artefact is what gets committed — or discarded.

This module owns the filesystem rules and nothing else. Everything here treats
the caller's filename as **hostile**: it arrives from a drag-and-drop or a
clipboard paste, which is the one place in this codebase where a user-supplied
name reaches a write path.
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

#: 250 MB (raised from 25 MB by [[ISS-0274]], Edwin 2026-09-02).
#:
#: The old comment justified 25 MB as "an unbounded write endpoint on a server
#: that binds 0.0.0.0 is a way to fill a disk from the LAN". That threat was
#: already closed: `_serve_inbox_store` calls `_require_loopback()` first, so
#: the LAN never reaches it. The real ceiling is memory, not disk — the
#: renderer base64s the whole file into one JSON request, so both ends hold it
#: at once, and 250 MB is about where that stops being pleasant.
MAX_ITEM_BYTES: int = 250 * 1024 * 1024

#: Suffixes `_serve_inbox_item` will serve with their own content type. This is
#: a **read-side** list and the only one left; the inbox stores any type
#: ([[ISS-0274]]).
#:
#: The write path used to carry the allow-list instead, which was the wrong end.
#: It stopped no attack — `_SAFE` and the containment re-check refuse a hostile
#: name without it, and nothing here executes what it stores — while admitting
#: `.svg`, which can carry `<script>` and came back at the cockpit's own
#: origin, and refusing `.zip`, which the server never opens.
#:
#: `.svg` stays inline so tray thumbnails keep working: `<img>` does not run
#: script in an SVG, and the CSP on every response closes the direct-navigation
#: case that `<img>` never had.
INLINE_SUFFIXES: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic", ".avif",
    ".pdf", ".txt", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml", ".log",
})

#: Suffixes that need `sandbox` on top of `default-src 'none'` — the ones a
#: browser will execute if you navigate to them. `sandbox` is not free: without
#: `allow-scripts` it is also how Chrome is usually made to DOWNLOAD a PDF
#: instead of rendering it, so it is applied where it buys something rather
#: than everywhere (independent review, 2026-09-02, finding 5).
#:
#: Non-inline types get it too — they are already an attachment, so there is
#: nothing to break.
SCRIPTABLE_SUFFIXES: frozenset[str] = frozenset({".svg"})

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_STEM = 60
#: A suffix is a label, not a payload. `.compressed-archive` is a real one;
#: 200 characters of unicode after a dot is somebody probing the write path.
_MAX_SUFFIX = 16


def inbox_dir(project_root: Path) -> Path:
    return project_root / "inbox"


def safe_name(raw: str, *, now: _dt.datetime | None = None) -> str | None:
    """A storable filename, or ``None`` if the input cannot be made safe.

    **Any file type is storable** ([[ISS-0274]]). The stem and the suffix are
    both rewritten rather than checked against a list, so
    ``../../.ssh/authorized_keys`` cannot survive as a path and neither can a
    suffix carrying anything but ``[A-Za-z0-9._-]``.

    Note honestly which line does that work. The ``_SAFE`` substitution below
    turns every separator into ``-``, and this function's docstring used to say
    the basename split was therefore redundant — *"removing it leaves every
    test green"*. **That stopped being true in this change and the sentence
    survived it** (independent review, 2026-09-02). ``"///"`` reaches the split
    as an empty basename and is refused; without the split it stores as
    ``item``, so `test_a_name_with_nothing_in_it_is_still_refused` goes red.
    The split is now load-bearing, and the note that said otherwise was left
    standing by the edit that falsified it — which is the same failure this
    file keeps finding, arriving as a stale comment rather than a dead guard.

    Containment is still re-checked at the write, because a filter that is the
    *only* defence is one edit away from not being one.

    Every result is prefixed with a timestamp, which is also why no dotfile can
    be created here: ``.bashrc`` becomes ``20260902-120000-bashrc``.
    """
    base = str(raw or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not base or base in (".", ".."):
        return None
    suffix = _SAFE.sub("-", Path(base).suffix.lower()).strip("-")[:_MAX_SUFFIX]
    if suffix in ("", "."):
        # No extension is a legitimate file (``Makefile``, ``README``), but a
        # suffix that sanitised down to nothing but punctuation is not one.
        suffix = ""
    stem = _SAFE.sub("-", Path(base).stem).strip("-.") or "item"
    stamp = (now or _dt.datetime.now()).strftime("%Y%m%d-%H%M%S")
    return "%s-%s%s" % (stamp, stem[:_MAX_STEM], suffix)


def header_filename(name: str) -> str:
    """``name`` reduced to something safe to put in a response header.

    `safe_name` already guarantees this for anything dropped through the UI.
    This exists for the other door: the inbox is a plain directory and `cp`
    into it is a supported way to add an item, so `list_items` and
    `resolve_item` both see names this module never built. macOS permits a
    quote and a newline in a filename, and either one unescaped in a
    ``Content-Disposition`` value is header injection.
    """
    #: **Stem and suffix separately, because `.strip("-.")` ate the dot.**
    #: Independent review, 2026-09-02: `报告.docx` came back as `docx` and
    #: `éé.zip` as `zip`. A leading non-ASCII run collapses to a single `-`,
    #: leaving `-.docx`, and stripping `-.` from the front then takes the
    #: separator AND the dot behind it. The extension survived only for names
    #: that began with an ASCII letter — and a name that did not is exactly
    #: the `cp` case this function exists for.
    stem = _SAFE.sub("-", Path(name).stem).strip("-.") or "item"
    suffix = _SAFE.sub("-", Path(name).suffix).strip("-")[:_MAX_SUFFIX]
    if suffix in ("", "."):
        suffix = ""
    return stem[:_MAX_STEM] + suffix


def unique_path(directory: Path, name: str) -> Path:
    """``name`` in ``directory``, suffixed if something is already there.

    Two screenshots in the same second is not a rare event when someone is
    capturing a sequence, and silently overwriting the first would lose
    evidence the user believed they had handed over.
    """
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem, suffix = Path(name).stem, Path(name).suffix
    for n in range(2, 1000):
        candidate = directory / ("%s-%d%s" % (stem, n, suffix))
        if not candidate.exists():
            return candidate
    raise FileExistsError("too many collisions for %s" % name)


def list_items(project_root: Path) -> list[dict]:
    """What is waiting, newest first.

    Newest first because the inbox is worked from the top: the thing just
    dropped is the thing being talked about.
    """
    directory = inbox_dir(project_root)
    if not directory.is_dir():
        return []
    out = []
    for path in directory.iterdir():
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        out.append({
            "name": path.name,
            "bytes": stat.st_size,
            "mtime": stat.st_mtime,
            "suffix": path.suffix.lower(),
        })
    out.sort(key=lambda i: i["mtime"], reverse=True)
    return out


def resolve_item(project_root: Path, name: str) -> Path | None:
    """An existing item by name, or ``None``.

    Resolves and re-checks containment, so a symlink planted in the inbox
    cannot be used to read or delete something outside it.

    The cheap name check below is a **fast path, not the guard**: the resolve
    plus ``relative_to`` refuses the same inputs, and removing the name check
    leaves every test green. Said plainly because a check that cannot fire,
    under a comment implying it protects something, is the defect this codebase
    has found repeatedly (ISS-0024, ISS-0049, ISS-0056).
    """
    if not name or "/" in name or "\\" in name or ".." in name.split("."):
        return None
    directory = inbox_dir(project_root).resolve()
    try:
        target = (directory / name).resolve()
        target.relative_to(directory)
    except (ValueError, OSError):
        return None
    return target if target.is_file() else None
