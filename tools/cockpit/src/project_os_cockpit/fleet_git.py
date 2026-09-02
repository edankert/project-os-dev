"""Publication state for a whole fleet, one JSON line per repo (TASK-0422).

``python -m project_os_cockpit.fleet_git <repo> [<repo> ...]``

Prints ``{root, ahead, remote, remote_kind, dirty}`` per line, from
:mod:`project_os_cockpit.git_state` — the module that already answers this
question for the sidecar's own repo.

**Why this exists.** The Electron shell needs the same answer for every
discovered workspace, live or cold, and until 2026-08-14 it got it by shelling
out to `git` itself in TypeScript (`desktop/src/ipc/git.ts`). That made
:doc:`FEAT-0100`'s claim — *one walk, so two surfaces cannot disagree* — false
of the code: the badge and History read `git_state.py` while the rail's
attention card and the fleet roll-up read an independent implementation on its
own clock. They agreed until one of them changed, and then one of them did:
the unknown-count repair of 2026-08-14 landed in Python only, and the card
went on rendering a count nobody could take as nothing owed. That is
[[ISS-0165]].

**Why not read the sidecar instead**, which is what the issue proposed: a
sidecar exists only for a workspace someone has **opened**. Answering from it
would give the open repo a good number and leave the other eleven blank, which
is [[ISS-0156]] with the sign flipped. The property that must survive is *one
clock for the whole fleet*; the property to gain is *one implementation*. A
batch the shell spawns on the clock it already has gives both.

**Serial, and cheap.** Two or three `git` invocations per repo against a dozen
repos, on a 60-second timer, in a subprocess — the cold validator on the same
shell does considerably more work every ten minutes. Nothing here builds an
index or reads a note, and this module deliberately imports `git_state` alone
rather than the cockpit, because import cost is paid on every tick.

**Read-only.** Like `fleet_validate`, this runs inside repositories this app
does not own. `git status`, `git remote`, `git rev-list`, `git log` — nothing
that writes, and a test asserts the argv rather than trusting this paragraph.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import git_state


def standing(project_root: Path) -> dict[str, object]:
    """One repo's publication state, in the shell's wire shape."""
    state = git_state.read_fresh(project_root)
    return {
        "root": str(project_root),
        # `null`, never 0, when there is no upstream to be ahead of. The whole
        # reason this module exists is that the distinction was being lost on
        # the way to the surfaces that render it (ADR-0027, admission test 4).
        "ahead": state.ahead,
        "remote": state.remote,
        "remote_kind": state.kind,
        "dirty": state.dirty,
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m project_os_cockpit.fleet_git <repo> [<repo> ...]",
              file=sys.stderr)
        return 2
    for raw in args:
        # One unreadable repo must not kill the batch — the same rule
        # `fleet_validate` follows, for the same reason: a fleet is a set of
        # other people's repositories and one of them is always mid-something.
        try:
            row = standing(Path(raw))
        except Exception as exc:  # noqa: BLE001 — a batch never dies on one repo
            row = {"root": raw, "ahead": None, "remote": None,
                   "remote_kind": "none", "dirty": 0, "error": str(exc)}
        print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
