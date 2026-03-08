---
type: "[[task]]"
id: TASK-0005
title: "Implement Claude Code hook scripts and hooks.json"
status: done
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0002-Hook-Contracts]]"
effort: L
due: ""
depends: [TASK-0002, TASK-0004]
blocks: []
related: []
tests: []
---

# Implement Claude Code hook scripts and hooks.json

## Definition of Done
- [x] `tools/adapters/claude-code/hooks.json` defines Claude Code hooks for each contract
- [x] `tools/adapters/claude-code/scripts/` contains executable shell scripts for each hook
- [x] Scripts read SNAPSHOT.yaml and relevant note frontmatter to perform checks
- [x] Scripts use standard exit codes (0 = pass, non-zero = block/warn)
- [x] Each script is documented with expected inputs and outputs

## Steps
- [x] Create hooks.json mapping Claude Code events to scripts
- [x] Implement verification-gate script (check test statuses before status transition)
- [x] Implement risk-trigger-check script (detect dependency file changes)
- [x] Implement phase-alignment script (check task phase vs focus.phase)
- [x] Implement snapshot-freshness script (check SNAPSHOT.yaml modification time)
- [x] Implement document-first-check script (verify focus.task is set before code edits)
- [x] Test each script against sample SNAPSHOT.yaml states
