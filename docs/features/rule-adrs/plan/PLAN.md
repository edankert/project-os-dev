---
type: "[[plan]]"
title: "Delivery plan — rule-ADRs in the template, and the pilot that does not wait for them"
status: draft
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[FEAT-0023]]"]
implements: ["[[FEAT-0023]]"]
related: ["[[ADR-0022]]", "[[REQ-0025]]", "[[ADR-0011]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — rule-ADRs

## Where the work lands

**Every file this feature changes is in `~/Dev/repos/project-os`, the template repo.** Nothing in `project-os-dev` changes except this record. That split is the standing arrangement (`CLAUDE.md`: *"changes planned here are implemented there"*), and it matters more than usual here because three of the four tasks edit template-owned files that `tools/scripts/sync-project-os.sh` then carries to eleven downstream repos.

## Delivery sequence

1. **[[TASK-0086]] — `tools/instructions/DECISIONS.md`.** The normative specification: the three sections and their semantics, the second-issue harvest trigger, the from-principle exception, the warning-first landing pattern. Everything downstream links to this file and restates none of it.
2. **[[TASK-0087]] — the template and the schema.** `docs/__templates__/adr.md` gains an optional commented block; `docs/__templates__/SCHEMAS.md` gains one sentence pointing at DECISIONS.md. Small, and deliberately after the specification exists so the comment can cite it.
3. **[[TASK-0088]] — the two skills.** `adr-authoring` learns to author a rule-ADR; `issue-intake` learns to harvest one. Independent of (2) and can run in parallel with it.
4. **[[TASK-0089]] — `DECISION-RULE`.** The check, its fixture, the severity decision, and the bundled copy under `tools/cockpit/`. Last, because it enforces a specification that has to exist first.

## Dependencies

**Hard:**

- TASK-0086 blocks TASK-0087, TASK-0088 and TASK-0089. A template comment, a skill step and a check all need something to point at, and pointing at four descriptions instead of one file is how ISS-0006 happened.

**Soft:**

- TASK-0087 and TASK-0088 are independent of each other.
- TASK-0089's severity decision wants the pilot's rule-ADRs to exist first, so the violation count at landing is a real number rather than a projection.

**Coordination, outside this repo's control:**

- `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` in `project-os` was **dirty with unrelated parallel work** at 2026-08-12. TASK-0089 must merge into whatever that work became, not overwrite it. Check `git status` in the template repo before touching it.
- `project-os-cockpit` carries a **deliberately diverged validator superset**: 44 distinct check codes against the template's 40 on 2026-08-12, including `PARENT-BACKLINK`, `DESIGN-GATE`, `ACCEPT-STALE` and `SNAPSHOT-MEMBERSHIP`. `DECISION-RULE` needs a recorded hand-merge there. **Nothing is filed in that repo yet** — deliberately, since the check does not exist. File it there when TASK-0089 lands, not before.
- `project-os-dev`'s own validator is **one sync behind** — 39 codes, missing `DECISION-OPTIONS`. Rule-ADRs authored here are therefore unchecked in this repo until it syncs, which is a reason to keep the pilot elsewhere and not a blocker for anything.

## The pilot, which starts before any of this

**`your-health`'s stat rules.** A phase is being created there on 2026-08-12 with two harvested rule-ADRs — *absence-is-never-zero* and *day-attribution* — drawn from the issue families the survey found.

**The pilot proceeds immediately, on the bare convention.** `## Rule`, `## Domain` and `## Conformance` are plain markdown headings; nothing has to ship for a project to write them, and the two rules are harvested from real issue families rather than invented, so they have the scars ADR-0023 asks a rule to carry. `DECISION-RULE` follows and finds them already conformant, or finds them not — either is a useful result, and the second is more useful.

That ordering is deliberate and worth stating, because it inverts the usual one: **the convention is validated by use before it is validated by code.** If two real rules cannot be written in this shape, the shape is wrong and the check should never be built.

## Open questions

- **What is the counted violation set at landing?** Number of notes across the fleet carrying `## Rule` without both other sections. Zero means `DECISION-RULE` is an error on day one under ADR-0021's precedent; non-zero means a `PROMOTIONS` entry no more than 90 days out, with ADR-0011 clause 3 forbidding promotion until the debt clears. TASK-0089 takes the count; nobody should guess it now.
- **How is a Conformance entry parsed?** `TST-*` IDs are resolvable and the requirement says a dangling one is reported. A validator check code, a type name, or a prose sentence is not resolvable and must not be treated as a dangling link. TASK-0089 has to draw that line explicitly rather than let a regex draw it.
- **Do the four `your-health` families reproduce under a stated method?** The survey's classification (~41% of 85 requirements and ~44% of 82 issues naming one metric; ≥15 issues in four families) is the motivating cost and the one figure in [[ADR-0023]] not independently re-derived. The corpus sizes were re-counted on 2026-08-12 and are exact. The pilot should restate the family counts with a reproducible method or drop them — FEAT-0022's independent review flagged exactly this failure mode ("reproduce under no stated method"), and a founding ADR is a bad place for it.
- **Does a rule-ADR want its own `## Options`?** [[ADR-0021]] requires two readable options only when the decision *offers a choice*. Many rules genuinely have alternatives (the rejected threshold, the rejected default); some are a plain yes/no. TASK-0086 should say whether rule-ADRs are expected to carry options, or inherit the existing "available, not required" rule unchanged.
