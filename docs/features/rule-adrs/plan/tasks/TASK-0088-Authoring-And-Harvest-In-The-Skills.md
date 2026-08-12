---
type: "[[task]]"
id: TASK-0088
aliases: ["TASK-0088"]
title: "adr-authoring learns to write a rule-ADR; issue-intake learns to harvest one on the second issue of a kind"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[REQ-0025]]"]
parent: "[[FEAT-0023]]"
effort: M
due: ""
depends: ["[[TASK-0086]]"]
blocks: []
related: ["[[ADR-0004]]", "[[ADR-0016]]", "[[ISS-0005]]"]
tests: []
---

# The two skills

## What

Two edits in `~/Dev/repos/project-os/tools/skills/`, doing genuinely different jobs.

**`adr-authoring/SKILL.md` — how to author one.** A branch in the checklist: if the decision is a quantified rule, add the three sections, and take the Domain seriously enough to fail fast. The step that earns its place is *name the domain first* — if the set cannot be enumerated, stop, because the rule is not ready and no amount of drafting will make it ready.

**`issue-intake/SKILL.md` — the harvest step.** On intake, before allocating an ID, look for a sibling: has an issue of this kind been filed before? If this is the **second**, propose a rule-ADR rather than filing a third one-off later.

## Why the harvest step is the one that changes behaviour

The authoring branch is a convenience — someone who has decided to write a rule can find the shape. The harvest step is the only part of this feature that catches a rule **nobody has thought to write**, and that is the entire measured cost: `your-health` filed at least 15 issues across four cross-cutting families (null-versus-zero, day-attribution, comparator-includes-today, rounding) retail, one at a time, because nothing at intake ever asked whether this one had siblings.

[[ISS-0005]] is the same failure at the other end of the lifecycle: five cross-cutting policies filed as feature-less requirements, discovered only when someone went looking a year later.

**Phrase it as a mandatory step with an explicit trigger, not a suggestion.** [[ADR-0004]] measured what conditional phrasing produces — agents skip the step by deciding the condition does not apply, *even when it did* — which is why risk scans, verification gating and impact analysis were made mandatory with explicit checklists. "Consider whether a rule might apply" will be skipped; "search the issue corpus for a sibling; if one exists, propose a rule-ADR" will not.

## The tension to resolve, not ignore

[[ADR-0016]] (`proposed`) argues ceremony should be proportionate to the change, with a declared fast path for small ones. A sibling search at every intake is ceremony added to the highest-frequency operation in the system.

Resolve it explicitly in the skill rather than leaving both rules standing and letting the next agent pick:

- Bound the search — the issue corpus of the current repo, by keyword and by the surface the issue touches, not a semantic reading of every note.
- Make the negative result cheap and recordable: "no sibling found" is one line, in the same spirit as the risk scan's explicit negative.
- State that the trigger is the second issue, so the first one — the common case — costs a lookup and nothing else.

## Definition of Done

- [x] `tools/skills/adr-authoring/SKILL.md` carries the rule-ADR branch, with *name the domain first, and stop if it cannot be enumerated* as an explicit step; semantics are linked to `DECISIONS.md`, not restated — evidence: project-os `6ca15f4`, checklist step 3, whose first bullet is the stop rule (with the observation that the missing registry is often the real first deliverable).
- [x] `tools/skills/issue-intake/SKILL.md` carries the harvest step as a mandatory step with an explicit trigger, positioned before ID allocation, with the bound on the search and the cheap negative result both stated — evidence: `6ca15f4`, checklist step 2 of 10 (ID allocation is step 3): bounded to grepping this repo's `docs/issues/` by keyword and surface; the negative is one recorded line, in the same spirit as the risk scan's explicit negative; the trigger is the second issue of a kind, which still gets filed — the rule-ADR is proposed so the third one-off never needs to be.
- [x] The ADR-0016 tension is addressed in the skill text itself, not only in this task note — evidence: the step says in as many words that the one-line negative is the entire cost in the common case, which keeps a mandatory step proportionate on the system's highest-frequency operation, and that it stays mandatory rather than conditional because conditional steps get skipped even when the condition holds (ADR-0004).
- [x] Both skills link to `tools/instructions/DECISIONS.md` and restate none of it (checked against TASK-0086's diff) — evidence: each cites the section by name ("A decision that states a rule") and adds only its own behaviour. **Corrected after review round one** (`244baec`): the first landing restated one normative sentence in each skill — the domain-readiness sentence in adr-authoring, the one-is-a-bug-two-is-a-domain sentence in issue-intake — and the box was ticked over them. Both are pointers since project-os `4aa2238` (adr-authoring names the `## Domain` bullet, issue-intake the Provenance paragraph), so a future amendment to either sentence has one home and no stale copy.
- [x] `python3 tools/scripts/generate-adapters.py --check` clean — evidence: all 35 artifacts current after both edits, with no regeneration needed: the generated skills are pointers to the canonical playbooks, so a checklist edit does not reach them.
- [x] `bash tools/scripts/validate-docs.sh` clean in `project-os` — evidence: pre-commit run on `6ca15f4`, exit 0.

## Notes

Both files are template-owned and sync to eleven repos. `issue-intake/SKILL.md` in particular is invoked constantly, so a step added there is paid on every intake in the fleet — which is the reason to bound it carefully and the reason it is worth adding at all.
