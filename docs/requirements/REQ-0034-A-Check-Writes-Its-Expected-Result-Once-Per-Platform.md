---
type: "[[requirement]]"
id: REQ-0034
aliases: ["REQ-0034"]
title: "A check writes its short expected result once, with one line per platform where the platforms differ"
status: approved
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]] (D2)", "Edwin, 2026-09-27, approving REQ-0033 to REQ-0037: 'approved, start stage 2'"]
priority: high
scope: "docs/__templates__/test.md, SCHEMAS.md, TESTING.md, the generator and validator"
acceptance:
  - "An Expect line marked [android] or [ios] prints only on that platform; an unmarked line prints on every platform"
  - "Tag .N pairs with the Nth Expect line that applies on the current platform"
  - "A platform name in brackets that has no ledger is refused by the validator"
  - "A procedure expectation line is its tags only; a quoted expectation is refused once consumers have migrated"
  - "The test template and SCHEMAS.md show the per-platform form, and TESTING.md states the rule once"
implements: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
verifies: []
related: ["[[ADR-0049-A-Walk-Step-May-Cite-A-Check-Without-Quoting-It]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]"]
tests: []
---

# A check writes its short expected result once, with one line per platform where the platforms differ

## Statement

An acceptance check's `## Expect` section shall be the only place its expected result is written. Where the result differs by platform, the check shall write one line per platform, marked with the platform in square brackets. The generator shall print only the lines that apply on the platform being tested.

Example, in a test note:

```markdown
## Expect
- [android] The Hub opens from the equipment icons in the top bar.
- [ios] The Hub opens from Settings.
- Four slots: Smart Trainer, Power Source, Cadence, Heart Rate.
```

On Android the page prints the first and third lines. On iOS it prints the second and third.

Reason: a result counts only if the tester read the check's own words (project-os-cockpit ADR-0041). One source also cannot drift, which a procedure's own copy did (ADR-0049). Today's Android sheet prints iOS wording because Expect lines mix both platforms in one sentence.

The four headings a check needs (Setup, Steps, Expect, Not this check) stay, so a stranger can still test it from the note alone ([[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger|ADR-0027]]).

## Acceptance Criteria

- [x] An Expect line marked [android] or [ios] prints only on that platform; an unmarked line prints on every platform — evidence: `Change.on` and `shown_expected` (TASK-0188, template 72b0d29); `test-release-test.sh` "a line marked [testbed] prints on testbed"
- [x] Tag .N pairs with the Nth Expect line that applies on the current platform — evidence: `expect_for` (TASK-0188); checked for every tag of your-trainer's 14 procedures by the reviewers of your-trainer TASK-0976
- [x] A platform name in brackets that has no ledger is refused by the validator — evidence: `test-release-test.sh` "an Expect line marked for a platform with no ledger is refused"
- [x] A procedure expectation line is its tags only; a quoted expectation is refused once consumers have migrated — evidence: tag-only lines (TASK-0188); refused by default since template 116d14e, with `quoted_lines: warning` for a project still moving
- [x] The test template and SCHEMAS.md show the per-platform form, and TESTING.md states the rule once — evidence: template 0289cb8: TESTING.md, SCHEMAS.md and the test template

## Traceability

- Implements: [[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]
- Verified by: the renamed `test-release-test.sh`, once TASK-0188 lands.
