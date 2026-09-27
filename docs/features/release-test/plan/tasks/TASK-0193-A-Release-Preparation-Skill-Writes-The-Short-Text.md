---
type: "[[task]]"
id: TASK-0193
aliases: ["TASK-0193"]
title: "One skill prepares a release for testing: screenshots, changed sections, procedures, what changed, short Expect lines, then the checks"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines, "Edwin, 2026-09-27: 'Are we considering writing a release skill which enables an LLM to build the release test pages?'", "Edwin, 2026-09-27: 'widen the task as suggested'"]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0191]]", "[[TASK-0192]]", "[[TASK-0194]]"]
blocks: []
related: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]"]
tests: []
---

# One skill prepares a release for testing: screenshots, changed sections, procedures, what changed, short Expect lines, then the checks

A new skill, `tools/skills/release-test-prep/SKILL.md`, turns "prepare v2.3.0 for testing" into one request. It does every job that gets a release test ready, for each platform, in a fixed order. An agent writes the words ([[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks|ADR-0050]], D3). Code still draws the page, keeps the progress and writes results to the ledger. Every edit the agent makes is checked by the length check and the validator before it is kept.

Edwin widened this task on 2026-09-27. It first covered only the what-changed lines and shortening over-long lines. Four jobs had no owner: recapturing screenshots, rewriting a changed section's setup, marking checks that cannot be done yet, and one place to start.

## The order the skill follows

1. **Screenshots.** Run the command named by `gallery:` in the project's section order file (your-trainer's is `tools/parity-gallery.sh`). Flag every capture older than a change that altered its screen. This is how ISS-0516 in your-trainer would have been caught.
2. **Changed sections.** Work out which sections' owed checks changed since the previous release, from the ledger and the generator's `--check`. Only those sections are touched.
3. **Procedures.** For each changed section, rewrite the procedure with the procedure skill (TASK-0194): groups with a starting state, short actions, the setup split into "On the bench", "Before you start" and "Later", and each check that cannot be done yet marked with its reason and suggested result.
4. **What changed.** Write the what-changed lines for each platform, one short line per change, grouped by section and screen.
5. **Expect lines.** Shorten each Expect line the length check reports, in the test note itself, keeping its meaning. Split a line that mixes platforms into `[android]` and `[ios]` lines.
6. **Checks.** Run the length check and the validator. Keep the edits only if both pass.
7. **Hand over.** Open the release test in the cockpit so the owner can look it over before testing starts, and list what the skill changed and what it could not settle.

## Definition of Done
- [ ] The skill follows the seven steps above, in that order, for each platform the release is tested on.
- [ ] Step 1 runs the project's `gallery:` command and reports every capture older than a change to its screen.
- [ ] Step 2 touches only sections whose owed checks changed since the previous release, and says which ones it skipped.
- [ ] Step 3 calls the procedure skill (TASK-0194) for each changed section, and the result has groups, starting states, the three-part setup and marked checks that cannot be done yet.
- [ ] Step 4 writes the what-changed file for each platform, one short line per change, grouped by section and screen.
- [ ] Step 5 shortens each Expect line the length check reports, in the test note, and splits mixed-platform lines into `[android]` and `[ios]` lines.
- [ ] Step 6 keeps the edits only if the length check and the validator both pass.
- [ ] Step 7 opens the release test in the cockpit and ends with a short list of what changed and what needs the owner.
- [ ] The skill says that a change of meaning in an Expect line is a change to the check, and reopens it in the ledger.
- [ ] `tools/skills/release-prep/SKILL.md` calls it before the release test is handed over, and the skills README, CLAUDE.md skill list and generated adapters list it.

## Steps
- [ ] Write the skill from the pattern of the procedure skill (TASK-0194).
- [ ] Wire it into release-prep.
- [ ] Dry-run it on a copy of your-trainer for the Equipment section, then for a whole platform.

## Notes
- The agent's edits are reviewed by the owner in the commit, as any other change to a note.
- The cockpit side of step 7 is project-os-cockpit FEAT-0155; the skill only opens the page.
- A project with no `gallery:` command skips step 1 and says so.
