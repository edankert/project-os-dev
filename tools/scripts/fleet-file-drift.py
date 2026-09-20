#!/usr/bin/env python3
"""Fleet file drift: which template-owned files in the fleet no longer match the template.

The sync reports drift for the one repo it is run in. Nothing reported it across
the fleet, so a template-owned file could sit stale in eleven repos with every
check green. That happened on 2026-09-20: `review-budget.py` was fixed in the
template and reached two repos, while an independent review had just declared
the fleet identical on the strength of one `md5` of `independent-review/SKILL.md`
-- a file the sync always carries. The file that enforced the review budget was
never compared (project-os-dev FEAT-0034, TASK-0146).

Ownership comes from `tools/sync/MANIFEST.yaml`, so this check covers whatever
the manifest calls `template` and needs no list of its own. `merge` and `seed`
paths are expected to diverge and are not reported. A file missing downstream is
drift too: the sync would have copied it.

**A repo may diverge on purpose**, and says so in its `.project-os-sync` under
`keep_local:`, with a reason per line. Those files are reported as kept, not as
drift, and do not fail the run -- reporting a recorded decision as a problem
buries the one file that really is stale. A kept file that now MATCHES the
template is reported too, the other way round: its exception has nothing left to
protect and the line can go.

**Not `fleet-drift.py`**, which project-os-cockpit has carried since 2026-08-29.
That one asks which validator *rules* each repo runs and reports line divergence;
this one asks which template-owned *files* differ, byte for byte. Two questions,
two scripts, and the names must stay apart: `tools/scripts/` is template-owned,
so a file named `fleet-drift.py` here would overwrite the cockpit's at the next
sync.

Usage: fleet-file-drift.py [--fleet-root DIR] [--repo DIR]... [--quiet]
Exit 1 when any repo has drifted, 0 when the fleet matches.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent.parent


def _sync_module():
    """Reuse the sync's manifest parser, so ownership is read one way only."""
    spec = importlib.util.spec_from_file_location("_pos_sync", HERE / "sync-project-os.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def template_files(sync, owners, excludes):
    """Every template-owned file in this template, as repo-relative paths."""
    out = []
    for path in sorted(TEMPLATE.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(TEMPLATE).as_posix()
        if rel.startswith(".git/") or sync.excluded(rel, TEMPLATE, excludes):
            continue
        if sync.ownership_for(rel, owners) == "template":
            out.append(rel)
    return out


def drift_for(repo, rels, kept_paths):
    """One repo's template-owned files, split four ways.

    stale/missing are drift. kept/moot are the `keep_local:` decisions: kept is
    diverging as intended, moot is an exception whose file now matches anyway.
    """
    stale, missing, kept, moot = [], [], [], []
    for rel in rels:
        target = repo / rel
        deliberate = rel in kept_paths
        if not target.is_file():
            (kept if deliberate else missing).append(rel)
        elif target.read_bytes() != (TEMPLATE / rel).read_bytes():
            (kept if deliberate else stale).append(rel)
        elif deliberate:
            moot.append(rel)
    return stale, missing, kept, moot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-root", default=str(TEMPLATE.parent),
                    help="Directory holding the repos (default: the template's parent)")
    ap.add_argument("--repo", action="append", default=[],
                    help="Check only this repo; repeatable. Overrides --fleet-root.")
    ap.add_argument("--quiet", action="store_true", help="Print only the repos that drifted")
    args = ap.parse_args()

    sync = _sync_module()
    manifest = TEMPLATE / "tools" / "sync" / "MANIFEST.yaml"
    if not manifest.is_file():
        print("fleet-file-drift: no tools/sync/MANIFEST.yaml in %s" % TEMPLATE, file=sys.stderr)
        return 2
    owners, excludes = sync.parse_manifest(manifest)
    rels = template_files(sync, owners, excludes)

    if args.repo:
        repos = [Path(r).resolve() for r in args.repo]
    else:
        root = Path(args.fleet_root).resolve()
        repos = sorted(p.parent for p in root.glob("*/SNAPSHOT.yaml"))
    repos = [r for r in repos if r != TEMPLATE]

    drifted = 0
    for repo in repos:
        kept_paths = set(sync.read_state(repo).get("keep_local") or [])
        stale, missing, kept, moot = drift_for(repo, rels, kept_paths)
        if stale or missing:
            drifted += 1
            print("DRIFT %-28s %d stale, %d missing" % (repo.name, len(stale), len(missing)))
            for rel in stale:
                print("        stale   %s" % rel)
            for rel in missing:
                print("        missing %s" % rel)
        elif not args.quiet:
            print("ok    %-28s %d template-owned file(s) match" % (repo.name, len(rels) - len(kept)))
        if kept and not args.quiet:
            print("      kept    %-22s %d file(s) this repo keeps different on purpose (.project-os-sync)"
                  % (repo.name, len(kept)))
            for rel in kept:
                print("        kept    %s" % rel)
        for rel in moot:
            print("      MOOT  %-22s keep_local: %s now matches the template; the line can go"
                  % (repo.name, rel))

    print("fleet-file-drift: %d repo(s) checked, %d drifted, %d template-owned file(s) compared"
          % (len(repos), drifted, len(rels)))
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
