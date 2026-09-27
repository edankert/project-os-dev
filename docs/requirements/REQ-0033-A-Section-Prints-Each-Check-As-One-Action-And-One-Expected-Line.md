---
type: "[[requirement]]"
id: REQ-0033
aliases: ["REQ-0033"]
title: "A release test section prints each check as a number, one action line, one expected line and its tag"
status: approved
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["Edwin, 2026-09-27: approval of the release test page example", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "Edwin, 2026-09-27, approving REQ-0033 to REQ-0037: 'approved, start stage 2'"]
priority: high
scope: "tools/scripts/walk-sheet.py (renamed release-test.py), docs/__templates__/procedure.md, TESTING.md"
acceptance:
  - "Per platform, the output lists the sections in order, each with its owed check count and one on-the-bench line"
  - "Per section, the output has three parts in this order: what changed, setup, checks"
  - "Setup is split into On the bench (things), Before you start (numbered actions) and Later (needs of a single check, naming its number)"
  - "Checks are numbered from 1 in each section; each is one action line, the check's own Expect line for this platform, and its tag"
  - "Checks sit in groups; each group has a heading and a start state printed once, and printed again only after skipped checks"
  - "A readiness problem prints as one line saying why and which result fits"
  - "The Markdown sheet and the cockpit's JSON carry the same sections, groups, numbers and lines"
implements: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
verifies: []
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[REQ-0031-Preparation-Is-Declared-And-Validated]]", "[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"]
tests: []
---

# A release test section prints each check as a number, one action line, one expected line and its tag

## Statement

For each release and platform, the generator shall print every section as three parts: what changed, setup, and checks. Each check shall appear as a section-local number, one action line, the check's own Expect line for this platform, and its TST tag. Checks shall sit in groups, each with a heading and a start state written once.

Words used here. A **section** is a group of checks tested with one setup (it was called a sitting). A **group** is a run of checks inside a section under one heading and one start state. The **start state** is what the app and the bench must look like before the group's first check. See [[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks|ADR-0050]].

How the procedure file expresses this:

- A `### ` heading under `## Steps` starts a group. The line under it that starts `Start:` is the group's start state. It replaces `state_for:` (ADR-0046).
- Each numbered item is one action line, followed by tag-only lines such as `` - `TST-0657.1` ``. The action no longer names the screen (ADR-0045, as amended).
- `readiness_for:` gains an optional `result:`, the result the tester is offered, such as `blocked` or `excused`. A `kind: decision` without one offers `question`.
- A setup item that `setup_for:` ties to one printed check goes under "Later", with that check's number. The section order file's `bench:` list is "On the bench". The procedure's `## Setup` items tied to every step are "Before you start".

The printed numbers are the only step numbers a tester sees. Text the generator writes, such as "check 13 needs Pro", uses them. This closes [[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose|ISS-0086]], whose problem was a procedure's prose citing numbers the page did not print.

A section with no procedure still prints: each owed check becomes one row, with its title as the action line and its Expect lines for this platform. The length check reports it.

## Acceptance Criteria

- [x] Per platform, the output lists the sections in order, each with its owed check count and one on-the-bench line — evidence: the section table (TASK-0190, template b2dc17f); your-trainer's REL-0017 page on both platforms
- [x] Per section, the output has three parts in this order: what changed, setup, checks — evidence: `render_section` (TASK-0190); TST-0040
- [x] Setup is split into On the bench (things), Before you start (numbered actions) and Later (needs of a single check, naming its number) — evidence: `_setup_payload` (TASK-0190); TST-0040, where Later names checks 13 and 19
- [x] Checks are numbered from 1 in each section; each is one action line, the check's own Expect line for this platform, and its tag — evidence: TASK-0190; TST-0040
- [x] Checks sit in groups; each group has a heading and a start state printed once, and printed again only after skipped checks — evidence: `Start:` groups (TASK-0189, template 73b8d07) and `readiness_line`; TST-0040
- [x] A readiness problem prints as one line saying why and which result fits — evidence: `readiness_line` with `result:` (TASK-0189); your-trainer Equipment checks 18, 27 and 28
- [x] The Markdown sheet and the cockpit's JSON carry the same sections, groups, numbers and lines — evidence: one model rendered two ways, `payload` and `render_page` (TASK-0190, template b2dc17f and d4b4010); the cockpit's route test compares the page with the ledger on your-trainer's corpus

## Traceability

- Implements: [[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]
- Changes what these earlier requirements describe: [[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk|REQ-0028]] criterion 4 (a row prints Setup, Steps and Expect) and [[REQ-0029-A-Release-Walk-Reads-As-A-Script|REQ-0029]] criterion 4 (steps name a screen and quote the check). Both stay `implemented` as records of what was built then.
- Verified by: [[TST-0040-A-Release-Test-Section-Reads-As-Short-Lines|TST-0040]], and the renamed `test-release-test.sh` once TASK-0189 and TASK-0190 land.
