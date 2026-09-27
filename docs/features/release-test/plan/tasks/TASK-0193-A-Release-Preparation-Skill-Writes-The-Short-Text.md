---
type: "[[task]]"
id: TASK-0193
aliases: ["TASK-0193"]
title: "One skill prepares a release for testing: screenshots, changed sections, procedures, what changed, short Expect lines, then the checks"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]", "Edwin, 2026-09-27: 'Are we considering writing a release skill which enables an LLM to build the release test pages?'", "Edwin, 2026-09-27: 'widen the task as suggested'"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0191]]", "[[TASK-0192]]", "[[TASK-0194]]"]
blocks: []
related: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]"]
tests: []
verification_waiver: "A skill: instruction text an agent follows; no harness can observe whether it does. Checked by reading it against TESTING.md and the procedure skill. It is run for real by your-trainer TASK-0975 (the Equipment section) and TASK-0976 (every Android section), which is its dry run."
waiver_expires: 2026-12-27
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
- [x] The skill follows the seven steps above, in that order, for each platform the release is tested on. `tools/skills/release-test-prep/SKILL.md` (project-os 25e4eed), "Checklist", steps 1 to 7.
- [x] Step 1 runs the project's `gallery:` command and reports every capture older than a change to its screen. It reads the stale flags TASK-0191 prints on the page.
- [x] Step 2 touches only sections whose owed checks changed since the previous release, and says which ones it skipped. A section needs work when `--check` refuses its procedure, finds none, or the length check names it; the rest are listed as left alone.
- [x] Step 3 calls the procedure skill (TASK-0194) for each changed section, and the result has groups, starting states, the three-part setup and marked checks that cannot be done yet.
- [x] Step 4 writes the what-changed file for each platform, one short line per change, grouped by section and screen. The generator groups them; the skill writes one line per change and screen with `tag:` set, and gives an undeclared change note its `platforms:`.
- [x] Step 5 shortens each Expect line the length check reports, in the test note, and splits mixed-platform lines into `[android]` and `[ios]` lines.
- [x] Step 6 keeps the edits only if the length check and the validator both pass.
- [x] Step 7 opens the release test in the cockpit and ends with a short list of what changed and what needs the owner.
- [x] The skill says that a change of meaning in an Expect line is a change to the check, and reopens it in the ledger. Step 5, with an invalidation naming the task and the reason, and "What not to do".
- [x] `tools/skills/release-prep/SKILL.md` calls it before the release test is handed over, and the skills README, CLAUDE.md skill list and generated adapters list it. release-prep step 2a; `.claude/skills/` and `.agents/skills/` copies and the Cursor rule generated.

## Steps
- [x] Write the skill from the pattern of the procedure skill (TASK-0194).
- [x] Wire it into release-prep.
- [x] Dry-run it on a copy of your-trainer for the Equipment section, then for a whole platform. Carried by your-trainer TASK-0975 and TASK-0976, which run it on the real repository; see the waiver.

## Notes
- The agent's edits are reviewed by the owner in the commit, as any other change to a note.
- The cockpit side of step 7 is project-os-cockpit FEAT-0155; the skill only opens the page.
- A project with no `gallery:` command skips step 1 and says so.
