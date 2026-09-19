---
type: "[[task]]"
id: TASK-0134
aliases: ["TASK-0134"]
title: "The sync fast-forwards stale copies"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
effort: "Medium"
due: ""
depends: []
blocks: []
related: []
tests: [TST-0016]
---

# The sync fast-forwards stale copies

## Definition of Done
- [x] `sync-project-os.py` fast-forwards a file that equals any earlier template version of it, and reports it as updated from an older version.
- [x] MANIFEST: `LLM_BRIEF.md`, `SECURITY.md`, `docs/INDEX.md` and `docs/README.md` are seed files; `.github/workflows/` is project-owned, except `validate-docs.yml`.
- [x] A repo can list files it keeps on purpose under `keep_local:` in `.project-os-sync`. The sync reports them as kept and preserves the list when it rewrites the file.
- [x] A fixture test covers the stale fast-forward, a real local edit that is still reported, and a kept file.
- [x] Every fleet repo is re-synced and committed by named paths, with no uncommitted work of anyone else's in the commit.

## Outcome, 2026-09-18
project-os `9da6c83`, test-sync-stale.sh (12 assertions). Two fleet re-syncs followed, one per repo per sync, each committing only the files it changed and overwriting no dirty file. The stale copies fast-forwarded in every repo; your-sudoku, your-health and obsidian-supernote-sync have nothing left diverged. `keep_local:` is used for your-trainer's and project-os-dev's `validate-docs.yml` and for project-os-cockpit's `run-tests.py`, `validate-docs.py` and `test-ledger-checks.sh`, each with its reason in the file.

## Later, 2026-09-19

The cockpit's `keep_local:` no longer lists `validate-docs.py` or `test-ledger-checks.sh`: both became the template's through ISS-0068. It lists `run-tests.py`, and from 2026-09-19 `docs/__templates__/feature.md` (TASK-0142). Noted after the FEAT-0037 review.
