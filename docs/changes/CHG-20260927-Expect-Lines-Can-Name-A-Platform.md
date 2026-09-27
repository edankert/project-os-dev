---
type: "[[change]]"
id: CHG-20260927-Expect-Lines-Can-Name-A-Platform
title: "An Expect line can name a platform and then prints only on that platform's release test, and a quoted procedure line is a warning"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0188-Expect-Lines-Can-Be-Marked-Per-Platform]]"]
commit: "project-os 72b0d29, 0289cb8"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/scripts/release-test-tags.py", "tools/scripts/test-release-test.sh", "tools/instructions/TESTING.md", "docs/__templates__/SCHEMAS.md", "docs/__templates__/test.md"]
issues: []
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0034-A-Check-Writes-Its-Expected-Result-Once-Per-Platform]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "[[TST-0042-An-Expect-Line-Marked-For-A-Platform-Prints-Only-There]]"]
---

# An Expect line can name a platform and then prints only on that platform's release test

## Summary

A check's Expect line may now start with a platform name in brackets, such as `- [ios] The Hub opens from Settings.` The Android release test page leaves that line out, and the iOS page prints it without the brackets. A tester stops reading iOS wording on the Android page once a consumer marks its lines. Someone running `release-test.py --check` also sees a new warning for every procedure line that quotes an expectation instead of giving its tags.

## Impact

- No screen changed: project-os has no surface notes. The release test page each consumer generates changes as the Summary says, once its checks mark their Expect lines.

What changed for someone writing or running these files:

- **A new line form in test notes.** Under `## Expect`, `- [android] ...` or `- [ios] ...` holds on that platform only; a line with no name holds on every platform. The name is a ledger's platform name. The rule is stated in `TESTING.md`, "A check is testable by a stranger".
- **Tags pair per platform.** A tag `TST-0657.2` prints the second Expect line among those that hold on the platform being tested, when the check has one such line per numbered step.
- **A new error.** `release-test.py --check` refuses a platform name the repo keeps no ledger for, naming the check and the line. `validate-docs.sh` runs it on every commit.
- **A new warning.** `--check` prints `WARN [RELEASE-TEST]` for a procedure line that quotes an expectation and for an action line that carries tags. Under `--quiet` it prints one line with the count. It does not fail the check. `QUOTED_EXPECTATIONS_REFUSED` in `release-test.py` makes it an error; it stays off until the consumers have moved.
- **`release-test-tags.py --all`.** Rewrites every quoted line as its tags alone and moves tags off action lines, reporting each line whose page text changes. Without `--all`, a quote is rewritten only when every platform the step runs on would print exactly those words.
- **Code names**, for project-os-cockpit's bundle: `expect_text`, `expect_for` and `expect_lines` take an optional `platform`; `expand_tag_only` takes `platform`; new `expect_entries`, `expect_marks` and `expect_block`; `Check.expect_problems`; `Procedure.parse_warnings` and `Procedure.warnings`; `check_repo_findings` returns problems, warnings and remarks, and `check_repo` still returns problems and remarks.

On a scratch copy of your-trainer the Android and iOS pages are byte for byte what they were, because none of its checks marks a line yet. `--check` there lists 724 quoted lines.

## Documentation Coverage (All Types Considered)

- features: not-applicable (FEAT-0040 continues)
- requirements: not-applicable (REQ-0034 is advanced at the feature's close-out)
- tasks: updated (TASK-0188)
- issues: not-applicable
- tests: new (TST-0042)
- workflows: not-applicable
- decisions: not-applicable (ADR-0050 D2 already records it)
- risks: not-applicable (no new dependency, path or setting; the warning is a new output line only)
- changes: new
- snapshot: updated

## Follow-ups

- [ ] Turn `QUOTED_EXPECTATIONS_REFUSED` on once your-trainer FEAT-0129 and the cockpit have moved to tags alone (TASK-0188 Notes).
