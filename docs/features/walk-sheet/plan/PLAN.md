---
type: "[[plan]]"
title: "Delivery plan — the walk sheet, six tasks in the template and two repos downstream"
status: done
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[FEAT-0029-The-Walk-Sheet]]"]
implements: ["[[FEAT-0029-The-Walk-Sheet]]"]
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[PHASE-0004-The-Walk]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — the walk sheet

## Where the work lands

**Every file this feature changes is in `~/Dev/repos/project-os`, the template repo.** This repo holds the record and receives its own vendored copies at the next sync, per `CLAUDE.md`. Two other repos then do their part: project-os-cockpit renders the sheet (its FEAT-0149) and your-trainer consumes it first (its FEAT-0119). Neither is a task here; TASK-0115 hands over to them.

## Delivery sequence

1. **[[TASK-0110-ADR-0027s-Four-Headings-Land-In-The-Test-Template|TASK-0110]] — the headings a row prints.** ADR-0027's Setup, Steps, Expect and Not this check go into the test template, TESTING.md and the test-authoring skill. First, because rule 5 of ADR-0029 reads them, and a generator written before they exist would invent its own.
2. **[[TASK-0111-TESTING-md-States-The-Walk-Once|TASK-0111]] — the normative text.** TESTING.md gains "The walk", the eight rules stated once. SCHEMAS.md and the test template gain `after:`. Everything after this links here.
3. **[[TASK-0112-The-WALK-md-Template|TASK-0112]] — the walk order's syntax.** `docs/__templates__/walk.md`. Before the generator, because the generator parses this and nothing else.
4. **[[TASK-0113-The-Generator-And-Its-Fixture-Test|TASK-0113]] — `walk-sheet.py` and `test-walk-sheet.sh`.** The fixture test is the feature's acceptance check.
5. **[[TASK-0114-The-Skills-And-Note-Templates-Hand-Over-The-Sheet|TASK-0114]] — the skills.** release-prep generates the sheet, release-verification walks it, close-out records the invalidations and offers the reopened section. Can run in parallel with 4 once 2 exists.
6. **[[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit|TASK-0115]] — sync and hand over.** Last, because it carries what the others produced.

## Dependencies

**Hard:**

- TASK-0110 blocks TASK-0113: the generator prints headings that must already be named.
- TASK-0111 blocks TASK-0112, TASK-0113 and TASK-0114: a template comment, a script docstring and a skill step each need one section to link to.
- TASK-0112 blocks TASK-0113: the parser needs a fixed syntax.
- TASK-0113 and TASK-0114 block TASK-0115.

**Soft:**

- TASK-0113 and TASK-0114 are independent of each other.
- ADR-0029 should be accepted before TASK-0113 lands, so the generator implements a decision rather than a proposal. TASK-0110 to TASK-0112 can proceed under the proposal, since each is also implied by ADR-0027 or is a template file that costs nothing to revise.

**Coordination, outside this repo's control:**

- project-os-cockpit carries a deliberately diverged validator superset and its own `ledger.py` with the `owed()` predicate. TASK-0113's generator must compute the same owed set; the fixture test should include a ledger the cockpit's tests already use, so the two cannot drift silently. The bundling decision is the cockpit's (ADR-0029 acceptance box 4).
- your-trainer's `tools/scripts/validate-docs.py` diverged at the 2026-09-03 rollout and needs a hand-merge at sync. TASK-0115 must not overwrite it.

## Open questions

- **Bundle or import.** ADR-0029 rule 7 says the cockpit bundles the generator the way it bundles the validator. The alternative is the generator importing the cockpit's `ledger.py`, which inverts the dependency and ties the template to the cockpit's tree. The cockpit decides and records it on FEAT-0149.
- **Is a committed generated sheet allowed.** Rule 1 permits it as a record. If the owner prefers it never enters git, `--out` defaults to a path under `.gitignore`. Decide at TASK-0113.
- **The enforcement date for "Setup: not stated".** The sheet prints the label from day one. Whether the validator also warns, and from when, is ADR-0027's acceptance box 2, not this feature's.
- **What "surface" means in a repo without `SUR-*` notes.** The survey groups by `area:` string in that case. TASK-0113 states this in the script's help text.
