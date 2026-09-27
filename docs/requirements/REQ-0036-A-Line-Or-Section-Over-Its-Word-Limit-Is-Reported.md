---
type: "[[requirement]]"
id: REQ-0036
aliases: ["REQ-0036"]
title: "An action line, an expected line or a section over its word limit is reported, and release preparation writes the short text and checks it"
status: implemented
review_verdict: approved
review_round: 2
review_date: 2026-09-27
reviewed_by: "model:claude-opus-5-5 (FEAT-0040 review, two rounds)"
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["Edwin, 2026-09-27: the length guard and the rollout order", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]] (D3)", "Edwin, 2026-09-27, approving REQ-0033 to REQ-0037: 'approved, start stage 2'"]
priority: high
scope: "the generator's --check, tools/skills/release-test-prep/, tools/skills/release-prep/"
acceptance:
  - "The check reports each action line over its limit (default 20 words) and each expected line over its limit (default 25 words), naming the section, the check number and the tag"
  - "The check reports a section whose printed words exceed its budget"
  - "The limits and the budget are set in one place, and a switch makes the report an error instead of a warning"
  - "release-test-prep writes the what-changed lines, shortens Expect lines and shortens procedure actions with an agent, and keeps its edits only when the length check and the validator pass"
  - "release-prep calls release-test-prep before the release test is handed over"
implements: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
verifies: []
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
tests: []
---

# An action line, an expected line or a section over its word limit is reported

## Statement

The validator shall report every action line, expected line and section that is longer than its limit. It shall start as a warning and become an error once your-trainer's sections pass. Release preparation shall include a skill that writes the short text with an agent and then runs this check.

The limits:

- An action line: about 20 words.
- An expected line: about 25 words.
- A section: a budget of printed words. The approved Equipment Hub example prints about 1,000 words for 28 checks. Edwin decided on 2026-09-27 that the pilot sets it: the rewritten Equipment section is measured, and the budget is set from it, for example as words per check.

A limit counts the words the tester sees on the page, after the generator has picked this platform's lines.

**The skill.** `tools/skills/release-test-prep/SKILL.md` runs at release preparation and prepares the whole release test in one request ([[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks|ADR-0050]], D3). Edwin widened it on 2026-09-27. For each platform it recaptures the screenshots and flags stale ones, finds the sections whose owed checks changed, rewrites those sections' procedures with the procedure skill, writes the what-changed lines (REQ-0035), and shortens each over-long Expect line in the test note itself (REQ-0034). A change of meaning is a change to the check and reopens it in the ledger. [[TASK-0193-A-Release-Preparation-Skill-Writes-The-Short-Text|TASK-0193]] lists the seven steps in order.

It then runs the length check and the validator. It keeps its edits only if both pass, and the owner reviews them in the commit.

## Acceptance Criteria

- [x] The check reports each action line over its limit (default 20 words) and each expected line over its limit (default 25 words), naming the section, the check number and the tag — evidence: `length_findings` (TASK-0192, template 9044d67)
- [x] The check reports a section whose printed words exceed its budget — evidence: `length_findings` section budget (TASK-0192)
- [x] The limits and the budget are set in one place, and a switch makes the report an error instead of a warning — evidence: `LengthLimits` and `length_limits:`; errors by default since template aa5fd7e (TASK-0196)
- [x] release-test-prep writes the what-changed lines, shortens Expect lines and shortens procedure actions with an agent, and keeps its edits only when the length check and the validator pass — evidence: the `release-test-prep` skill (TASK-0193, template 25e4eed), used to prepare your-trainer's v2.2.0 on 2026-09-27
- [x] release-prep calls release-test-prep before the release test is handed over — evidence: `release-prep` step 2a (TASK-0193, template 25e4eed)

## Traceability

- Implements: [[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]
- Verified by: the renamed `test-release-test.sh`, once TASK-0192 lands; the skill by the Equipment pilot in your-trainer.
