---
type: context
id: CTX-ROOT
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [llm, docs, golden-source]
---

# project-os contract (LLM + developers)

This documentation set is intended to be the **authoritative, task-starting context** for both humans and an LLM maintainer.

## What to read first (LLM + humans)
- `docs/INDEX.md` (human-friendly index)
- `SNAPSHOT.yaml` (agent snapshot; canonical for LLMs)
- `tools/instructions/README.md` (authoring rules)
- `tools/instructions/LIFECYCLE.md` (LLM lifecycle rules)
- `tools/skills/README.md` (playbooks)

## Edit policy

**Live (LLM may update frequently / keep current)**
- `docs/features/**/FEAT-*.md`
- `docs/features/**/plan/PLAN.md`
- `docs/features/**/plan/tasks/TASK-*.md`
- `docs/issues/*.md`
- `docs/workflows/WF-*.md`
- `docs/dashboards/*.md`
- `docs/changes/*.md`
- `SNAPSHOT.yaml`

**Reference (LLM should not change casually)**
- `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/STYLEGUIDE.md`
- `docs/requirements/*`, `docs/risks/*`, `docs/decisions/*`
- `tools/*` (operational scripts/instructions)

## Always keep these invariants
1. `SNAPSHOT.yaml` is canonical for agents/LLMs: keep it current for active work state, focus, and relationships.
2. Notes are the durable record for humans: keep note frontmatter (`id`, `status`, links) consistent with the snapshot so Bases dashboards reflect reality.
3. Notes are typed via `type: [[...]]` (e.g. `[[task]]`, `[[feature]]`, `[[issue]]`, `[[workflow]]`, `[[change]]`).
4. Every task note (`type: [[task]]`) has exactly one `parent` (link to a feature or issue note).
5. Every feature note (`type: [[feature]]`) links to its `requirements` and `tasks`.
6. Every meaningful repo change gets a change note (`type: [[change]]`) linked to the relevant issues/features.
7. Prefer **links to real repo files** over paraphrase.

## LLM operating rule (critical)
If a prompt implies work (bugfix/issue, new feature, refactor, behavior change), the LLM must:
1. **Document first** (update `SNAPSHOT.yaml` + create/update the relevant notes).
2. **Then implement** the code change(s).
3. **Then close out** (update statuses + add `CHG-*` when behavior/paths change).
