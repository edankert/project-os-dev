---
type: "[[task]]"
id: TASK-0149
aliases: ["TASK-0149"]
title: "No harness runs against a cached compile, and the one that exposed it is in the suite"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["[[ISS-0073-A-Validator-Test-Can-Run-Against-Code-That-Is-Not-The-Source]]", "Edwin, 2026-09-20: 'Can we close the PHASE-0007 now as well'"]
parent: "[[ISS-0073-A-Validator-Test-Can-Run-Against-Code-That-Is-Not-The-Source]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]", "[[TST-0020]]"]
tests: ["[[TST-0020]]"]
---

# No harness runs against a cached compile

## Problem

A test harness can report a verdict for code nobody is running. On 2026-09-20 `test-metric-counts.sh` reported two failures while the same assertions passed on the source in the working tree: it had executed a 14 September compile of `validate-docs.py`. Apple's `python3` sets `sys.pycache_prefix` to `~/Library/Caches/com.apple.python`, so the cache lives **outside the repository** and deleting `tools/scripts/__pycache__` does nothing.

The hazard runs both ways. A test can also pass against a fix that is not on disk.

## What was done

**Write no bytecode, so none can go stale.** `-B` is not enough on its own — it stops writing, not reading — but a cache that is never written can never be read. Every script that loads a module by path now refuses to write one:

- Seven shell harnesses export `PYTHONDONTWRITEBYTECODE=1` (two already did it per-invocation).
- Five Python tools set `sys.dont_write_bytecode = True` before importing anything by path: the three `test-*.py` harnesses, `fleet-file-drift.py` and `review-packet.py`.

Each carries the reason in a comment, so the next person does not remove it as noise.

The template already gitignored `__pycache__/` and `*.py[cod]`.

**And the harness that exposed it is now in the suite.** It was wired to no `TST-*` note, so `run-tests.py` never ran it and the recorded "17 passing, 0 failing" covered it in neither direction — [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]'s shape again. [[TST-0020]] now carries its command.

## Definition of Done

- [x] No script that loads a module by path writes bytecode.
- [x] Every cache cleared, and none recreated by a full run.
- [x] `test-metric-counts.sh` has a `TST-*` note, so the suite runs it.
- [x] Every affected harness still passes.

## Verification

Caches cleared (`tools/scripts/__pycache__` and the Apple prefix path), then every affected harness run: **test-metric-counts 6, test-review-budget 21, test-statuses-md 3, test-fleet-file-drift 20, test-walk-sheet 157, test-ledger-checks and test-review-and-issue-fields end to end, test-retention 26, test-decision-rule 26, test-walk-preparation OK** — all 0 failures. Afterwards `tools/scripts/__pycache__` does not exist and nothing new appeared under the Apple cache for these files.

**A mistake worth recording.** The first edit put `import sys` above `from __future__ import annotations`, which is a syntax error, and `test-retention.py` and `test-decision-rule.py` stopped running entirely. Caught by running them immediately rather than assuming a mechanical edit was safe.
