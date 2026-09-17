---
type: "[[feature]]"
id: FEAT-0033
aliases: ["FEAT-0033"]
title: "A release walk keeps the actions needed to reach each owed observation"
status: doing
phase: ""
owner: user:edwin
created: 2026-09-16
updated: 2026-09-17
source: ["Your Trainer FEAT-0122, 2026-09-16: implement and test the guided walk fully"]
goal: "A procedure can name required preparation, relevant setup and platform instructions, and the generator retains them without changing the owed check set."
requirements: ["[[REQ-0031-Preparation-Is-Declared-And-Validated]]"]
tasks: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
related: ["[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]"]
---

# A release walk keeps the actions needed to reach each owed observation

## Goal

The shared walk generator must give a rider the actions needed to reach every owed observation. A prerequisite action remains in the sequence even when the check originally attached to it already passed. It carries no new verdict.

The validator must also reject malformed backticked check tags. A valid tag beside an invalid one must not make the procedure appear complete while an observation is ignored. A rejected procedure keeps the per-check fallback visible.

An authored state reminder must continue until another declaration changes it. This lets a later retained step name the tier, ride or equipment state to restore after an interruption, without guessing from omitted actions.

An unscripted check can also name a platform-specific preparation or scope decision in its own frontmatter. The generator prints the reason on that platform's fallback row without dropping the owed check or inferring a reason from prose.

## Scope

- Add authored links from a procedure step to the earlier steps needed to perform it.
- Attach setup entries to the steps that need them, with platform variants and state transitions declared at the source.
- Validate missing or cyclic prerequisites, contradictory state and invalid platform coverage.
- Keep the owed set unchanged while the sheet and cockpit receive the same prepared sequence.
- Fix child-screen placement when only a child is named by a change note.

The generator does not infer an order from prose. Existing procedures without new fields keep their current valid behavior until their authors annotate them.

## Acceptance

- [ ] A later owed FREE-rides step retains its authored workout start and finish prerequisites when those earlier checks are settled.
- [ ] The final language sweep shows no AI key, translation fixture, email account or hosted redirect setup solely used by omitted steps.
- [ ] The validator reports missing and cyclic prerequisites without silently dropping an owed observation.
- [ ] A preparation action has no owed verdict tags and the sheet and cockpit agree on the resulting owed set.
- [ ] A changed child screen is displayed under its actual parent even when the parent has no change note.
- [x] A fallback check's declared readiness appears only on its named platform, and malformed declarations fail validation.

## Current browser finding

The shared generator now corrects the action heading seen in a Chrome render of Your Trainer's walk. A known `SUR-*` id shows its screen title while retaining the id for linking. An unknown id stays visible.

The shared generator now accepts `walk_readiness_for` on unscripted acceptance checks. It validates platform entries and prints the matching reason before fallback instructions. A malformed declaration prints a decision warning instead of a ready row. Twelve focused preparation tests and the shared sheet test pass; the generator is synced to Your Trainer and both cockpit copies. [[CHG-20260917-Declare-readiness-for-unscripted-walk-checks]] records the change. The broader readiness and corpus audits remain open.
