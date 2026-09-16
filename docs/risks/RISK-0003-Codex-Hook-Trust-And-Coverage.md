---
type: "[[risk]]"
id: RISK-0003
title: "Codex hooks can be unavailable or miss edits"
status: open
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["[[FEAT-0032-Codex-Native-Project-Adapter]]"]
likelihood: medium
impact: medium
mitigation: ["Keep pre-commit and CI validation as backstops", "Test hook payload shapes and document trust activation", "Fail closed only for confidently parsed project-os code edits"]
related: [FEAT-0032, REQ-0030]
---

# Codex hooks can be unavailable or miss edits

## Description
Codex loads repository hooks only when the project and hook commands are trusted. Hook event coverage can also miss edits through an unrecognized tool payload, so a local session may not see a lifecycle reminder.

## Mitigation
- Retain `validate-docs.sh` at pre-commit and in CI.
- Test native payload shapes and document activation in the adapter.
- Report hook coverage honestly instead of promising a hard gate for every write path.

## Triggers
- `/hooks` lists the project hook as untrusted or a fixture stops producing a decision.
- A code edit reaches a commit without the required change note.
