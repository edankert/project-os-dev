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

**Lifecycle-owned (the LLM creates and updates these, under the rules that govern them)**
- `docs/requirements/REQ-*.md` and `docs/risks/RISK-*.md` — required by `tools/instructions/LIFECYCLE.md` preflight step 4 and close-out step 4. Changing a requirement's acceptance criteria is a different matter and belongs to its owner (`tools/instructions/QUALITY.md`).
- `docs/decisions/ADR-*.md` — created per `tools/instructions/DECISIONS.md`; an accepted decision is amended, never quietly rewritten.
- `docs/tests/**`, `docs/phases/PHASE-*.md`, `docs/releases/REL-*.md`, `docs/designs/**`

**Reference (LLM should not change casually)**
- `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/STYLEGUIDE.md`
- `docs/reference/**/*`, `docs/research/**/*`
- `tools/*` (operational scripts/instructions)

## Always keep these invariants
1. `SNAPSHOT.yaml` is canonical for agents/LLMs; its statuses, counters and metrics are derived from the notes by the sync script (`tools/instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"), and focus, membership and relationships are curated by hand.
2. Notes are the durable record for humans: keep note frontmatter (`id`, `status`, links) consistent with the snapshot so Bases views reflect reality.
3. Notes are typed via `type: [[...]]` (e.g. `[[task]]`, `[[feature]]`, `[[issue]]`, `[[workflow]]`, `[[change]]`).
4. Every task note (`type: [[task]]`) has exactly one `parent`, with the deferred exception `tools/instructions/TRACEABILITY.md` states.
5. Every feature note links its `requirements` and `tasks` (`tools/instructions/TRACEABILITY.md`).
6. A change note (`type: [[change]]`) is added when behaviour, paths or contracts change (`tools/instructions/LIFECYCLE.md`, "Close-out"), linked to the relevant issues/features.
7. Prefer **links to real repo files** over paraphrase.
8. Keep structured project-os lifecycle notes in their established `docs/` lifecycle directories, keep non-lifecycle project documentation under purpose-specific `docs/` subdirectories such as `docs/reference/` or `docs/research/`, and keep agent/tool operating detail under `tools/`.
9. Do not hard-wrap Markdown prose to a fixed column width; follow `tools/instructions/MARKDOWN.md`.

## LLM operating rule (critical)
If a prompt implies work (bugfix/issue, new feature, refactor, behavior change): document first, then implement, then close out. The full rule is `tools/instructions/LIFECYCLE.md`.
