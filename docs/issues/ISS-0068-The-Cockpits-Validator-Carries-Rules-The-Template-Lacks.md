---
type: "[[issue]]"
id: ISS-0068
aliases: ["ISS-0068"]
title: "The cockpit's validator carries rules the rest of the fleet never gets"
status: triage
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[TASK-0136-The-Cockpits-Validator-Checks-Reach-The-Template]]"]
reported_by: agent
question: ""
severity: medium
component: "validator"
parent: "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"
related: ["[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"]
tests: []
---

# The cockpit's validator carries rules the rest of the fleet never gets

## Problem

project-os-cockpit checks things no other repo checks, because those rules were written into its own copy of `validate-docs.py` and never reached the template. They include:
- surface-orphan warnings;
- TEST-AUTOMATED-STATUS, which says an automated test holds no verdict;
- REVIEW-STALE, for an owed verdict that was never answered;
- the release-preparing checks.

The cockpit also keeps a bundled copy in `src/` that its tests hold byte-identical. So it cannot take the template's validator: on 2026-09-18, 41 of its tests failed when it did. Its copy is now listed under `keep_local:` in its `.project-os-sync`.

## Why this is filed rather than fixed

It is too large for the session that found it. TASK-0136 moved the four checks that were whole functions: the three ledger checks and the frontmatter-parse check. The rest sit inside functions the two copies share, and each needs to be ported with its test and a measurement of what it finds across the fleet.

## Next Actions

- [ ] List the cockpit-only rules, by diffing the two copies function by function.
- [ ] Port each rule with its cockpit test turned into a template fixture. Run each over the fleet, and give it a promotion date where there is debt.
- [ ] Then the cockpit takes the template's validator, and the `keep_local:` line goes.
