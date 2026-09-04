---
type: "[[requirement]]"
id: REQ-0027
aliases: ["REQ-0027"]
title: "Every normative rule is stated in exactly one file"
status: implemented
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: "2026-09-04"
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

- [x] Every normative rule in the scope has exactly one home file; every other document links to it — evidence: twelve sweep passes, 2026-09-03 to 2026-09-04, fixing 36 + 26 + 2 + 3 + 2 + 2 + 21 + 2 + 5 + 25 restatements across template commits `1b5956e` through `e2bee28`. The criterion is met in the sense it can be: the clean-pair test it was written against does not terminate on a corpus this size, and [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] replaced it with a bounded round plus a recorded residue. Pass 12's residue is on [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]], and the classes that keep recurring become checks ([[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks|ISS-0052]], first one built)
- [x] ISS-0041, ISS-0042 and ISS-0043 are resolved by deletion and linking — evidence: template commits `1b5956e`, `685eef7`, `0049206` (2026-09-03), each deleting the copy and linking the home
- [x] The six criteria of REQ-0018 remain satisfied — evidence: rows 4, 8, 13 and 14 of ISS-0048 were the state and transition rules restated, and all four were fixed in template commits `ab94b0c` and `09ae4dc`. Re-checked on 2026-09-04 after passes 11 and 12: the status value lists live only in STATUSES.md, the three documents that had grown their own copies (`docs/STYLEGUIDE.md`, `docs/releases/README.md`, `docs/phases/README.md`) now link it, and `BASE-STATUS` enforces the same rule for the shipped views mechanically
- [x] The docs-audit skill names this rule and the audit runs on cadence — evidence: template commit `c5dc296` (2026-09-03), dimension 6 names ADR-0024, the four issues, the fix and the cadence; the first run under it is ISS-0048
- [x] RULE-ONCE decided or declined — evidence: ADR-0024 "Acceptance", the second box: declined for now on a count of 36, 2026-09-03, with the reasons and the condition for reconsidering

## Why a requirement and not only the ADR

The ADR records the decision. The requirement is what a feature or an audit can be checked against, and what stays true after the four current issues close. Without it, the fifth restatement is filed as a one-off, which is the failure the intake harvest rule exists to catch.

## Traceability

- Decision: [[ADR-0024-A-Normative-Rule-Is-Stated-Once]]
- Supersedes: [[REQ-0018-State-Rules-Stated-Once]]
- Instances: ISS-0006 (fixed, July), ISS-0041, ISS-0042, ISS-0043
- Verified by: the docs-audit skill's instruction/template-drift dimension, run to quiescence
