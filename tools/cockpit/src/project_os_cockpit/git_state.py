"""What a repo has that its remote does not (TASK-0417).

**This is the only implementation** (TASK-0422 / [[ISS-0165]]). It answers for
the sidecar's own repo, because the obligation registry lives here and a badge
cannot count what the process serving it cannot see; and it answers for every
workspace in the fleet, through `fleet_git`, which the Electron shell spawns on
its own clock. Until 2026-08-14 the shell asked `git` itself in TypeScript and
`fleet_validate` asked a third time in Python, so *"one walk, so two surfaces
cannot disagree"* — the property [[FEAT-0100]] and [[FEAT-0089]] both claim —
was asserted in the notes and false of the code.

What still exists in two languages, deliberately, is the remote
**classification**: `git.ts` re-derives it because that module runs `git push`
and will not trust over IPC an answer that decides whether a live website gets
deployed. What must not exist twice is the *rule*, so the table below and its
counterpart in `git.ts` are asserted against the same set of URLs in both
suites.

`ahead` is None when there is no upstream to be ahead **of**, which is not the
same as being up to date and must never render as such (ADR-0027 test 4:
absent-at-zero means an unknown count is indistinguishable from nothing owed,
so "I cannot tell" may not be reported as a number).
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

#: Hosts whose remotes are a backup/forge rather than a deployment.
FORGE_HOSTS = ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org")

#: How long a reading stays fresh. The registry is walked on every nav change,
#: and `git log` per keystroke would be a subprocess storm; a commit is not
#: news for a few seconds.
CACHE_SECONDS = 10.0

#: Unpushed commits are read for their subjects, not only counted, because the
#: obligation's rows ARE the commits (ADR-0020: an obligation lives with its
#: subject).
#:
#: **Deliberately uncapped.** A cap was written here first and removed the same
#: hour: the registry's invariant is that a count IS the length of its rows —
#: that is the whole repair TASK-0416 made — and a capped list with a separate
#: total reintroduces exactly the disagreement it removed, in the one place a
#: reader would never think to check. `git log` over a few hundred commits is
#: milliseconds, and the 5s timeout bounds the pathological case.


def remote_kind(url: str) -> str:
    """``backup`` | ``deploy`` | ``none``, from the URL rather than a setting.

    This decides whether anything may push automatically, so it is derived and
    not configured: a setting can be wrong, and being wrong here means
    deploying a website. Unknown shapes are **deploy** — the safe default for
    "I do not recognise this" is "do not publish to it".
    """
    u = (url or "").strip()
    if not u:
        return "none"
    lowered = u.lower()
    for host in FORGE_HOSTS:
        if f"//{host}/" in lowered or f"@{host}:" in lowered:
            return "backup"
    return "deploy"


@dataclass(frozen=True)
class Commit:
    """One unpublished commit — the subject of a publication obligation."""

    sha: str
    subject: str
    when: str


@dataclass(frozen=True)
class GitState:
    remote: str | None
    kind: str                       # backup | deploy | none
    ahead: int | None
    commits: tuple[Commit, ...]     # newest first, uncapped (see read())
    #: Notes changed and not committed — the rung BELOW "saved but not
    #: published", and scoped to :data:`RECORD_SCOPE` for the same reason
    #: History's band is: two numbers behind one word on two surfaces
    #: describing one project is the defect this feature kept finding.
    #:
    #: Zero when git cannot answer. Unlike ``ahead`` there is no unknown to
    #: distinguish: `git status` fails only when the repo does, and a repo
    #: that cannot be read has no publication row to be wrong about.
    dirty: int = 0


#: What counts as *the record* when asking whether work is uncommitted.
RECORD_SCOPE: tuple[str, ...] = ("docs/", "SNAPSHOT.yaml")

_EMPTY = GitState(remote=None, kind="none", ahead=None, commits=(), dirty=0)

_cache: dict[str, tuple[float, GitState]] = {}


def _git_raw(project_root: Path, *args: str) -> str | None:
    """git's stdout, **unstripped** — porcelain codes live in column 1.

    ``git status --porcelain`` writes ` M path` for a modified-not-staged
    file, so stripping the output eats the first line's status code and
    shifts its path by one character. Every other caller wants the strip,
    which is why it lives in :func:`_git` rather than here.
    """
    try:
        proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["git", "-C", str(project_root), *args],
            capture_output=True, text=True, timeout=5.0, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _git(project_root: Path, *args: str) -> str | None:
    out = _git_raw(project_root, *args)
    return out.strip() if out is not None else None


def dirty_paths(
    project_root: Path, scope: tuple[str, ...] | list[str] = RECORD_SCOPE,
) -> tuple[tuple[str, str], ...]:
    """``(code, path)`` per uncommitted file in ``scope``, newest walk.

    One walk for two consumers: History's band decorates these rows with the
    note each path resolves to, and the fleet card counts them. They were two
    walks with two copies of the rename handling until TASK-0422 — the same
    shape as the `ahead` duplication one number to the right.

    Failure is silent and empty: an absent or slow git means no rows, never a
    broken page.
    """
    raw = _git_raw(project_root, "status", "--porcelain", "--", *scope)
    if raw is None:
        return ()
    out: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2].strip(), line[3:].strip()
        # Renames read `old -> new`; the new path is the one that exists.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        out.append((code, path.strip('"')))
    return tuple(out)


def read(project_root: Path, *, now: float | None = None) -> GitState:
    """Publication state for one repo, cached for :data:`CACHE_SECONDS`."""
    key = str(project_root)
    stamp = time.monotonic() if now is None else now
    hit = _cache.get(key)
    if hit is not None and stamp - hit[0] < CACHE_SECONDS:
        return hit[1]

    state = _read_uncached(project_root)
    _cache[key] = (stamp, state)
    return state


def read_fresh(project_root: Path, *, now: float | None = None) -> GitState:
    """Publication state for one repo, ignoring (and refreshing) the cache.

    :data:`CACHE_SECONDS` exists because the registry is walked on every nav
    change inside a long-lived server, where a commit is not news for a few
    seconds. A one-shot process — `fleet_validate`, `fleet_git`, the shell's
    60-second pass — has no such storm to damp, and a cached answer there
    would mean a reading older than the process asking for it.
    """
    stamp = time.monotonic() if now is None else now
    state = _read_uncached(project_root)
    _cache[str(project_root)] = (stamp, state)
    return state


def clear_cache() -> None:
    """Drop every cached reading — for tests, and for a workspace that moved."""
    _cache.clear()


def _read_uncached(project_root: Path) -> GitState:
    if not (project_root / ".git").exists():
        return _EMPTY

    # Before the remote is classified, because a repo with nowhere to publish
    # can still have work in flight — and that rung of the ladder is the one
    # thing such a repo CAN be told about.
    dirty = len(dirty_paths(project_root))

    url = _git(project_root, "remote", "get-url", "origin")
    if url is None:
        # No `origin`, but there may be another remote — and if it is a deploy
        # target, that is exactly what the caller needs to know.
        first = (_git(project_root, "remote") or "").splitlines()
        url = _git(project_root, "remote", "get-url", first[0]) if first else None
    kind = remote_kind(url or "")
    if kind == "none":
        # Nothing to be ahead of. A different and worse fact than "nothing to
        # publish", and it keeps its own shape rather than reporting zero.
        return GitState(remote=None, kind="none", ahead=None, commits=(), dirty=dirty)

    counted = _git(project_root, "rev-list", "--count", "@{u}..HEAD")
    try:
        ahead = int(counted) if counted is not None else None
    except ValueError:
        ahead = None
    if not ahead:
        return GitState(remote=url, kind=kind, ahead=ahead, commits=(), dirty=dirty)

    # `%x1f` (unit separator) rather than a printable delimiter: a commit
    # subject may contain any of them, and splitting on `|` would truncate the
    # one commit whose message explained something.
    raw = _git(
        project_root, "log", "@{u}..HEAD", "--format=%h%x1f%s%x1f%cs",
    ) or ""
    commits: list[Commit] = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        commits.append(Commit(sha=parts[0], subject=parts[1], when=parts[2]))
    return GitState(
        remote=url, kind=kind, ahead=ahead, commits=tuple(commits), dirty=dirty,
    )
