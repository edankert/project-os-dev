---
type: instruction-index
id: INSTR-INDEX
status: active
owner: group:maintainers
created: 2026-01-26
updated: 2026-01-26
tags: [instructions]
---

# Instructions

This directory contains **normative instructions** for how documentation and automation should be authored and maintained in this repo.

## Rules for instruction documents
- Keep instruction files stable and broadly applicable; prefer updating tasks/issues for one-off work.
- Use a short title and explicit “Rules” bullets; avoid narrative prose where possible.
- If a rule affects existing content, update both the instruction and any templates/views that rely on it.
- Prefer repo-relative paths in code spans (e.g. `../../docs/INDEX.md`, `scripts/build.sh`).
- Do not hard-wrap Markdown prose; follow `MARKDOWN.md` for repository Markdown formatting policy.

## Instructions index
- Obsidian conventions: `OBSIDIAN.md`
- Lifecycle rules: `LIFECYCLE.md`
- Snapshot rules: `SNAPSHOT.md`
- Status taxonomy: `STATUSES.md`
- Taxonomy values: `TAXONOMY.md`
- Ownership: `OWNERSHIP.md`
- Traceability: `TRACEABILITY.md`
- Markdown authoring: `MARKDOWN.md`
- Decisions/ADRs: `DECISIONS.md`
- Quality/close-out: `QUALITY.md`
- Hook contracts: `HOOKS.md`
