---
type: "[[adr]]"
id: ADR-0024
aliases: ["ADR-0024"]
title: "A normative rule is stated in one file and linked everywhere else"
status: "accepted"
owner: user:edwin
created: 2026-09-03
updated: "2026-09-03"
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 1.1-1.3", "issue-intake harvest trigger, second issue of a kind"]
decision: "Option 1. Widen REQ-0018 from state rules to every normative rule; a terminal requirement is not reopened, so REQ-0027 supersedes it. Discharge is the docs-audit drift dimension; a mechanical RULE-ONCE check stays an open acceptance thread"
decided_option: 1
context: "Four issues in fourteen months describe the same failure: a rule stated in two or more files, amended in one, leaving the others instructing agents to apply a rule the project had already changed."
alternatives: []
consequences: []
supersedes: ""
superseded: ""
related: ["[[ISS-0006-Status-Transition-Test-Gates-Requirements]]", "[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]", "[[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]]", "[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]", "[[REQ-0018-State-Rules-Stated-Once]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[ADR-0023-A-Quantified-Rule-Is-A-Decision]]"]
---

# A normative rule is stated in one file and linked everywhere else

**Accepted 2026-09-03 with option 1** (decision record below). This note exists because the issue-intake harvest trigger fired: three issues of one kind were filed on 2026-09-03 and a fourth was fixed in July, and the playbook says the second issue of a kind proposes a rule covering the family. Option 1 widens REQ-0018 from state rules to every normative rule. A terminal requirement is not reopened, so the widening is recorded as [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]], which supersedes REQ-0018.

## Context

Four instances, same shape:

| Issue | The rule | Stated in | Amended in | Result |
|---|---|---|---|---|
| [[ISS-0006-Status-Transition-Test-Gates-Requirements]] (fixed) | requirements are not gated on linked tests | 4 files | 3 | every repo told agents to apply a gate ADR-0007 had reverted |
| [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]] | what makes a reviewer independent | 6 files | 2 | the skill contradicts itself two paragraphs apart |
| [[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]] | how a gate is grandfathered | 2 files | 1 | two mechanisms, one implemented |
| [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]] | status and test vocabulary | 8 places | the taxonomy only | the release flow writes values that do not exist |

Nothing detects any of this, because no check compares prose to prose. Each was found by a person reading two files in one sitting.

[[REQ-0018-State-Rules-Stated-Once]] already states this rule and is `implemented` — but only for state and transition rules. Three of the four instances above are not state rules. The requirement is not wrong; its domain is narrower than the failure.

## Options

1. **Widen REQ-0018.** Amend it to cover every normative rule, not only state rules. Cheapest, and keeps one statement of the rule. Costs: it reopens an `implemented` requirement, and a requirement is a thing to build, whereas this is a standing constraint on how the corpus is written.

2. **A rule-ADR (this note).** Record it as a quantified rule under [[ADR-0023-A-Quantified-Rule-Is-A-Decision]], leaving REQ-0018 as the delivered state-rule case. Costs: a second document about one subject, which is the thing the rule itself objects to, unless REQ-0018 explicitly defers to it.

3. **File the fifth one-off when it happens.** Honest baseline. Costs: the four above took a reader with two files open; the fifth needs the same luck.

## Rule

Every normative rule in project-os is stated in exactly one file. Every other document links to that statement rather than restating it.

## Domain

The files under `tools/instructions/`, `tools/skills/` and `docs/__templates__/` in the project-os template, plus the adapter outputs generated from them (`.cursor/rules/*.mdc`, `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`, `AGENTS.md`). Enumerable: 17 instruction files, 25 skills, 18 templates, and the generator's outputs as of 2026-09-03.

## Conformance

**Option 1, decided 2026-09-03.** [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]] carries the acceptance criteria and supersedes REQ-0018. The discharge is the docs-audit skill's "instruction/template drift" dimension, run to quiescence at each backlog-grooming pass and before each release. It is a pass a person or agent runs, and the rule is honest about that: it would have caught all eight rows of ISS-0043, and it catches nothing when nobody runs it. Authoritative on conflict: the file the rule names as its home; the restating file is the one in error.

A mechanical `RULE-ONCE` validator check over a registry of rule phrases is the alternative that survives nobody running anything. It is not decided here. Under [[ADR-0011-No-Permanent-Warning-Tier]] it would need a counted violation set and either an error from day one or a dated cutover, and the count today is four. It stays open as the second acceptance thread below.

## Acceptance

- [x] **REQ-0018 widened:** [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]] approved and REQ-0018 superseded by it — evidence: both notes, 2026-09-03, this commit
- [x] **`RULE-ONCE`:** declined for now, on a count of 36 — evidence: the first drift sweep at the close of PHASE-0003 (2026-09-03, [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]]) found 36 confirmed restatements. Under ADR-0011 a check over that debt could only land warning-first with a dated cutover and a 36-entry grandfather list, and it would need a registry of rule phrases that does not exist. The docs-audit drift dimension is the discharge, and it found the 36 without a registry. Reconsider when ISS-0048 closes: a corpus at zero is when an error-from-day-one check can land. Recorded by the implementing session, not by the owner; the owner may overturn it on ISS-0048.

## Consequences

- If accepted with the docs-audit discharge: the audit becomes due on a cadence rather than on suspicion, and the rule is honest about being human-run.
- If accepted with `RULE-ONCE`: a new validator check, a registry, and a counted violation set taken at landing (the ADR-0021 precedent).
- If rejected: ISS-0041 to ISS-0043 are still fixed on their own merits. Nothing in the plan depends on this note.

## Decision record

> [!note] Accept — 2026-09-03 (user:edwin)
> Let's go for option 1.

> [!note] Decline `RULE-ONCE` for now — 2026-09-03 (model:claude-fable-5-1, implementing PHASE-0003)
> The first sweep counted 36 restatements. A mechanical check over that debt would be a permanent warning tier in all but name, and the sweep found the 36 without a registry. Declined until ISS-0048 brings the count to zero; the owner may overturn this.
