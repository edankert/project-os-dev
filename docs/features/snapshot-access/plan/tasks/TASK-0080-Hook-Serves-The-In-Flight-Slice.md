---
type: "[[task]]"
id: TASK-0080
aliases: ["TASK-0080"]
title: "SessionStart emits the in-flight slice instead of a reminder to read the file"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-03
updated: 2026-08-03
source: ["ISS-0031"]
parent: "[[FEAT-0021]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ISS-0031]]", "[[ADR-0002]]", "[[ADR-0017]]"]
tests: []
---

# The hook serves orientation

## What changes

`snapshot-freshness.sh` currently ends:

```bash
echo "REMINDER: Read SNAPSHOT.yaml to understand current project state, focus, and active work before proceeding."
```

It emits the orientation content instead: `focus`, `metrics.counts`, and items whose status is in-flight (`doing`, `review`, `open`, `triage`), with fields trimmed to title / status / file / parent / phase.

Contract **HC-002** changes with it — its check logic today is *"Required context files exist and `SNAPSHOT.yaml` can be read"*, and the failure mode it guards (missing files) must survive the rewrite rather than being replaced by the new behaviour.

## The token budget is the design constraint

Measured 2026-08-03: 513 (project-os-cockpit), 778 (your-applications.com), 1,294 (your-sudoku), 1,663 (project-os-dev), 3,418 (your-health) — and **11,573 in your-trainer**, for 58 items where your-health fits 67 in 3,418.

The difference is title length, not item count. Decide the rule before implementing:

- truncate titles to a fixed width (simplest; loses the tail of long titles, which in `your-trainer` is where the substance often is), or
- cap total output and drop the least relevant items when over budget (needs a relevance order, which is a judgement the hook should probably not be making), or
- emit IDs and statuses only above a threshold, with titles below it.

**A hook that injects 11.5k tokens into every session has re-created the cost this line of work was checking for.** State the budget in the note, and make exceeding it a failure of this task rather than a discovered surprise.

## Constraints

- **Fail open.** A hook that errors must not block the session; the current one exits 0 unconditionally and that property is load-bearing.
- **Cheap.** It runs on every session start. Parsing a 386 KB YAML must stay fast enough to be unnoticeable, and must not require a Python import chain that may be absent.
- **Per-tool implementations move together** (ADR-0002): Claude Code's `snapshot-freshness.sh` and the Codex/generic `tools/agents/bootstrap.sh`. Regenerate adapters and run `generate-adapters.py --check`.
- **The startup instruction surface must stop telling agents to read the whole file** once the hook serves it, or the two disagree and ISS-0031 reappears with the roles reversed. That means `CLAUDE.md`, the user-level `CLAUDE.md`, `CONTEXT.md` and HC-002 — stated once per REQ-0018, referenced from the rest.

## Definition of Done

- [ ] Hook emits focus, counts and in-flight items; the reminder string is gone.
- [ ] HC-002's existing guard (required files present, snapshot readable) still fires, with its failure path unchanged.
- [ ] Stated token budget, met in all twelve repos including `your-trainer`, with the truncation rule recorded.
- [ ] Codex/generic implementation updated in step; `generate-adapters.py --check` clean.
- [ ] Startup instructions reconciled so nothing still directs a whole-file read.
- [ ] Verified by running a session in a large repo and a small one and confirming what actually lands in context.
