---
type: "[[task]]"
id: TASK-0204
aliases: ["TASK-0204"]
title: "validate-docs.sh --as-committed copies HEAD into a folder with the repo's own name, so a repo whose plugin name falls back to its folder name passes there as it does in CI"
status: done
phase: ""
owner: user:edwin
created: 2026-10-16
updated: 2026-10-16
source: ["[[FEAT-0041-Project-Os-Mod]]"]
parent: "[[FEAT-0041-Project-Os-Mod]]"
effort: "XS"
due: ""
depends: ["[[TASK-0199-The-Mod-Reaches-Every-Repo-Through-The-Template-Sync]]"]
blocks: []
related: []
tests: []
---

# The committed-state check copies the repo under its own folder name

Before pushing the template on 2026-10-16, `bash tools/scripts/validate-docs.sh --as-committed` failed in `~/Dev/repos/project-os` with `generate-adapters: STALE .claude-plugin/marketplace.json`. Nothing was missing from the commit.

The cause is in TASK-0199's naming. The plugin's registration name is `project-os-<project>`, taken from `project.name` in `SNAPSHOT.yaml`. The template's own snapshot still says "REPLACE ME", so the generator falls back to the repo's folder name, `project-os`. The committed-state check unpacks HEAD into a folder `mktemp -d` names, such as `tmp.342MebW40A`. There the generator expects `project-os-tmp-342mebw40a`, so the committed `project-os-project-os` looks stale. GitHub's CI checks out into a folder named after the repository, so CI itself is not affected; only the local check before a push gives the wrong answer.

The check's own promise is to see HEAD "as a fresh clone would see it". A fresh clone is a folder named after the repo. So the fix is in the check: it unpacks HEAD into `<temporary folder>/<repo folder name>` instead of into the temporary folder itself.

## Definition of Done

- [x] `validate-docs.sh --as-committed` unpacks HEAD under a subfolder named like the repo's folder, and still removes the whole temporary folder on exit.
- [x] In `~/Dev/repos/project-os`, `--as-committed` passes on HEAD; with the fix reverted it fails with the STALE line above.
- [x] Synced into project-os-dev and project-os-cockpit.

## Result

Fixed in project-os d813929. In `~/Dev/repos/project-os`, `--as-committed` failed before the fix with the STALE line and passes after it. The new case in `test-plugin-registration.py` runs the real check on a fixture repo whose snapshot says "REPLACE ME"; it passes with the fix and fails with `STALE .claude-plugin/marketplace.json` when the old `validate-docs.sh` is restored. The template's other script tests are unchanged: 32 pass, and the two that fail are ISS-0107's. Synced here and into project-os-cockpit.
