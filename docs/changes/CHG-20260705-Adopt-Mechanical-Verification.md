---
type: "[[change]]"
id: CHG-20260705-Adopt-Mechanical-Verification
aliases: ["CHG-20260705-Adopt-Mechanical-Verification"]
title: "Adopt mechanical verification change set from project-os template"
status: merged
owner: unassigned
created: 2026-07-05
updated: 2026-07-05
source: []
commit: ""
pr: ""
impacts:
  - "tools/scripts"
  - "tools/adapters/claude-code"
  - "tools/skills"
  - "tools/instructions"
  - "docs/__templates__"
  - ".github/workflows"
  - ".claude"
issues: []
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related:
  - tools/scripts/validate-docs.py
  - tools/skills/independent-review/SKILL.md
  - tools/skills/docs-audit/SKILL.md
---

# Adopt Mechanical Verification Change Set from project-os Template

## Summary
Syncs the "mechanical verification" change set from the canonical project-os template (upstream CHG-20260705-Mechanical-verification-and-independent-review) into this repo. The change set converts project-os's core invariants from convention into mechanism: a deterministic docs validator, a blocking verification gate, git pre-commit and CI enforcement, and new independent-review and docs-audit skills.

## Impact
- **New docs validator (`tools/scripts/validate-docs.py` + `.sh` wrapper):** checks snapshot↔filesystem agreement, frontmatter/status consistency, counter integrity, link-graph integrity, and the verification invariant (no terminal status without passing linked tests).
- **Verification gate is now blocking:** `tools/adapters/claude-code/hooks/verification-gate` moved from advisory PostToolUse to blocking PreToolUse (new `verification-gate.py`); it denies edits that set `done`/`closed`/`verified` while linked `TST-*` notes are not `passing`, with a recorded-waiver escape (`verification_waiver`). `.claude/settings.json` hooks were re-merged from `tools/adapters/claude-code/hooks.json` to pick this up.
- **Git + CI enforcement:** `tools/scripts/install-git-hooks.sh` installed a pre-commit hook running the validator; `.github/workflows/validate-docs.yml` (new in this repo) runs it in CI.
- **New skills:** `independent-review` (different-model review pass over `TST-*`/`CHG-*` changes, recorded via `reviewed_by` frontmatter) and `docs-audit` (periodic cross-document consistency audit run to quiescence), both registered in `CLAUDE.md` and `tools/skills/README.md`.
- **Instruction/skill/template updates:** HOOKS.md, QUALITY.md, TESTING.md, SYNCING.md, LIFECYCLE.md, issue-intake (spec-ambiguity checklist), snapshot-sync, backlog-grooming, close-out, release-prep, claude-code adapter files, `sync-project-os.sh`, and the `test`/`change` templates plus SCHEMAS.md (adequacy/mutation_score and reviewed_by/review_date/review_verdict fields).
- **Drift fixed during sync:** `SNAPSHOT.yaml` `counters.WF` was `0` while WF-0001..WF-0003 workflow notes exist; raised to `3`. Validator went from 3 errors to 0. All 19 template-owned files synced matched the pre-change template baseline exactly, so no hand-merges were needed.

## Documentation Coverage (All Types Considered)
Set each item to one of: `updated`, `new`, `not-applicable`, `deferred`.

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable
- issues: not-applicable
- tests: not-applicable
- workflows: not-applicable
- decisions: not-applicable
- risks: deferred
- changes: new
- snapshot: updated

## Follow-ups
- [ ] Consider a `RISK-*` note for the new `python3` (stdlib-only) requirement of the validator and hooks.
