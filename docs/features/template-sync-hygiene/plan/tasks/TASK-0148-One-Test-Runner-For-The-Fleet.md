---
type: "[[task]]"
id: TASK-0148
aliases: ["TASK-0148"]
title: "One test runner for the fleet, and the cockpit's CI starts running tests"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["[[ISS-0075-Two-Test-Runners-Are-Maintained-Against-Two-Decisions]]", "Edwin, 2026-09-20: 'Fix ISS-0074 and ISS-0075 fully!'"]
parent: "[[ISS-0075-Two-Test-Runners-Are-Maintained-Against-Two-Decisions]]"
effort: "Medium"
due: ""
depends: []
blocks: []
related: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[TASK-0147-The-Scaffold-Offers-The-Gates-The-Validator-Runs]]"]
tests: ["[[TST-0008]]"]
---

# One test runner for the fleet, and the cockpit's CI starts running tests

## What the issue got wrong, and what was actually true

[[ISS-0075-Two-Test-Runners-Are-Maintained-Against-Two-Decisions|ISS-0075]] said to "expect to supersede one ADR rather than merge two scripts, because the scripts differ because the decisions do". **That was wrong, and the opposite is true.**

The two decisions are the same decision. [[ADR-0025-An-Executable-Test-Records-No-Verdict|ADR-0025]] is the fleet-wide adoption of the cockpit's ADR-0038: it lists "project-os-cockpit ADR-0038" in its own `source:`, its Context says ADR-0038 "went one step further", and its chosen option is titled "No verdict on the note. Follow ADR-0038". `STATUSES.md` already states the merged rule with both citations. **No ADR is superseded.** One implementation is deleted.

The scripts diverged because the template kept being fixed after the cockpit forked, and the cockpit took only one of those fixes — and broke it in transit.

## What the cockpit was missing

| Template gained | Cockpit had it? |
|---|---|
| An unrunnable command fails the run in CI | No |
| `PROJECT_OS_ALLOW_UNRUNNABLE=1` to accept the gap deliberately | No |
| A repeated command runs once and shares its outcome | No |
| A failing command prints its last 40 lines, not one | No |
| `--ci` runs the declared suite | Copied, **crashes** |

The crash is real and verified: the cockpit's `main` unpacks four values at line 175 from a `run_one` that returns three-tuples everywhere. It is latent only because the cockpit declares no `ci:` block. Declaring one before swapping the runner would have crashed it — which is why the swap and the declaration land in one commit.

## The finding that matters more than the reconciliation

**The cockpit's CI has been reporting success without running a single test.** 43 of its 44 test commands begin with `.venv/bin/`; its workflow installs with `pip install -e ".[dev]"` and never creates a `.venv`. Every one of those commands exits 127 on a runner. The cockpit's runner called that *unrunnable*, printed "an environment gap, not a failure", and exited 0.

Verified here rather than taken on trust: 43 of 44 commands matched `.venv/bin`, and the workflow has no venv step.

The template's runner treats an unrunnable test in CI as a failure, which is ADR-0025's whole point — a test CI cannot execute has no verdict, and a green build that ran nothing is a lie.

## Definition of Done

- [x] The template's `test-verdict-model.sh` runs its runner checks in every repo: the `keep_local` skip branch that exempted exactly one repo is deleted.
- [x] The one guard the cockpit had that the template lacked is ported upstream: the runner carries no `fm_set` and no `write_text`. Structural, because a dead writer is one edit away from writing again.
- [x] The cockpit takes the template's runner.
- [x] Its `tests/test_runner_writes_nothing.py` passes against it.
- [ ] Its `SNAPSHOT.yaml` declares `ci.suite_command`, so CI runs the suite once instead of 44 commands it cannot run.
- [x] Its `keep_local:` list is empty; it keeps nothing back from the template.
- [x] `REQ-0058`'s two `--write` lines are corrected, and a `CHG-*` records the CI finding.
- [ ] The template's harness is synced to the fleet.

## Verification

`bash tools/scripts/test-verdict-model.sh`: **32 assertions, 0 failures** (31 before). The new structural assertion fails when `fm_set` is added back to the runner — checked.

`.venv/bin/pytest tests/test_runner_writes_nothing.py -q` in the cockpit, against the template's runner: **6 passed**. Every assertion it made already held for the template's runner except `--write`, which is now asserted to be refused rather than accepted.

## What was lost

`--write` as an accepted no-op. ADR-0038 kept it because "every existing invocation passes it"; on 2026-09-20 no executable caller in the fleet passed it — every grep hit is past-tense prose — and the template's runner had refused it since 2026-09-03. The cockpit's guard now asserts the refusal, so the decision is recorded as a test rather than as a comment.
