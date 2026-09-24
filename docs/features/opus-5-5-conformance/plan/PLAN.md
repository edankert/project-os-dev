---
type: "[[plan]]"
title: "Delivery plan: five changes from the Opus 5.5 guide review"
status: done
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]"]
implements: ["[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]"]
related: ["[[Opus-5-5-Prompting-Guide-Review-2026-09-24]]", "[[TASK-0080]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:`; why, and how they are found,
     is stated once in tools/instructions/STATUSES.md, `[[plan]]`. -->
# Delivery plan: five changes from the Opus 5.5 guide review

## Where the work lands

All of it is in the template, `~/Dev/repos/project-os`. The template's working tree already holds uncommitted changes from other work: the three `rank-*.py` scripts from PHASE-0008 and a one-line status-quoting fix in the Codex `dispatch.py` with its test. This work does not commit or revert them. [[TASK-0157]] edits `dispatch.py` too, on different lines.

## Delivery sequence

1. [[TASK-0156]]: pins in `generate-adapters.py`, regenerate, `--check`.
2. [[TASK-0160]]: `review-budget.py`, HC-010, `test-review-budget.sh`. It goes early so this feature's own independent review runs with the running count, which gives one real sample against the 34-call baseline.
3. [[TASK-0157]]: `close-out-check.sh`, Codex `dispatch.py`, HC-006, `test-hooks.sh`, `test-codex-adapter.py`.
4. [[TASK-0158]]: `LIFECYCLE.md`, regenerate the Cursor bundle, `test-word-budgets.sh` and `test-pause-rule.sh`.
5. [[TASK-0159]]: two instruction files.
6. [[TASK-0080]] runs alongside, under FEAT-0021. It changes `snapshot-freshness.sh` and `bootstrap.sh` and is tested in `test-hooks.sh`, so it shares step 3's test run.
7. Run the template's full test suite, sync this repo from the template, validate, then the independent review.
