---
type: plan
status: done
parent: "[[FEAT-0010-Template-Completeness-Program]]"
created: 2026-07-17
updated: 2026-07-17
---

# Plan: Template Completeness Program

## Approach

Execute the five review-derived steps in order of leverage: fix internal contradictions first (cheap, unblocks taxonomy-dependent work), then modernize the Claude Code adapter (biggest behavior gain per effort, un-stubs Cursor as a side effect), then surface verification health in the cockpit (delegated to a parallel agent in that repo, no commits there while the PHASE-007 batch is uncommitted), then mechanize fleet sync, then wire external tools. Changes land in the project-os template repo; this repo tracks the program; the cockpit repo tracks its own FEAT-0018.

## Tasks

- [x] TASK-0041: Consistency-debt pass in the template
- [x] TASK-0042: Native Claude Code adapter (generated native skills, reviewer subagent, one-step install)
- [x] TASK-0043: Cockpit verification health (FEAT-0018 in project-os-cockpit)
- [x] TASK-0044: Sync manifest + fleet validator
- [x] TASK-0045: External tool wiring
