---
type: "[[adr]]"
id: ADR-0019
aliases: ["ADR-0019"]
title: "A change note records what happened and does not owe a review — the REVIEW gate narrows to tests and terminal transitions, answering the question ADR-0011 left open"
status: accepted
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["Edwin 2026-08-11, using project-os-cockpit: 'Not sure why these CHG notes are open, they seem to in general store the changes that happened and do not need any review.'", "Measured 2026-08-11 in project-os-cockpit: the overview obligation badge read 87 and 87 of 87 were change-note reviews"]
decision: "A CHG-* note carries no independent-review obligation. REVIEW gates TST-* notes and the transitions to requirement `implemented` and feature `done`. `REVIEW_SETTLED_STATUSES` drops its `changes` entry; QUALITY.md drops `CHG-*` from the requiring sentence."
context: "ADR-0011 promoted REVIEW on a dated cutover (2026-10-23) and named its scope an open question in its own consequences. A year of evidence answered it: the obligation was never discharged anywhere."
alternatives:
  - "Wire review into close-out so it does run — ADR-0011's other branch. Rejected on the evidence: it HAS been wired into close-out in the adapter for months, and the notes still went unreviewed, because the step that gets skipped under context pressure is the one whose value nobody can state"
  - "Discharge in bulk at release time, one pass per release. Rejected: it keeps a gate whose value nobody can state and attaches it to the moment already carrying the most work"
  - "Keep it and make the surface lead to the queue. Rejected by Edwin: making 87 six-month-old notes easier to work through is not the same as their being worth working through"
  - "Narrow to CHG-* only, the wording ADR-0011 actually used. Rejected as the exact inverse of the evidence: the TST-* half is where a second pair of eyes changes an outcome, and it is the half that was being skipped alongside"
consequences:
  - "`REVIEW_SETTLED_STATUSES` loses its `changes` entry; the 2026-10-23 promotion still lands, for tests only, and no longer reds every repo's CI over change notes"
  - "Fleet effect measured 2026-08-11: 87 findings clear in project-os-cockpit alone, and every repo's obligation surface stops counting records-of-the-past as work"
  - "`tools/cockpit/`'s bundled validator carries the same table and is owed the same edit; it is a verbatim copy of the canonical script and was left untouched here because it is dirty with unrelated in-flight work"
  - "Downstream repos pick this up on their next template sync. project-os-cockpit made the registry change locally the day before and recorded the disagreement rather than editing template-owned code, which is the boundary working as intended"
supersedes: ""
superseded: ""
related: [ADR-0011, ADR-0013, ADR-0004]
---

# A change note is not reviewed

## Context

[[ADR-0011]] made every validator rule an error or a deletion, with `warn` surviving only as a dated migration state. `REVIEW` was its hardest case, and it said so:

> *"REVIEW is the hardest case: 206 findings means independent review is effectively not running. It is either wired into close-out so it does run, or its scope narrows."*

**That question was never answered, and the dated cutover kept running toward it.** Measured 2026-08-11 in `project-os-cockpit`, the repo whose own subject is making obligations visible: its overview badge read **87, and all 87 were change-note reviews** — the largest obligation in the registry, none of them discharged, the oldest from May, every one accruing toward `2026-10-23`.

The first branch was tried. An `independent-reviewer` subagent exists, it is wired into the Claude adapter, and close-out names it. The notes still went unreviewed for six months, which is the strongest available evidence about which branch is real.

## Decision

**A `CHG-*` note carries no independent-review obligation.** REVIEW gates:

1. **`TST-*` notes** — the author of a fix must not be the sole judge of the test that guards it.
2. **requirement → `implemented`** and **feature → `done`** — a claim that something is finished.

## Why this and not the other branch

**A change note is a record, not a claim.** It says *this happened*. What a reviewer could usefully challenge is the change itself — and that review happens against the diff while the work is live, which is what the two remaining gates are for. Reviewing the note months later reviews the prose.

The value is not zero, and that is worth being honest about: a change note can overstate what shipped, and a reviewer reading it cold would catch that. But the same reviewer reading the *diff* catches it better and sooner, and the gate that produced 206 unread findings is not the mechanism that was catching it.

**An obligation nobody discharges is a countdown, not a standard.** ADR-0011's own argument, applied to one of its own clauses: a warning that never changes anyone's behaviour is worse than absent, because it trains readers to skim past what is printed beside it. Six months of `REVIEW` findings did exactly that.

## What this does not change

- **Self-review stays forbidden** ([[ADR-0013]]), and independence stays clean-context rather than model-family.
- **The dated-promotion mechanism stands.** This narrows what REVIEW checks; it does not grant a permanent warning, which is the thing [[ADR-0011]] exists to forbid. The 2026-10-23 cutover lands on schedule for tests.
- **Reviewing a change note remains possible** and is never wrong. It stops being owed.
