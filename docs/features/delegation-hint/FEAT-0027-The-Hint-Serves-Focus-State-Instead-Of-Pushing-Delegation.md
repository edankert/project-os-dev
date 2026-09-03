---
type: "[[feature]]"
id: FEAT-0027
aliases: ["FEAT-0027"]
title: "The hint serves focus state instead of pushing delegation"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 2.2, 3.1, 3.2, 7.3"]
goal: "Turn the per-prompt hint from an instruction to delegate into a statement of where the work stands, and make the two hooks name actions an agent can actually take. Delegation, when it is recommended, carries the user's own words."
requirements: []
tasks: ["[[TASK-0102]]", "[[TASK-0103]]", "[[TASK-0104]]", "[[TASK-0105]]"]
release: ""
related: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]", "[[ADR-0003-Delegate-Orchestration]]"]
tests: ["[[TST-0007]]"]
---

# The hint serves focus state instead of pushing delegation

## Goal

HC-008 fires on every prompt. In every terminal or empty state it says "delegate preflight to the 'planner' subagent before coding", and every variant ends with "Independent review goes to 'independent-reviewer'" — including on prompts that are questions. Preflight for a one-line bug fix is one issue note and one snapshot entry; a planner subagent re-reads the repo to produce them.

**The documentation requirement does not change.** Every change still gets its note before the code. What changes is who writes the note: the main loop for a single issue or task, the planner for a multi-item scaffold or an ambiguous ask.

The Stop hook has the same shape of problem. It blocks the stop and says "acknowledge to continue", which is not an action, so the model either writes a sentence of acknowledgement or resumes work it had decided to hand off.

## Scope

| Task | Finding | Files |
|---|---|---|
| [[TASK-0102]] | 2.2 | `hooks/close-out-check.sh` |
| [[TASK-0103]] | 3.1 | `hooks/model-routing-hint.sh`, `HOOKS.md` HC-008, `ADAPTER.md` routing table |
| [[TASK-0104]] | 3.2 | `generate-adapters.py` (hint and planner prompt) |
| [[TASK-0105]] | 7.3 | `docs/__templates__/issue.md`, `ad-hoc-intake/SKILL.md`, `issue-intake/SKILL.md` |

Finding 2.4, the document-first gate blocking files outside any project-os repo, is already on record as point 3 of [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]] and is not duplicated here. [[TST-0007]] covers it, because the same harness that tests the other two hooks can run its four-path table.

## Out of scope

- **The SessionStart hook.** [[FEAT-0021-Serve-Orientation-Answer-Lookup]] owns HC-002. This feature must not grow into it; see the plan for how the two are kept from serving the same state twice.
- **Changing what preflight produces.** The notes, the IDs and the snapshot entries are unchanged.
- **Removing the hint.** A per-prompt reminder derived from focus is the shape the guides recommend; what is wrong is that it instructs where it should inform.

## Acceptance

- [x] The hint states the focus item, its status and its phase, and recommends the planner only for a multi-item scaffold or an ambiguous ask — evidence: [[TST-0007]] passing 2026-09-03, assertions 7 to 13 and 15 to 17; template commits `3e5c1b3` and `f264cb7`
- [x] The review sentence appears only in review states — evidence: [[TST-0007]] assertions 14 and 18 to 23 (all six non-review states, after the review round), and inversions A and 1
- [x] The Stop hook's block names two actions: close out now, or write the handoff and stop — evidence: [[TST-0007]] assertions 1 to 6; template commit `80a4a85`, which also made the hook block for the first time
- [x] A delegation to the planner carries the user's prompt verbatim and one sentence on what the result enables — evidence: [[TST-0007]] assertion 12; template commits `3e5c1b3` (hint) and `f6ac538` (planner rule 6)
- [x] A verbatim prompt in an issue note reads as a quotation, under a labelled blockquote — evidence: template commit `8d35297`, `issue.md` "As reported" callout and the two intake skills

## Risk scan

Run against the LIFECYCLE.md triggers. One fires: these are hook contracts, and HC-008's output is injected into every prompt in twelve repos. The hazard is the same one [[TASK-0080]] records for HC-002 — state served on every turn is paid for on every turn. The mitigation is in the plan, not a `RISK-*`: the hint stays a few lines, and [[TST-0007]] asserts an upper bound on what it emits.

## Links

- Review: [[Prompting-Guide-Review-2026-09-03]]
- Implementation target: `~/Dev/repos/project-os`.
