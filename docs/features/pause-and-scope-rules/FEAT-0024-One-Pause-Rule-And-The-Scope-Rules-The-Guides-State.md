---
type: "[[feature]]"
id: FEAT-0024
aliases: ["FEAT-0024"]
title: "One pause rule, and the scope rules the guides state"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 2.1, 2.3, 5.3, 6.1, 6.2, 7.1, 7.2, 7.4, 8.1"]
goal: "State once, in LIFECYCLE.md, when an agent stops and asks the user, and make the eleven scattered stop-points link to it. Add the six one-sentence rules the guides state and project-os does not."
requirements: []
tasks: ["[[TASK-0090]]", "[[TASK-0091]]", "[[TASK-0092]]", "[[TASK-0093]]", "[[TASK-0094]]", "[[TASK-0095]]"]
release: ""
related: ["[[ADR-0004-Mandatory-Skill-Steps]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix]]"]
tests: ["[[TST-0005]]"]
---

# One pause rule, and the scope rules the guides state

## Goal

project-os has eleven places that tell an agent to stop and ask the user, each worded on its own: "stop and present resolution options", "warn and require explicit user confirmation", "Present the list to the user for decision". None of them says what to finish before asking. This feature states the rule once and turns the eleven into a named decision plus a link.

The same pass adds six rules the prompting guides state and project-os is silent on. Each is one or two sentences in a file that already exists.

## Scope

| Task | Finding | Files |
|---|---|---|
| [[TASK-0090]] | 2.1 (rule), 6.1 | `tools/instructions/LIFECYCLE.md` |
| [[TASK-0091]] | 2.1 (the eight stop-points) | HOOKS.md, four skills, the planner prompt in the generator |
| [[TASK-0092]] | 2.3 | `issue-intake/SKILL.md`, `generate-adapters.py` |
| [[TASK-0093]] | 5.3, 7.1, 7.2, 7.4 | QUALITY.md, HANDOFF.md, MARKDOWN.md, `skills/README.md` |
| [[TASK-0094]] | 6.2 | `test-authoring/SKILL.md` |
| [[TASK-0095]] | 8.1 | `independent-review/SKILL.md`, and this repo's `tools/scripts/review-external.py` |

## Out of scope

- **Deleting any stop-point.** All eleven are legitimate: an impact conflict, a task ahead of its phase, release scope, a manual test verdict. What changes is the wording and what an agent does before asking, not whether it asks.
- **The hook that blocks the stop** ([[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]] carries that).
- **Trimming the files this feature edits.** LIFECYCLE.md gets two rules here and loses its anecdotes in [[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]. Doing both at once makes the diff unreadable; this one goes first because the trim should not have to re-trim new text.

## Acceptance

- [ ] One file states the pause rule, and a grep across `tools/` and the generator finds exactly one full statement of it — evidence: [[TST-0005]]
- [ ] Each of the eight stop-points names the decision the user owns and links the rule, in under three lines — evidence: [[TST-0005]]
- [ ] The spec-ambiguity check still runs on every intake, and now says what to do when the readings do not diverge — evidence: the diff of `issue-intake/SKILL.md` step 1
- [ ] A reviewer is asked for every finding, and the repro filter is applied when findings are transcribed into notes — evidence: the diff of `independent-review/SKILL.md` and `review-external.py`

## Risk scan

Run against the LIFECYCLE.md triggers. No new risks: no dependency, env var, path or runtime change. [[TASK-0095]] changes an output schema in this repo's `review-external.py`, which is a contract change to a script no other repo calls; recorded here rather than as a `RISK-*`.

## Links

- Review: [[Prompting-Guide-Review-2026-09-03]]
- Implementation target: `~/Dev/repos/project-os`, except [[TASK-0095]]'s second half, which is this repo's `tools/scripts/review-external.py`.
