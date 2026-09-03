---
type: "[[task]]"
id: TASK-0092
aliases: ["TASK-0092"]
title: "Give the spec-ambiguity check a threshold; the planner allocates what is settled"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 2.3"]
parent: "[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"
effort: S
depends: []
related: ["[[ADR-0004-Mandatory-Skill-Steps]]"]
tests: []
---

# Give the spec-ambiguity check a threshold; the planner allocates what is settled

## Definition of Done
- [x] `issue-intake/SKILL.md` step 1 says to check in only when different readings lead to materially different work; otherwise implement the reading the wording most directly supports and record the assumption in the note.
- [x] The check itself stays mandatory and still runs on every intake. What changes is the action on a term with two harmless readings, not whether the check happens.
- [x] The planner's rule 5 in `tools/scripts/generate-adapters.py` reads: allocate and draft what is settled, and return the ambiguities as questions beside it.
- [x] The generator is re-run and `.claude/agents/planner.md` committed with it.

## Steps
- [x] Edit the five bullets of the check so the threshold applies to all of them, not only the first.
- [x] Edit the planner prompt string; keep the sentence that ambiguity is upstream of documentation.

## Notes

**Tension with [[ADR-0004-Mandatory-Skill-Steps]], stated rather than resolved silently.** ADR-0004's finding is that conditional steps get skipped by deciding the condition does not apply. A threshold is a judgement, so it can be misused the same way. Two things keep it honest: the check stays unconditional, and the assumption must be written into the note, which makes a wrong reading visible to the next reader instead of invisible. If the owner disagrees, the fallback is to keep the stop and add only the planner half.

Today a term with two meanings fails bullet one even when both readings lead to the same fix, and the planner returns zero notes for a five-part scaffold with one unclear item.

Landed as template commit `7ae32ed` on 2026-09-03. The ADR-0004 tension is stated in the skill text: the check is not conditional, only the action on a failure is.
