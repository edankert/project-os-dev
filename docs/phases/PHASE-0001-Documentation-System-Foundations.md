---
type: "[[phase]]"
id: PHASE-0001
aliases: ["PHASE-0001"]
title: "Documentation system foundations"
status: done
order: 1
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
goal: "Build the project-os documentation system: tool adapters, hook contracts, mandatory skill steps, the relationship and phase models, the Obsidian cockpit, and mechanical enforcement of deferral and requirement lifecycle"
features: [FEAT-0001, FEAT-0002, FEAT-0003, FEAT-0004, FEAT-0005, FEAT-0006, FEAT-0007, FEAT-0008, FEAT-0009, FEAT-0010, FEAT-0011, FEAT-0012]
requirements: [REQ-0001, REQ-0002, REQ-0003, REQ-0004, REQ-0005, REQ-0006, REQ-0007, REQ-0008, REQ-0009, REQ-0010, REQ-0011, REQ-0012, REQ-0013, REQ-0014, REQ-0015]
tasks: []
issues: [ISS-0001, ISS-0002, ISS-0004]
related: [ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0007]
tags: [phase, foundations]
---

# Documentation system foundations

## Goal

Everything project-os was built out of, from the first tool adapter to mechanical enforcement of the requirement lifecycle. This phase is **closed retroactively** — it was not planned as a phase, it is the name now given to the work that shipped before phases existed here (created 2026-07-25).

## Scope

Twelve features, in the order they landed:

| Feature | Delivered |
|---|---|
| [[FEAT-0001]] – [[FEAT-0004]] | Tool adapters, hook contracts, orchestration delegation |
| [[FEAT-0005-Mandatory-Skill-Steps\|FEAT-0005]] | Risk scans, verification gating, impact analysis made mandatory ([[ADR-0004-Mandatory-Skill-Steps\|ADR-0004]]) |
| [[FEAT-0006]] | Release tracking as first-class notes |
| [[FEAT-0007-Relationship-Model\|FEAT-0007]] | Relationship model — scalar parent down, `implements` up ([[REQ-0015-Relationship-Model\|REQ-0015]]) |
| [[FEAT-0008-Phase-Notes\|FEAT-0008]] | Phases as first-class notes — the machinery this registry finally uses |
| [[FEAT-0009-Cockpit-Layout\|FEAT-0009]] | Three-pane Obsidian cockpit |
| [[FEAT-0010-Template-Completeness-Program\|FEAT-0010]] | Consistency debt, native Claude adapter, fleet sync, tool wiring |
| [[FEAT-0011-Deferral-Descoping\|FEAT-0011]] | Deferral as descoping ([[ADR-0005-Deferral-As-Descoping\|ADR-0005]], fixes [[ISS-0002-Deferred-Items-Satisfy-Parent-Completeness\|ISS-0002]]) |
| [[FEAT-0012-Requirement-Lifecycle-Closure\|FEAT-0012]] | Requirements advance on evidence ([[ADR-0006-Requirement-Advancement-On-Evidence\|ADR-0006]], fixes [[ISS-0004-Requirements-Never-Advance\|ISS-0004]]) |

Tasks are not enumerated here; each carries `phase: [[PHASE-0001]]` and is reached through its parent feature.

## Out of scope

- Contracting the system. Every feature in this phase *added* structure; [[PHASE-0002-State-Model-Simplification|PHASE-0002]] is the first that removes any.

## Exit criteria

- [x] All twelve features `done`
- [x] All fifteen requirements terminal (`implemented`, or `superseded` for REQ-0010)
- [x] ADR-0001 through ADR-0007 accepted
- [x] Validator enforcing snapshot↔filesystem agreement, deferral invariants, and requirement lifecycle at three layers (Stop hook, pre-commit, CI)

## Notes

The phase closes with two issues still open — [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing|ISS-0003]] and [[ISS-0005-Feature-Less-Requirement-Triage|ISS-0005]]. Neither blocks it: both are low-severity residue, and both are re-homed to [[PHASE-999-Parking-Lot|PHASE-999]] rather than dragged forward, per the deferral principle that parked work keeps a forward home rather than an open-ended one.

The 2026-07-25 fleet audit that opened PHASE-0002 measured this phase's output in use across 10 repos. Its central finding is worth recording against the work rather than only against its successor: the structure built here is sound, and roughly a third of it is never exercised.
