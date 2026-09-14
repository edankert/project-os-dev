---
type: "[[task]]"
id: TASK-0118
aliases: ["TASK-0118"]
title: "TESTING.md rule 2 and walk-sheet.py build the survey from change notes merged since the last release tag, grouped by the screens they name, with before and after captures and no test ids"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 1"]
parent: "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"
effort: L
due: ""
depends: ["[[TASK-0116-TAXONOMY-States-What-A-Surface-Is]]", "[[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed]]"]
blocks: ["[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
tests: ["[[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]"]
---

# The survey comes from change notes and captures

## What

The first section of the walk sheet lists the screens changed since the last release. For each screen it prints the sentences from every change note that named it, then the capture from the last release tag beside the capture from the release candidate, where the repo maps a capture key to that screen. It prints no test id.

## Definition of Done

- [x] TESTING.md "The walk" rule 2 is rewritten to ADR-0045 decision 1, and rule 8's close-out sentence is narrowed to say change notes now carry the Impact list.
- [x] `walk-sheet.py` finds the last release tag for the platform, lists `docs/changes/CHG-*` notes added since it, reads each Impact list, and groups by surface with children under their parent screen.
- [x] Before and after captures are resolved through the capture-key map TASK-0116 settles. Where only the after capture exists (a new screen or state), the survey says "new". Where neither exists, it prints the sentence alone.
- [x] Without a reachable tag (a shallow clone, or no released `REL-*`), the survey prints one line saying so. It never prints an empty survey silently.
- [x] The survey contains no `TST-` string. Asserted.
- [x] `test-walk-sheet.sh` gains a fixture repo with a git tag, change notes before and after it, and a capture map. Its survey assertions become TST-0011's command. The old invalidation-event survey assertions in TST-0009 are rewritten, not deleted silently.
- [x] REQ-0028's criterion 2 is amended in its `## Amendments` section with the reason (ADR-0045).

## Steps

- [x] Settle the tag lookup (PLAN.md, the release-tag open question) before writing code.
- [x] Write the fixture first, watch the survey assertions fail, then change the generator.
- [x] Rerun the 28 existing TST-0009 mutations that touch the survey; record which ones no longer apply.

## Notes

- The cockpit bundles this module byte for byte (project-os-cockpit `walk_sheet_bundled.py`). A git call inside it runs inside the cockpit's sidecar too. Check that the sidecar's working directory makes the tag lookup work.

## How the tag is found, which was this task's open question

**From the release notes, not from a tag pattern.** The newest `REL-*` note at `status: released` whose `platform:` matches (an empty `platform:` counts for every platform, the same opt-in rule release contents use), sorted by `date:` then id, and its `tag:` field. Then `git rev-parse --verify <tag>^{commit}` to confirm the checkout has it, and `git diff --diff-filter=A --name-only <tag>..HEAD -- docs/changes` for the notes added since.

A tag *pattern* was the alternative and it is a guess. your-trainer tags Android `v2.1.8` and iOS `ios/v0.1.0`, so a pattern needs a per-platform convention that exists nowhere; the release note already carries both the platform and the tag, so the per-platform answer falls out with no new convention at all.

Three ways it can have no answer, and each says which:

- no released `REL-*` note for this platform;
- the newest released note carries no `tag:`, and the message names the note;
- the tag is not in this checkout, which is the shallow-clone case, and the message names the tag.

In every one the survey prints the reason and the rest of the sheet still prints. It never prints an empty survey silently, and it never lists change notes it cannot date.

## Where the captures live

`docs/tests/acceptance/gallery/<tag>/<key>.<ext>` for the screens at the release tagged `<tag>`, and `docs/tests/acceptance/gallery/candidate/<key>.<ext>` for the build being walked. `<key>` comes from the surface note's `gallery:` list, so the surface note is the only place a screen and its pictures are joined. A key with an after picture and no before one is marked **new**; a key with neither prints nothing, so a `gallery:` listing a state nobody has captured costs nothing on the sheet.

## What happened to the old survey assertions

Eight assertions in `test-walk-sheet.sh` tested the invalidation-event survey: the surface heading with its owed count, the task that reopened it, the quoted `## Acceptance checks reopened` section, both change-id resolution forms, and the `SUR-*` label. They were **rewritten, not deleted**: five `hasnt` assertions now pin that the old answer is gone (a surface no longer heads its owed count, an invalidation no longer names its change note, the reopened section is no longer quoted), and two new `has` assertions cover the new answer on a fixture with no release note.

The twenty-odd mutations recorded on TST-0009 that touched the survey no longer apply, because the code they mutated is gone. TST-0011's own mutation set replaces them and is recorded there: the tag verification, the since-the-tag restriction, the before/after ordering, the "new" flag, the parent nesting, and the anchoring of the Impact id.

## The cockpit's working directory

The note asked whether a git call inside the bundled module works in the sidecar. It does, and the reason is that nothing guesses: `walk_payload` passes `docs_root.parent` as the repo root, and `_git` runs `git -C <that path>`. A sidecar started anywhere reads the workspace it was given. Where git is missing entirely, `_git` returns a code rather than raising, so the survey is lost and the walk is not.
