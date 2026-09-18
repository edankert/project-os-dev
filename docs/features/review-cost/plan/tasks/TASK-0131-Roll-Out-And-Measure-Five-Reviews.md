---
type: "[[task]]"
id: TASK-0131
aliases: ["TASK-0131"]
title: "Roll out and measure five reviews"
status: backlog
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Medium"
due: ""
depends: [TASK-0129, TASK-0130]
blocks: []
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]", "[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
tests: []
---

# Roll out and measure five reviews

## Definition of Done
- [ ] ADR-0047 is accepted, or Edwin has said to roll this out without it.
- [ ] The template changes are synced to `your-trainer` and `project-os-cockpit`, together with the cockpit's `QUALITY.md`, which is two months behind. The cockpit's `.claude/agents/independent-reviewer.md` is re-copied by hand and the hook is installed in both repos.
- [ ] **Sonnet trial.** The next three small reviews run on Sonnet. Each has an Opus review of the same packet to compare against. Sonnet is kept for small features only if it missed nothing the Opus review marked *refuted*. The result is recorded here.
- [ ] **Five measured reviews.** The next five `your-trainer` feature reviews are measured with the reference note's query. The numbers go into PHASE-0007: median tool calls, minutes, total context tokens, and whether any review hit the limit.
- [ ] The acceptance targets in FEAT-0034 are met, or the gap is recorded with what to change.

## Steps
- [ ] Run `tools/scripts/sync-project-os.sh` in each repo and review the diff before committing.
- [ ] Run the trial and the measurements as the reviews happen. Nothing needs scheduling, because they are normal feature reviews.

## Notes
- The other nine fleet repos get this at their next sync. That is not part of this task.
