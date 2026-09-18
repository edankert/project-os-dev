---
type: "[[task]]"
id: TASK-0126
aliases: ["TASK-0126"]
title: "The review packet script"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Medium"
due: ""
depends: []
blocks: [TASK-0127, TASK-0129, TASK-0130]
related: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]"]
tests: [TST-0013]
---

# The review packet script

## Definition of Done
- [x] `tools/scripts/review-packet.sh <FEAT-ID>` exists in `~/Dev/repos/project-os` and writes one Markdown file, by default under the system temp directory, and prints its path.
- [x] The packet holds, in this order:
  - [x] the feature's title and goal;
  - [x] its acceptance criteria, copied word for word from the note;
  - [x] the commits found for the feature (see Steps), each as hash and subject;
  - [x] the source diff of those commits, with `docs/` and `SNAPSHOT.yaml` left out;
  - [x] the test files added or changed, as a list;
  - [x] the author's last full test run: the command, the date and the result count, read from the feature note's `## Verification` section;
  - [x] an empty "Author's claims" section for up to three extra claims.
- [x] A packet whose diff is over 1500 lines prints a warning naming the largest files, so the author can split the review or accept the size knowingly.
- [x] A fixture test covers a feature with commits, a feature with none (the script exits non-zero with a clear message), and the docs exclusion.
- [x] Run against `your-trainer`'s FEAT-0107 at `a5425c6e^`, the packet includes the six write guards in `BluetoothManager.kt`.

## Steps
- [x] Find the commits: every commit whose message names the feature or one of its `tasks:` IDs. Allow `--range <base>..<head>` to override when commit messages do not name them.
- [x] Read the acceptance criteria from the note's `## Acceptance` section, and the test run from `## Verification`.
- [x] If the feature note has no `## Verification` section, add one to the feature template, holding the command, the date and the result count. Record that template change in this task.
- [x] Write the fixture test beside the existing script tests.

## Notes
- The packet is the review's scope. Anything the reviewer reads outside it must be reached from a line in the diff.
- Keep the script free of repo-specific paths, so all 12 fleet repos can run it unchanged.

## Done, 2026-09-18
Implemented in `~/Dev/repos/project-os` commit `3c979ee`: `tools/scripts/review-packet.py`, its test `test-review-packet.sh` ([[TST-0013]], 23 assertions), and a `## Verification` section in the feature template. Run against your-trainer's FEAT-0107 at `a5425c6e^`, the first packet was 9,038 lines. Two changes brought it to 183 lines plus an indexed 5,533-line `.diff`: generated and translated files are left out (the Room schema, the `.xcstrings` catalogue and eight translated `strings.xml` were a fifth of the diff), and commits are matched on the subject line, because a body that mentions the feature in passing is other work. All six write guards behind ISS-0466 stay in it. The script also reads tests linked through `covers:` (ADR-0032), which the first version missed.
