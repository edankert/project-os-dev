---
type: "[[task]]"
id: TASK-0071
aliases: ["TASK-0071"]
title: "Wire independent review into close-out so it runs, or narrow its scope to CHG-* notes"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0017-Enforcement-Severity]]"
effort: M
due: ""
depends: [TASK-0069]
blocks: []
related: [REQ-0024, ADR-0011, REQ-0005]
tests: []
---

# Independent review wiring

## Definition of Done

- [ ] A decision, recorded: **enforce at current scope** (and make it actually run) or **narrow to `CHG-*`** (and enforce that).
- [ ] `REVIEW` gets its disposition per [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] — error with a cutover, or deleted at the narrowed scope.
- [ ] If enforcing: close-out invokes the reviewer as a step that cannot be skipped silently, not as a numbered instruction an agent may drop under context pressure.
- [ ] `QUALITY.md` "Independent review" section matches whatever is decided.
- [ ] The 206 existing findings are cleared or explicitly grandfathered with a rationale.

## Steps

- [ ] Sample the 206 findings: which are `TST-*`, which `CHG-*`, which requirement/feature transitions. The mix determines whether narrowing actually helps.
- [ ] Decide scope.
- [ ] Implement — either the wiring or the narrowing.
- [ ] Update `QUALITY.md` and regenerate adapters.

## Notes

**206 findings across 10 repos means the rule is not running at all.** The machinery exists: an `independent-reviewer` subagent is defined and wired into the Claude adapter, and the routing hook advertises it on every prompt. What is missing is a point at which not running it stops the work — which is exactly [[ADR-0004-Mandatory-Skill-Steps|ADR-0004]]'s thesis, unapplied to this rule.

**Narrowing is a legitimate answer, not a defeat.** The current scope — every `TST-*`, every `CHG-*`, every requirement-terminal and feature-done transition — is broad, and the evidence says the practice cannot sustain it. `CHG-*` only would be narrower, enforceable, and would still cover the cases where an outside eye has historically caught things: ADR-0007's own review found four blocking defects, and the FEAT-0012 review returned `changes-requested` on a ticked-but-false criterion.

**What must not happen is the third option** — leaving it at current scope, unenforced, with 206 findings. That is the state ADR-0011 exists to end, and it is where this rule has sat for months.

Note the tension with [[REQ-0005-Orchestration-Delegation|REQ-0005]]: project-os delegates agent coordination to native tool orchestration, so "wire the reviewer in" must mean *the skill invokes it*, not project-os growing its own orchestration layer.
