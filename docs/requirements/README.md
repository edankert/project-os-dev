---
type: reference
id: REQUIREMENTS-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [requirements]
---

# `docs/requirements/`

Requirements define **what must be true** (acceptance criteria) and enable traceability to features and verification.

## What goes here
- `REQ-####-*.md` created from `../__templates__/requirement.md`.

## When to add a requirement
- When you want stable acceptance criteria that multiple tasks/features can implement.
- When you need to demonstrate coverage (e.g. tests produce specific artifacts; build outputs land in a specific path).

## What to link
- `implements:` / `verifies:` should point to features, scripts, tests, or workflows that demonstrate the requirement is met.
