---
type: "[[requirement]]"
id: REQ-0027
aliases: ["REQ-0027"]
title: "Every normative rule is stated in exactly one file"
status: approved
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
priority: high
scope: "tools/instructions/, tools/skills/ and docs/__templates__/ in the project-os template, and the adapter outputs generated from them"
source: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]] option 1", "[[Prompting-Guide-Review-2026-09-03]] findings 1.1 to 1.3"]
acceptance:
  - "Every normative rule in the scope has exactly one home file; every other document links to it rather than restating it."
  - "ISS-0041, ISS-0042 and ISS-0043 are resolved by deleting the restatement and linking, not by correcting another copy."
  - "The six criteria of REQ-0018 remain satisfied after the widening."
  - "The docs-audit skill names this rule as what its instruction/template-drift dimension checks, and the audit is run to quiescence before each release and at each backlog-grooming pass."
  - "A mechanical check (RULE-ONCE) is decided or declined, recorded in ADR-0024's Acceptance section with the violation count that decided it."
implements: ""
supersedes: "[[REQ-0018-State-Rules-Stated-Once]]"
verifies: []
related: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[REQ-0018-State-Rules-Stated-Once]]", "[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]", "[[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]]", "[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]"]
tests: []
---

# Every normative rule is stated in exactly one file

## Statement

Every normative rule in project-os shall be stated in exactly one file. Every other document shall link to that statement rather than restate it. A restatement is a copy that the next amendment can miss, and four issues in fourteen months show that it does get missed.

This widens [[REQ-0018-State-Rules-Stated-Once|REQ-0018]] from state and transition rules to every normative rule. REQ-0018 was `implemented`, and a terminal requirement is not reopened, so this requirement supersedes it (ADR-0024, option 1). REQ-0018's six criteria stay in force through criterion 3 below.

## Acceptance Criteria

- [ ] Every normative rule in the scope has exactly one home file; every other document links to it — evidence: the docs-audit drift sweep at the close of PHASE-0003
- [ ] ISS-0041, ISS-0042 and ISS-0043 are resolved by deletion and linking — evidence: the three template commits, each removing the restated text
- [ ] The six criteria of REQ-0018 remain satisfied — evidence: REQ-0018's ticked criteria, re-checked in the same sweep
- [ ] The docs-audit skill names this rule and the audit runs on cadence — evidence: `tools/skills/docs-audit/SKILL.md` "Audit dimensions", and the CHG note of the first audit run under this rule
- [ ] RULE-ONCE decided or declined — evidence: ADR-0024 "Acceptance", the second box

## Why a requirement and not only the ADR

The ADR records the decision. The requirement is what a feature or an audit can be checked against, and what stays true after the four current issues close. Without it, the fifth restatement is filed as a one-off, which is the failure the intake harvest rule exists to catch.

## Traceability

- Decision: [[ADR-0024-A-Normative-Rule-Is-Stated-Once]]
- Supersedes: [[REQ-0018-State-Rules-Stated-Once]]
- Instances: ISS-0006 (fixed, July), ISS-0041, ISS-0042, ISS-0043
- Verified by: the docs-audit skill's instruction/template-drift dimension, run to quiescence
