---
type: "[[plan]]"
title: "Delivery plan: a review costs what the change is worth"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
implements: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]"]
---

# Delivery plan: a review costs what the change is worth

## Where the work lands

Every file this feature changes is in `~/Dev/repos/project-os`, the template repo:
- the script and the hook under `tools/`;
- the skill;
- the reviewer agent emitted by `generate-adapters.py`.

This repo holds the record. `your-trainer` and `project-os-cockpit` receive the files at the sync in TASK-0131. The cockpit's `.claude/agents/` copy is re-copied by hand, because its sync never touches `.claude/`.

## Delivery sequence

1. **[[TASK-0126-The-Review-Packet-Script|TASK-0126]]: the packet.** First, because everything else assumes the reviewer starts from it.
2. **[[TASK-0127-The-Reviewer-Checks-A-List-Of-Claims|TASK-0127]]: the procedure.** The claims list, targeted tests, context rules, and `effort: medium` in the agent file.
3. **[[TASK-0128-A-Hook-Stops-The-Reviewer-At-Its-Budget|TASK-0128]]: the hook.** It can be built in parallel with step 2. Its messages quote the skill's wording, so it is finished after step 2.
4. **[[TASK-0129-Round-Two-Verifies-Fixes-Only|TASK-0129]]: round two.** A packet mode for fixes, a 15-call limit, and the round number recorded.
5. **[[TASK-0130-Re-Run-The-FEAT-0107-Review-The-New-Way|TASK-0130]]: the proof.** The gate before rollout. If the re-run misses the known defect, go back to step 2 or 3 before continuing.
6. **[[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]]: rollout.** The sync is done and reached every fleet repo. The Sonnet trial was dropped on 2026-09-19 and the five measured reviews on 2026-09-20; the task is `cancelled` and says why. Two reviewers on one packet was already chosen on measured evidence in TASK-0130.

## Dependencies

- ADR-0047 should be accepted before step 6, because the rollout changes what every repo's reviewer does. Steps 1–5 are reversible and can run before that.
- The measurement query is in the reference note. Keep it unchanged, so the numbers compare with the baseline.
