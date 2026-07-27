---
type: "[[task]]"
id: TASK-0079
aliases: ["TASK-0079"]
title: "Propagate the design type to the fleet and migrate REF-0001"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["[[FEAT-0019]]"]
parent: "[[FEAT-0019]]"
effort: "S"
depends: ["[[TASK-0078]]"]
blocks: []
related: []
tests: []
---

# Propagate and migrate

## Definition of Done

- [x] Template-owned files synced to all 11 repos; every repo validates 0 errors
- [x] `generate-adapters.py --check` clean in every repo carrying it
- [x] project-os-cockpit's `REF-0001-Overview-Redesign-Dossier` becomes `DES-0001`, moved to `docs/designs/` with its 139KB asset
- [x] Every inbound `design:` link (FEAT-0040, FEAT-0041, PHASE-008, CHG-20260726) repointed, and no dangling reference remains
- [x] The cockpit's `_DESIGN_DIR_RE` path regex is replaced by type-based membership, or a follow-up records why not
- [x] The cockpit's own suite passes

## Steps

- [x] Sync template-owned files repo by repo, validating each
- [x] Migrate the note: new ID, new location, `type: "[[design]]"`, status set honestly
- [x] Repoint inbound links; grep for stragglers
- [x] Run the cockpit suite

## Notes

The migrated note's status is a real decision, not bookkeeping. The dossier was accepted and **built** — PHASE-008 shipped from it — so `implemented` is the honest value. Recording it as `accepted` would understate what happened, and `draft` would be false.

Watch the sweep. Propagation loops in this session have twice caused damage: one committed an unrelated non-project-os repo (Atelier-parser) because the guard was `[ -d .git ]` rather than a project-os marker. Guard on `tools/scripts/validate-docs.py` existing, and check `git status` per repo before committing.
