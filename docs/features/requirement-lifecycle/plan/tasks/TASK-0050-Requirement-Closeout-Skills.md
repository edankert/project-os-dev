---
type: "[[task]]"
id: TASK-0050
aliases: ["TASK-0050"]
title: "Requirement advancement in skills: close-out step, scaffold approval gate, canonical acceptance surface"
status: done
phase: []
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "docs-only change set; verified mechanically — generate-adapters --check clean over 32 artifacts after regeneration, validate-docs clean on template"
source: []
parent: "[[FEAT-0012-Requirement-Lifecycle-Closure]]"
effort: S
due: ""
depends: []
blocks: [TASK-0051, TASK-0052]
related: [ADR-0006]
tests: []
---

# Requirement advancement in skills

## Definition of Done

- [x] `close-out/SKILL.md`: a requirement-advancement step — for each requirement linked to the closing feature, walk its acceptance criteria, tick satisfied ones with an evidence pointer, reconcile departures via impact-analysis (amend/narrow/supersede with rationale, never tick to fit), and set `approved → implemented` when **all** implementing features are `done`.
- [x] `feature-scaffold/SKILL.md`: approval gate — a feature may not move to `in-progress` while a linked requirement is `draft`.
- [x] `status-transition/SKILL.md`: requirement branch pointing at the same rules (advancement is a transition too).
- [x] `SCHEMAS.md`: frontmatter `acceptance:` = criteria of record; body `## Acceptance Criteria` checkboxes = per-criterion verification record; they must describe the same criteria.
- [x] `STATUSES.md`/`QUALITY.md`: `implemented` defined as the close-out target for delivered requirements; `verified` gate explicitly unchanged.
- [x] `generate-adapters.py` re-run, `--check` clean.

## Steps

- [x] Edit the skills and instruction files in `~/Dev/repos/project-os`.
- [x] Regenerate adapters.
