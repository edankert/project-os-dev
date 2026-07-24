---
type: "[[task]]"
id: TASK-0049
aliases: ["TASK-0049"]
title: "Cockpit: surface deferred as parked (not archived) in status ordering"
status: done
phase: []
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "one-line ordering change; verified by the cockpit repo's full test suite (223 passed, 1 skipped) after the edit; the deferral edit is mirrored identically in both copies (the canonical file otherwise carries newer unrelated work — do not wholesale-copy over it when syncing)"
source: []
parent: "[[FEAT-0011-Deferral-Descoping]]"
effort: XS
due: ""
depends: []
blocks: []
related: [ADR-0005]
tests: []
---

# Cockpit parked surfacing

## Definition of Done

- [x] `TASK_STATUS_ORDER` in `cockpit.py` moves `deferred` out of the archived tail (currently after `cancelled`/`reverted`) into the parked band directly after `blocked`/`failing`/`reopened`, so parked items sort with actionable work instead of history.
- [x] Change lands in the canonical repo (`~/Dev/repos/project-os-cockpit`) and the vendored copy (`~/Dev/repos/project-os/tools/cockpit/`) stays in lockstep.

## Notes

External implementation target: `../project-os-cockpit/src/project_os_cockpit/cockpit.py`. Chip colors unchanged — position, not palette, is what buried parked items.

Close-out note: the cockpit repo had in-flight uncommitted work from another session (its focus on TASK-0182), so this one-line change was made there without touching its `SNAPSHOT.yaml`; it should be absorbed into that repo's next close-out or recorded as a micro-task there.
