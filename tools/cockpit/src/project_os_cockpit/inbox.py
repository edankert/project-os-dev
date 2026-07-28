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

#: 25 MB. A screenshot is ~1 MB; a screen recording is not what this is for,
#: and an unbounded write endpoint on a server that binds 0.0.0.0 is a way to
#: fill a disk from the LAN.
MAX_ITEM_BYTES: int = 25 * 1024 * 1024

#: What may be stored. An allow-list rather than a deny-list: the inbox exists
#: to hold evidence a human dropped, and an executable is not evidence.
ALLOWED_SUFFIXES: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic", ".avif",
    ".pdf", ".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".log",
})

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_STEM = 60


def inbox_dir(project_root: Path) -> Path:
    return project_root / "inbox"


def safe_name(raw: str, *, now: _dt.datetime | None = None) -> str | None:
    """A storable filename, or ``None`` if the input cannot be made safe.

    The caller's name is used only for its **basename and suffix**, and even
    those are rewritten, so ``../../.ssh/authorized_keys`` cannot survive as a
    path.

    Note honestly which line does that work: the ``_SAFE`` substitution below
    turns every separator into ``-``, so **the basename split is redundant** —
    removing it leaves every test green. It stays because it makes the intent
    legible at the top of the function, not because it is the guard. The guard
    is ``_SAFE`` plus the suffix allow-list, and containment is re-checked at
    the write because a filter that is the *only* defence is one edit away from
    not being one.
    """
    base = str(raw or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not base or base in (".", ".."):
        return None
    suffix = Path(base).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return None
    stem = _SAFE.sub("-", Path(base).stem).strip("-.") or "item"
    stamp = (now or _dt.datetime.now()).strftime("%Y%m%d-%H%M%S")
    return "%s-%s%s" % (stamp, stem[:_MAX_STEM], suffix)


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
