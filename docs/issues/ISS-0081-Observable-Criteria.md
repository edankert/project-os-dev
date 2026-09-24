---
type: "[[issue]]"
aliases: ["ISS-0081"]
id: ISS-0081
title: "A requirement's acceptance criteria mix what the system must do with what a person would notice, and nothing checks the second kind is measurable"
status: deferred
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-22
updated: 2026-09-22
source: ["[[Comparable-Systems-Spec-Kit-2026-09-22]] — Spec Kit's FR-### and SC-### split, read 2026-09-22"]
reported_by: agent
question: "Should a requirement separate observable outcomes from system behaviour? Options: (a) a second frontmatter list and section for measurable outcomes, gated like `acceptance:`; (b) a convention in the template with no schema change; (c) decline, because most project-os requirements govern the documentation system itself and have no user-observable outcome. Recommendation: (b) first. The evidence for (a) is one external template, and this repo's own requirements are the weakest case for it."
severity: low
component: templates
parent: ""
related: ["[[Comparable-Systems-Spec-Kit-2026-09-22]]", "[[ADR-0007-Requirement-Terminality-And-Ownership]]", "[[ADR-0006-Requirement-Advancement-On-Evidence]]", "[[Comparable-Systems-Review-2026-07]]"]
tests: []
---

# A requirement's criteria mix system behaviour with observable outcome

## Problem

`docs/__templates__/requirement.md` gives a requirement one list of acceptance criteria, each ticked with an evidence pointer. Two different kinds of statement end up in that one list: what the system must do, which a test can assert, and what a person or the project would notice, which needs a measurement. Nothing distinguishes them, so nothing can check that the second kind was ever stated in measurable terms.

The practical cost is that a requirement can be fully ticked and still not say what would count as the change having worked.

## Expected

A requirement states system behaviour and observable outcome as separate, separately identified things, and the observable half is required to be measurable and independent of how it is built.

## Actual

One `acceptance: []` list, one `## Acceptance Criteria` section, one checkbox shape. The validator's REQ-BOXES gate checks that every box is ticked with evidence or reconciled. It cannot check that any of them was worth ticking.

[[REQ-0032-Ranking-Claims-Measured]] is the counter-example that makes this worth filing: it exists precisely because a claim about note ranking needed a measurement, and it had to say so in prose because the template has no slot for it.

## Evidence

Spec Kit's `templates/spec-template.md` mandates two numbered sections.

Functional requirements, each an assertion about the system:

```text
- FR-002: System MUST validate email addresses
```

Success criteria, required to be technology-agnostic and measurable:

```text
- SC-001: Users can complete account creation in under 2 minutes
- SC-003: 90% of users successfully complete primary task on first attempt
```

`templates/commands/analyze.md` builds a coverage inventory keyed on both identifier families and reports requirements with no task and tasks with no requirement. It deliberately excludes post-launch business metrics from the buildable set, which is the detail that keeps the second family from filling up with things nobody will ever check.

## Next Actions

- [ ] Decide (see `question:` in the frontmatter).
- [ ] Before building anything, sample a dozen existing `REQ-*` notes and count how many have an observable outcome that is not already a test. If the answer is low, this is ceremony and should be declined.
- [ ] Compare against EARS notation, which [[Comparable-Systems-Review-2026-07]] recorded as an unfiled groomable from Kiro. EARS constrains how a criterion is phrased; this constrains what kinds of criteria exist. They are complementary and should be decided together.
- [x] Triaged by Edwin on 2026-09-22 and parked in [[PHASE-999-Parking-Lot|PHASE-999]]. Deferred means still wanted: the `question:` above is the decision re-adoption has to make, not one that is waiting on anyone now.
