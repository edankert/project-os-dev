# Phase Registry

This document is the **semantic source of truth** for this project's development phases. It maps phase IDs to milestones, enabling machine-filtering, automated progress tracking, and dashboard grouping.

Individual `PHASE-*` notes under `phases/` hold the detailed scope, exit criteria, and item links. This file is the overview.

## How Phases Work

- **Property**: `phase` (a `[[PHASE-####]]` link)
- **Location**: YAML frontmatter of features, tasks, requirements, and issues
- **Purpose**: Groups related work into cohesive delivery milestones
- **Active phase**: tracked as `focus.phase` in `../SNAPSHOT.yaml`

## Phase Definitions

| Phase | Name | Status | Scope |
|-------|------|--------|-------|
| [[PHASE-0001-Documentation-System-Foundations\|PHASE-0001]] | Documentation system foundations | `done` | Everything project-os was built out of: tool adapters, hook contracts, mandatory skill steps, the relationship and phase models, the Obsidian cockpit, deferral and requirement-lifecycle enforcement. FEAT-0001–FEAT-0012, REQ-0001–REQ-0015, ADR-0001–ADR-0007 |
| [[PHASE-0002-State-Model-Simplification\|PHASE-0002]] | State model simplification | `done` | The first phase that removes structure. Collapse the status taxonomy, state the rules once, generate the snapshot, stamp test status by execution, end the permanent warning tier. FEAT-0013–FEAT-0017, REQ-0016–REQ-0024, ADR-0008–ADR-0011 |
| [[PHASE-0003-Prompting-Guide-Conformance\|PHASE-0003]] | Prompting-guide conformance | `active` | The template's instructions, skills, hooks and subagents brought in line with the Claude 5 prompting guides: four contradictions fixed, every rule stated once, the always-loaded files trimmed, hooks and hints that no longer teach bypasses. FEAT-0024–FEAT-0027, REQ-0026–REQ-0027, ADR-0024, ISS-0041–ISS-0045 |
| [[PHASE-999-Parking-Lot\|PHASE-999]] | Parking lot — future and unplanned | `planned` | Forward home for deferred items and for tracked-but-unscheduled work. Never completes; items leave by adoption or cancellation |

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

1. **Verify phase alignment**: check the item's `phase` against `focus.phase` before starting work.
2. **Consult this registry** and the relevant `PHASE-*` note for the phase's boundaries.
3. **Prevent phase bleeding**: do not introduce implementations from future phases prematurely.
4. **Flag scope concerns**: if work requires future-phase dependencies, document it and discuss before proceeding.

Full rules in `../tools/instructions/LIFECYCLE.md`, "Phase alignment".

## History

Phases were introduced to this repo on 2026-07-25, after `PHASE-0001`'s work had already shipped. `PHASE-0001` is therefore a retroactive grouping — the name given to what was built before phases were tracked here — rather than a milestone that was planned and then executed. The machinery it uses was itself built in that phase ([[features/phase-notes/FEAT-0008-Phase-Notes|FEAT-0008]]).

---

*This file is part of the Project OS documentation system. See [docs/README.md](README.md) for overview.*
