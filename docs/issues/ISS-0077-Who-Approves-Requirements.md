---
type: "[[issue]]"
id: ISS-0077
aliases: ["ISS-0077"]
title: "Two files disagree about who approves a requirement, so an agent can approve its own acceptance criteria"
status: "open"
phase: ""
owner: user:edwin
created: 2026-09-21
updated: "2026-09-26"
source: ["planning pass for [[FEAT-0038-Note-Relevance-Harness|FEAT-0038]], 2026-09-21"]
reported_by: agent
question: "Which file keeps the rule — OWNERSHIP.md (approval is the owner's) or feature-scaffold step 7 (the scaffolding agent approves)? REQ-0027 says delete the copy and link, never correct the copy, so the answer decides which one loses its sentence. Recommendation: OWNERSHIP.md keeps it, because it is the file about who owns what and the skill is a playbook that should link."
severity: medium
component: instructions
parent: ""
related: ["[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[ISS-0006-Rules-Stated-In-More-Than-One-File]]", "[[REQ-0032-Ranking-Claims-Measured]]"]
tests: []
---

# Two files disagree about who approves a requirement

## Problem

An agent scaffolding a feature reads that it should approve the requirement itself, and an agent reading the ownership rules reads that approval belongs to the requirement's owner. Both are in `tools/instructions/` or `tools/skills/`, both are current, and neither links to the other. An agent that reads only the first one approves its own acceptance criteria and moves the feature to `doing` without the stakeholder ever seeing them — which is the outcome the gate exists to prevent.

This is the defect class [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]] exists to stop, and the fourth instance the repo has recorded after the [[ISS-0006-Rules-Stated-In-More-Than-One-File]] family.

## Repro

```
grep -n -A3 'Requirement approval gate' tools/skills/feature-scaffold/SKILL.md
grep -n -B2 -A4 'stakeholder' tools/instructions/OWNERSHIP.md
```

## Expected

One file states who approves a requirement. Every other document links to it.

## Actual

`tools/skills/feature-scaffold/SKILL.md:51-53` — "**Requirement approval gate:** The gate is `STATUSES.md` `[[feature]]`: approve the requirement (or amend it first, then approve) before the feature moves to `doing`. Approval means the acceptance criteria are the ones you intend to build against". Addressed to the scaffolding agent, naming no human.

`tools/instructions/OWNERSHIP.md:30` — "`[[requirement]]`: stakeholder/approver".

`tools/instructions/STATUSES.md`'s who-writes-the-status table reserves "human decision" for `adr` alone, so it does not settle the question either.

## Evidence

- Found live on 2026-09-21: the planner scaffolding [[FEAT-0038-Note-Relevance-Harness|FEAT-0038]] stopped rather than approve [[REQ-0032-Ranking-Claims-Measured|REQ-0032]], took the ownership rule as the more specific one, and handed the approval to Edwin. A less careful pass would have read step 7 alone and approved it.
- REQ-0032 was approved by Edwin on 2026-09-21, so this issue is not blocking that feature.

## Next Actions

- [ ] Decide which file keeps the rule (see `question:` in the frontmatter).
- [ ] Delete the statement from the other and replace it with a link; do not correct both copies ([[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]).
- [ ] Check whether `STATUSES.md`'s who-writes-the-status table should name the approver for `requirement`, since today it is silent for every type but `adr`.
