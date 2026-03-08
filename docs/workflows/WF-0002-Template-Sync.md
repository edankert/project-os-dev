---
type: "[[workflow]]"
id: WF-0002
title: "Template sync"
status: draft
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
entrypoints:
  - tools/scripts/sync-project-os.sh
prereqs:
  - upstream project-os clone
inputs:
  - upstream project-os path
outputs:
  - updated template-owned files
related:
  - ../INDEX.md
  - ../../tools/instructions/SYNCING.md
---

# Template sync

## When to use
- You want to pull upstream project-os template updates into a dev repo.

## Entrypoint(s)
- `tools/scripts/sync-project-os.sh <path-to-upstream>`

## Prerequisites
- An upstream project-os clone (outside the dev repo is fine).

## Inputs
- Path to the upstream project-os clone.

## Outputs
- Updated template-owned files in the dev repo.

## Notes / Troubleshooting
- Review changes with `git diff` before committing.
- Run `tools/skills/snapshot-sync/SKILL.md` after syncing.
