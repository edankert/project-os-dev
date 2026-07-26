---
type: "[[task]]"
id: TASK-0042
aliases: ["TASK-0042"]
title: "Native Claude Code adapter: plugin, generated skills, reviewer subagent, mechanical review check"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-07-17
updated: 2026-07-17
verification_waiver: "docs/tooling change set; verified mechanically — generate-adapters --check clean (32 artifacts), regeneration idempotent, validator REVIEW check exercised against fleet repos"
source: []
parent: "[[FEAT-0010-Template-Completeness-Program]]"
fixes: []
effort: L
due: ""
depends: [TASK-0041]
blocks: []
related: [REQ-0002, ADR-0001]
tests: []
waiver_expires: 2026-10-23

---

# Native Claude Code adapter

## Definition of Done

- [x] A generator (`tools/scripts/generate-adapters.py` or equivalent) emits, from the canonical `tools/skills/*/SKILL.md` playbooks: native Claude Code skills (`.claude/skills/<name>/SKILL.md` with `name` + `description` frontmatter) and Cursor rules (`.cursor/rules/*.mdc`), keeping the playbooks the single source of truth.
- [x] The Claude Code adapter is installable as one unit (hooks + generated skills + independent-reviewer subagent), replacing the manual `hooks.json → .claude/settings.json` copy step; SYNCING.md updated accordingly.
- [x] `.claude/agents/independent-reviewer.md` subagent ships, wired to the independent-review skill's different-model-family requirement.
- [x] Validator (or verification gate) mechanically checks `reviewed_by`/`review_verdict` on TST-*/CHG-bearing closures, same escape-hatch pattern as `verification_waiver`.
- [x] AGENTS.md/LLM_BRIEF.md repositioned as the generic adapter layer; codex adapter becomes a thin pointer; cursor adapter un-stubbed via the generator.
- [x] The template repo itself has the generated artifacts installed (dogfooding).
