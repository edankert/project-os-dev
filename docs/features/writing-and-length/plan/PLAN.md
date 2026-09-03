---
type: "[[plan]]"
title: "Delivery plan — the writing rules, then the lengths"
status: done
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0025-Writing-Rules-For-The-Final-Message-And-Length-Limits]]"]
implements: ["[[FEAT-0025-Writing-Rules-For-The-Final-Message-And-Length-Limits]]"]
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — the writing rules, then the lengths

## Where the work lands

`~/Dev/repos/project-os`: `tools/instructions/WRITING.md`, `tools/instructions/SNAPSHOT.md`, `AGENTS.md`, and three files under `docs/__templates__/`.

## Sequence

[[TASK-0096]] and [[TASK-0097]] are independent. Run them in either order or together; they share no file.

## Why this feature comes before the trim

[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]] rewrites six instruction files. It should be rewriting them against the finished rule set, not against a rule set that gains a mannered-prose ban a week later. That is the whole dependency.

## What is deliberately deferred

A validator check on title length, and the backfill of the titles and notes that are already too long. Both need a counted violation set, and neither is needed for the rule to start applying to new notes.
