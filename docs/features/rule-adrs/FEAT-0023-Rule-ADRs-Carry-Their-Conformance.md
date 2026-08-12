---
type: "[[feature]]"
id: FEAT-0023
aliases: ["FEAT-0023"]
title: "Rule-ADRs: the template carries the convention, and the validator refuses the shape that binds nothing"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[ADR-0022]]", "user decision 2026-08-12", "three-repo survey 2026-08-12"]
goal: "Give project-os a surface for a project-authored quantified rule — the thing REQ, ADR and RISK are all the wrong shape for — by specifying `## Rule` / `## Domain` / `## Conformance` inside the decision kind, teaching the two skills that author and harvest them, and adding the check that stops a rule-ADR from binding nothing."
requirements: ["[[REQ-0025]]"]
tasks: ["[[TASK-0086]]", "[[TASK-0087]]", "[[TASK-0088]]", "[[TASK-0089]]"]
release: ""
related: ["[[ADR-0022]]", "[[ADR-0023]]", "[[ADR-0011]]", "[[ADR-0021]]", "[[ISS-0005]]"]
tests: ["[[TST-0004]]"]
reviewed_by: "model:claude-opus-5[1m]"
review_date: 2026-08-12
review_verdict: changes-requested
---

# Rule-ADRs

## Goal

Implements [[ADR-0023]], under [[ADR-0022]]'s constraint that it be a convention rather than a kind. Four changes to the template, in the order the specification has to exist before anything can point at it.

The gap it closes: **project-os has nowhere to put a rule.** Every note kind is singular — a requirement is a thing to build, a decision is a choice taken, a risk is a hazard that might happen — and the only quantified rules in the system are the validator's own 40 check codes, which are template-owned and closed to projects. The three per-repo levers over them (the `STATUSES.md` overlay, `tools/GRANDFATHERED.yaml`, `verification.staleness_days`) all subtract; none adds.

## Scope

- **[[TASK-0086]]** — `tools/instructions/DECISIONS.md`: the normative specification of the three sections, the provenance and harvest conventions, and the landing pattern. Everything else links here.
- **[[TASK-0087]]** — `docs/__templates__/adr.md` gains the block as an optional commented stanza; one sentence in `docs/__templates__/SCHEMAS.md`.
- **[[TASK-0088]]** — `tools/skills/adr-authoring/SKILL.md` learns to author one; `tools/skills/issue-intake/SKILL.md` learns to harvest — on intake, look for a sibling issue, and let the second of a kind propose a rule-ADR instead of filing a third one-off.
- **[[TASK-0089]]** — `tools/scripts/validate-docs.py`: the `DECISION-RULE` check, plus the bundled copy under `tools/cockpit/`.

## Out of scope

- **A new note kind.** [[ADR-0022]] is the decision and this feature is its first application. `POL-*` is revivable only on two recorded instances of the convention failing structurally.
- **Converting the existing population.** [[ISS-0005]]'s five feature-less policies get a *mechanism* here, not a migration; converting a requirement into an ADR removes a requirement note and is not reversible by a status flip, so it stays a decision awaiting sign-off.
- **Rendering rule-ADRs in the cockpit.** A surface that groups rules by domain, or shows which are unconformed, is a downstream feature with its own evidence. Nothing here depends on it.
- **Deciding which rules are template-owned.** Fleet-level rules stated once upstream and cited downstream is a consequence in ADR-0023, not a deliverable here.
- **A `RULES.md` per project.** Rejected as ADR-0023's option 2 for rules; still right for [[ISS-0005]]'s three conventions, which are style, not law.

## Ordering, and the one non-obvious dependency

**TASK-0086 first, and everything else points at it.** REQ-0018 makes state and transition rules normative in exactly one file; the same discipline is why this convention gets one home and three links rather than four descriptions that drift. ISS-0006 is the worked example of what the alternative costs — a rule stated in four files, amended in three, leaving every repo in the fleet instructing agents to apply a gate the ADR had just reverted, with nothing detecting it because no check compares prose to prose.

**TASK-0089 last, and its severity is a decision it must take rather than inherit.** [[ADR-0011]] permits `warn` only as a dated migration state; [[ADR-0021]]'s precedent says a brand-new convention has nothing to migrate and should error on day one. Which applies depends on a number nobody has yet: how many notes carrying `## Rule` exist across the fleet when the check lands. The pilot creates some of them this week, which is exactly why the count has to be taken at landing rather than assumed now.

## Risk scan

Run against the `LIFECYCLE.md` triggers. **No new risks identified** — no new external dependency or version constraint, no new env var or configuration surface, no directory-layout or artifact-path change, no long-running step, no credential or licence exposure. The check is a pure-Python addition to a script that already walks `docs/decisions/`.

Two **coordination hazards**, recorded here and carried in the plan rather than as `RISK-*` notes, because both are ordinary sequencing rather than hazards to the running system:

