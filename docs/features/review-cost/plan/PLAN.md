---
type: "[[plan]]"
title: "Delivery plan: a review costs what the change is worth"
status: draft
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
implements: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]"]
---

# Delivery plan: a review costs what the change is worth

1. **The rule text.** Change `QUALITY.md` so a review gate is one feature. Put the procedure and the budget into `independent-review/SKILL.md` and into the reviewer agent that `generate-adapters.py` emits. All of this is in `~/Dev/repos/project-os`.
2. **Round counts.** Add a `review_rounds:` field to the note frontmatter and have the validator report a value above 2 ([[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]]).
3. **Sync** to `your-trainer` and `project-os-cockpit`. Re-copy the agent file by hand in the cockpit, because its sync does not touch `.claude/`.
4. **The model trial**, run on the next three small reviews.
5. **Measure** the next five reviews and write the numbers into PHASE-0007.

Tasks are minted when step 1 starts, after Edwin accepts ADR-0047.
