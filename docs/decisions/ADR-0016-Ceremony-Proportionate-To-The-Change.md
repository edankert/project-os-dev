---
type: "[[adr]]"
id: ADR-0016
aliases: ["ADR-0016"]
title: "Ceremony is proportionate to the change: a declared fast path, or the rule that every change is documented stops being followed"
status: proposed
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
source: ["landscape review 2026-07-29: BMAD v6 scale-adaptive levels; Thoughtworks Technology Radar placing SDD in Assess"]
decision: "The lifecycle declares more than one path through itself, selected by the size of the change rather than by the agent's appetite. A small change gets an issue note, a commit and the validator — no feature, no task, no CHG-*, no independent review. The full path stays mandatory for anything that changes a contract, a path, a status vocabulary, or the fleet. The selector is written down and mechanical, not left to judgement in the moment"
context: "LIFECYCLE.md's No Orphaned Code rule requires a Task under a Feature for every functional code change, excluding only typos, comments, formatting and pure documentation. There is exactly one path and it is sized for the largest work the system does. Nothing in the system currently authorises doing less, so an agent facing a one-line fix either pays the full cost or quietly skips the rule"
alternatives:
  - "Keep one path and rely on judgement — rejected: this is the current state, and an undeclared exception is indistinguishable from non-compliance. It also makes the rule unenforceable, since no validator can tell 'correctly skipped' from 'skipped'"
  - "Make the fast path an agent decision at intake — rejected: the party that benefits from less ceremony picks the ceremony, which is the ADR-0010 conflict of interest with different nouns"
  - "Scale by effort field (XS/S vs M/L/XL) — rejected: effort estimates what the work costs, not what it can break. A one-line change to a status table is XS and fleet-wide (ISS-0011); a large isolated refactor is L and blast-radius-zero"
  - "Adopt BMAD's five levels wholesale — rejected: five tracks for a solo fleet is more taxonomy than there is work to sort into it, and ADR-0008 already ruled that declared values must be observed in use"
consequences:
  - "The rule that every functional change is documented becomes affordable, and therefore checkable — today it is neither"
  - "A second path is a second thing to keep correct, and REQ-0018's 'stated once' pressure applies: the selector must live in STATES.md or LIFECYCLE.md, once, and be linked from the skills rather than restated in each"
  - "Some changes will be routed to the fast path and later prove to have deserved the full one. The mitigation is that the fast path still produces an ISS-* note, so promoting it is adding artefacts rather than reconstructing history"
  - "The independent-review population shrinks, which is the point: review is currently required for every CHG-* and every TST-*, and its value is diluted across changes that did not need it"
related: [ADR-0004, ADR-0008, ADR-0011, ADR-0014]
supersedes: ""
superseded: ""
---

# Ceremony is proportionate to the change

## Context

`LIFECYCLE.md` states the rule plainly under **Mandatory Automated Documentation**:

> **No Orphaned Code:** Every functional code change must have a corresponding Task under `docs/features/<slug>/plan/tasks/`.
> Functional code changes include: new features, bug fixes, refactors that alter behavior, API changes, and dependency updates.
> Excluded: typo fixes, comment-only edits, formatting changes, and pure documentation updates.

There is one path, and it is sized for the largest thing the system does. Walking it for a one-line bug fix costs: classify the prompt, run the spec-ambiguity check, allocate IDs, write an `ISS-*`, ensure a parent `FEAT-*` exists (create one if not), write a `TASK-*`, possibly run impact analysis and a risk scan, implement, close out, write a `CHG-*` if any path or behaviour moved, run the validator, and — because a `CHG-*` was written — obtain an independent clean-context review.

That is the correct cost for a status-vocabulary migration across ten repos. It is not the correct cost for correcting a wrong word in a constant.

