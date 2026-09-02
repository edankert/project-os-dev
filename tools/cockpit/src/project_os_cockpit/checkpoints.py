"""Per-turn checkpoints — an undo unit smaller than a session (FEAT-0078).

[[RISK-0006]]'s first hazard is **compounding judgment**: a wrong assumption at
hour one is the context of every decision after it, and unattended wrongness
compounds until somebody reads the digest. Today the only unit of undo is the
close-out commit — the whole session's work, or nothing.

A checkpoint per agent turn turns *"the worker went wrong somewhere in three
hours"* from an archaeology problem into a slider.

**Outside `refs/heads`, and outside every push path.** Checkpoints are local
safety, not history to publish: they live under ``refs/cockpit/turns/`` so a
branch listing, a `git push`, and the fleet roll-up's push action never see
them. Publishing is a person's deliberate act (FEAT-0055's line) and a
checkpoint is the opposite of deliberate — it is taken automatically, dozens of
times an hour.

**Untracked files are included.** An agent's damage is often a file it *added*,
and a checkpoint that captured only tracked changes would restore a tree still
carrying it.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
from pathlib import Path
from typing import Any

#: The namespace. Deliberately not under `refs/heads` or `refs/tags`: both are
#: pushed by default and shown by `git branch`, and a hundred turn refs in a
#: branch list is a tool nobody keeps.
REF_NAMESPACE = "refs/cockpit/turns"

#: Pruning, stated where it is set rather than in a config nobody reads.
#: A day of hard use is a few hundred turns; keeping the most recent 200 keeps
#: roughly that, and anything older has been superseded by a commit anyway.
MAX_CHECKPOINTS = 200

_TIMEOUT = 10.0


def _git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 — fixed argv, no shell
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=_TIMEOUT, check=check,
    )


def available(root: Path) -> bool:
    return (root / ".git").exists()


def capture(root: Path, *, label: str = "", session: str = "") -> dict[str, Any]:
    """Capture the working tree, including untracked files, as one ref.

    Uses a temporary index so the real one is untouched — an agent mid-`git
    add` must not have its staging area rewritten by a checkpoint it did not
    ask for. That is the difference between a safety net and a second actor.
    """
    if not available(root):
        return {"ok": False, "error": "not a git repository"}

    import os
    import tempfile

    env = dict(os.environ)
    with tempfile.TemporaryDirectory() as tmp:
        env["GIT_INDEX_FILE"] = str(Path(tmp) / "index")
        add = subprocess.run(  # noqa: S603
            ["git", "-C", str(root), "add", "-A", "--force", "."],
            capture_output=True, text=True, timeout=_TIMEOUT, check=False, env=env,
        )
        if add.returncode != 0:
            return {"ok": False, "error": add.stderr.strip()[:200]}
        tree = subprocess.run(  # noqa: S603
            ["git", "-C", str(root), "write-tree"],
            capture_output=True, text=True, timeout=_TIMEOUT, check=False, env=env,
        )
        if tree.returncode != 0:
            return {"ok": False, "error": tree.stderr.strip()[:200]}
        tree_sha = tree.stdout.strip()

    parent = _git(root, "rev-parse", "HEAD").stdout.strip()
    message = f"checkpoint: {label or 'turn'}" + (f" [{session}]" if session else "")
    args = ["commit-tree", tree_sha, "-m", message]
    if parent:
        args += ["-p", parent]
    made = _git(root, *args)
    if made.returncode != 0:
        return {"ok": False, "error": made.stderr.strip()[:200]}
    sha = made.stdout.strip()

    # **Sortable by name, to microseconds.** Git's `creatordate` has SECOND
    # granularity, and two checkpoints in the same second tie — which reversed
    # the timeline the first time it was rendered. For a "where did it go
    # wrong" slider, out-of-order turns are worse than no turns, so the order
    # lives in the ref name where it cannot tie.
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    ref = f"{REF_NAMESPACE}/{stamp}-{sha[:8]}"
    updated = _git(root, "update-ref", ref, sha)
    if updated.returncode != 0:
        return {"ok": False, "error": updated.stderr.strip()[:200]}
    prune(root)
    return {"ok": True, "sha": sha, "ref": ref, "label": label, "session": session}


def listing(root: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Checkpoints, newest first."""
    if not available(root):
        return []
    # Sort by REFNAME descending, not `creatordate`: the name carries a
    # microsecond stamp precisely because the date ties (see `capture`).
    out = _git(
        root, "for-each-ref", f"--count={limit}", "--sort=-refname",
        "--format=%(refname)%09%(objectname)%09%(creatordate:iso-strict)%09%(contents:subject)",
        REF_NAMESPACE,
    )
    rows: list[dict[str, Any]] = []
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        rows.append({
            "ref": parts[0], "sha": parts[1], "at": parts[2], "subject": parts[3],
        })
    return rows


