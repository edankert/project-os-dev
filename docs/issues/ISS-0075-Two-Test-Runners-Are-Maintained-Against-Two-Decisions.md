---
type: "[[issue]]"
id: ISS-0075
aliases: ["ISS-0075"]
title: "The fleet runs two different test runners, built to two decisions that were never reconciled"
status: fixed
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-20
updated: 2026-09-20
source: ["The FEAT-0034 review of 2026-09-20, via fleet-file-drift.py", "project-os-cockpit .project-os-sync: 'Reconcile the two designs, then drop this line'"]
reported_by: review
question: ""
severity: medium
component: "tools/scripts"
parent: ""
related: ["[[TASK-0146-The-Four-Findings-Round-One-Left]]", "[[ADR-0025-An-Executable-Test-Carries-No-Verdict]]", "[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"]
tests: ["[[TST-0008]]"]
tasks: ["[[TASK-0148]]"]
---

# The fleet runs two different test runners, built to two decisions that were never reconciled

## Problem

`tools/scripts/run-tests.py` is the command that says whether a repo's tests pass. Twelve repos run the template's version, built to ADR-0025. `project-os-cockpit` runs its own, built to its ADR-0038, and the two differ by 170 lines. So "the tests pass" does not mean quite the same thing in the cockpit as it does everywhere else, and a change to how verdicts are reported has to be made twice or it is made once and forgotten.

The exception's own note says what is owed: *"Reconcile the two designs, then drop this line."*

## Evidence

`project-os-cockpit/.project-os-sync`:

> `tools/scripts/run-tests.py` — ADR-0038 runner (accepts `--write` as a no-op, its own tests in `tests/test_runner_writes_nothing.py`); the template's is ADR-0025. Reconcile the two designs, then drop this line.

Sizes on 2026-09-20: the template's is 225 lines, the cockpit's 207, and `diff` reports 170 lines differing. The docstrings state different authorities — the template's cites ADR-0025 and `STATUSES.md`, the cockpit's cites ADR-0038 — and they describe unrunnable commands and CI behaviour differently.

Found by `tools/scripts/fleet-file-drift.py` on 2026-09-20, and already recorded as a kept divergence by [[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template|TASK-0142]] on 2026-09-19.

## Why it matters

This is the script CI runs to decide whether a change is safe to land. Two implementations of that, against two decisions, is the same hazard as two copies of a rule: the day one is corrected, the other stays wrong, and nobody is told. The template's own instructions already warn about exactly this shape (REQ-0027, a rule stated once).

It is not urgent — both runners work, and the cockpit's has its own tests — but it is the kind of divergence that gets more expensive the longer it stands, and it has stood since ADR-0038 was written.

## What a fix looks like

Read ADR-0025 and the cockpit's ADR-0038 side by side and decide which behaviour the fleet wants, or whether the two are compatible and one runner can serve both. ~~Whoever does it should expect to supersede one ADR rather than merge two scripts: the scripts differ because the decisions do.~~ **Wrong, corrected 2026-09-20.** The decisions do not differ; see below.

Then the surviving runner goes in the template, the cockpit's `keep_local:` line goes, and `tests/test_runner_writes_nothing.py` either moves with it or is shown to be covered.

**Do not resolve this by copying one over the other.** The cockpit's runner has tests the template's does not, and the template's carries the unrunnable-in-CI rule that FEAT-0028 added.

## Fixed, 2026-09-20

Recorded in [[TASK-0148-One-Test-Runner-For-The-Fleet|TASK-0148]]. Template `284fada` and `project-os-cockpit`, which now runs the template's runner and keeps nothing back from the template at all.

**The two ADRs never conflicted, and this issue said they did.** [[ADR-0025-An-Executable-Test-Records-No-Verdict|ADR-0025]] *is* the fleet-wide adoption of the cockpit's ADR-0038: it names "project-os-cockpit ADR-0038" in its own `source:`, its Context says ADR-0038 "went one step further", and its chosen option is titled "No verdict on the note. Follow ADR-0038". `STATUSES.md` states the merged rule with both citations. Nothing is superseded. One implementation was a month behind and was deleted.

The cockpit's copy was missing four template fixes — an unrunnable command failing the run in CI, the `PROJECT_OS_ALLOW_UNRUNNABLE` escape hatch, a repeated command running once, and a failing command printing its last forty lines rather than one — and it had copied a fifth, `--ci`, without the matching signature change: its `main` unpacked four values from a `run_one` that returns three. Latent only because it declared no `ci:` block.

**What the reconciliation actually turned up.** The cockpit's CI had been reporting success without running a single test. 43 of its 44 test commands begin with `.venv/bin/`; its workflow installs into the runner's system Python and never creates a `.venv`, so every one exited 127 and the old runner counted them as an environment gap and exited 0. The job finished in 21–33 seconds. Its snapshot now declares `ci.suite_command`, so CI runs the suite once and a test CI cannot run fails the build.

**Only `--write` was lost.** ADR-0038 kept it inert because every invocation of the day passed it; on 2026-09-20 no executable caller in the fleet did. The cockpit's guard now asserts it is refused, so the decision is a test rather than a comment.

**The guard survived intact and went upstream.** Every assertion in `tests/test_runner_writes_nothing.py` already held for the template's runner. Its one unique check — the script carries no `fm_set` and no `write_text` — is now in the template's `test-verdict-model.sh`, so all thirteen repos have it. 32 assertions, up from 31.

Also filed on the way: project-os-cockpit ISS-0314, a `done` feature carrying four unticked acceptance boxes.

