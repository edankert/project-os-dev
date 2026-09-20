---
type: "[[task]]"
id: TASK-0147
aliases: ["TASK-0147"]
title: "The feature scaffold offers the gates the validator runs"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["[[ISS-0074-The-Feature-Template-Lacks-The-Acceptance-And-Design-Fields-The-Cockpit-Uses]]", "Edwin, 2026-09-20: 'Fix ISS-0074 and ISS-0075 fully!'"]
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[TASK-0146-The-Four-Findings-Round-One-Left]]"]
tests: ["[[TST-0018]]"]
---

# The feature scaffold offers the gates the validator runs

## Problem

The validator has warned on a feature's `acceptance:` (FEAT-0064 ACCEPT-STALE) and `design:` (FEAT-0070 DESIGN-GATE) for months, and `docs/__templates__/feature.md` offered neither field. Anyone scaffolding a feature the normal way never learned the gates existed. The one repo whose features could opt in was `project-os-cockpit`, which had edited its own copy and carried it as a `keep_local:` sync exception ever since.

## Definition of Done

- [x] `feature.md` carries `acceptance:` and `design:`, optional and empty, with comments saying what writes each and that the design gate warns rather than blocks.
- [x] A test asserts the scaffold offers every field the validator's feature gates read, and that the gates it advertises are gates the validator runs.
- [x] The same test refuses a scaffold that declares a frontmatter key twice.
- [x] `project-os-cockpit` drops its `keep_local:` line and takes the template's copy.
- [x] All thirteen repos carry both, each with the test run there.

## What the issue got wrong

[[ISS-0074-The-Feature-Template-Lacks-The-Acceptance-And-Design-Fields-The-Cockpit-Uses|ISS-0074]] said the template had no `reviewed_by:` or `review_date:` either. It has had all four review fields for some time. Reading the two files side by side before changing anything showed that, and turned up the defect the issue had missed.

**The cockpit's copy declared the four review fields twice.** `reviewed_by`, `review_date`, `review_verdict` and `review_round` each appear in two consecutive blocks. YAML keeps one value and drops the other, so an edit to the first block was silently lost. Nothing reported it, in either repo. Taking the template's copy removes the duplication, and the new duplicate-key assertion stops it recurring in any scaffold.

## Verification

`bash tools/scripts/test-note-templates.sh`: **9 assertions, 0 failures**, run in all thirteen repos.

Both ways, as the rule requires:

- Restoring the previous `feature.md`: **4 failures** — the two gate fields and the two comments that explain them.
- Putting the cockpit's copy in its place: **1 failure**, the duplicate-key assertion.
- Restored: 0 failures.

## Where it landed

Template `1f6dff4`; then `feature.md` and the new harness to twelve repos, with `project-os-cockpit` `381faea` also dropping the `keep_local:` line in the same commit. `fleet-file-drift.py` afterwards: the cockpit no longer reports `feature.md` as kept.

The new harness is wired to [[TST-0018]] here, so `run-tests.py` runs it rather than leaving it to be invoked by hand — the gap [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]] describes.
