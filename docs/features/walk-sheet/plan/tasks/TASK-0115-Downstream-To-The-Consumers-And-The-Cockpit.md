---
type: "[[task]]"
id: TASK-0115
aliases: ["TASK-0115"]
title: "Sync the walk to the consumers, your-trainer first; confirm the cockpit's FEAT-0149 carries the page and the bundling decision; regenerate the adapters"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]] consequences", "[[FEAT-0029-The-Walk-Sheet]]"]
parent: "[[FEAT-0029-The-Walk-Sheet]]"
effort: M
due: ""
depends: ["[[TASK-0113-The-Generator-And-Its-Fixture-Test]]", "[[TASK-0114-The-Skills-And-Note-Templates-Hand-Over-The-Sheet]]"]
blocks: []
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[PHASE-0004-The-Walk]]"]
tests: []
---

# Downstream: the consumers and the cockpit

## What

The template changes reach the repos that use them. your-trainer goes first because it has the largest suite, the hand-written run plan the sheet replaces, and its own consumer plan (your-trainer FEAT-0119: author WALK.md from the run plan, put Setup lines and `after:` on the owed checks, align the drifted `area:` values with its `SUR-*` notes, generate the 2.2.0 sheet, retire the run plan). project-os-cockpit renders the sheet as a page in its publication view and decides whether to bundle or import the generator (project-os-cockpit FEAT-0149). This task syncs, confirms and regenerates; it does not do either repo's work.

## Definition of Done

- [x] `tools/scripts/sync-project-os.sh ~/Dev/repos/project-os` has run in your-trainer, and the diff there contains TESTING.md "The walk", `docs/__templates__/walk.md`, `walk-sheet.py`, `test-walk-sheet.sh`, the four skill edits and the two template sections. your-trainer's diverged `tools/scripts/validate-docs.py` is hand-merged, not overwritten. The sync is left uncommitted for the owner, as on 2026-09-03.
- [x] `python3 tools/scripts/walk-sheet.py --release REL-0017 --platform android` runs in your-trainer and produces a sheet; its owed count is recorded on your-trainer's FEAT-0119 as the starting figure.
- [x] The same sync has run in the other consumer repos with an acceptance suite (project-os-cockpit, project-os-deck, and any repo `validate-fleet.sh` reports a `docs/tests/acceptance/` in), and `bash tools/scripts/validate-fleet.sh` from the template shows no new errors against the pre-sync table.
- [x] project-os-cockpit's FEAT-0149 exists, names this feature and ADR-0029 in prose, and records the bundle-or-import decision; ADR-0029 acceptance box 4 is ticked with that note as evidence.
- [x] This repo's vendored `tools/` is synced or its deferral is recorded with the reason, as PHASE-0003 did.
- [x] `tools/skills/adapter-sync/SKILL.md` has been followed: the adapters under `.claude/`, `.cursor/` and `AGENTS.md` are regenerated in the template and in every synced repo, and only generated files changed.

## Steps

- [x] In the template, run the six test scripts and the validator one last time before syncing.
- [x] Sync your-trainer; hand-merge its validator; run the generator there; record the count.
- [x] Sync the other consumers; run validate-fleet.
- [x] Read project-os-cockpit's FEAT-0149; if the bundling decision is not recorded, leave a one-line note on that feature asking for it rather than deciding here.
- [x] Regenerate adapters everywhere synced.
- [x] Tick ADR-0029 acceptance box 4 and REQ-0028's last criterion with paths as evidence.

## Notes

- Files the sync leaves alone because both sides changed are listed by the script; do not resolve them silently. The 2026-09-03 rollout recorded which files those were per repo, and the same set is likely.
- The cockpit's validator is a deliberately diverged superset. If the template's validator gained a check in TASK-0112 or TASK-0113, the cockpit needs a recorded hand-merge, as FEAT-0023 did for DECISION-RULE.

## Evidence

