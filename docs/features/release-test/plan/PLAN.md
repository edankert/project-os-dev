---
type: "[[plan]]"
title: "The release test reads in short lines: delivery plan"
status: draft
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
implements: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
---

# The release test reads in short lines: delivery plan

The rename goes first, because every other task edits the files it renames. Then the three inputs change (Expect lines, procedure shape, what changed), then the generator's output, then the length check and the skill. The pilot runs last in this repo's plan and continues in your-trainer.

| Order | Task | What it delivers | Depends on |
|---|---|---|---|
| 1 | [[TASK-0187]] | Every name in ADR-0050's rename map, a migration script for consumers, old names refused | nothing; the ledger key waits on Edwin |
| 2 | [[TASK-0188]] | Expect lines marked `[android]` or `[ios]` | TASK-0187 |
| 2 | [[TASK-0189]] | Procedures grouped under headings with a `Start:` line; `readiness_for:` gains `result:` | TASK-0187 |
| 2 | [[TASK-0191]] | Change notes declare `platforms:`; what changed per section and platform; stale screenshots flagged | TASK-0187 |
| 3 | [[TASK-0190]] | The new output: sections, setup in three parts, numbered checks in groups, in Markdown and JSON | TASK-0188, TASK-0189 |
| 3 | [[TASK-0194]] | The procedure skill renamed and rewritten for the new shape | TASK-0187, TASK-0189 |
| 4 | [[TASK-0192]] | The length check, as a warning | TASK-0190 |
| 5 | [[TASK-0193]] | The `release-test-prep` skill, called from release-prep | TASK-0191, TASK-0192 |
| 6 | [[TASK-0195]] | Sync to project-os-cockpit and your-trainer; the Equipment section pilot on Android | TASK-0190 to TASK-0194 |
| 7 | [[TASK-0196]] | The length check becomes an error | TASK-0195 and your-trainer's other sections |

Rollout, as Edwin set it on 2026-09-27: pilot the Equipment section end to end in Your Trainer on Android, then the other Android sections, then iOS, then turn the warning into an error.

Work in the other two repositories:

- project-os-cockpit: the release test page in the Tests pane (ID to follow). It reads TASK-0190's JSON and renames the cockpit's bundle, route and tests.
- your-trainer: rewrite of the procedures and test notes, Equipment section pilot (ID to follow). It shortens Expect lines, splits them per platform, regroups the procedures and writes the what-changed lines.

Complexity by blast radius: High overall, because the rename reaches three repositories and every acceptance check's Expect lines change. The pilot is Medium.
