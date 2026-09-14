---
type: "[[test]]"
id: TST-0011
aliases: ["TST-0011"]
title: "The survey lists the screens change notes named since the last release tag, with their rider-facing sentences and before and after captures, and no test id"
status: active
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 1", "[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
scope: feature
level: acceptance
entrypoint: ""
command: ""
last_verified: ""
covers: ["[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"]
issues: []
tasks: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
artifacts: []
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
area: "the walk"
after: []
---

# The survey lists changed screens with before and after

## Setup

The template repo checked out beside this one. The fixture TASK-0118 adds to `test-walk-sheet.sh`: a git repo with a release tag, one change note before the tag and two after it, three surface notes (one a dialog with `parent:`), and a capture map with a before and after image for one surface and an after image only for another. When TASK-0118 lands, its path goes in `command:`.

## Steps

1. Generate the sheet for the fixture.
2. Generate it again in a shallow clone of the fixture with no tags.

## Expect

- The survey lists exactly the surfaces named by the two change notes after the tag, and not the one before it.
- Under each surface, each change's one sentence appears.
- The dialog appears under its parent screen.
- One surface shows a before and an after capture; one shows the after capture marked new; one shows only its sentence.
- The survey contains no `TST-` string.
- In step 2, the survey prints one line saying no release tag was found, and the rest of the sheet still prints.

## Not this check

- The procedure and its validator. That is [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].
- Whether a consumer's change notes name the right screens. That is each consumer's own work.