The evidence that the ratio has drifted is in this repo's own numbers: 210 notes and ~94,000 words of documentation, plus ~10,000 words of instructions and 26 skills, governing ~3,700 lines of Python. The documentation is an order of magnitude larger than the thing it documents. Some of that is legitimate — this repo's *product* is the documentation system, so its notes are the deliverable. But it is not all legitimate, and the system has no way to tell which part is which, because it has no notion of a change too small to deserve the full treatment.

The comparable systems have all landed on the same answer independently. BMAD v6's scale-adaptive levels route Level 0–1 work (bug fixes, clear-scope features) to a tech-spec and one or two stories with no PRD at all, targeting two hours request-to-production, while Level 3–4 gets the full multi-agent treatment. Thoughtworks, placing spec-driven development in *Assess* rather than *Adopt*, makes the point directly: small fixes do not warrant the ceremony, so governance needs a proportionate fast path. Every serious critique of SDD in 2026 names over-specification of small work as the dominant failure mode — not under-specification.

The deeper problem is not the cost. It is that **an undeclared exception is indistinguishable from non-compliance.** When the only sanctioned path is too expensive for the work in front of it, the agent either pays or quietly skips — and a skip leaves no trace, so no check can find it and no reader can tell whether the rule is being followed. A declared fast path converts an invisible violation into a visible, auditable route.

## Decision

The lifecycle declares more than one path through itself, and the selection is written down.

### 1. Two paths, not five

**Fast path** — an `ISS-*` note, the fix, the validator, the commit. No `FEAT-*`, no `TASK-*`, no `CHG-*`, no independent review. The issue note carries what changed and why; git carries the diff.

**Full path** — the current `LIFECYCLE.md` preflight and close-out, unchanged.

Two, not BMAD's five. [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]] settled that declared values must be values the fleet actually writes, and a solo fleet does not generate enough work to populate five tracks meaningfully. If a middle path proves necessary in use, it can be added on the same evidence standard.

### 2. The selector is blast radius, not effort

A change takes the full path when it does any of:

- changes a **contract**: a status value, a field name, a check code, a template, a hook, a script interface
- changes a **path** or an artefact location
- touches anything **propagated to the fleet** by `sync-project-os.sh`
- changes **behaviour a `REQ-*` names**, or would advance a requirement
- introduces a dependency, an environment variable, or a credential surface (the existing `LIFECYCLE.md` risk-scan triggers)

Everything else may take the fast path.

Blast radius rather than effort, because effort measures what the work costs and the gates exist to guard what it can break. `ISS-0011` is the case in point: a one-word fix, XS by any estimate, latent in eleven files across ten repos. Effort would have routed it fast; blast radius routes it correctly.

### 3. The fast path is recorded, not silent

Fast-path changes still produce an `ISS-*`. The path taken is recorded on it, so "this took the fast path" is a fact in the record rather than an inference from missing artefacts — which is what makes the choice auditable at all, and what makes promotion cheap when a fast-path change turns out to have deserved the full one.

### 4. Stated once

The selector lives in exactly one file and is linked from `LIFECYCLE.md`, `issue-intake`, `ad-hoc-intake` and `close-out`. [[REQ-0018]] exists because state rules were stated in four places and three were corrected. A routing rule restated in four skills would reproduce `ISS-0006` exactly.

## Why this and not more discipline

The reflex is to say the full path is not that expensive and should simply be followed. That is the current rule, and this repo's ratio of documentation to governed code is what following it produces.

It also mistakes where the risk is. The full path's gates were each added because something specific went wrong — deferred items satisfying parents (`ISS-0002`), requirements frozen at draft (`ISS-0004`), a vocabulary rename missing three tables (`ISS-0011`). Every one of those was a **contract** change. None of them was a small isolated fix, and none would have been caught any less well by a system that routed small isolated fixes elsewhere. The gates are aimed at blast radius already; the routing rule just says so out loud.

## Consequences

See frontmatter. The load-bearing one: this is the first decision in the series that makes the system *do less*, and it should be judged on whether the fast path's population turns out to contain a defect the full path would have caught. That is a measurable question, and the answer should be measured after some months of use rather than argued now.