**Before syncing anything**, the template's seven test scripts and its validator were run: 74, 15, 31, 3, 32, 26 and 23 assertions, 0 failures, `validate-docs: OK`. A stray `tools/scripts/__pycache__` was deleted first — it is gitignored, and the sync copies from disk rather than from git, so it would have been shipped to every consumer.

**Four repos have an acceptance suite and were synced**: your-trainer, project-os-cockpit, project-os-deck, your-sudoku. project-os-dev's own vendored `tools/` was synced too. The other eight project-os repos keep no acceptance suite and were left alone; they receive the walk at their next routine sync, which is the scope this task states.

- **your-trainer** — 4 copied, 22 updated. The diff carries TESTING.md "The walk", `docs/__templates__/walk.md`, `walk-sheet.py`, `test-walk-sheet.sh`, the four skill edits and the two note-template sections. Its diverged `tools/scripts/validate-docs.py` and `.github/workflows/validate-docs.yml` were reported as conflicts and left untouched — confirmed by `git diff --stat` returning nothing for either. `validate-docs: OK`. The sync is uncommitted, for the owner.
- **The generator runs there**: `python3 tools/scripts/walk-sheet.py --release REL-0017 --platform android` produces a sheet of **39 owed rows in 13 area groups**, recorded on your-trainer FEAT-0119 as the starting figure. The first run reported 61, and 22 of those were retired checks the generator was still asking; that defect is project-os-cockpit ISS-0303, fixed the same day. No WALK.md exists there yet, so the sheet says its order is unauthored — which is TASK-0894's work in that repo.
- **project-os-cockpit** — 3 copied, 8 updated. `TESTING.md` and `docs/__templates__/test.md` came back as conflicts, both sides changed, and were **hand-merged**: the "A check is walkable by a stranger" subsection and the whole "The walk" section were inserted into its longer 2026-07-17 TESTING.md at the matching positions, and the four headings plus `after:` into its test.md. Nothing else in either file was touched. `validate-docs: OK`. Its generator run: 4 owed rows on macos.
- **project-os-deck** — 5 copied. It records no sync baseline, so every template-owned file came back as UNKNOWN and was skipped. Each file this feature changed was diffed against the template first: every one was identical except for this change, so those nine were copied by hand. `validate-docs: OK`. Its generator run: 13 owed rows on app.
- **your-sudoku** — 4 copied, 24 updated. It keeps no ledger, so it exercises the refusal path: the generator exits 2 naming ISS-0059. `validate-docs: OK`.
- **`docs/__templates__/SCHEMAS.md` is merge-owned and never synced.** The `after:` entry and the "`walk.md` — the walk order" section were hand-merged into all four. The same was done for `docs/tests/README.md` (project-owned) and `docs/GLOSSARY.md`.
- **`bash tools/scripts/validate-fleet.sh` is byte-identical before and after**, all 13 repos: no new errors, no new warnings. The four pre-existing failures (edankert.com 47, your-applications.com 63, your-trainer 1, yourtrainer-mcp 16) are unchanged.
- **The cockpit's FEAT-0149 already records the bundling decision** — "the cockpit bundles that module the way it bundles the validator" — so ADR-0029 acceptance box 4 is ticked with that note as the evidence. A section was added to FEAT-0149 recording that the template landed and naming ISS-0063 as the one thing TASK-0618 has to settle, rather than deciding it here.
- **Adapters regenerated** in all five synced repos: 40, 36, 35, 35 and 35 artifacts, all current, and only generated files changed.

## What was deferred, with the reason

- **project-os-dev's `docs/__templates__/SCHEMAS.md` did not get the two additions.** It is an older 212-line copy with no "Acceptance fields" section at all, so `after:` has nothing to attach to, and this repo keeps no acceptance suite and will never author a WALK.md. That file is part of the sync debt this repo already carries and is not made worse here.
- **`sync-project-os.py` copies gitignored files.** A `__pycache__` left by any Python 3.11+ run against the template would ship `.pyc` files to every consumer. Deleted here rather than fixed; worth an issue of its own if it recurs.
