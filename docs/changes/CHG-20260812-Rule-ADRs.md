---
type: "[[change]]"
id: CHG-20260812-Rule-ADRs
aliases: ["CHG-20260812-Rule-ADRs"]
title: "Rule-ADRs land in the template: `## Rule`/`## Domain`/`## Conformance` specified once in DECISIONS.md, taught by two skills, carried commented by the template, and enforced by DECISION-RULE as an error from day one"
status: merged
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[FEAT-0023]]", "[[ADR-0023]]", "[[ADR-0022]]"]
commit: "project-os 6ca15f4; this repo's close-out commit carries the record"
pr: ""
impacts: ["../project-os/tools/instructions/DECISIONS.md", "../project-os/docs/__templates__/adr.md", "../project-os/docs/__templates__/SCHEMAS.md", "../project-os/tools/skills/adr-authoring/SKILL.md", "../project-os/tools/skills/issue-intake/SKILL.md", "../project-os/tools/scripts/validate-docs.py", "../project-os/tools/scripts/test-decision-rule.py", "../project-os/tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py (working tree only — see below)"]
issues: []
features: [FEAT-0023]
tests: [TST-0004]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: [ADR-0011, ADR-0021, ADR-0010, REQ-0025, ISS-0005]
---

# Rule-ADRs land in the template

## Summary

[[FEAT-0023]] implemented, entirely in `~/Dev/repos/project-os` (commit `6ca15f4`) — nothing changed in this repo except the record, per the standing split. A quantified rule — *every member of DOMAIN satisfies P* — now rides inside the decision kind as three body sections, `## Rule` (one testable sentence; the heading's presence is the marker), `## Domain` (the enumerable set; if it cannot be named the rule is not ready), and `## Conformance` (the named discharge plus which side is authoritative on disagreement). A convention rather than a kind, per [[ADR-0022]]; the shape, per [[ADR-0023]].

The specification lives once, in `tools/instructions/DECISIONS.md` ("A decision that states a rule"); the ADR template, `SCHEMAS.md` and both skills link to it and restate nothing — REQ-0018 applied, with [[ISS-0006]] as the reason it matters.

## Impact

- **Authoring**: `adr-authoring/SKILL.md` gains the rule-ADR branch, led by *name the domain first, and stop if it cannot be enumerated*.
- **Harvest**: `issue-intake/SKILL.md` gains a mandatory sibling search before ID allocation — bounded to a keyword/surface grep of the repo's own issues, with a one-line recordable negative — and on the second issue of a kind, the step is to propose a rule-ADR rather than leave a third one-off to be filed. The [[ADR-0016]] tension is resolved in the skill text: the one-line negative is the entire common-case cost, and the step stays mandatory because conditional steps get skipped even when the condition holds ([[ADR-0004]]).
- **Template**: `docs/__templates__/adr.md` carries the three headings inside an HTML comment — structural, not stylistic, since an uncommented `## Rule` would mark every template-derived ADR as a rule-ADR.
- **Enforcement**: `DECISION-RULE` in `validate-docs.py` — any decision note carrying `## Rule` (outside fences and HTML comments) must carry non-empty `## Domain` **and** `## Conformance`, at any ADR status; `TST-####` under Conformance must resolve; check codes, type names and prose there are never dangling references; a TST is deliberately not required (the type that makes a violation unrepresentable is the stronger discharge, [[ADR-0010]]'s inversion avoided).

## Severity: error from day one, from a counted set

Censused at landing (2026-08-12): `grep '^## Rule'` over `docs/decisions/*.md` across all 12 repos under `~/Dev/repos` → exactly two notes, your-health ADR-0020/0021 (the pilots), both conforming, TST-0018/0019 resolving; one near-miss (`### Rules`, your-trainer ADR-0009) correctly outside the marker. **Zero violations → error on day one** ([[ADR-0021]]'s precedent under [[ADR-0011]]); no `PROMOTIONS` entry, no `GRANDFATHERED.yaml` entries. Count, method and reasoning are in the check's docstring, where this codebase keeps them.

## The bundled copy: applied, verified, deliberately not committed

`tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` in project-os was already dirty with unrelated parallel work (the FEAT-0022 claimants fix) — the coordination hazard the plan predicted. The DECISION-RULE addition is applied **in place beside that work** (disjoint hunks) and verified there (`--self-check` clean; the full suite passes against the bundled copy). Commit `6ca15f4` does **not** include the file: staging it would have dragged the parallel diff into this change. The parallel work's own close-out carries the file with both changes; until then the bundled copy's committed state lacks the check while its working tree has it. Also inherited, not caused here: project-os HEAD currently fails `generate-adapters --check` on `.cursor/rules/obsidian.mdc` (stale since the parallel session committed `OBSIDIAN.md` without the regenerated artifact) — pre-existing at `HEAD~1`, unchanged by `6ca15f4`.

## Verification

- [[TST-0004]] — `tools/scripts/test-decision-rule.py`, 23 assertions, stamped `passing` by `run-tests.py` (2026-08-12T16:23Z, exit 0). Adequacy by inversion: four deliberate breaks of the check each fail the suite; the comment-stripping canary is deliberately asymmetric so a comment-blind parser cannot pass it by accident.
- New validator against the fleet: **zero `DECISION-RULE` findings in all 12 repos**; your-health's pilots positively parsed; its 2 pre-existing TEST-FIELDS errors byte-identical under the HEAD validator.
- project-os gates at `6ca15f4`: `validate-docs.sh` exit 0 (one pre-existing BRIEF-PLACEHOLDER warning), `--self-check` exit 0, `sync-snapshot --check` clean, `generate-adapters --check` all 35 artifacts current in the working tree.
- This repo verified directly with the **new** validator (zero findings; [[ADR-0022]]/[[ADR-0023]] correctly unmarked — they describe the convention without carrying `## Rule`). Its own validator remains a sync behind by design; `sync-project-os.sh` is deliberately a separate later step.

## Documentation Coverage (All Types Considered)

- features: updated ([[FEAT-0023]] done, criteria ticked with evidence)
- requirements: updated ([[REQ-0025]] draft → approved → implemented; authority Edwin 2026-08-12)
- tasks: updated (TASK-0086..0089 done with evidence; TASK-0089 carries the bundled-copy record)
- issues: not-applicable (none filed; the one unfixable-here obligation is a follow-up below, not a validator error)
- tests: new ([[TST-0004]])
- workflows: not-applicable
- decisions: not-applicable ([[ADR-0022]]/[[ADR-0023]] accepted before this change, `0ad54f1`)
- risks: not-applicable (re-checked against the LIFECYCLE triggers: pure-Python addition to an existing walk, no new dependency, env var, path change, or long-running step)
- changes: new (this note; its counterpart in project-os is `docs/changes/CHG-20260812-Rule-ADRs.md` there, per the Model-Routing precedent for template changes)
- snapshot: updated (focus → FEAT-0023 close-out; TST-0004 and this note registered)

## Follow-ups

- [ ] `project-os-cockpit` hand-merge: its deliberately diverged 44-code validator does not gain `DECISION-RULE` until it is hand-merged and recorded there. Now due — TASK-0089 has landed; deliberately not done as a side-effect commit to a third repo.
- [ ] The bundled copy's DECISION-RULE addition rides in project-os's working tree; the parallel FEAT-0022-claimants close-out commits that file with both changes.
- [ ] Fleet rollout via `sync-project-os.sh` — deliberately not run as part of this change; this repo's own validator gains the check (and `DECISION-OPTIONS`, which it also lacks) on its next sync.
