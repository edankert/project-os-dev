---
type: "[[test]]"
id: TST-0005
aliases: ["TST-0005"]
title: "One pause rule stated once, and eight stop-points that link it"
status: draft
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]", "[[TASK-0091]]"]
scope: feature
level: acceptance
entrypoint: ""
command: "bash ../project-os/tools/scripts/test-pause-rule.sh"
last_run: ""
requirements: []
features: ["[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"]
issues: []
tasks: ["[[TASK-0090]]", "[[TASK-0091]]"]
artifacts: []
adequacy: ""
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
---

# One pause rule stated once, and eight stop-points that link it

## Purpose

[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]] claims two things a grep can settle: the pause rule is stated in exactly one file, and each stop-point links it instead of restating it. This note executes that check.

**Draft until [[TASK-0091]] writes the harness this note names.** It is not run before then, so it is never recorded as failing.

It is deliberately a text check and not a behaviour check. Whether an agent actually pauses better is a question for the review pass on the first few sessions after the change; what this pins is the property the feature is allowed to claim.

## Procedure

`tools/scripts/test-pause-rule.sh` in `~/Dev/repos/project-os`, written by [[TASK-0091]]. The command is cross-repo for the same reason [[TST-0004]]'s is: every file under test lives in the template, and this repo's copies are a sync behind.

The script asserts:

1. Exactly one file under `tools/` plus `tools/scripts/generate-adapters.py` contains the full pause rule (the anchor sentence [[TASK-0090]] writes into LIFECYCLE.md).
2. Each of the eight stop-point sites contains a link to that anchor: `HOOKS.md`, `status-transition/SKILL.md`, `issue-intake/SKILL.md` (two sites), `feature-scaffold/SKILL.md`, `release-prep/SKILL.md`, `close-out/SKILL.md`, and the planner prompt string in the generator.
3. `.claude/agents/planner.md` matches what the generator would produce, so the regeneration was not forgotten.

## Expected results

- Exit 0 once [[TASK-0090]] and [[TASK-0091]] have landed.
- Exit 1 before then, naming the site that still carries its own phrasing. That is the correct result today.

## Adequacy (who verifies this test?)

The check is inverted by deleting the link from any one stop-point and re-running; assertion 2 must fail and name that file. Record the inversion in this section when the script is written — a grep suite that passes with the links removed is checking nothing.
