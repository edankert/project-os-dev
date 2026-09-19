# Phase Registry

This document is the **semantic source of truth** for this project's development phases. It maps phase IDs to milestones, enabling machine-filtering, automated progress tracking, and dashboard grouping.

Individual `PHASE-*` notes under `phases/` hold the detailed scope, exit criteria, and item links. This file is the overview.

## How Phases Work

- **Property**: `phase` (a `[[PHASE-####]]` link)
- **Location**: YAML frontmatter of features, tasks, requirements, and issues
- **Purpose**: Groups related work into cohesive delivery milestones
- **Active phase**: tracked as `focus.phase` in `../SNAPSHOT.yaml`

## Phase Definitions

Each phase is a note under `docs/phases/`, and its status, scope and exit criteria are written there and only there. The table that used to sit here repeated every status by hand, which is how your-health's copy came to show a finished phase as planned (ISS-0072). It was removed on 2026-09-19. To see every phase and its status, list `docs/phases/` or open the cockpit.

## Conventions

### Numbering

Real phases are allocated sequentially from `counters.PHASE` in `../SNAPSHOT.yaml` and use the four-digit form (`PHASE-0001`).

`PHASE-999` is the **all-9s sentinel** for the parking lot. `validate-docs.py` exempts all-9s IDs from counter integrity (`if set(str(num)) == {"9"}`), which is why it is three digits and not `PHASE-0999` — a `0` in the number loses that exemption and would force `counters.PHASE` to 999, silently permitting any phase ID below that without counter discipline. The three-digit form is the one named in `../tools/instructions/STATUSES.md` and `../tools/skills/status-transition/SKILL.md`, so it is also what every other repo and skill already expects.

### In frontmatter

```yaml
---
type: "[[task]]"
id: TASK-0053
status: backlog
phase: "[[PHASE-0002-State-Model-Simplification]]"
---
```

### Filtering by phase

Use the `phase` property in Obsidian Bases or queries to group items by milestone, track progress within a phase, and identify items with no phase at all.

### Phase inheritance

- **Features** define the phase for a body of work.
- **Tasks** carry the phase of their parent feature explicitly (the link is written, not inferred, so Bases can filter on it).
- **Requirements** and **issues** carry a phase when relevant to milestone planning.

## Status lifecycle

`planned` → `active` → `done`, or `planned` → `deferred`. See `../tools/instructions/STATUSES.md`.

## Operational rules for LLMs

The phase-alignment rules are stated once in `../tools/instructions/LIFECYCLE.md`, "Phase alignment (optional gating)": verify the phase before starting, consult this registry, do not build a later phase's work early, and a task that needs a future-phase dependency is the user's decision (`../tools/instructions/LIFECYCLE.md`, "When to pause for the user").

## History

Phases were introduced to this repo on 2026-07-25, after `PHASE-0001`'s work had already shipped. `PHASE-0001` is therefore a retroactive grouping — the name given to what was built before phases were tracked here — rather than a milestone that was planned and then executed. The machinery it uses was itself built in that phase ([[features/phase-notes/FEAT-0008-Phase-Notes|FEAT-0008]]).

---

*This file is part of the Project OS documentation system. See [docs/README.md](README.md) for overview.*
