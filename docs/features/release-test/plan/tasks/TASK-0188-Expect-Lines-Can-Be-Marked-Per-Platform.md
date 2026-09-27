---
type: "[[task]]"
id: TASK-0188
aliases: ["TASK-0188"]
title: "Expect lines in a test note can be marked for one platform, and the generator prints only this platform's lines"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "M"
due: ""
depends: ["[[TASK-0187]]"]
blocks: []
related: ["[[REQ-0034-A-Check-Writes-Its-Expected-Result-Once-Per-Platform]]", "[[ADR-0049-A-Walk-Step-May-Cite-A-Check-Without-Quoting-It]]"]
tests: ["[[TST-0042-An-Expect-Line-Marked-For-A-Platform-Prints-Only-There]]"]
---

# Expect lines in a test note can be marked for one platform, and the generator prints only this platform's lines

A test note's Expect line may start with `[android]` or `[ios]`, and the page for the other platform leaves it out. This stops iOS wording from appearing in the Android release test.

## Definition of Done
- [x] The generator prints a marked Expect line only on its platform, and an unmarked line on every platform. project-os 72b0d29: `expect_entries` reads the mark, and the tag-only expansion, the quote comparison and the per-check rows all use the lines for the platform being tested, with the brackets removed. TST-0042: on testbed the `[testbed]` line prints and the `[bench]` line does not, and the reverse on bench; making the filter always true fails 5 assertions.
- [x] Tag `.N` pairs with the Nth Expect line that applies on the current platform (ADR-0049's pairing rule, counted per platform). `expect_for` takes the platform. TST-0042: TST-0401 has four Expect lines for three steps, three on each platform, and `.3` prints only the third; counting every platform's lines fails 14 assertions.
- [x] The validator refuses a bracketed platform with no ledger, naming the check and the line. `release-test.py --check`, which `validate-docs.sh` runs on every commit, prints `ERROR [RELEASE-TEST] ... TST-0405: an Expect line is marked [andriod], and this repo keeps ledgers only for bench, testbed: - [andriod] ...` and exits 1. Removing it fails 1 assertion.
- [x] A procedure line that quotes an expectation instead of giving tags only is reported. It is a warning until consumers have migrated, then an error. `--check` prints `WARN [RELEASE-TEST]` for each quoted line and for an action line carrying tags, exit 0; `--quiet` prints one line with the count. `QUOTED_EXPECTATIONS_REFUSED` in `release-test.py` makes each one a problem. It stays off: your-trainer's procedures hold 724 quoted lines today, and turning it on is owed once your-trainer FEAT-0129 and the cockpit have migrated (see Notes). Mutations: warning removed, 4 failures; switch ignored, 1; count off, 1.
- [x] `docs/__templates__/test.md` shows the per-platform form, `SCHEMAS.md` describes it, and TESTING.md states the rule once. project-os 0289cb8: the rule is in TESTING.md, "A check is testable by a stranger", Expect; rule 5 and rule 9 link to it; SCHEMAS.md's acceptance fields describe the form.
- [x] Tests in `test-release-test.sh` cover each of the above, and each test fails when its guard is removed. 25 new assertions (179 to 204); twelve mutations each fail the harness, listed in TST-0042's adequacy.

## Steps
- [x] Parse the platform marker in the Expect reader the generator and validator share (`expect_entries`, `expect_marks`).
- [x] Change the pairing count to per-platform lines.
- [x] Update `release-test-tags.py` so it converts remaining quoted lines to tags: `--all` rewrites every quoted line as its tags and moves tags off action lines; the lossless default now compares on every platform the step runs on.
- [x] Update the template, SCHEMAS.md and TESTING.md.

## Notes
- Shortening Expect lines in consumer notes is not this task. The skill in TASK-0193 does it, and your-trainer's own item does it for its notes.
- **The switch to an error is not flipped.** `QUOTED_EXPECTATIONS_REFUSED = False` in `release-test.py`. Flipping it is a one-line change in a later template release, once your-trainer FEAT-0129 has run `release-test-tags.py --all --apply` (or the procedure skill has rewritten its procedures) and the cockpit's bundle has been refreshed. It fits with TASK-0196, which turns the length warning into an error at the same point in the rollout.
- **Where the refusal runs.** "The validator" here is `release-test.py --check`, the part of `validate-docs.sh` that reads acceptance checks against ledgers. The check reads the platform names from the ledger file names, as the other platform checks do, so a repo with no ledgers is not checked.
- **The quiet count.** Under `--quiet`, which is how `validate-docs.sh` runs it, the warnings print as one line per kind with a count. On a scratch copy of your-trainer that line reads 724; without `--quiet`, `--check` lists all 724. Listing them on every commit would bury the errors.
- **A mark must follow the list marker.** `- [android] text`. The name is lower case, so a bracketed word such as `[Save]` is not read as a platform; `[x]` would be, and is refused unless a ledger is named `x`.
- your-trainer on a scratch copy (Android and iOS, REL-0017): the two sheets are byte for byte the same as before this task, because no check there marks a line yet.
- Commits in project-os: 72b0d29 (code and tests), 0289cb8 (instructions and template).
