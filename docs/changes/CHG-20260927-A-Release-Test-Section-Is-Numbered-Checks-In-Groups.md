---
type: "[[change]]"
id: CHG-20260927-A-Release-Test-Section-Is-Numbered-Checks-In-Groups
title: "A release test section prints what changed, setup in three parts and numbered checks in groups, and the page is also printed as JSON"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0190-The-Generator-Prints-Sections-Groups-And-Numbered-Checks]]"]
commit: "project-os b2dc17f, d4b4010"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/scripts/test-release-test.sh", "tools/scripts/test-release-test-preparation.py", "tools/instructions/TESTING.md"]
platforms: []
issues: ["[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"]
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[TST-0045-A-Release-Test-Section-Prints-Numbered-Checks-In-Groups-From-One-Model]]"]
---

# A release test section prints numbered checks in groups

## Summary

A tester now reads each section as three parts: what changed on its screens, its setup, and its checks numbered from 1, each one action and its expected lines. The page starts with a table of the sections and what each needs on the bench. `release-test.py --json` prints the same page as data, which is what the cockpit will draw from.

## Impact

- No screen changed: project-os has no surface notes. In each consumer, the release test page changes as below at its next template sync.

What changed for someone reading or building on the page:

- **Sections table.** Before what changed, one row per section: number, name, owed count, and its `bench:` list joined with " · ".
- **Setup in three parts.** "On the bench" is the section's `bench:`. "Before you start" is numbered: the procedure's setup items every step needs, or the ones check 1 needs. "Later" names the printed check that first needs each other item.
- **Checks.** Numbered from 1 in each section; the procedure's own numbers are not printed. Each is `- [ ] **N.** action`, then its expected lines, each with only the tags still owed. A leading "Step N:" is removed from an Expect line. Group headings print with their `Start:` line once; "Start again:" prints after skipped steps. A readiness problem is one line ending "Suggested: Blocked." or "Suggested: Question.".
- **A section with no procedure** prints one numbered check per owed check: its title linked to its note, its Setup and Steps indented, then its Expect lines.
- **Gone:** the "Step N — screen" headings, "Required state:", "(already tested: ...)", the closing tick list per procedure, and the per-row "tested, and the result recorded" box.
- **JSON.** `--json` prints the page's data; its shape is TESTING.md, "The release test", rule 10. The Markdown is rendered from it (`payload`, `render_page`), so the two cannot differ. `render_check` and `render_procedure` are removed; `render_section`, `section_payload`, `shown_expected` and `readiness_line` are new.
- **ISS-0086.** The generator half is done. The issue closes when the cockpit's section page draws these numbers.

On a scratch copy of your-trainer, before its pilot rewrite, the Equipment section on Android is 3,052 words and 6 headings, against about 4,300 words and 28 headings today. The Android page is 31,953 words and the iOS page 64,838.

## Documentation Coverage (All Types Considered)

- features: not-applicable (FEAT-0040 continues)
- requirements: not-applicable (REQ-0033 is advanced at the feature's close-out)
- tasks: updated (TASK-0190)
- issues: updated (ISS-0086)
- tests: new (TST-0045)
- workflows: not-applicable
- decisions: not-applicable (ADR-0050 records the design)
- risks: not-applicable (no new dependency, path or setting; `--json` is a new output, documented in rule 10)
- changes: new
- snapshot: updated

## Follow-ups

- [ ] project-os-cockpit TASK-0640 reads the page from `payload` through its bundle, and TASK-0643 draws the section page from it.
- [ ] TASK-0192 counts words on this page.
