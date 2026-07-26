---
type: "[[task]]"
id: TASK-0047
aliases: ["TASK-0047"]
title: "Deferral procedure in skills: status-transition branch, grooming re-adoption, close-out guard"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "docs-only change set; verified mechanically — generate-adapters regenerated (4 .mdc rules rewritten) and --check clean over all 32 artifacts; generated skills are pointers to the canonical playbooks"
source: []
parent: "[[FEAT-0011-Deferral-Descoping]]"
effort: S
due: ""
depends: [TASK-0046]
blocks: []
related: [ADR-0005]
tests: []
waiver_expires: 2026-10-23

---

# Deferral procedure in skills

## Definition of Done

- [x] `status-transition/SKILL.md`: mandatory deferral branch — descope from parent (`tasks:` → `deferred:`), set `origin`, clear `parent`, assign forward home (`phase:` future phase or `PHASE-999` parking lot, creating the parking-lot note once if absent), mirror in snapshot; plus the re-adoption branch (new parent, `origin` kept as history).
- [x] `backlog-grooming/SKILL.md`: mandatory parked-item review step — every pass, each deferred item is re-adopted or cancelled-or-kept with rationale.
- [x] `close-out/SKILL.md`: pre-terminal guard — a feature may not go `done` while `deferred` IDs remain in its `tasks:` list; point at the deferral procedure.
- [x] `tools/scripts/generate-adapters.py` re-run so native skills/rules reflect the changes (`--check` clean).

## Steps

- [x] Edit the three skill playbooks in `~/Dev/repos/project-os/tools/skills/`.
- [x] Regenerate adapters and verify with `generate-adapters.py --check`.
