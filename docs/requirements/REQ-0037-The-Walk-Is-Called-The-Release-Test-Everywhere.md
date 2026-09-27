---
type: "[[requirement]]"
id: REQ-0037
aliases: ["REQ-0037"]
title: "The walk is called the release test everywhere, and a consumer's old names are migrated by a script and then refused"
status: approved
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

- [ ] Every name in ADR-0050's rename map has its new name in the template, and no file outside history uses walk, sitting or survey for this feature — evidence:
- [ ] The walk-procedure skill is renamed release-test-procedure in tools/skills, .claude/skills and .agents/skills, and describes the new procedure shape — evidence:
- [ ] A migration script moves a consumer's WALK.md and walk/ folder and rewrites sitting: and walk_readiness_for:, and running it twice changes nothing — evidence:
- [ ] After migration the validator reports each old name as an error that names the new one — evidence:
- [ ] A template sync removes the old script and skill files from a consumer — evidence:
- [ ] Stored result values are unchanged, new ledger entries use the key `result`, and every reader still accepts `mark` — evidence:

## Traceability

- Implements: [[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]
- Risk: [[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths|RISK-0005]]
- Verified by: a grep over the template for the old names, and the migration script's own test, once TASK-0187 lands.
