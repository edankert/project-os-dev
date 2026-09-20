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


def drift_for(repo, rels):
    """(stale, missing) for one repo: template-owned files that differ or are absent."""
    stale, missing = [], []
    for rel in rels:
        target = repo / rel
        if not target.is_file():
            missing.append(rel)
        elif target.read_bytes() != (TEMPLATE / rel).read_bytes():
            stale.append(rel)
    return stale, missing


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
        stale, missing = drift_for(repo, rels)
        if not stale and not missing:
            if not args.quiet:
                print("ok    %-28s %d template-owned file(s) match" % (repo.name, len(rels)))
            continue
        drifted += 1
        print("DRIFT %-28s %d stale, %d missing" % (repo.name, len(stale), len(missing)))
        for rel in stale:
            print("        stale   %s" % rel)
        for rel in missing:
            print("        missing %s" % rel)

    print("fleet-file-drift: %d repo(s) checked, %d drifted, %d template-owned file(s) compared"
          % (len(repos), drifted, len(rels)))
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
