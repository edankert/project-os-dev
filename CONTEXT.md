---
type: context
id: CTX-ROOT
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-05-08
tags: [llm, docs, golden-source]
---

# project-os contract (LLM + developers)

This documentation set is intended to be the **authoritative, task-starting context** for both humans and an LLM maintainer.

Keep the content split explicit:
- `docs/`: durable project documentation, including structured project-os lifecycle notes and ordinary project reference/research material
- `tools/agents/`: agent-facing operating playbooks
- `tools/`: project-os machinery plus project-specific automation, scripts, adapters, and instructions

## What to read first (LLM + humans)
- `AGENTS.md` (agent startup contract + docs-first gate)
- `LLM_BRIEF.md` (machine-oriented project brief)
- `docs/INDEX.md` (human-friendly index)
- `SNAPSHOT.yaml` (agent snapshot; canonical for LLMs)
- `tools/instructions/README.md` (authoring rules)
- `tools/instructions/MARKDOWN.md` (Markdown formatting rules)
- `tools/instructions/LIFECYCLE.md` (LLM lifecycle rules)
- `tools/instructions/HOOKS.md` (Codex hook-equivalent contracts)
- `tools/skills/README.md` (playbooks)
- `tools/adapters/codex/ADAPTER.md` (Codex adapter model)
- `tools/cockpit/README.md` (optional local docs cockpit)

## Edit policy

**Live (LLM may update frequently / keep current)**
- `docs/features/**/FEAT-*.md`
- `docs/features/**/plan/PLAN.md`
- `docs/features/**/plan/tasks/TASK-*.md`
- `docs/issues/*.md`
- `docs/workflows/WF-*.md`
- `docs/changes/*.md`
- `SNAPSHOT.yaml`

**Reference (LLM should not change casually)**
- `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/STYLEGUIDE.md`
- `docs/requirements/*`, `docs/risks/*`, `docs/decisions/*`
- `docs/reference/**/*`, `docs/research/**/*`
- `tools/*` (operational scripts/instructions)

## Always keep these invariants
1. `SNAPSHOT.yaml` is canonical for agents/LLMs: keep it current for active work state, focus, and relationships.
2. Notes are the durable record for humans: keep note frontmatter (`id`, `status`, links) consistent with the snapshot so Bases views reflect reality.
3. Notes are typed via `type: [[...]]` (e.g. `[[task]]`, `[[feature]]`, `[[issue]]`, `[[workflow]]`, `[[change]]`).
4. Every task note (`type: [[task]]`) has exactly one `parent` (link to a feature or issue note).
5. Every feature note (`type: [[feature]]`) links to its `requirements` and `tasks`.
6. Every meaningful repo change gets a change note (`type: [[change]]`) linked to the relevant issues/features.
7. Prefer **links to real repo files** over paraphrase.
8. Keep structured project-os lifecycle notes in their established `docs/` lifecycle directories, keep non-lifecycle project documentation under purpose-specific `docs/` subdirectories such as `docs/reference/` or `docs/research/`, and keep agent/tool operating detail under `tools/`.
9. Do not hard-wrap Markdown prose to a fixed column width; follow `tools/instructions/MARKDOWN.md`.

## LLM operating rule (critical)
If a prompt implies work (bugfix/issue, new feature, refactor, behavior change), the LLM must:
1. **Document first** (update `SNAPSHOT.yaml` + create/update the relevant notes).
2. **Then implement** the code change(s).
3. **Then close out** (update statuses + add `CHG-*` when behavior/paths change).
