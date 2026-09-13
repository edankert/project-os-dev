---
type: "[[task]]"
id: TASK-0112
aliases: ["TASK-0112"]
title: "docs/__templates__/walk.md: the template for a project's authored walk order, in a syntax the generator parses and nothing else"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]] rule 3", "your-trainer docs/tests/ACCEPTANCE_RUN_PLAN.md, the twelve phases and the pre-flight section, 2026-09-12"]
parent: "[[FEAT-0029-The-Walk-Sheet]]"
effort: M
due: ""
depends: ["[[TASK-0111-TESTING-md-States-The-Walk-Once]]"]
blocks: ["[[TASK-0113-The-Generator-And-Its-Fixture-Test]]"]
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]"]
tests: []
---

# The walk order's template and syntax

## What

A project authors its sitting order once, in `docs/tests/acceptance/WALK.md`. This task ships the template for that file and fixes the syntax. The syntax is the whole decision: the generator parses exactly this and the cockpit renders exactly this, so a second way to write a sitting is a defect (ADR-0029 acceptance box 1).

## The syntax, proposed

The file is a note with frontmatter `type: "[[reference]]"`, `status: active`, `title:`, `owner:`, `created:`, `updated:`, so it validates as a standing document and carries no lifecycle beyond active or deprecated (STATUSES.md, `[[reference]]`). Its body is prose the walker reads once, then one fenced `yaml` block per sitting under a `### ` heading. The heading is the sitting's name as the sheet prints it. The block carries:

```yaml
surfaces: ["Riders & profiles", "SUR-0010"]   # area: strings or SUR-* ids; first match wins, in file order
checks: ["TST-0658"]                           # optional: ids pulled in regardless of area
state: "Fresh install, no rider yet. Cheapest: Settings > Developer > Clear data."
bench: ["Tablet with the candidate build", "KICKR on the bench, powered", "HRM strap"]
```

`state` is the product state the sitting needs and the cheapest way to reach it, in ADR-0027's Setup register. `bench` is what must be physically present or signed in. Neither carries a duration. A sitting with no `surfaces` and no `checks` is a validator warning at generate time, because it can claim nothing.

The sheet omits a sitting with nothing owed, and appends a final sitting "Unplaced" for checks no block claims. That sitting is the author's worklist and is never written into WALK.md by hand.

## Definition of Done

- [x] `~/Dev/repos/project-os/docs/__templates__/walk.md` exists with the frontmatter above, a three-line body explaining what the file is for and linking to TESTING.md "The walk", and two example sittings in the syntax above, one of them showing `checks:`.
- [x] `~/Dev/repos/project-os/docs/__templates__/SCHEMAS.md` documents the per-sitting keys (`surfaces`, `checks`, `state`, `bench`) in one short table under a "Walk order (WALK.md)" heading, and says the file is `[[reference]]` typed and lives at `docs/tests/acceptance/WALK.md`.
- [x] `~/Dev/repos/project-os/docs/tests/README.md` (or the acceptance README the template ships) gains one paragraph saying where the walk order lives and that a sitting is claimed by surface.
- [x] The syntax is recorded on ADR-0029's acceptance box 1 as the decision.
- [x] `bash tools/scripts/validate-docs.sh` accepts a repo that has the template instantiated and a repo that has not.

## Steps

- [x] Write the template file. Take the two example sittings from your-trainer's run plan, "Fresh install and first rider" and "Hardware on the bench", rewritten in the syntax, with the minutes removed.
- [x] Add the SCHEMAS.md table and the README paragraph.
- [x] Tick ADR-0029 acceptance box 1 with the path as evidence.
- [x] Validate.

## Notes

- The order in the file is the order on the sheet. your-trainer's twelve phases are a state machine over tier upgrades and device wipes, and that is the ordering knowledge the file exists to keep. Say so in the template's body so an author knows what to write down.
- `surfaces:` matches an `area:` string exactly, or a `SUR-*` id whose note's `title:` is the area string. A repo with no `SUR-*` notes uses strings only.

## Evidence

- `~/Dev/repos/project-os/docs/__templates__/walk.md` exists: `[[reference]]` frontmatter with an optional `gallery:`, a body that says the order is a state machine over the product rather than a priority list, and two sittings in the syntax — "Fresh install and first rider" and "Hardware on the bench", taken from your-trainer's hand-written run plan with the minutes removed. The second shows `checks:`.
- The keys are documented once, in `docs/__templates__/SCHEMAS.md` under "`walk.md` — the walk order (`WALK.md`)": a four-row table, the `[[reference]]` type, the `docs/tests/acceptance/WALK.md` path, and the rule that a block claiming nothing is reported. The template points there instead of repeating the table.
- `docs/tests/README.md` gains "Where the walk order lives": one paragraph saying a sitting claims a check by surface and naming the generator command.
- ADR-0029 acceptance box 1 is ticked with `docs/__templates__/walk.md` as the evidence.
- `bash tools/scripts/validate-docs.sh` is OK in the template, which has no instantiated WALK.md; a repo that has one is covered by the fixture test in TASK-0113.
