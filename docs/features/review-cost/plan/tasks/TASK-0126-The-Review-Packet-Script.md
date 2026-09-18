---
type: "[[task]]"
id: TASK-0126
aliases: ["TASK-0126"]
title: "The review packet script"
status: backlog
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
tests: []
---

# The review packet script

## Definition of Done
- [ ] `tools/scripts/review-packet.sh <FEAT-ID>` exists in `~/Dev/repos/project-os` and writes one Markdown file, by default under the system temp directory, and prints its path.
- [ ] The packet holds, in this order:
  - [ ] the feature's title and goal;
  - [ ] its acceptance criteria, copied word for word from the note;
  - [ ] the commits found for the feature (see Steps), each as hash and subject;
  - [ ] the source diff of those commits, with `docs/` and `SNAPSHOT.yaml` left out;
  - [ ] the test files added or changed, as a list;
  - [ ] the author's last full test run: the command, the date and the result count, read from the feature note's `## Verification` section;
  - [ ] an empty "Author's claims" section for up to three extra claims.
- [ ] A packet whose diff is over 1500 lines prints a warning naming the largest files, so the author can split the review or accept the size knowingly.
- [ ] A fixture test covers a feature with commits, a feature with none (the script exits non-zero with a clear message), and the docs exclusion.
- [ ] Run against `your-trainer`'s FEAT-0107 at `a5425c6e^`, the packet includes the six write guards in `BluetoothManager.kt`.

## Steps
- [ ] Find the commits: every commit whose message names the feature or one of its `tasks:` IDs. Allow `--range <base>..<head>` to override when commit messages do not name them.
- [ ] Read the acceptance criteria from the note's `## Acceptance` section, and the test run from `## Verification`.
- [ ] If the feature note has no `## Verification` section, add one to the feature template, holding the command, the date and the result count. Record that template change in this task.
- [ ] Write the fixture test beside the existing script tests.

## Notes
- The packet is the review's scope. Anything the reviewer reads outside it must be reached from a line in the diff.
- Keep the script free of repo-specific paths, so all 12 fleet repos can run it unchanged.