1. `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` in `project-os` is **dirty in the working tree with unrelated parallel work** as of 2026-08-12. The implementing session must coordinate rather than overwrite.
2. `project-os-cockpit` holds a **deliberately diverged validator superset** — 44 check codes against the template's 40, including `PARENT-BACKLINK`, `DESIGN-GATE`, `ACCEPT-STALE` and `SNAPSHOT-MEMBERSHIP` that exist nowhere upstream. `DECISION-RULE` will need a recorded hand-merge there, filed in that repo when this lands and deliberately not before.

## Acceptance

- [x] A project can state a rule over an enumerable domain, in a note kind that already exists, and the record shows both what the rule ranges over and what discharges it — evidence: your-health ADR-0020/0021, the pilot pair, each carrying `## Rule`/`## Domain`/`## Conformance` with named TST discharges and an authority sentence; the convention's normative home is project-os `tools/instructions/DECISIONS.md`, "A decision that states a rule" (`6ca15f4`).
- [x] A rule-ADR missing its domain or its conformance is reported by the validator rather than by a reviewer noticing — evidence: `DECISION-RULE`, error severity, firing on either section absent or empty at any ADR status; [[TST-0004]] passing (26 assertions after review round one, inversion-verified five ways including the check's own call site deleted — the suite now runs the real CLI end-to-end, so it fails if the check is unwired).
- [x] An ordinary yes/no ADR is completely unaffected — no new required section, no new finding, no template churn visible to a decision that is not a rule — evidence: the template block is inside an HTML comment (the heading's presence is the marker, so uncommented would arm the check against every template-derived ADR); fixture cases "ordinary ADR is silent" and "the raw template trips nothing"; the new validator run across all 12 fleet repos reports zero `DECISION-RULE` findings.
- [x] The harvest trigger is written where intake happens, so the second issue of a kind is the moment a rule gets proposed rather than the moment a third one-off gets filed — evidence: `tools/skills/issue-intake/SKILL.md` step 2 (mandatory, before ID allocation, bounded search, one-line negative), `6ca15f4`.
- [x] The convention is usable on the bare markdown before the check exists — the pilot does not wait for `DECISION-RULE` — evidence: the pilots were authored and accepted on plain headings the morning of 2026-08-12, before the check landed that afternoon, and the check then found them already conformant — the useful result the plan named.

## Independent review — 2026-08-12, `model:claude-opus-5[1m]`, **changes-requested**

Clean-context pass (fresh session; the notes and the two commits `6ca15f4` / `bc2d840`, never the authoring session's reasoning). Authored by `model:claude-fable-5`, reviewed by `model:claude-opus-5[1m]`.

**All five acceptance criteria above reproduce on their own evidence, and no defect was found in the shipped check.** The convention is usable on bare markdown (the pilot pair was authored before the check existed and is found conformant by it); `DECISION-RULE` fires at error severity on either section absent or empty at any status, confirmed by seven mutations and by an end-to-end run of `validate-docs.py --repo-root` over a malformed fixture (2 errors, exit 1); an ordinary decision is untouched, confirmed by the raw-template fixture case and by zero findings across all 12 fleet repos; the harvest trigger is at `issue-intake/SKILL.md` step 2, before ID allocation at step 3, as claimed. Both validators exit 0, `--self-check` is clean, `sync-snapshot --check` is clean, and the disclosed `generate-adapters` staleness on `.cursor/rules/obsidian.mdc` is confirmed pre-existing at `HEAD~1` and `HEAD~2` and untouched by this change.

**The verdict is `changes-requested` on the record, not on the engineering.** Two blocking findings sit on the requirement this feature is `done` on the strength of, and two on the test that guards it:

1. **`implemented` on uncommitted state.** REQ-0025's own `scope:` names the bundled cockpit validator; that copy exists only in project-os's working tree, in no commit, guarded by no check. See REQ-0025.
2. **The pending landing is attributed to a close-out that already happened** (2026-08-04), while the open issue chain that actually owes it is named in no note of this feature. That is a handoff-surface defect, which is the thing a clean-context pass is for. See REQ-0025.
3. **The suite cannot detect its own check being unwired** — deleting the call site in `validate()` leaves it 23/23 green while the corpus goes unchecked. See TST-0004.
4. **`adequacy:` records a bundled-copy run that the harness cannot perform "unchanged".** The claim's substance is true; the procedure as recorded is not reproducible. See TST-0004.

Non-blocking: the two skills each restate one normative sentence from `DECISIONS.md` against a DoD box that says none is restated; the `_decision_sections` docstring claims three contracts the suite does not pin; and a descriptive or plural `## Rule` heading escapes the marker silently, an asymmetry ADR-0023's consequences do not record.

## Links

- Requirement: [[REQ-0025]]
- Decisions: [[ADR-0023]] (the convention), [[ADR-0022]] (why a convention and not a kind)
- Tasks: [[TASK-0086]], [[TASK-0087]], [[TASK-0088]], [[TASK-0089]]
- Implementation target: `~/Dev/repos/project-os` — every file this feature changes lives in the template repo, not here.
- Pilot: `your-health` stat rules (see `plan/PLAN.md`).
