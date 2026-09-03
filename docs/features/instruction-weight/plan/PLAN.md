---
type: "[[plan]]"
title: "Delivery plan — trim the always-loaded file first, then the rest"
status: draft
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"]
implements: ["[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"]
related: ["[[Prompting-Guide-Review-2026-09-03]]", "[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — trim the always-loaded file first

## Where the work lands

`~/Dev/repos/project-os`: five instruction files, two templates, the adapter generator, and the ADRs that receive the moved text.

## Sequence

1. **[[TASK-0098]] first**, alone. LIFECYCLE.md is the file every session pays for, it has the only stated target, and doing it by itself gives a measured before and after that the other three can be judged against.
2. **[[TASK-0099]]** next, one file per commit. Four files in one commit is a diff nobody reviews.
3. **[[TASK-0100]]** and **[[TASK-0101]]** are independent of both and of each other.

## Ordering against the other features

This feature runs **after** [[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]] and [[FEAT-0025-Writing-Rules-For-The-Final-Message-And-Length-Limits]]. FEAT-0024 adds three rules to LIFECYCLE.md's Execution section; trimming first means trimming twice. FEAT-0025 adds the mannered-prose rule that this pass applies.

## Open question for the owner

**Budgets for the other four files.** The review states one number, LIFECYCLE.md under 800. STATUSES.md at 2,772 words is the largest and is loaded on demand rather than every session, so it may not want a number at all. [[REQ-0026-Instruction-Files-Carry-Rules-Not-History]] deliberately counts only the always-loaded file and gates the rest on shape. If the owner wants numbers for the other four, they belong in the requirement's acceptance list before [[TASK-0099]] starts.

## How the moved text is not lost

Every anecdote removed is either already in an ADR or gets added to that ADR's Context section in the same commit. The change note carries the table: sentence, source file and line, destination. A trim that quietly deletes a reason is the failure mode here, and the table is what makes it visible in review.
