"""Validate repos with no running sidecar (FEAT-0028 / TASK-0249).

``python -m project_os_cockpit.fleet_validate <repo> [<repo> ...]``

Prints one JSON object per line — ``{root, state, errors, warnings,
checked_at, detail?}`` — where ``errors``/``warnings`` are counts, not
lists: the fleet badge and roll-up need a number and a state, and
shipping every violation for ten repos across a pipe would be a lot of
bytes nobody reads. Opening a workspace gets you the full report from
its own sidecar.

**Whose validator runs: the repo's own.** ``ValidationRunner``'s locate
order picked that in FEAT-0018 and said why — a repo's own copy honours
its own ``STATUSES.md``, and a repo that has deliberately pinned an
older template should not be marked drifting against a rule it has not
adopted. ``tools/scripts/validate-fleet.sh`` chooses the other way
("uses THIS repo's validate-docs.py for uniform semantics"), which is
right for a manual diagnostic where comparability is the point and
wrong for a badge, where a red mark the repo's own CI would not raise
is a false positive. This module deliberately reuses the runner rather
than re-deciding.

Serial by design. Ten validators at once is a visible stall on the
machine the user is working on, and these are repos nobody is looking
at — there is nothing to be gained by finishing sooner.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .validation import validate_repo


def summarise(project_root: Path) -> dict[str, object]:
    """One repo's validator state, counts only.

    Carries **which** validator produced it. The per-repo choice above is
    only defensible if the reader can see it was made: without this, a
    fleet of mixed template versions looks uniform, which is the
    assumption ISS-0026 was filed for (a bundled validator copy drifting
    silently from the template). `"repo"` means that repo's own
    `tools/scripts/validate-docs.py`; `"bundled"` means the cockpit's
    fallback, used for a repo that predates the validator.
    """
    from .validation import BUNDLED_VALIDATOR, ValidationRunner

    located = ValidationRunner(project_root).locate_validator()
    which = (None if located is None
             else "bundled" if located == BUNDLED_VALIDATOR else "repo")
    report = validate_repo(project_root)
    standing = git_standing(project_root)
    return {
        "validator": which,
        "ahead": standing["ahead"],
        "remote_kind": standing["remote_kind"],
        "root": str(project_root),
        "state": report.get("state"),
        "errors": len(report.get("errors") or []),
        "warnings": len(report.get("warnings") or []),
        "checked_at": report.get("checked_at"),
        **({"detail": report["detail"]} if report.get("detail") else {}),
        **({"digest": digest} if (digest := _digest_counts(project_root)) else {}),
    }


def _digest_counts(project_root: Path) -> dict[str, object] | None:
    """Since-you-looked numbers for a repo **nobody has open** (TASK-0419).

    The attention panel's cards were drawing on two sources with two different
    reaches: publication from the shell, which sees every discovered workspace,
    and the since-line from that project's own sidecar, which exists only for a
    workspace opened this session. Ten workspaces, one digest — so an unopened
    project got a card with a headline and no second line, an intermediate
    state nobody chose.

    This rides the batch that already runs rather than adding a process per
    repo. It costs one index build and one `git log` per repo per cold pass,
    beside the validator subprocess already being spawned for each.

    Returns None rather than a wrong answer: a repo with no ``docs/``, no git,
    or an unreadable watermark has nothing to say here, and saying nothing is
    what leaves the card honest.
    """
    docs_root = project_root / "docs"
    if not docs_root.is_dir():
        return None
    try:
        from .cockpit import digest_payload
        from .index import Index
        from .watermark import Watermark

        payload = digest_payload(
            project_root, Index.build(docs_root), Watermark(project_root).seen_at,
        )
    except Exception:  # noqa: BLE001 — one bad repo must not take the batch down
        return None
    if not payload.get("available"):
        return None
    return {
        "seen_at": payload.get("seen_at") or "",
        "transitions": payload.get("transition_count") or 0,
        "needs_you": payload.get("needs_you_count") or 0,
        "computed_at": payload.get("computed_at") or "",
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m project_os_cockpit.fleet_validate <repo> [...]",
              file=sys.stderr)
        return 2
    for raw in args:
        root = Path(raw).expanduser()
        try:
            line = summarise(root)
        except Exception as exc:  # never let one bad repo kill the batch
            line = {"root": str(root), "state": "unavailable",
                    "errors": 0, "warnings": 0, "checked_at": None,
                    "detail": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(line), flush=True)
    return 0




# ---- git standing (FEAT-0055 / TASK-0265) ----------------------------
#
# This section used to be the THIRD implementation of "what is unpublished"
# (TASK-0422 / ISS-0165): its own remote table, its own `rev-list`, its own
# handling of the missing upstream — beside `git_state.py` and beside
# `probeGitState` in the shell. Nobody read it: the shell computes these fields
# and deliberately discards them, because ISS-0156 moved the git question onto
# one fleet-wide clock. A rule that exists three times and is consumed twice
# has already stopped being a rule, so both names below now forward to the
# module that owns it.
#
# They keep their names and their shape. `python -m project_os_cockpit.
# fleet_validate` is a documented wire format, and other people's scripts do
# not care which module inside this package answered.

from . import git_state as _git_state

#: `backup` | `deploy` | `none`, from the URL rather than a setting — see
#: :func:`project_os_cockpit.git_state.remote_kind`, which owns the table and
#: the reasoning about why an unknown shape is *deploy*.
remote_kind = _git_state.remote_kind


def git_standing(project_root: Path) -> dict[str, object]:
    """How far ahead of its remote a repo is, and what kind of remote.

    ``ahead`` is None when there is no upstream to be ahead *of* — which
    is not the same as being up to date, and must not render as such.
    """
    state = _git_state.read_fresh(project_root)
    return {
        "ahead": state.ahead,
        "remote": state.remote,
        "remote_kind": state.kind,
    }


if __name__ == "__main__":
    raise SystemExit(main())
