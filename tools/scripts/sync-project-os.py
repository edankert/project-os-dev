#!/usr/bin/env python3
"""Manifest-driven project-os template sync with baseline divergence detection.

Replaces the blunt rsync sync: every template-owned file is compared against the
baseline (the template commit recorded in .project-os-sync at the last sync).

  target == new template version          -> up to date
  target missing                          -> copied (seed paths: only ever copied once)
  target == baseline version              -> safe fast-forward, overwritten
  target != baseline (locally modified)   -> SKIPPED and reported for hand-merge
                                             (--force overwrites template-owned only)
  'merge'-owned path, diverged            -> ALWAYS skipped, even with --force: real project
                                             content lives here and would be destroyed

Ownership per path comes from tools/sync/MANIFEST.yaml in the UPSTREAM template
(more specific path wins). After a non-dry run the upstream HEAD sha is recorded
in .project-os-sync as the next baseline, git hooks are reinstalled, and derived
adapter artifacts are regenerated (tools/scripts/generate-adapters.py).

Stdlib only. Usage: sync-project-os.py <path-to-upstream-project-os> [--dry-run] [--force] [--baseline SHA]
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = ".project-os-sync"


def parse_manifest(path):
    owners, excludes = {}, {}
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^paths:\s*$", line):
            section = "paths"
            continue
        if re.match(r"^excludes:\s*$", line):
            section = "excludes"
            continue
        if re.match(r"^\S", line):
            section = None
            continue
        m = re.match(r'^\s+"([^"]+)":\s*(\w[\w-]*)\s*(#.*)?$', line)
        if section == "paths" and m:
            owners[m.group(1)] = m.group(2)
            continue
        m = re.match(r'^\s+"([^"]+)":\s*\[(.*)\]\s*(#.*)?$', line)
        if section == "excludes" and m:
            excludes[m.group(1)] = re.findall(r'"([^"]+)"', m.group(2)) or [
                p.strip().strip("'") for p in m.group(2).split(",") if p.strip()
            ]
    return owners, excludes


def ownership_for(rel, owners):
    """Most specific manifest entry that covers rel (dirs end with '/')."""
    best, best_len = None, -1
    for path, owner in owners.items():
        if path.endswith("/"):
            if (rel + "/").startswith(path) and len(path) > best_len:
                best, best_len = owner, len(path)
        elif rel == path and len(path) > best_len:
            best, best_len = owner, len(path)
    return best


def excluded(rel, src_base, excludes):
    for base, patterns in excludes.items():
        if not (rel + "/").startswith(base):
            continue
        for part in rel[len(base):].split("/"):
            if any(fnmatch.fnmatch(part, pat) for pat in patterns):
                return True
    return False


def git_show(src_repo, sha, rel):
    """Bytes of rel at sha in the upstream repo, or None if unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(src_repo), "show", "%s:%s" % (sha, rel)],
            capture_output=True, check=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, OSError):
        return None


def read_state(root):
    path = root / STATE_FILE
    if not path.is_file():
        return {}
    state = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+):\s*\"?([^\"]*)\"?\s*$", line)
        if m:
            state[m.group(1)] = m.group(2)
    return state



def triage_divergence(current, new, base):
    """Why does this downstream file differ, and is --force safe?

    `DIVERGED` alone forces the operator to hand-diff before they can act, and
    it conflates two cases that want opposite responses: a fix made downstream
    and never pushed up (forcing destroys it, silently and permanently), versus
    a merely older copy (forcing is the correct fix and loses nothing).

    What this can decide mechanically is narrow, and the labels say only that:

      SUBSET         every downstream line exists upstream. --force is safe.
      LOCAL-CONTENT  N lines exist only downstream. --force discards them.
      CONFLICT       both sides moved since the baseline.
      UNKNOWN        no baseline recorded, so no claim is made.

    LOCAL-CONTENT deliberately does NOT say "push this upstream". Whether those
    lines are a valuable fix or stale prose is a judgement the tool cannot make
    -- the six repos carrying an older migrate-status-vocabulary.py have
    downstream-only lines that are simply an outdated docstring, and telling
    someone to upstream those would be confidently wrong. The tool reports the
    fact; the operator reads the diff.

    UNKNOWN is the same discipline: an inability to tell is not evidence either
    way, and a guess here would be worse than silence.
    """
    def lines(b):
        if b is None:
            return None
        return b.decode("utf-8", errors="replace").splitlines()

    cur_l, new_l = lines(current), lines(new)
    only_downstream = [ln for ln in cur_l if ln.strip() and ln not in new_l]

    if not only_downstream:
        return ("SUBSET", "every downstream line exists upstream; --force is safe")

    base_l = lines(base)
    n = len(only_downstream)
    sample = only_downstream[0].strip()
    if len(sample) > 56:
        sample = sample[:53] + "..."
    detail = "%d line(s) exist only downstream, e.g. %r" % (n, sample)

    if base_l is None:
        return ("UNKNOWN", "no baseline recorded. " + detail)
    if new_l != base_l:
        return ("CONFLICT", "both sides changed since the baseline. " + detail)
    return ("LOCAL-CONTENT", detail + " -- read them before forcing; --force discards them")



