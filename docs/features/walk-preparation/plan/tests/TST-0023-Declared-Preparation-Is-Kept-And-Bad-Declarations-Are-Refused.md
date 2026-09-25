---
type: "[[test]]"
id: TST-0023
aliases: ["TST-0023"]
title: "Declared preparation is kept in the walk, and a declaration that is broken or contradicts another is refused"
status: active
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
scope: feature
level: unit
entrypoint: "../project-os/tools/scripts/test-walk-preparation.py"
command: "python3 -B ../project-os/tools/scripts/test-walk-preparation.py"
features: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
requirements: ["[[REQ-0031-Preparation-Is-Declared-And-Validated]]"]
tasks: ["[[TASK-0125]]"]
artifacts: []
evidence: []
adequacy: "2026-09-24, template working tree, 16 tests. Eight mutations of walk-sheet.py, each confirmed to have landed and restored from a scratchpad copy: M1 prerequisites not followed, 4 failures; M2 every setup item printed, 0 failures at first, so test_setup_for_an_omitted_step_is_left_out was added and then failed; M3 state not carried forward, 1; M4 cycle not reported, 1; M5 duplicate declarations not reported, 1; M6 never-applicable setup not reported, 1; M7 unknown platforms not reported, 1; M8 platform-limited steps kept on the other platform, 1. Pristine 16 of 16 after each. Round 2, after the FEAT-0033 review found three guards no test held: N1 closure stopped after one hop, 1 failure (test_prerequisites_are_followed_through_a_chain); N2 a later step allowed as a prerequisite, 1 (test_a_later_step_cannot_be_a_prerequisite); N6 frontmatter split on any ---, 1 (test_frontmatter_ends_at_its_own_delimiter). The --check readiness guards are held by test-walk-sheet.sh (N3 3 failures, N4 1, N5 1). Pristine 19 of 19 and 160 of 160. Round 3, after the round-two review: N7 the numbering remark counting every step, in a full copy of the template, 1 failure (test_the_numbering_remark_counts_only_this_platforms_steps). Pristine 20 of 20."
related: ["[[TST-0011]]"]
---

# Declared preparation is kept in the walk, and a declaration that is broken or contradicts another is refused

## Purpose

`test-walk-preparation.py` is the fixture suite for rule 9's declared preparation (TESTING.md, "The walk"). It builds one procedure with prerequisites, scoped setup, platform steps, state, captures, a timer and readiness, and checks what the sheet keeps. It ran in the template's CI from 2026-09-18, but no note here carried its command, so `run-tests.py` never ran it in this repo.

## Procedure

`python3 -B -m unittest tools/scripts/test-walk-preparation.py` in `~/Dev/repos/project-os`. Cross-repo, like [[TST-0011]].

1. Transitive prerequisites are kept in authored order and marked as preparation, with no verdict.
2. Only setup that a kept step needs is printed, including when the left-out step runs on the same platform.
3. A `state_for` reminder carries forward across omitted steps and respects platform.
4. Captures, timers, platform action wording and unscripted readiness appear only where they apply.
5. Refused, with the sitting falling back to its per-check rows: absent, future or cyclic prerequisites; prerequisites unavailable on the platform; malformed tags beside valid ones; one step or setup id declared twice in a map; a setup, readiness or action declaration that can never apply on its step's platforms; a platform name the repo keeps no ledger for.
6. A changed child screen prints under its unchanged parent in the survey.

## Expected results

- Exit 0: 20 of 20, 2026-09-24, after both review rounds.
- Exit 1: the unittest failure report.
