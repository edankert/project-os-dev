---
type: "[[task]]"
id: TASK-0188
aliases: ["TASK-0188"]
title: "Expect lines in a test note can be marked for one platform, and the generator prints only this platform's lines"
status: doing
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
tests: []
---

# Expect lines in a test note can be marked for one platform, and the generator prints only this platform's lines

A test note's Expect line may start with `[android]` or `[ios]`, and the page for the other platform leaves it out. This stops iOS wording from appearing in the Android release test.

## Definition of Done
- [ ] The generator prints a marked Expect line only on its platform, and an unmarked line on every platform.
- [ ] Tag `.N` pairs with the Nth Expect line that applies on the current platform (ADR-0049's pairing rule, counted per platform).
- [ ] The validator refuses a bracketed platform with no ledger, naming the check and the line.
- [ ] A procedure line that quotes an expectation instead of giving tags only is reported. It is a warning until consumers have migrated, then an error.
- [ ] `docs/__templates__/test.md` shows the per-platform form, `SCHEMAS.md` describes it, and TESTING.md states the rule once.
- [ ] Tests in `test-release-test.sh` cover each of the above, and each test fails when its guard is removed.

## Steps
- [ ] Parse the platform marker in the Expect reader the generator and validator share.
- [ ] Change the pairing count to per-platform lines.
- [ ] Update `release-test-tags.py` so it converts remaining quoted lines to tags.
- [ ] Update the template, SCHEMAS.md and TESTING.md.

## Notes
- Shortening Expect lines in consumer notes is not this task. The skill in TASK-0193 does it, and your-trainer's own item does it for its notes.
