---
type: "[[plan]]"
title: "Delivery plan — the runner, the validator, the prose, then this repo"
status: active
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"]
implements: ["[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"]
related: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — the runner, the validator, the prose, then this repo

## Sequence

1. [[TASK-0107]] first: the validator must accept a `command:` test at `active` before any note is stripped, or every repo that strips goes red.
2. [[TASK-0106]] and [[TASK-0108]] next, in either order; they share no file.
3. [[TASK-0109]] last: it syncs the template's tools into this repo and needs all three above committed there.

## Why this repo goes last and costs the most

Its vendored validator is a month old. The template's validator reports 47 errors here on checks that landed since (PARENT-BACKLINK 41, SNAPSHOT-MEMBERSHIP 3, METRICS 2, DECISION-OPTIONS 1). Those are cleared in the same task, before the sync, so pre-commit keeps passing.
