---
type: "[[issue]]"
aliases: ["ISS-0080"]
id: ISS-0080
title: "An ambiguity the agent decided to live with leaves no trace, so the next reader cannot tell a settled question from an unasked one"
status: deferred
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-22
updated: 2026-09-22
source: ["[[Comparable-Systems-Spec-Kit-2026-09-22]] — Spec Kit's [NEEDS CLARIFICATION] markers and /speckit-clarify, read 2026-09-22"]
reported_by: agent
question: "Should an unresolved ambiguity be a marker in the note rather than a judgement made once at intake? Options: (a) an inline `[NEEDS CLARIFICATION: ...]` token plus a validator check that a terminal status carries none; (b) a frontmatter list, which sorts and counts but loses the position in the text; (c) decline, since the `question:` field already exists for the blocking case. Recommendation: (a), because the whole value is that it sits at the sentence it is about, and the `question:` field only covers ambiguities that stopped the work."
severity: medium
component: templates
parent: ""
related: ["[[Comparable-Systems-Spec-Kit-2026-09-22]]", "[[ISS-0077-Who-Approves-Requirements]]", "[[ADR-0014-Evidence-Is-Typed-And-Checkable]]"]
tests: []
---

# An ambiguity the agent decided to live with leaves no trace

## Problem

`tools/skills/issue-intake/SKILL.md` step 1 tells an agent to check a prompt for ambiguity, and `LIFECYCLE.md` sets the threshold for stopping: implement the reading the wording most directly supports and state the assumption, ask only when proceeding would be unsafe or useless. That is the right rule, and it produces nothing durable. The assumption is stated in a turn summary the next session will never read.

A later reader of a requirement cannot tell which sentences were considered and judged clear, which were ambiguous and resolved by a decision, and which nobody looked at.

## Expected

An ambiguity an agent chose not to stop for is marked in the note, at the sentence it is about. A note carrying a marker cannot reach a terminal status.

## Actual

There are two places an open question can live and neither covers this case. The issue template's `question:` field is for an item that is waiting on its owner, so it only holds ambiguities that stopped the work. The requirement template's Acceptance Criteria carry evidence pointers once ticked, which records how a criterion was satisfied and not whether it was clear.

Nothing holds "this phrase admits two readings, I took the first, and here is the other".

## Evidence

Spec Kit's `templates/spec-template.md` writes ambiguity inline, in the requirement itself:

```text
- FR-006: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- FR-007: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]
```

`templates/commands/clarify.md` then scans the spec against a fixed taxonomy — functional scope and behaviour, domain and data model, interaction and UX flow, non-functional quality attributes, integrations and external dependencies, edge cases and failure handling, constraints and tradeoffs — marks each category Clear, Partial or Missing, asks at most five targeted questions, and writes the answers back into the spec. The bound of five is what stops the pass becoming an interrogation.

The template also mandates an `## Assumptions` section, which is the durable half of the same idea: the defaults chosen where the description did not specify.

## Next Actions

- [ ] Decide (see `question:` in the frontmatter).
- [ ] If adopted: add the marker to the requirement and feature templates, and a validator check that refuses `implemented` or `done` on a note that still carries one.
- [ ] Consider the taxonomy separately from the marker. The seven categories are usable as a review prompt on their own, and they are cheaper than the marker because they need no schema change.
- [ ] Check whether an `## Assumptions` section belongs in the requirement template regardless of the rest.
- [x] Triaged by Edwin on 2026-09-22 and parked in [[PHASE-999-Parking-Lot|PHASE-999]]. Deferred means still wanted: the `question:` above is the decision re-adoption has to make, not one that is waiting on anyone now.
