---
type: "[[requirement]]"
id: REQ-0018
aliases: ["REQ-0018"]
title: "State and transition rules must be normative in exactly one file; every other document links rather than restates"
status: superseded
superseded_by: "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]"
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-09-03
priority: high
scope: docs-system
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0014]
related: [ADR-0008, ISS-0006, REQ-0001]
tests: []
acceptance:
  - "One file states, for every note type, the allowed status values, the gates on each terminal transition, and who or what writes the value."
  - "No instruction file or skill restates a state rule; each links to the normative file instead."
  - "The requirement-advancement rule, currently stated in four files, exists in one."
  - "The deferral procedure, currently written twice near-verbatim, exists in one."
  - "Generated adapters (CLAUDE.md, AGENTS.md, generated skills) reference the contract and do not embed a copy of it."
  - "ISS-0006 is resolved by deletion of the restatement, not by correcting a fourth copy."
---

# State rules are stated once

> **Superseded 2026-09-03** by [[REQ-0027-Every-Normative-Rule-Is-Stated-Once|REQ-0027]], which widens the rule from state and transition rules to every normative rule (ADR-0024, option 1). Nothing here is retracted: the six criteria below stay satisfied and are re-checked as REQ-0027's third criterion.

## Statement

The rules governing an item's status — allowed values, the gates on terminal transitions, and which actor or process writes the value — shall be normative in exactly one file. Instruction files and skills shall reference that file. No document shall restate a state rule in its own words, because a restatement is a copy that the next amendment can miss.

## Acceptance Criteria

- [x] One file states values, gates, and writer per note type — evidence: `tools/instructions/STATUSES.md` "The contract at a glance" table
- [x] No instruction or skill restates a state rule — evidence: sweep recorded in TASK-0058; QUALITY.md and status-transition now link to STATUSES.md as normative
- [x] Requirement advancement stated once (was four) — evidence: same sweep; the ISS-0006 sentence was deleted rather than corrected a fifth time
- [x] Deferral procedure stated once (was twice) — evidence: STATUSES.md "Deferral and re-adoption"
- [x] Adapters reference rather than embed — evidence: `generate-adapters.py` re-run across 10 repos, 33–38 artifacts current
- [x] ISS-0006 resolved by deletion — evidence: fixed in all 10 repos; `grep` for the offending sentence returns 0

## Evidence for the requirement

604 lines across eight files describe state and transitions. Requirement advancement is stated in `QUALITY.md`, `STATUSES.md`, `close-out/SKILL.md` and `status-transition/SKILL.md`. Verification gating appears in four. The deferral procedure is written twice, near-verbatim.

[[ISS-0006-Status-Transition-Test-Gates-Requirements|ISS-0006]] is the failure this predicts, already realised: ADR-0007's amendment corrected requirement test-gating in the validator, `QUALITY.md`, `STATUSES.md` and `close-out` — and missed `status-transition/SKILL.md`, which now instructs agents in **all 10 repos** to apply a gate the ADR explicitly reverted. No mechanical check detected it, because none compares prose to prose.

The "who writes the value" column is not merely tidier. It is what makes [[REQ-0019-Snapshot-Generated|REQ-0019]], [[REQ-0021-Transitions-Advance-On-Evidence|REQ-0021]] and [[REQ-0022-Test-Status-Stamped|REQ-0022]] expressible as a contract instead of as scattered procedure — each of those requirements is, precisely, a change to that column.

## Impact analysis (2026-07-25)

- [[REQ-0001-Tool-Agnostic-Rules|REQ-0001]] — **directly aligned.** REQ-0001 requires rules maintainable in one place and deliverable to any tool. This applies the same principle within the rule set, where it was not being held.
- [[REQ-0002-Native-Instruction-Format|REQ-0002]] — respected: adapters still deliver rules in each tool's native format; what changes is that they reference the contract rather than embedding a copy that can drift from it.
- [[REQ-0014-Requirement-Lifecycle-Advancement|REQ-0014]] / [[REQ-0013-Deferral-Semantics|REQ-0013]] — content preserved verbatim; only its location changes. No rule is altered by this requirement.
- **Sequencing constraint, not a conflict:** FEAT-0013, FEAT-0015 and FEAT-0016 each change what the contract says. Authoring it before they land means writing it four times. The feature is therefore best sequenced last.

**No conflicts found.**

## Traceability

- Feature: [[FEAT-0014-Single-State-Contract|FEAT-0014]]
- Fixes: [[ISS-0006-Status-Transition-Test-Gates-Requirements|ISS-0006]]
