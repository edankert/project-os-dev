---
type: "[[issue]]"
id: ISS-0090
aliases: ["ISS-0090"]
title: "The Stop hook validates without syncing the snapshot first, so a note another agent just wrote blocks the turn"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: "2026-09-26"
source: ["your-trainer session your-trainer-b8, on Edwin's instruction (2026-09-26: 'review where most of the time went', then 'Make it so')"]
reported_by: review
question: ""
severity: medium
component: "tools/adapters/claude-code/hooks/close-out-check.sh; tools/adapters/codex/hooks/dispatch.py"
parent: ""
related: ["[[ISS-0085-Parallel-Reviewers-Mutate-The-Same-Working-Tree]]"]
tasks: ["[[TASK-0171]]"]
tests: ["[[TST-0029-The-Stop-Hooks-Sync-Before-They-Validate]]"]
---

# The Stop hook validates without syncing the snapshot first, so a note another agent just wrote blocks the turn

## Problem

`close-out-check.sh` runs `validate-docs.sh` without first running `sync-snapshot.py`; `.githooks/pre-commit` runs the sync first. So a note that raises a counter blocks a stop with an error the next commit would have fixed by itself. The Codex stop handler in `dispatch.py` does the same.

## Evidence

- In your-trainer, a background planner created REQ-0221 to REQ-0223 mid-run. The main session's turn was then blocked by `ERROR [COUNTER] REQ-0221 ... exceeds counters.REQ = 220`.

## Proposal (from the report)

The Stop hook runs `sync-snapshot.py` before validating, as the pre-commit hook does. A consideration for the fix: the sync writes SNAPSHOT.yaml, which makes the Stop hook a second writer while another agent may be editing it.

## Relation to ISS-0085

Both come from two agents working in one tree, but this is a different mechanism: a validation order in one hook, not two reviewers mutating the same file. Filed separately so each can be fixed on its own.

## Fixed, 2026-09-26

TASK-0171. Both Stop hooks run `sync-snapshot.py` before the validator. The report's concern, that the hook becomes a second writer of SNAPSHOT.yaml, is handled in the sync: it re-reads the file just before writing and leaves it alone if anything changed, then replaces it in one step. TST-0029 tests both hooks and that guard.