def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync project-os template-owned files with divergence detection.")
    ap.add_argument("src", help="Path to the upstream project-os template repo")
    ap.add_argument("--repo-root", default=".", help="Downstream repo root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true", help="Report actions without writing")
    ap.add_argument("--force", action="store_true", help="Overwrite locally diverged template-owned files")
    ap.add_argument("--baseline", default=None, help="Baseline template commit (default: from %s)" % STATE_FILE)
    args = ap.parse_args(argv)

    src = Path(args.src).resolve()
    root = Path(args.repo_root).resolve()
    if not (src / "tools" / "sync" / "MANIFEST.yaml").is_file():
        print("sync-project-os: no tools/sync/MANIFEST.yaml in upstream %s" % src, file=sys.stderr)
        return 2
    if src == root:
        print("sync-project-os: upstream and downstream are the same directory", file=sys.stderr)
        return 2
    owners, excludes = parse_manifest(src / "tools" / "sync" / "MANIFEST.yaml")
    baseline = args.baseline or read_state(root).get("baseline_sha") or None

    copied, updated, seeded, uptodate = [], [], [], []
    diverged, merge_pending, gone = [], [], []
    processed = set()

    def sync_file(rel, owner):
        if rel in processed:
            return
        processed.add(rel)
        src_file = src / rel
        target = root / rel
        new = src_file.read_bytes()
        if not target.is_file():
            (seeded if owner == "seed" else copied).append(rel)
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, target)
            return
        if owner == "seed":
            return  # seeded once; downstream owns it now
        current = target.read_bytes()
        if current == new:
            uptodate.append(rel)
            return
        base = git_show(src, baseline, rel) if baseline else None
        if base is not None and current == base:
            updated.append(rel)
            if not args.dry_run:
                shutil.copy2(src_file, target)
            return
        # --force covers template-owned files only. 'merge' paths are where real
        # project content lives (a repo's own PHASES.md, ROADMAP.md, SCHEMAS.md);
        # overwriting one destroys project data, so they are always left for a
        # hand-merge no matter what. This guard is load-bearing: without it a
        # forced sync replaced a downstream repo's real 15-phase registry with
        # the template's placeholder table.
        if args.force and owner != "merge":
            updated.append(rel + " (forced)")
            if not args.dry_run:
                shutil.copy2(src_file, target)
            return
        if owner == "merge":
            merge_pending.append(rel)
        else:
            label, hint = triage_divergence(current, new, base)
            diverged.append((rel, label, hint))

    # walk manifest-owned files as they exist upstream
    for rel_base, owner in sorted(owners.items()):
        if owner in ("project", "generated"):
            continue
        base_path = src / rel_base
        if rel_base.endswith("/"):
            if not base_path.is_dir():
                continue
            for f in sorted(p for p in base_path.rglob("*") if p.is_file()):
                rel = f.relative_to(src).as_posix()
                if ".git" in f.parts or excluded(rel, rel_base, excludes):
                    continue
                eff = ownership_for(rel, owners)
                if eff in ("project", "generated"):
                    continue
                sync_file(rel, eff)
            # deletions: downstream files under a template dir that upstream no longer ships
            tgt_dir = root / rel_base
            if owner == "template" and tgt_dir.is_dir():
                for f in sorted(p for p in tgt_dir.rglob("*") if p.is_file()):
                    rel = f.relative_to(root).as_posix()
                    if ".git" in f.parts or excluded(rel, rel_base, excludes):
                        continue
                    if ownership_for(rel, owners) == "template" and not (src / rel).is_file():
                        gone.append(rel)
        elif base_path.is_file():
            sync_file(rel_base, owner)

    prefix = "[dry-run] " if args.dry_run else ""
    print("%ssync-project-os: %d copied, %d updated, %d seeded, %d up-to-date (baseline: %s)" % (
        prefix, len(copied), len(updated), len(seeded), len(uptodate), baseline or "none"))
    for rel in copied + updated + seeded:
        print("%s  synced  %s" % (prefix, rel))
    if diverged:
        print("%sACTION REQUIRED — locally diverged template-owned files:" % prefix)
        # Ordered so the destructive case is read first: PUSH-UPSTREAM is the one
        # where --force loses work.
        rank = {"LOCAL-CONTENT": 0, "CONFLICT": 1, "UNKNOWN": 2, "SUBSET": 3}
        for rel, label, hint in sorted(diverged, key=lambda d: (rank.get(d[1], 9), d[0])):
            print("%s  %-14s %s" % (prefix, label, rel))
            print("%s                 %s" % (prefix, hint))
        risky = [rel for rel, label, _ in diverged if label != "SUBSET"]
        if risky:
            print("%s  --force overwrites all of the above. Only SUBSET is provably safe; read the rest first." % prefix)
    if merge_pending:
        print("%sExpected-divergence (merge-owned) files left alone (--force does not touch these) — merge upstream changes by hand if relevant:" % prefix)
        for rel in merge_pending:
            print("%s  MERGE  %s" % (prefix, rel))
    if gone:
        print("%sUpstream no longer ships (left in place; remove manually if obsolete):" % prefix)
        for rel in gone:
            print("%s  GONE  %s" % (prefix, rel))

    if not args.dry_run:
        try:
            sha = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"],
                                 capture_output=True, check=True, text=True).stdout.strip()
        except (subprocess.CalledProcessError, OSError):
            sha = ""
        if sha:
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
            (root / STATE_FILE).write_text(
                'baseline_sha: "%s"\nsynced: "%s"\nsource: "%s"\n' % (sha, stamp, src), encoding="utf-8")
        for cmd in (["bash", str(root / "tools" / "scripts" / "install-git-hooks.sh")],
                    ["python3", str(root / "tools" / "scripts" / "generate-adapters.py"),
                     "--repo-root", str(root), "--install-hooks"]):
            if Path(cmd[1]).is_file():
                r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
                if r.returncode != 0:
                    print("WARN: %s failed: %s" % (Path(cmd[1]).name, (r.stderr or r.stdout).strip()[:200]))

    print("%sSync complete. Review changes, run bash tools/scripts/validate-docs.sh, then tools/skills/snapshot-sync/SKILL.md for anything it reports." % prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
