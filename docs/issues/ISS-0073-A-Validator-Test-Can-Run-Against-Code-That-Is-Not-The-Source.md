---
type: "[[issue]]"
id: ISS-0073
aliases: ["ISS-0073"]
title: "A validator test can pass or fail against a stale compiled copy instead of the code on disk"
status: fixed
phase: "[[PHASE-0007]]"
owner: unassigned
created: 2026-09-20
updated: 2026-09-20
source: ["The FEAT-0036 independent review, 2026-09-20, which reported test-metric-counts.sh failing when it passes on the current source"]
reported_by: review
question: ""
severity: high
component: "tools/scripts"
parent: ""
related: ["[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]", "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"]
tests: ["[[TST-0020]]"]
tasks: ["[[TASK-0149]]"]
---

# A validator test can pass or fail against a stale compiled copy instead of the code on disk

## Problem

A test harness can report a result for code nobody is running. On 2026-09-20 `tools/scripts/test-metric-counts.sh` reported two failures in this repo while the same assertions pass on the source in the working tree. The harness was executing a compiled copy of `validate-docs.py` from 14 September that Python had cached outside the repo. Anyone reading that output would go looking for a bug in code that is already correct — or, in the other direction, would see a test pass against a fix that is not there.

> [!quote] As reported — 2026-09-20 (an independent reviewer of FEAT-0036)
> `bash tools/scripts/test-metric-counts.sh` in project-os-dev today prints: `FAIL a test with a command: is executable` / `FAIL a test without one is manual`. Whether the suite regressed after the recorded run or the record is wrong, the feature cannot close on a failing test in code it changed.

## Repro

With `tools/scripts/validate-docs.py` unmodified in the working tree:

1. `bash tools/scripts/test-metric-counts.sh` → `6 assertions, 2 failure(s)`.
2. `cp tools/scripts/validate-docs.py tools/scripts/vd-COPY.py`, then run the same harness body against the copy → **0 failures**. `cmp` reports the two files byte-identical.
3. `git checkout -- tools/scripts/validate-docs.py`, which changes nothing but the file's modification time → the original now passes, twice in a row.

Adding any line to the file has the same effect as step 3. The variable is not the content.

## Evidence

`python3 -c "import sys; print(sys.pycache_prefix)"` prints `/Users/edwin/Library/Caches/com.apple.python`. The Python that runs these harnesses keeps compiled bytecode **outside the repository**, so deleting `tools/scripts/__pycache__` does not clear it, and a cache entry that Python judges current is used in place of the source.

`fields` inside `compute_metric_counts` held the right frontmatter throughout; the loaded function was simply an older compile. `inspect.getsource` reads the file rather than the cache, so it showed the current text and agreed with the disk — which is why the first few readings of this made no sense.

Five other fleet repos also carry an in-repo `tools/scripts/__pycache__/`: `your-trainer`, `project-os`, `project-os-deck`, `your-sudoku` and `project-os-cockpit`. Nothing in this repo's `.gitignore` mentions `__pycache__` or `*.pyc`.

## Why it matters

The validator is what the fleet trusts to say whether the record is true. A harness that can report a verdict for code that is not on disk weakens every result it produces, in both directions. The failure that exposed this cost most of a session to chase, and it was reported by a reviewer as a blocking finding against a feature that had not broken anything.

This also bears on [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]: `test-metric-counts.sh` is not wired to any `TST-*` note, so `run-tests.py` never runs it and the repo's recorded "passing=17 failing=0" never covered it either way.

## Proposed fix

Small, and in one place each:

- Run the harnesses with `python3 -B`, or set `PYTHONDONTWRITEBYTECODE=1` in them, so a harness never reads or writes a cache.
- Add `__pycache__/` and `*.pyc` to `.gitignore` here and in the template, and remove the five committed-adjacent directories in the fleet.
- Wire `test-metric-counts.sh` to a `TST-*` note so `run-tests.py` actually runs it (ISS-0065's work).

The fix belongs in `~/Dev/repos/project-os` and reaches the fleet at the next sync.

## Fixed, 2026-09-20

[[TASK-0149-No-Harness-Runs-Against-A-Cached-Compile|TASK-0149]], template `436ddf6`, synced to all twelve.

**Write no bytecode, so none can go stale.** `-B` alone would not have done it — it stops writing, not reading — but a cache that is never written can never be read. Seven shell harnesses now export `PYTHONDONTWRITEBYTECODE=1` and five Python tools set `sys.dont_write_bytecode = True` before loading anything by path, each with the reason in a comment.

Verified by clearing every cache, in the repo and under Apple's `sys.pycache_prefix`, running all ten affected harnesses green, and confirming none came back.

**The proposed fix listed three things and one was already done**: the template has gitignored `__pycache__/` and `*.py[cod]` for some time. The in-repo directories the issue counted in five other repos are ignored, not committed.

**The third item is done too**: `test-metric-counts.sh` was wired to no `TST-*` note, so `run-tests.py` never ran it and the recorded "17 passing, 0 failing" covered it in neither direction. [[TST-0020]] now carries it.

