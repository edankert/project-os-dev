---
type: "[[phase]]"
id: PHASE-0003
aliases: ["PHASE-0003"]
title: "Prompting-guide conformance"
status: active
order: 3
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
goal: "Bring the template's instructions, skills, hooks and subagents in line with the Claude 5 prompting guides: remove the contradictions, state each rule once, trim what every session loads, and stop the hooks and hints from teaching bypasses"
features: [FEAT-0024, FEAT-0025, FEAT-0026, FEAT-0027]
requirements: [REQ-0026, REQ-0027]
tasks: [TASK-0090, TASK-0091, TASK-0092, TASK-0093, TASK-0094, TASK-0095, TASK-0096, TASK-0097, TASK-0098, TASK-0099, TASK-0100, TASK-0101, TASK-0102, TASK-0103, TASK-0104, TASK-0105]
issues: [ISS-0003, ISS-0041, ISS-0042, ISS-0043, ISS-0044, ISS-0045, ISS-0047]
related: [ADR-0024, "[[Prompting-Guide-Review-2026-09-03]]"]
tags: [phase, prompting-guides]
---

# Prompting-guide conformance

## Goal

On 2026-09-03 the template was reviewed against the Claude Fable 5.1, Fable 5 and Opus 5 prompting guides ([[Prompting-Guide-Review-2026-09-03]]). The review found the rules mostly right and the delivery wrong: four contradictions, instruction files that carry history into every session, and stop-points and delegation hints tuned for a model that had to be told to pause. This phase is the work that follows from it.

The items were first parked in PHASE-999. Edwin decided the same day that a coherent body of work with an order and a plan is a phase, not parking, so they moved here.

## Scope

- **The four contradictions**, one commit each in the template: [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family|ISS-0041]], [[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways|ISS-0042]], [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary|ISS-0043]], [[ISS-0044-The-Adapter-Calls-The-Pinned-Subagent-Model-The-Strongest|ISS-0044]].
- **Two smaller gaps**: [[ISS-0045-Nothing-Says-A-Review-Or-Design-Deliverable-Is-Filed|ISS-0045]] (deliverables are filed in the repo) and [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing|ISS-0003]] (the document-first hook's fallback), whose fix is tested inside FEAT-0027's hook test.
- **One regression found on the way**: [[ISS-0047-DECISION-RULE-Vanished-From-The-Template-Validator|ISS-0047]]. Running the template's own tests while landing the contradictions showed that the validator had lost the DECISION-RULE check on 2026-08-18. ADR-0024, this phase's own rule-ADR, relies on that check, so the restore belongs here rather than in the parking lot.
- **Four features** carrying the other findings: FEAT-0024 (one pause rule and the scope rules), FEAT-0025 (writing rules for the final message and length limits), FEAT-0026 (trim the instruction files loaded every session), FEAT-0027 (the hint serves focus state instead of pushing delegation).
- **Two requirements and one decision**: REQ-0026 (word budgets), REQ-0027 (every normative rule stated once, superseding REQ-0018), ADR-0024 (accepted with option 1).

## Out of Scope

- Harness and API items the guides raise that project-os leaves to the tool (section 10 of the review).
- The optional cockpit change ISS-0045 mentions (an HTML asset on a reference note). That belongs in project-os-cockpit.
- FEAT-0021 (snapshot access). FEAT-0027 coordinates with it and does not absorb it.

## Exit Criteria

- [ ] ISS-0041 to ISS-0045 and ISS-0003 are fixed in the template — evidence: the template commits, and TST-0007 passing for the hook rows. ISS-0041 to ISS-0044 landed 2026-09-03 as template commits `1b5956e`, `685eef7`, `0049206`, `fda2e8a`
- [x] ISS-0047 is fixed in the template and TST-0004 records a real pass — evidence: template commit `66cd2a4`, TST-0004 stamped passing by the runner at 2026-09-03T15:31Z
- [ ] FEAT-0024 to FEAT-0027 are done, each with its acceptance check passing or its exception recorded
- [ ] REQ-0026 and REQ-0027 are implemented, every criterion ticked with evidence
- [ ] ADR-0024's two acceptance threads are closed: REQ-0018 superseded by REQ-0027, and a mechanical RULE-ONCE check decided or declined
- [ ] The template changes are synced to the downstream repos with the generator re-run — evidence: the validate-fleet.sh summary after the rollout

## Notes

- Sequencing follows the review's "Suggested order": the contradictions first, then the one-sentence rules, then WRITING.md and the length limits, then the trim and the hook and hint rewrites. FEAT-0027 and FEAT-0021 both serve focus state; the proposed split is that SessionStart carries the slice and the per-prompt hint carries only what changes within a session.
- Decisions Edwin took on 2026-09-03: ADR-0024 accepted with option 1; a real phase instead of parking; retarget the subagent pins (ISS-0044); no test may sit failing, so TST-0005 to TST-0007 are draft until their harnesses exist; the word budgets for the four files other than LIFECYCLE.md are provisional and he is unsure how useful they are (REQ-0026).
- Everything lands in `~/Dev/repos/project-os` except the second half of TASK-0095, which edits this repo's review runner.
