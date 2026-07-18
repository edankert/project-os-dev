---
type: "[[feature]]"
id: FEAT-0010
aliases: ["FEAT-0010"]
title: "Template completeness program — consistency debt, native adapters, verification health, fleet sync, tool wiring"
status: in-progress
owner: user:edwin
created: 2026-07-17
updated: 2026-07-17
phase: []
goal: "Close the gaps found by the 2026-07-17 full review of project-os: internal consistency debt, underused native Claude Code machinery, missing verification observability in the cockpit, fleet-blind sync tooling, and unwired external tools"
requirements: [REQ-0002, REQ-0006, REQ-0009]
related: [ADR-0001, ADR-0002, ADR-0004]
tasks: [TASK-0041, TASK-0042, TASK-0043, TASK-0044, TASK-0045]
---

# Template Completeness Program

## Goal

Close the gaps found by the 2026-07-17 full review of the project-os template, the adapter layer, and the cockpit. The review (three parallel exploration passes over ~/Dev/repos/project-os and ~/Dev/repos/project-os-cockpit) concluded the enforcement core is sound but found consistency debt inside the template, a lopsided adapter story (Claude Code is the only tool with real-time enforcement yet project-os uses almost none of its native machinery), no observability for the validator, single-repo tooling for a 9-repo fleet, and external tool slots named but never wired.

## Context

The 2026-07-05 mechanical-verification rollout (validator + blocking hooks + pre-commit/CI, fleet-wide) proved that mechanism beats convention. This program is the follow-through: make the template internally consistent with its own doctrine, deliver the rules through native tool machinery instead of prose lists, surface enforcement results to humans, and mechanize the fleet-sync recipe that the rollout had to improvise by hand.

## Scope (five sequenced steps)

1. **Consistency-debt pass** ([[TASK-0041-Consistency-Debt-Pass|TASK-0041]]) — release-lifecycle unification, hook-code unification, validator metrics enforcement, stale/contradictory docs, Bases field fixes, sync double-copy, acceptance-test taxonomy, dogfooded hooks in the template repo itself.
2. **Native Claude Code adapter** ([[TASK-0042-Native-Claude-Adapter|TASK-0042]]) — generator emitting native skills and Cursor rules from the canonical playbooks, plugin packaging, independent-reviewer subagent, mechanical review check, generic repositioning of AGENTS.md/LLM_BRIEF.md.
3. **Cockpit verification health** ([[TASK-0043-Cockpit-Verification-Health|TASK-0043]]) — implement FEAT-0018 (TASK-0111..0113) in project-os-cockpit; scaffold fleet-health and MCP-server follow-ups there.
4. **Sync manifest + fleet validator** ([[TASK-0044-Sync-Manifest-Fleet-Validator|TASK-0044]]) — per-path ownership manifest with baseline-SHA divergence detection replacing blunt rsync; fleet-wide validator aggregation.
5. **External tool wiring** ([[TASK-0045-External-Tool-Wiring|TASK-0045]]) — prettier/markdownlint/yamllint/lychee configs + CI, named mutation-testing tools in TESTING.md.

## Out of scope

- Redistributing this change set to the 8 downstream repos (separate rollout, same pattern as 2026-07-05).
- Implementing fleet health in the cockpit desktop shell and the cockpit MCP server (scaffolded as backlog features in project-os-cockpit).
- GitHub Projects export skill (noted as optional per-repo wiring).
