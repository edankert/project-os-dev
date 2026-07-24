---
type: "[[requirement]]"
id: REQ-0008
aliases: ["REQ-0008"]
title: "Impact analysis must run as mandatory preflight for new requirements"
status: implemented
owner: user:edwin
created: 2026-03-08
updated: 2026-07-21
priority: high
implements: ["[[FEAT-0005]]"]
acceptance:
  - "Feature-scaffold skill includes impact analysis as a mandatory step for features carrying requirements"
  - "Issue-intake skill runs impact analysis when the issue touches existing features or is spec-ambiguous"
  - "Impact analysis skill exists as a structured playbook; the mandatory STOP on unresolved conflict is stated by every call site (feature-scaffold, issue-intake, LIFECYCLE preflight)"
  - "LIFECYCLE.md includes impact analysis in preflight for new requirements"
related: [ADR-0004]
---

# Impact analysis must run as mandatory preflight for new requirements

## Acceptance Criteria

- [x] Feature-scaffold includes impact analysis as a mandatory step for features carrying requirements — evidence: `tools/skills/feature-scaffold/SKILL.md` step 6 "Impact analysis (mandatory for features with requirements)".
- [x] Issue-intake runs impact analysis when the issue touches existing features or is spec-ambiguous — evidence: `tools/skills/issue-intake/SKILL.md` step 7 (issues linking existing features) and step 1's spec-ambiguity check.
- [x] The impact-analysis skill exists as a structured playbook with a STOP on unresolved conflict — evidence: `tools/skills/impact-analysis/SKILL.md` (5-step checklist: surface → constraints → tensions → findings → resolution); the hard STOP is enforced at every call site — `feature-scaffold/SKILL.md`, `issue-intake/SKILL.md`, and `LIFECYCLE.md` preflight step 5 all read "If conflicts are found, stop and present resolution options before implementation".
- [x] LIFECYCLE.md preflight includes impact analysis for new requirements — evidence: `tools/instructions/LIFECYCLE.md` preflight step 5, "Run … when creating or materially changing requirements", plus new features/issues touching constrained areas.

## Amendments (2026-07-21)

**Criteria 1 and 2** were narrowed from unconditional to conditional, matching what shipped: impact analysis is mandatory *for features that carry requirements* and *for issues that touch existing features or are spec-ambiguous*. Running a full impact analysis for a typo-fix issue was judged waste; the trigger conditions are explicit in each skill.

**Criterion 3** was reconciled on where the STOP lives. The skill's own step 5 offers four resolution routes (supersede / narrow / ADR / stop for user decision); the *mandatory* stop is stated by the three callers instead. That is the shipped enforcement shape and the criterion now names it. A reader of the skill alone would not see a hard STOP — accepted, since the skill is only ever entered from a caller that states it.

