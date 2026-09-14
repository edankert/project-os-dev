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
entrypoint: "../project-os/tools/scripts/test-walk-sheet.sh"
command: "bash ../project-os/tools/scripts/test-walk-sheet.sh"
last_verified: ""
covers: ["[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"]
issues: []
tasks: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
artifacts: []
adequacy: "Covered by the 28-mutation run recorded on [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]; six of the mutations are survey rules"
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

The template repo checked out beside this one. The harness is `tools/scripts/test-walk-sheet.sh` there, and it is this note's `command:`, so the note records no verdict (ADR-0025).

Its survey fixture is a **real git repository**, because "the last release tag" and "added since it" are git questions and a fixture that faked them would be testing the fake. It holds a released `REL-*` note carrying `tag: v1.0`, a tagged commit, one change note written before the tag and four after it, three surface notes (one a dialog with `parent:`), and a gallery with a before and after picture for one capture key and an after picture only for another.

## Steps

1. Generate the sheet for the fixture.
2. Generate it again in a shallow clone of the fixture (`git clone --depth 1`), which has the commits and not the tag.
3. Blank the `tag:` on the released note and generate it again.

## Expect

- The survey says which release it compared against and which tag.
- It lists exactly the screens the change notes after the tag name, and not the one named only before it.
- Under each screen, each change's one sentence appears, followed by that change's title. A bare `SUR-####` id in an Impact line is read the same as a wikilink, and a wikilink with display text has the link cut off the sentence.
- The dialog prints one heading level under its parent screen, between its parent and the next screen.
- One screen shows a before and an after picture; one shows an after picture marked **new**; the dialog shows only its sentence. A `gallery:` key with no picture at either end prints nothing.
- A change note that says "No screen changed" adds no screen. An Impact line that only mentions a screen id mid-sentence adds none either, and neither does a paragraph under Impact that is not a list item.
- The survey contains no `TST-` string.
- In step 2 the survey names the tag it could not find, lists no screen, and the rest of the sheet still prints its rows.
- In step 3 it names the release note that carries no tag.

## Not this check

- The procedure and its validator. That is [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].
- Whether a consumer's change notes name the right screens. That is each consumer's own work.
