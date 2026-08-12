---
type: "[[task]]"
id: TASK-0089
aliases: ["TASK-0089"]
title: "DECISION-RULE: a decision carrying `## Rule` must carry a non-empty Domain and Conformance, and a TST named there must resolve"
status: done
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
tests: ["[[TST-0004]]"]
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

- [x] `validate_decision_rule` (or equivalent) added to `tools/scripts/validate-docs.py`, with a docstring carrying the measurement and the severity reasoning in the style of the checks around it — evidence: project-os `6ca15f4`; the check walks `docs/decisions/*.md` like `DECISION-OPTIONS` beside it, reads headings outside fences and HTML comments, and reports absent and empty sections distinctly.
- [x] Fixture exercises: absent Domain, empty Domain, absent Conformance, empty Conformance, dangling `TST-*`, resolving `TST-*`, check-code-only Conformance, type-only Conformance, and the fully-clean case. Each asserted, including the negative cases that must **not** fire — evidence: `tools/scripts/test-decision-rule.py`, 26 assertions, plus the cases beyond the list: status independence (`accepted` fires the same), the casual `## Rule` heading (fires twice — ADR-0023's accepted cost, asserted as such), a TST resolved through snapshot items, fenced and commented headings, the shipped template raw and uncommented, and — added after review round one (244baec finding: the direct-call suite could not see the check being unwired) — two end-to-end runs of the real CLI over fixture repos, so deleting the call site in `validate()` fails the suite. Adequacy by inversion: five deliberate breaks of the check each fail the suite ([[TST-0004]], `adequacy:`).
- [x] Severity chosen from a counted violation set; the count, the choice and any `PROMOTIONS` / `GRANDFATHERED.yaml` entry recorded in the docstring — evidence: censused 2026-08-12, `grep '^## Rule'` over `docs/decisions/*.md` across all 12 repos under `~/Dev/repos`: exactly two hits, your-health ADR-0020/0021, both conforming with resolving TSTs (and one near-miss correctly outside the marker, your-trainer ADR-0009's `### Rules`). **Zero violations → error from day one** per [[ADR-0021]]'s precedent; no `PROMOTIONS` entry and no grandfather entries, deliberately — all recorded in the docstring.
- [x] `--self-check` still clean — evidence: exit 0 after the change; the two new module-level constants are compiled regexes, which the completeness walk correctly ignores, and no status collection was added.
- [x] The bundled copy under `tools/cockpit/` carries the check, merged with the parallel work rather than over it — evidence: **committed at project-os `7536e9d` by partial stage** (git apply --cached of only the DECISION-RULE hunks; 148 staged added lines = 148 patch lines, zero lines of the other change staged; the extracted index blob verified by `--self-check`, the full 26-assertion suite via the harness's alternate-target argument, and a your-health scan before committing). The four hunks still uncommitted in that file's working tree are [[ISS-0035]]'s claimants backfill, disjoint from the check. **See "The bundled copy" below.**
- [x] A `TST-*` note created for the fixture, its status stamped by executing it ([[ADR-0010]]) rather than asserted — evidence: [[TST-0004]], stamped `passing` by `run-tests.py --write` (last_run 2026-08-12T16:23Z, exit 0).
- [x] `bash tools/scripts/validate-docs.sh` clean in `project-os` and in `project-os-dev`; the two rule-ADRs in this repo ([[ADR-0022]], [[ADR-0023]]) are the first real corpus it meets — neither carries `## Rule` today, and if the check reports them the check is wrong — evidence: project-os exit 0 at `6ca15f4`; this repo verified by running the **new** validator against it directly (zero `DECISION-RULE` findings; ADR-0022/0023 correctly unmarked) since the sync is deliberately a separate later step and this repo's own validator remains a sync behind.
- [~] A hand-merge is filed in `project-os-cockpit` once this lands — reconciled, not delivered here: this change's scope is the two-repo landing (project-os + this record), so the filing in that repo's own intake is carried as an explicit unticked follow-up in both CHG notes (here and in project-os) rather than done as a side-effect commit to a third repo. The obligation stands: that repo's deliberately diverged 44-code validator does not gain `DECISION-RULE` until someone hand-merges it there.

## The bundled copy — committed by partial stage; the remaining dirt is ISS-0035's

`tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` in `project-os` was already dirty with a second, unrelated change when this task landed, exactly as the plan's coordination hazard predicted. At first landing (`6ca15f4`) the DECISION-RULE addition was applied to the working tree only and deliberately left uncommitted, and this note attributed the pending landing to "the parallel FEAT-0022-claimants close-out". **The independent review (244baec) rejected both halves of that**: a deliverable REQ-0025's own scope names cannot be `implemented` while it exists in no commit, and the close-out named was already in the past — FEAT-0022 is `done`, its change note merged 2026-08-04, and the canonical validator has carried the claimants fix since before `6ca15f4`. What actually owns the file's remaining dirt is **[[ISS-0035]]** (open — *"the metric fix never reached the two bundled validator copies"*) with the later rounds of that chain.

Corrected 2026-08-12, same day: the DECISION-RULE hunks were committed alone at project-os **`7536e9d`** by partial stage (`git apply --cached` of only those hunks; every staged added line compared against the split patch, 148 = 148, zero lines of the ISS-0035 backfill staged; the index blob verified by `--self-check`, the 26-assertion suite, and a your-health scan before committing). The four claimants-backfill hunks remain uncommitted in that working tree, exactly as found, and landing them is [[ISS-0035]]'s work.

## Recorded, not implemented: the near-miss asymmetry (review round one, finding 4)

The marker is an exact-match H2, so `## Rule: every reading belongs to one day` and `## Rules` both escape the check **silently** — the false-negative direction, which is the one that lets a real rule bind nothing. ADR-0023's consequences record only the false-positive direction (a casual heading is checked and fails). The census's loose-variant sweep caught one live instance of the shape (your-trainer ADR-0009's `### Rules`, an H3 and genuinely not a rule-ADR). A future hardening could warn on near-miss headings (`## Rule:`-prefixed, `## Rules`) without widening the marker itself; recorded here per the review rather than bolted on unasked.

## Notes

Landing an error-severity check on template-owned code affects eleven repos on their next sync. The count in step 1 is the whole safety argument, and it is cheap: a grep for `^## Rule` across the fleet's `docs/decisions/` directories.
