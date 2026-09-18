---
type: "[[task]]"
id: TASK-0131
aliases: ["TASK-0131"]
title: "Roll out and measure five reviews"
status: backlog
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Medium"
due: ""
depends: [TASK-0129, TASK-0130]
blocks: []
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]", "[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
tests: []
---

# Roll out and measure five reviews

## Definition of Done
- [ ] ADR-0047 is accepted, or Edwin has said to roll this out without it.
- [ ] The template changes are synced to `your-trainer` and `project-os-cockpit`, together with the cockpit's `QUALITY.md`, which is two months behind. The cockpit's `.claude/agents/independent-reviewer.md` is re-copied by hand and the hook is installed in both repos.
- [ ] **Sonnet trial.** The next three small reviews run on Sonnet. Each has an Opus review of the same packet to compare against. Sonnet is kept for small features only if it missed nothing the Opus review marked *refuted*. The result is recorded here.
- [ ] **Five measured reviews.** The next five `your-trainer` feature reviews are measured with the reference note's query. The numbers go into PHASE-0007: median tool calls, minutes, total context tokens, and whether any review hit the limit.
- [ ] The acceptance targets in FEAT-0034 are met, or the gap is recorded with what to change.

## Steps
- [ ] Run `tools/scripts/sync-project-os.sh` in each repo and review the diff before committing.
- [ ] Run the trial and the measurements as the reviews happen. Nothing needs scheduling, because they are normal feature reviews.

## Notes
- The other nine fleet repos get this at their next sync. That is not part of this task.

## Progress, 2026-09-18
- ADR-0047 is accepted.
- **The sync is done**, as a partial sync of only the files this work changed: your-trainer `5b317fb4`, project-os-cockpit `f120f35`, including the cockpit's `QUALITY.md`. Neither repo's `.project-os-sync` baseline moved. A full sync of the cockpit still needs a hand-merge of `TESTING.md`, `test-walk-sheet.sh`, `validate-docs.py` and `walk-sheet.py`, which is outside this task.
- **Still to do:** the Sonnet trial (now one pair per packet), and measuring five real reviews. The FEAT-0034 targets are now per pair: see its Acceptance.

## Fleet rollout, 2026-09-18

Edwin, 2026-09-18: "Is this up-streamed and down-streamed to all projects?", then "go ahead". **Every fleet repo now carries the rules**: the packet script, the budget hook registered in `.claude/settings.json`, the review skill, and the validator checks. Each was checked after its commit: validator green, generated adapters current, and uncommitted work unchanged. Nothing is pushed.

| Repo | How | Commits |
|---|---|---|
| your-trainer, project-os-cockpit | partial sync, earlier today | `5b317fb4`, `9919145b`; `f120f35`, `67ddc77` |
| your-sudoku, project-os-dev, project-os-deck, articles, obsidian-supernote-sync, project-os-bench | full sync | `2a584ab`/`b7afae2`, `bb04c41`/`453ef29`, `fa2ac5f`/`479025e`, `ed041d8`/`80b3f10`, `a9e31a7`/`c5a204b`, `56ba3dd`/`b9a6288` |
| your-health | full sync | `8d9dda5` |
| edankert.com, your-applications.com, yourtrainer-mcp | full sync, validator kept | `c0b92ba`, `dc4440f`, `488bbbb` |

- **The full syncs also brought the Codex adapter** the template now ships.
- **In the last three repos the validator stayed at their previous version (upstream `59bd47c`)**, with only this work's three checks merged in. The template's current validator fails there on existing debt: edankert.com has 40 PARENT-BACKLINK and 7 SNAPSHOT-MEMBERSHIP errors, your-applications.com 50 and 13, and yourtrainer-mcp 6 SNAPSHOT-MEMBERSHIP plus 10 stale manual VERIFY errors. Moving those three repos to the current validator needs that grooming first.
- **REVIEW-ROUND fix (project-os `31cd043`).** your-health recorded `review_round` 3, 6 and 8 before the field was defined, and the check blocked its commit. The check now reads only reviews dated from 2026-09-18.

**Hand-merge list.** These template-owned files are locally edited, so the sync left them alone. They were already diverged before this work; only this work's own lines were applied where it needed them.
- **project-os-dev**: `docs/__templates__/procedure.md`, `tools/skills/walk-procedure/SKILL.md`, `.github/workflows/validate-docs.yml` (both sides changed), `tools/instructions/TESTING.md` (both sides changed), `tools/scripts/test-walk-sheet.sh` (both sides changed), `tools/scripts/walk-sheet.py` (both sides changed)
- **project-os-deck**: `SECURITY.md`, `docs/__templates__/design.md`, `tools/instructions/OBSIDIAN.md`, `tools/instructions/STATUSES.md`, `tools/instructions/TRACEABILITY.md`, `tools/scripts/run-tests.py`, `tools/scripts/test-verdict-model.sh`, `tools/skills/design-authoring/SKILL.md`, `.github/workflows/validate-docs.yml` (both sides changed), `LLM_BRIEF.md` (both sides changed), `tools/sync/MANIFEST.yaml` (both sides changed), `tools/instructions/SNAPSHOT.md`, `tools/scripts/install-git-hooks.sh`
- **your-sudoku**: `AGENTS.md`, `tools/instructions/WRITING.md`
- **your-health**: `AGENTS.md`, `tools/instructions/WRITING.md`
- **articles**: `AGENTS.md`, `SECURITY.md`, `docs/__templates__/acceptance-tests.md`, `tools/instructions/WRITING.md`, `LLM_BRIEF.md` (both sides changed), `tools/instructions/SNAPSHOT.md` (both sides changed), `tools/instructions/STATUSES.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed)
- **edankert.com**: `AGENTS.md`, `docs/__templates__/acceptance-tests.md`, `tools/instructions/WRITING.md`, `tools/scripts/migrate-status-vocabulary.py`, `tools/instructions/SNAPSHOT.md` (both sides changed), `tools/instructions/STATUSES.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed)
- **obsidian-supernote-sync**: `AGENTS.md`, `tools/instructions/WRITING.md`
- **project-os-bench**: `AGENTS.md`, `SECURITY.md`, `docs/__templates__/acceptance-tests.md`, `tools/instructions/WRITING.md`, `LLM_BRIEF.md` (both sides changed), `tools/instructions/SNAPSHOT.md` (both sides changed), `tools/instructions/STATUSES.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed)
- **your-applications.com**: `AGENTS.md`, `docs/__templates__/acceptance-tests.md`, `tools/instructions/WRITING.md`, `tools/scripts/migrate-status-vocabulary.py`, `tools/instructions/SNAPSHOT.md` (both sides changed), `tools/instructions/STATUSES.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed)
- **yourtrainer-mcp**: `AGENTS.md`, `docs/__templates__/acceptance-tests.md`, `tools/instructions/WRITING.md`, `tools/scripts/migrate-status-vocabulary.py`, `tools/instructions/SNAPSHOT.md` (both sides changed), `tools/instructions/STATUSES.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed)
- **project-os-cockpit** (partial sync, so every diverged file is still here): `AGENTS.md`, `CONTEXT.md`, `SECURITY.md`, `docs/INDEX.md`, `docs/README.md`, `docs/__templates__/acceptance-tests.md`, `tools/instructions/STATUSES.md`, `tools/instructions/TAXONOMY.md`, `tools/instructions/WRITING.md`, `tools/scripts/run-tests.py`, `LLM_BRIEF.md` (both sides changed), `docs/__templates__/feature.md` (both sides changed), `docs/__templates__/test.md` (both sides changed), `tools/adapters/codex/ADAPTER.md` (both sides changed), `tools/instructions/QUALITY.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed), `tools/scripts/test-walk-sheet.sh` (both sides changed), `tools/scripts/validate-docs.py` (both sides changed), `tools/scripts/walk-sheet.py` (both sides changed)
- **your-trainer** (partial sync, so every diverged file is still here): `AGENTS.md`, `tools/cockpit/src/project_os_cockpit/publication.py`, `tools/cockpit/src/project_os_cockpit/server.py`, `tools/instructions/WRITING.md`, `.github/workflows/validate-docs.yml` (both sides changed), `LLM_BRIEF.md` (both sides changed), `docs/__templates__/test.md` (both sides changed), `tools/instructions/TESTING.md` (both sides changed), `tools/scripts/validate-docs.py` (both sides changed), `tools/scripts/walk-sheet.py` (both sides changed)
