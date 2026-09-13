---
type: "[[issue]]"
id: ISS-0065
aliases: ["ISS-0065"]
title: "The template repo ships seven test scripts and its own CI runs none of them, because nothing in its docs/ declares a command:"
status: triage
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["Independent review of FEAT-0029, 2026-09-13, consistency finding"]
severity: medium
component: tooling
related: ["[[FEAT-0029-The-Walk-Sheet]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
tests: []
---

# The template's CI runs none of the template's tests

## Problem

`~/Dev/repos/project-os` ships seven harnesses — `test-decision-rule.py`, `test-hooks.sh`, `test-pause-rule.sh`, `test-retention.py`, `test-verdict-model.sh`, `test-walk-sheet.sh`, `test-word-budgets.sh` — and its own GitHub workflow runs `run-tests.py --ci`, which finds nothing to run. The template's `docs/` holds no `TST-*` note with a `command:`, so a change to any of those scripts is green in the template's CI whatever it does.

They are not unrun: every one of them is the `command:` on a `TST-*` note in **project-os-dev**, written as `bash ../project-os/tools/scripts/<script>.sh`, and that repo's workflow checks the template out beside itself so the commands resolve. That is the arrangement TST-0005 to TST-0009 all follow and it works. The gap is narrower than it looks and still real: a push that breaks a harness goes green in the repo that owns the harness and red in a different repo, which is the wrong place to find out.

## Evidence

- `cd ~/Dev/repos/project-os && python3 tools/scripts/run-tests.py` → `project-os — no TST-* notes declare a command:`.
- `.github/workflows/validate-docs.yml:34-36` runs `run-tests.py --ci` when the script exists.
- `grep -rl "^command:" ~/Dev/repos/project-os/docs` → nothing.

## Next Actions

- [ ] Decide where the template's own harnesses are declared. A `TST-*` note per script in the template's `docs/tests/` would make its CI run them, and would also be seeded into every new project created from the template, which is noise those projects do not want — so the choice is between that noise and a CI step that names the scripts directly.
- [ ] Whichever wins, say it once, so the next person adding a harness knows where its note goes. TASK-0113's Definition of Done guessed wrong about this and had to be reconciled.
