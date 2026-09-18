---
type: "[[task]]"
id: TASK-0129
aliases: ["TASK-0129"]
title: "Round two verifies fixes only"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Small"
due: ""
depends: [TASK-0126, TASK-0128]
blocks: [TASK-0131]
related: ["[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]"]
tests: [TST-0013, TST-0015]
---

# Round two verifies fixes only

## Definition of Done
- [x] `review-packet.sh <FEAT-ID> --round 2 --since <commit>` writes a round-two packet. It holds round one's blocking findings, copied from the feature note, and the diff since round one. It holds nothing else.
- [x] The skill states the round-two job: answer *fixed* or *not fixed* for each blocking finding, with the command that shows it. Raise no new findings.
- [x] The hook uses a limit of 15 for round two. It learns the round from the packet or the agent's prompt, whichever TASK-0128 finds reliable.
- [x] The reviewed note records `review_round: 1` or `2` beside `review_verdict`. The validator reports a value above 2, which closes [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]].
- [x] `SCHEMAS.md` and the note templates carry the new field.

## Steps
- [x] Add the round mode to the packet script and its fixture test.
- [x] Add the field, the template entries and the validator check with its fixture.
- [x] Add the round-two section to the skill.

## Notes
- FEAT-0107's round two made 48 calls, 36 of them before its first test run. With the packet, round two should not need to re-learn the code.

## Done, 2026-09-18
Implemented in `3c979ee`: `review-packet.py --round 2 --since`, the 15-call round-two budget in the hook (it switches when the reviewer reads a `review-packet-…-r2` file), `review_round` in the feature and test templates and `SCHEMAS.md`, and the validator's `REVIEW-ROUND` error. This closes [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]].
