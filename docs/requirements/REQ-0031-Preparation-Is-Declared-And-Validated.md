---
type: "[[requirement]]"
id: REQ-0031
aliases: ["REQ-0031"]
title: "Walk preparation is declared, validated and retained"
status: approved
phase: ""
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["Your Trainer FEAT-0122, 2026-09-16"]
priority: high
scope: "Shared walk generator and validator"
acceptance: ["Required preparation survives filtering without creating a verdict", "Only setup needed by retained steps is shown", "Invalid prerequisite declarations leave owed checks visible", "The survey keeps a changed child under its parent"]
implements: "[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"
verifies: []
related: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
tests: []
---

# Walk preparation is declared, validated and retained

## Statement

The generator must preserve the actions and setup required to perform every owed observation, while the validator rejects invalid authored links and keeps the owed check set visible.

## Acceptance Criteria

- [x] Required preparation survives filtering without creating a verdict — evidence: `tools/scripts/test-walk-preparation.py` checks transitive actions and unchanged owed rows.
- [x] Only setup needed by retained steps is shown — evidence: the same fixture checks Android and iOS setup selection.
- [x] Invalid prerequisite declarations leave owed checks visible — evidence: the broken-reference and cross-platform fixtures check fallback with the owed row intact.
- [x] The survey keeps a changed child under its parent — evidence: the synthetic-parent fixture checks the survey hierarchy.

## Traceability

- Implements: [[FEAT-0033-A-Walk-Keeps-Required-Preparation]].
- Verified by: `python3 -m unittest tools/scripts/test-walk-preparation.py` (7 passed) and `bash tools/scripts/test-walk-sheet.sh` (157 assertions passed), 2026-09-16.
