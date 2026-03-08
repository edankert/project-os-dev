# Phase Registry

This document is the **semantic source of truth** for the project's development phases. It maps phase numbers to specific technical and business milestones, enabling machine-filtering, automated progress tracking, and dashboard grouping.

## How Phases Work

- **Property**: `phase` (Integer 1–N, optional)
- **Location**: YAML frontmatter of features, tasks, requirements, and issues
- **Purpose**: Groups related work into cohesive delivery milestones

## Phase Definitions

> **Instructions**: Replace the example phases below with your project's actual roadmap. Each phase should represent a coherent milestone with clear boundaries.

| Phase | Name | Description | Key Deliverables |
|-------|------|-------------|------------------|
| 1 | Foundation | Core infrastructure and stability | Database schema, authentication, base architecture |
| 2 | Core Engine | Primary business logic | Domain models, core algorithms, API contracts |
| 3 | Product | User-facing features | UI/UX, integrations, licensing |
| 4 | Portability | Data exchange and interoperability | Import/export, external API support |
| 5 | Intelligence | AI and automation features | LLM integration, smart features |
| 6 | Launch | Production readiness | Store assets, deployment config, documentation |

## Usage

### In Frontmatter

```yaml
---
type: "[[task]]"
id: TASK-0042
phase: 2
status: doing
parent: "[[FEAT-0015]]"
---
```

### Filtering by Phase

Use the `phase` property in Obsidian bases or queries to:
- Group items by delivery milestone
- Track progress within a phase
- Identify scope creep (items without phases)

### Phase Inheritance

- **Features** define the phase for a body of work
- **Tasks** inherit phase from their parent feature (or override explicitly)
- **Requirements** and **Issues** can specify phase when relevant to milestone planning

## Operational Rules for LLMs

When executing work, the LLM must:

1. **Verify phase alignment**: Check the `phase` property in the task/feature frontmatter before starting work.
2. **Consult this registry**: Understand the broader context and boundaries of the current phase.
3. **Prevent phase bleeding**: Do not introduce implementations from future phases prematurely.
   - Example: Don't build Phase 4 export logic while working on a Phase 2 core engine task.
4. **Flag scope concerns**: If a task requires future-phase dependencies, document it and discuss before proceeding.

## Phase Progression

Phases are generally sequential but may overlap:
- **Active phase**: Primary focus of current development
- **Maintenance phases**: Earlier phases may receive bug fixes
- **Blocked phases**: Future phases awaiting dependencies

Track the current active phase in `SNAPSHOT.yaml` under `focus.phase`.

---

*This file is part of the Project OS documentation system. See [docs/README.md](README.md) for overview.*
