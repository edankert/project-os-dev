---
type: "[[change]]"
id: CHG-20260927-The-Length-Check-And-The-Release-Test-Prep-Skill
title: "The release test reports lines and sections that are too long, and one skill prepares a release for testing"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0192-The-Validator-Reports-Over-Long-Lines-And-Sections]]", "[[TASK-0193-A-Release-Preparation-Skill-Writes-The-Short-Text]]"]
commit: "project-os 9044d67, 25e4eed"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/instructions/TESTING.md", "docs/__templates__/SCHEMAS.md", "docs/__templates__/release-test.md", "tools/skills/release-test-prep/SKILL.md", "tools/skills/release-prep/SKILL.md", "CLAUDE.md", "tools/adapters/claude-code/ADAPTER.md"]
platforms: []
issues: []
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]", "[[TST-0046-The-Length-Check-Reports-What-Is-Too-Long]]"]
---

# The length check and the release-test-prep skill

## Summary

`release-test.py --check` now warns about every action line over 20 words, expected line over 25, and section over its word budget, on the page a tester reads. A new skill, `release-test-prep`, prepares a release for testing in one request, and `release-prep` calls it.

## Impact

- No screen changed: project-os has no surface notes.

What changed for someone running or preparing a release test:

- **The length check.** Warnings of kind `length`, one counted line under `--quiet`. The budget is 300 words plus 40 for each printed check. `length_limits:` in RELEASE-TEST.md's frontmatter changes any limit, and `error: true` makes them errors (TESTING.md, "The release test", rule 10; SCHEMAS.md).
- **Counts.** The page's header and sections table count printed checks, with the test notes behind them beside the count: "28 checks · 4 test notes".
- **release-test-prep.** Seven steps per platform: screenshots, the sections that need work, their procedures, what-changed lines, shorter Expect lines, the checks, and handing over in the cockpit. `release-prep` step 2a calls it; the old 2a and 2b are now 2b and 2c. CLAUDE.md, the Claude Code adapter's skill list and the skills README list it, and its adapters are generated.
- **Consumers.** On your-trainer the check will print one counted line for 827 reports until the sections are rewritten; it does not fail a commit.

## Documentation Coverage (All Types Considered)

- features: not-applicable (FEAT-0040 continues)
- requirements: not-applicable (REQ-0036 is advanced at the feature's close-out)
- tasks: updated (TASK-0192, TASK-0193)
- issues: not-applicable
- tests: new (TST-0046)
- workflows: not-applicable
- decisions: not-applicable (ADR-0050 D3)
- risks: not-applicable (a new frontmatter key in a file each project owns, documented in SCHEMAS.md; no dependency or path)
- changes: new
- snapshot: updated

## Follow-ups

- [ ] your-trainer TASK-0975 measures its rewritten Equipment section, and the budget default is set from it.
- [ ] TASK-0196 makes the reports errors once every section passes.
