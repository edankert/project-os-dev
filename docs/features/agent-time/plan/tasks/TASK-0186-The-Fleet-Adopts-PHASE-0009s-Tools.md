---
type: "[[task]]"
id: TASK-0186
aliases: ["TASK-0186"]
title: "Every downstream repo derives its lists, and the repos with a release archive their released tickets"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["Edwin, 2026-09-26: 'Can you turn on derived lists (and other parts of the solution) and archive or migrate the notes for each of these repos?'"]
parent: "[[ISS-0091-Finished-Notes-Have-No-Archive]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ISS-0095-One-Relationship-Is-Written-In-Six-Places]]", "[[ISS-0099-Ledger-Field-Warnings-Wait-Ninety-Days]]", "[[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It]]", "[[TASK-0180]]", "[[TASK-0172]]"]
tests: ["[[TST-0030-A-Relationship-Written-On-The-Child-Reaches-Every-List]]", "[[TST-0035-An-Edit-To-A-Released-Ticket-Warns]]", "[[TST-0033-A-Reworded-Check-Breaks-No-Tag-Only-Walk]]", "[[TST-0027-The-Note-Cache-Never-Changes-What-The-Checks-Say]]"]
---

# Every downstream repo derives its lists, and the repos with a release archive their released tickets

## Definition of Done
- [x] Ten of the eleven downstream repos set `retention.derive_lists: true`, with each list conflict read and settled on the side that is right. articles waits: another session has three uncommitted tasks there (TASK-0064 to TASK-0066) that the derived lists would name, so turning it on now would commit lists naming notes that are not committed.
- [x] your-trainer and project-os-cockpit archive their released, finished tickets (1,063 and 631 notes); the other repos have no release yet.
- [x] your-trainer runs `migrate-ledger-fields.py` (236 of 654 notes cleared) and converts its lossless walk lines to tags (232), after the cockpit's bundled walk module could render them. The REL-0017 sheets are identical line for line before and after each step.
- [x] Each repo validates, `validate-docs.sh --as-committed` passes in all twelve, the cockpit's full suite passes (2,206), and each change is committed on its own.

## Steps
- [x] One commit per repo and per change, touching only what the tools wrote. In your-applications.com, SNAPSHOT.yaml carried another session's uncommitted edits, so only the `derive_lists` line was staged, through a patch applied to the index.

## What the rollout found, and fixed in the template

Each of these reached the fleet before it was caught, and each has its own commit and test in project-os:

- **The Stop hook skipped validation on a fresh clone** (ISS-0103, TASK-0185), found by CI after the first push.
- **The per-process note index hid a tool's own writes** from it (`f1c2775`). The cockpit's `migrate-fleet-validator.py` writes notes and asks again. The index is now rebuilt when any note's path, size or mtime changes.
- **A deferred task got its old parent written back** (`b5cd1b5`), which the validator refused as DEFER-PARENT in the cockpit. The stale list entry is dropped instead.
- **Released notes depended on git tags** (`acc64c3`). A shallow clone or an archive has none, so it hid nothing. They are now found from the release note's date.
- **A tag-only walk line broke emphasis and collapsed spacing**, and `walk-tags.py` stopped part way when its output was cut short (`51471ef`, `681675d`).

The cockpit also needed its bundled walk and validator modules refreshed, a label for FRONTMATTER-TYPO, and its grandfathered PARENT-BACKLINK block removed: all 66 of those ids name notes released at v1.0.0.

## List conflicts, and which side was right

- The child's own field was right in 17 cases: the cockpit's 8, your-trainer's 2, and your-health's FEAT-0052, ISS-0051, FEAT-0117, REQ-0118, TASK-0022, FEAT-0008 and FEAT-0009, all as their phase notes say.
- project-os-bench's REQ-0002 had no evidence either way, so its own `phase:` won.
- The list was right in 3 cases, all in your-health: ISS-0014 (closed in PHASE-0005) and TASK-0032 and TASK-0050 (done in PHASE-0001). Their `phase:` fields were corrected.
