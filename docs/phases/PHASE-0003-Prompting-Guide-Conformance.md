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
features: [FEAT-0024, FEAT-0025, FEAT-0026, FEAT-0027, FEAT-0028]
requirements: [REQ-0026, REQ-0027]
tasks: [TASK-0090, TASK-0091, TASK-0092, TASK-0093, TASK-0094, TASK-0095, TASK-0096, TASK-0097, TASK-0098, TASK-0099, TASK-0100, TASK-0101, TASK-0102, TASK-0103, TASK-0104, TASK-0105, TASK-0106, TASK-0107, TASK-0108, TASK-0109]
issues: [ISS-0003, ISS-0041, ISS-0042, ISS-0043, ISS-0044, ISS-0045, ISS-0046, ISS-0047, ISS-0048]
related: [ADR-0024, ADR-0025, "[[Prompting-Guide-Review-2026-09-03]]"]
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

- [x] ISS-0041 to ISS-0045 and ISS-0003 are fixed in the template — evidence: template commits `1b5956e`, `685eef7`, `0049206`, `fda2e8a` (ISS-0041 to ISS-0044), `2b6ef10` (ISS-0045), `7b6890f` (ISS-0003), and TST-0007 passing 2026-09-03 at 25 of 25 with the four-path table as assertions 22 to 25
- [x] ISS-0047 is fixed in the template and TST-0004 records a real pass — evidence: template commit `66cd2a4`, TST-0004 stamped passing by the runner at 2026-09-03T15:31Z
- [x] FEAT-0024 to FEAT-0027 are done, each with its acceptance check passing or its exception recorded — evidence: TST-0005 (14 of 14), TST-0006 (3 of 3) and TST-0007 (34 of 34) passing on 2026-09-03, each approved by an independent review after one round of changes; FEAT-0025 carries its acceptance exception and its fifth criterion is ticked on the review of the first notes written under the new rules
- [ ] REQ-0026 and REQ-0027 are implemented, every criterion ticked with evidence — REQ-0026 implemented 2026-09-03 after two amendments recorded on the note; REQ-0027 stays `approved`: its first criterion is not met, the drift sweep at the close of the phase found 36 restatements (ISS-0048), and its third is owed with that issue
- [x] ADR-0024's two acceptance threads are closed: REQ-0018 superseded by REQ-0027, and a mechanical RULE-ONCE check decided or declined — evidence: ADR-0024 Acceptance, both boxes ticked 2026-09-03; RULE-ONCE declined for now on the drift sweep's count of 36 (ISS-0048), recorded by the implementing session for the owner to overturn
- [x] The template changes are synced to the downstream repos with the generator re-run — evidence: the validate-fleet.sh summary after the rollout, recorded under "Fleet rollout, 2026-09-03" below; ten repos synced and regenerated, this repo's own sync deferred for the reason given there

## Fleet rollout, 2026-09-03

`tools/scripts/sync-project-os.sh ~/Dev/repos/project-os` ran in the ten other downstream repos, each followed by the generator the script runs itself. Between 60 and 95 files changed per repo, all template-owned; no note under `docs/` was touched. The changes are in each repo's working tree, uncommitted, for the owner to review and commit. Files the sync left alone because both sides changed since the baseline, to hand-merge: `AGENTS.md` and `tools/instructions/WRITING.md` in the four repos synced in August (obsidian-supernote-sync, your-health, your-sudoku, your-trainer), `ROADMAP.md` in articles and project-os-bench, `tools/scripts/validate-docs.py` in your-trainer, and the merge-owned `docs/PHASES.md` and `docs/__templates__/SCHEMAS.md` nearly everywhere. This repo's own sync is deferred: its vendored validator is a sync behind, and the template's validator reports 47 errors here that pre-date today (below), so syncing it would block every commit until those are cleared.

`bash tools/scripts/validate-fleet.sh` from the template after the rollout:

| repo | result | errors | warnings | waivers |
|---|---|---|---|---|
| articles | OK | 0 | 0 | 0 |
| edankert.com | FAIL | 47 | 12 | 0 |
| obsidian-supernote-sync | OK | 0 | 21 | 0 |
| project-os-bench | OK | 0 | 0 | 0 |
| project-os-cockpit | FAIL | 77 | 271 | 22 |
| project-os-dev | FAIL | 47 | 52 | 19 |
| project-os | OK | 0 | 1 | 0 |
| your-applications.com | FAIL | 63 | 30 | 0 |
| your-health | OK | 0 | 102 | 0 |
| your-sudoku | OK | 0 | 130 | 3 |
| your-trainer | OK | 0 | 239 | 8 |
| yourtrainer-mcp | FAIL | 16 | 46 | 0 |

**Second rollout, 2026-09-04 (early hours), from template `1afc71e`.** The same ten repos re-synced after FEAT-0028 and the eight drift-pass commits (34 to 45 files updated each, uncommitted). `validate-fleet.sh` afterwards:

| repo | result | errors | warnings | waivers |
|---|---|---|---|---|
| articles | OK | 0 | 0 | 0 |
| edankert.com | FAIL | 47 | 12 | 0 |
| obsidian-supernote-sync | OK | 0 | 21 | 0 |
| project-os-bench | OK | 0 | 0 | 0 |
| project-os-cockpit | OK | 0 | 271 | 22 |
| project-os-dev | OK | 0 | 51 | 19 |
| project-os | OK | 0 | 1 | 0 |
| your-applications.com | FAIL | 63 | 30 | 0 |
| your-health | OK | 0 | 123 | 0 |
| your-sudoku | OK | 0 | 134 | 3 |
| your-trainer | OK | 0 | 304 | 8 |
| yourtrainer-mcp | FAIL | 16 | 46 | 0 |

Two repos moved from FAIL to OK between the tables: project-os-cockpit (77 VERIFY errors) and this repo (47), because the verification gate now treats a test with a `command:` as settled by CI (ADR-0025) and this repo cleared its back-link debt. The warning counts in your-health and your-trainer rose by the COMMAND-VERDICT warnings on their stamped tests, due before 2026-12-02. The three failures left are the pre-existing PARENT-BACKLINK and SNAPSHOT-MEMBERSHIP debt in edankert.com and your-applications.com and VERIFY in yourtrainer-mcp.

The five failures in the first table are not caused by today's changes. The fleet script runs the template's validator over each repo's notes, and every error is from a check that landed after those repos last synced: PARENT-BACKLINK (edankert.com 40, project-os-dev 41, your-applications.com 50), SNAPSHOT-MEMBERSHIP (7, 3, 13, and 6 in yourtrainer-mcp), VERIFY (project-os-cockpit 77, yourtrainer-mcp 10), plus METRICS 2 and DECISION-OPTIONS 1 here. Clearing that debt is its own work in each repo; this repo's 47 are the next thing to do here before its own sync.

## Notes

- Sequencing follows the review's "Suggested order": the contradictions first, then the one-sentence rules, then WRITING.md and the length limits, then the trim and the hook and hint rewrites. FEAT-0027 and FEAT-0021 both serve focus state; the proposed split is that SessionStart carries the slice and the per-prompt hint carries only what changes within a session.
- Decisions Edwin took on 2026-09-03: ADR-0024 accepted with option 1; a real phase instead of parking; retarget the subagent pins (ISS-0044); no test may sit failing, so TST-0005 to TST-0007 are draft until their harnesses exist; the word budgets for the four files other than LIFECYCLE.md are provisional and he is unsure how useful they are (REQ-0026).
- Everything lands in `~/Dev/repos/project-os` except the second half of TASK-0095, which edits this repo's review runner.
