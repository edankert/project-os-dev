---
type: "[[requirement]]"
id: REQ-0037
aliases: ["REQ-0037"]
title: "The walk is called the release test everywhere, and a consumer's old names are migrated by a script and then refused"
status: implemented
review_verdict: approved
review_round: 2
review_date: 2026-09-27
reviewed_by: "model:claude-opus-5-5 (FEAT-0040 review, two rounds)"
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["Edwin, 2026-09-27: rename everywhere in one go, internal names included, 'to avoid confusion later on'", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]] (D1)", "Edwin, 2026-09-27, approving REQ-0033 to REQ-0037: 'approved, start stage 2'"]
priority: high
scope: "every template file in ADR-0050's rename map, and sync-project-os"
acceptance:
  - "Every name in ADR-0050's rename map has its new name in the template, and no file outside history uses walk, sitting or survey for this feature"
  - "The walk-procedure skill is renamed release-test-procedure in tools/skills, .claude/skills and .agents/skills, and describes the new procedure shape"
  - "A migration script moves a consumer's WALK.md and walk/ folder and rewrites sitting: and walk_readiness_for:, and running it twice changes nothing"
  - "After migration the validator reports each old name as an error that names the new one"
  - "A template sync removes the old script and skill files from a consumer"
  - "Stored result values are unchanged, new ledger entries use the key `result`, and every reader still accepts `mark`"
implements: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
verifies: []
related: ["[[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths]]"]
tests: []
---

# The walk is called the release test everywhere

## Statement

Every script, field, path, skill, template, route and instruction that says "walk", "sitting" or "survey" for this feature shall use the new words: release test, section, and what changed. What a person sees as a mark or verdict shall be called a result. The full old-to-new map is in [[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks|ADR-0050]], D1.

Closed ADRs, change notes and archived notes keep the old words. They are history.

A consumer repository takes the rename at its next template sync. A migration script, run once, moves its files and rewrites its fields. After that, the validator refuses an old name and says which new name to use, so nothing is silently ignored. The old scripts are not kept as aliases.

Where "walk" is ordinary English and not the name of this feature (for example "walk up the directory tree" in code), it stays.

## Acceptance Criteria

- [x] Every name in ADR-0050's rename map has its new name in the template, and no file outside history uses walk, sitting or survey for this feature — evidence: TASK-0187 (template cb01d0a); live notes swept in your-trainer d98ed48c and project-os-cockpit 89e4655; what still names the walk records the rename or is ordinary English
- [x] The walk-procedure skill is renamed release-test-procedure in tools/skills, .claude/skills and .agents/skills, and describes the new procedure shape — evidence: TASK-0194 (template 8309260); the adapters are regenerated in each consumer
- [x] A migration script moves a consumer's WALK.md and walk/ folder and rewrites sitting: and walk_readiness_for:, and running it twice changes nothing — evidence: `migrate-release-test-names.py` (template 88d0c8b) and `test-migrate-release-test-names.sh`, which runs it twice
- [x] After migration the validator reports each old name as an error that names the new one — evidence: `OLD-NAME` in `validate-docs.py`; it named project-os-dev's own leftovers on 2026-09-27
- [x] A template sync removes the old script and skill files from a consumer — evidence: the sync removed `walk-sheet.py`, `walk-tags.py` and the walk-procedure skill from project-os-dev on 2026-09-27 (b5a29ab)
- [x] Stored result values are unchanged, new ledger entries use the key `result`, and every reader still accepts `mark` — evidence: TASK-0187; readers accept `mark` and `result`, new entries write `result` (project-os-cockpit `ledger.py`)

## Traceability

- Implements: [[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]
- Risk: [[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths|RISK-0005]]
- Verified by: a grep over the template for the old names, and the migration script's own test, once TASK-0187 lands.
