---
type: "[[issue]]"
id: ISS-0068
aliases: ["ISS-0068"]
title: "The cockpit's validator carries rules the rest of the fleet never gets"
status: fixed
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

- [x] List the cockpit-only rules, by diffing the two copies function by function.
- [x] Port each rule with its cockpit test turned into a template fixture. Run each over the fleet, and give it a promotion date where there is debt.
- [x] Then the cockpit takes the template's validator, and the `keep_local:` line goes.

## Plan, 2026-09-18 (Edwin: "Do ISS-0068 now")

A function-by-function diff of the two copies, run before starting:

- **Only in the cockpit, to be ported:** STATUS-VALUE-NOTE (an illegal status on a note the snapshot does not list), CHECK-SUBJECT, SURFACE-ORPHAN, REVIEW-STALE, RELEASE-PREPARING, and VERIFY's check that an automated test's command still names something that exists (`resolve_command` and its helpers).
- **The same rule written twice:** the cockpit's TEST-AUTOMATED-STATUS and TEST-AUTOMATED-EVIDENCE (its ADR-0038) and the template's COMMAND-VERDICT (ADR-0025) both say a test with a `command:` records no verdict. The template's code stays; the cockpit's tests move to it.
- **Newer in the template, kept:** the ledger-settled acceptance gate, the field counts, `deprecated` for reference notes, ACCEPT-LOCATION, BASE-STATUS, DECISION-RULE, RELEASE-FEATURES, and the dated promotion of the ledger checks.

Each ported check is measured across the fleet first, and dated where a repo has debt. Then the cockpit takes the template's validator, its bundled copy stays byte-identical to it, its tests are pointed at the merged behaviour, and the `keep_local:` line for the validator goes. `run-tests.py` stays local: reconciling ADR-0038's runner with ADR-0025's is a separate decision.

## Fixed, 2026-09-18

Every repo now runs the same `validate-docs.py`. project-os-cockpit's copy, its bundled copy and the template's are byte-identical, and its `keep_local:` line for the validator and `test-ledger-checks.sh` is gone.

- **Template 4b5fa83** ports STATUS-VALUE-NOTE, CHECK-SUBJECT, SURFACE-ORPHAN, REVIEW-STALE, RELEASE-PREPARING and the broken-command check (now VERIFY-COMMAND). Measured over the 13 repos first; all but RELEASE-PREPARING warn until 2026-12-17, and no repo gains an error. Counts are in the commit and in the PROMOTIONS comment.
- **project-os-cockpit b546625** takes the file. Its TEST-AUTOMATED-STATUS/EVIDENCE tests now name COMMAND-VERDICT, the same rule under the template's name; every case in their matrix answers as before. Its suite gives the same 10 failures with and without the change (listed in its CHG-20260918 note), and none of the 10 involves the validator.
- **The command search was too slow to port as it was.** It took your-health's validator from 9 s to 197 s, searching `.git`, build output and a Python environment for every command. It now lists the tree once and skips those folders: 12 s. The cockpit's `command_targets.py` skips the same folders.
- **Two template defects found by the cockpit's tests, fixed in 4b5fa83:** the sealed-ledger check used `hashlib` without importing it (latent: no repo vouches for a ledger yet), and an acceptance check with a command at `ready` was reported under two codes.
- Synced to all 12 repos.

**What the new warnings show, for whoever works in those repos:** your-health's TST-0027 and TST-0028 name six test classes that no longer exist, so ISS-0105 to 0107 are verified by nothing; your-trainer has seven change notes at `landed`, a status change notes do not allow; 93 finished notes across seven repos carry `changes-requested` with no `review_response:`.

`run-tests.py` stays local in the cockpit: reconciling its ADR-0038 runner with ADR-0025's is a separate decision.