def prune(root: Path, keep: int = MAX_CHECKPOINTS) -> int:
    """Drop the oldest refs beyond `keep`. Returns how many went."""
    rows = listing(root, limit=keep + 500)
    dropped = 0
    for row in rows[keep:]:
        if _git(root, "update-ref", "-d", row["ref"]).returncode == 0:
            dropped += 1
    return dropped


def turns(root: Path, limit: int = 50) -> list[dict[str, Any]]:
    """The turn timeline: each checkpoint with what changed since the one
    before it (TASK-0336).

    **Shares [[ISS-0096]]'s shape function rather than growing a second one.**
    "Which files, grouped by kind" is one question and it now has one answer;
    computing it a second way here is how the two would come to disagree about
    what counts as a test.

    Newest first, and each row describes the step *into* it — so reading down
    the list is reading the work backwards, which is how somebody looks for
    where a thing went wrong.
    """
    from .cockpit import _shape_kind

    rows = listing(root, limit=limit + 1)
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows[:limit]):
        parent = rows[i + 1]["sha"] if i + 1 < len(rows) else None
        files: list[str] = []
        if parent:
            diffed = _git(root, "diff", "--name-only", parent, row["sha"])
            files = [ln.strip() for ln in diffed.stdout.splitlines() if ln.strip()]
        kinds: dict[str, int] = {}
        for path in files:
            kind = _shape_kind(path)
            kinds[kind] = kinds.get(kind, 0) + 1
        out.append({
            **row,
            "files": len(files),
            "kinds": kinds,
            # No parent means the first checkpoint: there is nothing to diff
            # against, and reporting 0 files would read as "this turn did
            # nothing" rather than "we started measuring here".
            "from_start": parent is None,
        })
    return out


#: Identities that may never restore. ADR-0009 makes rewind principal-owned:
#: **a worker can never rewind itself.** A loop that can undo its own turns can
#: erase the evidence of having gone wrong, which is the one thing the
#: checkpoints exist to preserve.
WORKER_IDENTITIES: frozenset[str] = frozenset({"agent", "worker", "agent:worker"})


def restore(root: Path, sha: str, *, actor: str = "") -> dict[str, Any]:
    """Rewind the working tree to a checkpoint (TASK-0337).

    Two guards, and they are the feature:

    **Principal-owned.** A worker identity is refused as firmly as the server
    refuses an agent-owned transition (REQ-0026's shape, applied to rewind).
    ADR-0009 puts this judgment with the principal, and the reason is not
    ceremony: a loop that can undo its own turns can erase the evidence of
    having gone wrong.

    **A restore is never the end of a road.** The current state is captured
    *first*, so the thing being rewound away is itself recoverable. Without
    that, "restore" is a destructive verb wearing a safe name.
    """
    if not available(root):
        return {"ok": False, "error": "not a git repository"}
    who = (actor or "").strip().lower()
    if not who:
        return {"ok": False, "error": "restore needs an actor; rewind is principal-owned (ADR-0009)"}
    if who in WORKER_IDENTITIES or who.startswith("agent:") and who != "agent:principal":
        return {
            "ok": False,
            "error": (
                f"{actor!r} may not restore: rewind is principal-owned (ADR-0009). "
                "A worker that can undo its own turns can erase the evidence of "
                "having gone wrong."
            ),
        }

    target = _git(root, "rev-parse", "--verify", f"{sha}^{{commit}}")
    if target.returncode != 0:
        return {"ok": False, "error": f"no such checkpoint: {sha}"}
    resolved = target.stdout.strip()

    # Capture BEFORE rewinding. A restore that lost the state it replaced
    # would make this feature a way to destroy work rather than recover it.
    safety = capture(root, label=f"before restore to {resolved[:8]}", session=actor)
    if not safety.get("ok"):
        return {"ok": False, "error": f"refusing to restore: could not capture first ({safety.get('error')})"}

    applied = _git(root, "checkout", resolved, "--", ".")
    if applied.returncode != 0:
        return {"ok": False, "error": applied.stderr.strip()[:200]}
    return {
        "ok": True,
        "restored": resolved,
        "safety_checkpoint": safety["sha"],
        "actor": actor,
    }
