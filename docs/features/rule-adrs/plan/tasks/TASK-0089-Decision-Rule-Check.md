---
type: "[[task]]"
id: TASK-0089
aliases: ["TASK-0089"]
title: "DECISION-RULE: a decision carrying `## Rule` must carry a non-empty Domain and Conformance, and a TST named there must resolve"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[REQ-0025]]", "[[ADR-0011]]"]
parent: "[[FEAT-0023]]"
effort: M
due: ""
depends: ["[[TASK-0086]]"]
blocks: []
related: ["[[ADR-0021]]", "[[ADR-0011]]", "[[ADR-0010]]"]
tests: []
---

# The check

## What

A new check in `~/Dev/repos/project-os/tools/scripts/validate-docs.py`, code **`DECISION-RULE`** — named for consistency with `DECISION-OPTIONS`, which it sits beside and shares a corpus with.

Any note under `docs/decisions/` containing a `## Rule` heading **must** carry a non-empty `## Domain` and a non-empty `## Conformance`. `TST-*` IDs named under Conformance must resolve to notes in the repo.

**It fires regardless of the note's status.** A `proposed` rule binds nothing yet, but it is malformed in exactly the same way, and a check that waits for `accepted` would let every rule enter the corpus unexamined and fire only at the moment someone is trying to take a decision.

## Why this check is the point of the whole feature

[[ADR-0022]]'s discharge clause: a convention standing in for a type must name what checks it, or it is a preference. `QUALITY.md` states the theory in one line — *"Convention-only rules get silently skipped under context pressure; the validator does not"* — and a rule-ADR without a Domain is not a mildly untidy note. It is a rule that binds nothing, wearing the clothes of one that does.

## The severity decision this task must take

**Do not inherit a severity; measure and choose.**

[[ADR-0011]]: every rule is an error or is deleted; `warn` survives only as a dated migration state, encoded in `PROMOTIONS`, no more than 90 days out — and **clause 3 forbids promoting over debt**. [[ADR-0021]] applied it to a brand-new convention and reached the opposite answer from the usual one: *"a brand-new convention has nothing to migrate: no repo has an `## Options` section written against it, so there is no debt, and a warning would be the permanent tier that ADR forbids."*

Which applies here depends on a number that does not exist yet:

1. **Count**, across the fleet at landing, the notes under `docs/decisions/` carrying a `## Rule` heading without both other sections. The pilot (`your-health`) is creating rule-ADRs this week, so take the count at landing rather than projecting it now.
2. **Zero → error on day one.** ADR-0021's precedent, directly.
3. **Non-zero → `PROMOTIONS["DECISION-RULE"]`**, no more than 90 days out (on or before **2026-11-10** for a 2026-08-12 landing), with the violating notes either fixed before promotion or listed in `tools/GRANDFATHERED.yaml` with reasons.
4. **Record the count and the choice in the check's docstring**, as every other check in this file does. The docstring is where this codebase keeps its reasoning, and a severity with no recorded measurement is the thing ADR-0011 exists to prevent.

## The parsing line to draw explicitly

`## Conformance` may name three different things and only one is resolvable:

- **`TST-*` IDs** — resolvable, and a dangling one is reported ([[REQ-0025]]).
- **A validator check code** (`DECISION-RULE`, `REQ-BOXES`) — prose. Must not be treated as a dangling link.
- **A type, or a sentence** ("the enum makes it unrepresentable") — prose.

Draw the line in code deliberately rather than letting a regex draw it. `extract_ids` reads all three frontmatter shapes and would happily pull an ID out of a sentence; the check needs to resolve only what it means to resolve, and the docstring should say which.

**Do not require a `TST-*`.** A type that makes a violation unrepresentable is the *strongest* conformance in [[ADR-0023]]'s list, and a check that demanded a test note would push authors toward the weaker discharge — the inversion [[ADR-0010]] warns about, where the instrument that is easy to satisfy displaces the one that is true.

## The bundled copy, and the repo that diverged

- **`tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` must get the check too.** As of 2026-08-12 that file is **dirty in `project-os`'s working tree with unrelated parallel work** — merge into whatever it has become, do not overwrite. Check `git status` there first.
- **`project-os-cockpit` holds a deliberately diverged superset** — 44 distinct check codes against the template's 40 on 2026-08-12 (`PARENT-BACKLINK`, `DESIGN-GATE`, `ACCEPT-STALE`, `SNAPSHOT-MEMBERSHIP` exist only there). `DECISION-RULE` needs a **recorded hand-merge** in that repo, filed there when this lands. Nothing is filed there now, deliberately.

## Definition of Done

- [ ] `validate_decision_rule` (or equivalent) added to `tools/scripts/validate-docs.py`, with a docstring carrying the measurement and the severity reasoning in the style of the checks around it.
- [ ] Fixture exercises: absent Domain, empty Domain, absent Conformance, empty Conformance, dangling `TST-*`, resolving `TST-*`, check-code-only Conformance, type-only Conformance, and the fully-clean case. Each asserted, including the negative cases that must **not** fire.
- [ ] Severity chosen from a counted violation set; the count, the choice and any `PROMOTIONS` / `GRANDFATHERED.yaml` entry recorded in the docstring.
- [ ] `--self-check` still clean — the new code registers no unregistered status table.
- [ ] The bundled copy under `tools/cockpit/` carries the check, merged with the parallel work rather than over it.
- [ ] A `TST-*` note created for the fixture, its status stamped by executing it ([[ADR-0010]]) rather than asserted.
- [ ] `bash tools/scripts/validate-docs.sh` clean in `project-os` and in `project-os-dev` after sync; the two rule-ADRs in this repo ([[ADR-0022]], [[ADR-0023]]) are the first real corpus it meets — neither carries `## Rule` today, and if the check reports them the check is wrong.
- [ ] A hand-merge is filed in `project-os-cockpit` once this lands.

## Notes

Landing an error-severity check on template-owned code affects eleven repos on their next sync. The count in step 1 is the whole safety argument, and it is cheap: a grep for `^## Rule` across the fleet's `docs/decisions/` directories.
