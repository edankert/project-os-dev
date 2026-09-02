"""Does the thing a `command:` names still exist? (ADR-0039, TASK-0566)

An automated test's claim is *a machine executes this*. The claim rots exactly
one way: the test it points at is renamed, deleted or disabled, and the command
goes on naming something that is not there. Nothing else about an automated note
can go stale -- which is why this is the only obligation one can carry, and why
[[ADR-0038]] preferred a `command:` to a stamped `passing` in the first place. A
stamp cannot notice a rename. This can.

**Three answers, never two.** `RESOLVES`, `BROKEN`, and `UNCHECKABLE` for a
command whose shape names no target this can find -- a shell pipeline, a
wrapper script, a bare `make`. Folding `UNCHECKABLE` into `RESOLVES` would
quietly assert coverage nobody verified; folding it into `BROKEN` would put 5 of
the fleet's 139 automated notes on a list of things to fix that are not broken.

**This logic exists twice on purpose.** `validate_docs_bundled.py` is stdlib-only
and self-contained because it is copied into every downstream repo, so it cannot
import this module. `tests/test_command_target_parity.py` asserts the two agree
on every command in the corpus *and* on the constructed cases below -- which is
the same treatment `_SETTLED_MARKS` gets, and for the same reason.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

RESOLVES = "resolves"
BROKEN = "broken"
UNCHECKABLE = "uncheckable"

#: A JVM test named on a Gradle command line: `--tests com.x.FooTest`, or
#: `-Pandroid.testInstrumentationRunnerArguments.class=com.x.FooTest`. The
#: capital after the last dot is what distinguishes a class from a package.
_JVM_CLASS = re.compile(r"(?:--tests|class=)\s*([A-Za-z_][\w.]*\.[A-Z]\w+)")

#: Source extensions a JVM class could live in. Kotlin first: the fleet's one
#: JVM repo is Kotlin, and the order only affects which stat call happens first.
_JVM_SUFFIXES = (".kt", ".java")

_SOURCE_PATH = re.compile(r"\.(py|ts|tsx|js|mjs|swift)$")


def targets(command: str) -> list[tuple[str, str]]:
    """Every target a command names, as (kind, value) pairs. Pure."""
    out: list[tuple[str, str]] = []
    if not command:
        return out
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        # An unbalanced quote is not a broken test, it is a command this
        # cannot read. Fall through to the class scan and let the caller
        # report UNCHECKABLE if that finds nothing either.
        tokens = []
    for token in tokens:
        if token.startswith("-"):
            continue
        # `tests/test_foo.py::test_bar` -- the file is the checkable part.
        head = token.split("::", 1)[0]
        if _SOURCE_PATH.search(head):
            out.append(("path", head))
    for match in _JVM_CLASS.finditer(command):
        out.append(("class", match.group(1)))
    return out


def _exists(kind: str, value: str, root: Path) -> bool:
    if kind == "path":
        if (root / value).exists():
            return True
        # A command may `cd` first (`cd android && ./gradlew …`), so a relative
        # path can be rooted anywhere. Fall back to the basename, which is what
        # a rename actually changes.
        return any(root.rglob(Path(value).name))
    leaf = value.rsplit(".", 1)[-1]
    return any(any(root.rglob(leaf + suffix)) for suffix in _JVM_SUFFIXES)


def _checkable(kind: str, value: str, root: Path) -> bool:
    """Is there source here to look in at all?

    **A missing file inside a directory that exists is a rename. A missing
    directory is a tree that was never here**, and the two must not report the
    same thing.

    Without this the validator silently acquired a dependency on the source
    tree: run it against a docs-only checkout and every automated test reports
    a broken command at once. Caught by `test_fleet_validate`, whose fixture
    copies `SNAPSHOT.yaml`, `docs/` and `tools/` and nothing else — **71 errors
    against a corpus that is valid**. A gate that fails that way teaches people
    to stop reading it, which is the failure ADR-0038 exists to end.
    """
    if kind == "path":
        parent = (root / value).parent
        return parent.is_dir()
    return any(any(root.rglob("*" + suffix)) for suffix in _JVM_SUFFIXES)


def resolve(command: str, root: Path) -> str:
    """RESOLVES / BROKEN / UNCHECKABLE for one command against one repo."""
    found = targets(command)
    if not found:
        return UNCHECKABLE
    checkable = [(k, v) for k, v in found if _checkable(k, v, root)]
    if not checkable:
        return UNCHECKABLE
    for kind, value in checkable:
        if not _exists(kind, value, root):
            return BROKEN
    return RESOLVES


def is_broken(command: str, root: Path) -> bool:
    """Only a target this can check, and which is missing, counts as broken."""
    return resolve(command, root) == BROKEN
