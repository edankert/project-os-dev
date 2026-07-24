---
type: "[[adr]]"
id: ADR-0004
aliases: ["ADR-0004"]
title: "Shift from optional to mandatory skill steps"
status: accepted
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
decision: "Make risk scans, verification gating, and impact analysis mandatory steps with explicit trigger checklists rather than conditional steps"
supersedes:
superseded:
related: [FEAT-0005, REQ-0006, REQ-0007, REQ-0008]
---

# Shift from optional to mandatory skill steps

## Context

Several project-os skills contained steps phrased as conditional ("if new dependencies were added, consider creating a risk note"). This meant agents could — and frequently did — skip these steps by determining the condition didn't apply, even when it did.

An audit of the project-os template against documented capabilities revealed that risk scans, verification gating, and impact analysis were all described as enforced capabilities in external documentation, but were implemented as optional/conditional steps in the actual skills.

## Decision

Shift all critical workflow steps from conditional phrasing to mandatory phrasing with explicit trigger checklists:

1. **Risk scans**: Changed from "if applicable, create a risk note" to a mandatory step with an explicit trigger checklist (new dependencies, env vars, path changes, performance impacts, security exposure). Agent must review the checklist and either create a RISK-* note or explicitly record "No new risks identified."

2. **Verification gating**: Moved from a mid-process check to the **first step** in close-out and a pre-transition gate in status-transition. Agent must check linked test statuses and STOP if any are not passing.

3. **Impact analysis**: Added as a mandatory preflight step for new requirements during feature-scaffold and issue-intake. Created a dedicated impact-analysis skill with a STOP gate on conflict detection.

## Alternatives Considered

1. **Keep optional phrasing, add CI enforcement**: Rejected — project-os is documentation-only, CI enforcement would require infrastructure.
2. **Add "MUST" keywords without restructuring**: Rejected — agents respond better to structural changes (step ordering, explicit checklists) than to keyword emphasis.
3. **Leave as-is and soften documentation claims**: Partially adopted — documentation language was softened for capabilities that cannot be technically enforced, but skills were also hardened where possible.

## Consequences

- Skills are slightly longer due to explicit trigger checklists
- Agents spend marginally more time on each close-out/scaffold step
- Consistency of risk and verification tracking significantly improved
- Documentation claims about enforcement are now accurate
