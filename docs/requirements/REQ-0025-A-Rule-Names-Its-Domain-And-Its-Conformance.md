---
type: "[[requirement]]"
id: REQ-0025
aliases: ["REQ-0025"]
title: "A rule stated as a decision names the domain it ranges over and the conformance that discharges it, and the validator refuses one that names neither"
status: implemented
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[ADR-0022]]", "user decision 2026-08-12"]
priority: medium
scope: "The template's decision conventions: DECISIONS.md, the ADR template and SCHEMAS.md, the adr-authoring and issue-intake skills, and the DECISION-RULE check in validate-docs.py plus its bundled copy."
acceptance:
  - "DECISIONS.md is the single normative statement of the three sections, the provenance/harvest convention and the landing pattern; every other file links to it"
  - "The ADR template carries the block as an optional, commented stanza, and a decision authored without it validates unchanged"
  - "DECISION-RULE fires on a decision note containing `## Rule` whose `## Domain` or `## Conformance` is absent or empty, at any ADR status"
  - "A TST-* ID named under `## Conformance` that resolves to no note is reported by the same check"
  - "The check's severity follows ADR-0011: error on day one, or a warning with a cutover encoded in PROMOTIONS no more than 90 days out, chosen against a counted violation set"
  - "A rule-ADR carrying all three sections validates clean, and the check reaches the bundled validator under tools/cockpit/"
implements: ["[[FEAT-0023]]"]
verifies: []
related: ["[[ADR-0022]]", "[[ADR-0023]]", "[[ADR-0011]]", "[[ISS-0005]]"]
tests: ["[[TST-0004]]"]
reviewed_by: "model:claude-opus-5[1m]"
review_date: 2026-08-12
review_verdict: changes-requested
---

# A rule names its domain and its conformance

*Status history: `draft` → `approved` 2026-08-12 (authority: Edwin, "accept the four ADRs and start the implementation" — the same act that accepted [[ADR-0022]] and [[ADR-0023]]); `approved` → `implemented` 2026-08-12 at [[FEAT-0023]] close-out, each criterion ticked below against the landed change (project-os commit `6ca15f4`).*

## Statement

A decision note that states a quantified rule — *"every member of DOMAIN satisfies P"*, marked by a `## Rule` heading — **must** name the domain the rule ranges over and the conformance that discharges it. `validate-docs.py` **must** report a rule-ADR that omits either section, and **must** refuse it once the check reaches error severity.

The requirement is on both halves for a reason. A rule with a domain and no conformance is unenforced by construction — [[ISS-0005]] measured five such rules already in the fleet, filed as feature-less requirements, *"already effectively feature-exempt with no mechanism at all"*. A rule with a conformance and no domain cannot be conformed to, because nothing says what the check must range over. Either omission alone produces a rule that binds nothing, which is why the check fires on either and not only on both.

## Acceptance Criteria

- [x] `tools/instructions/DECISIONS.md` specifies `## Rule`, `## Domain` and `## Conformance` — their semantics, the second-issue harvest trigger, the from-principle exception, and the warning-first landing pattern — as the **single normative statement**; the ADR template, `SCHEMAS.md`, `adr-authoring/SKILL.md` and `issue-intake/SKILL.md` link to it and restate none of it (REQ-0018's rule, applied) — evidence: project-os `6ca15f4`: `tools/instructions/DECISIONS.md:92` ("A decision that states a rule"); linkers `docs/__templates__/adr.md:23`, `docs/__templates__/SCHEMAS.md:55`, `tools/skills/adr-authoring/SKILL.md:27`, `tools/skills/issue-intake/SKILL.md:33` — each a pointer plus its own behaviour, none a restatement.
- [x] `docs/__templates__/adr.md` carries the three sections as a commented, optional block, and an ADR authored from the template without the block validates with zero new findings — evidence: `tools/scripts/test-decision-rule.py` case "the raw template trips nothing", which reads the real template into a fixture repo (and its sibling case validates the block uncommented and filled); [[TST-0004]] passing.
- [x] `DECISION-RULE` reports any note under `docs/decisions/` containing a `## Rule` heading whose `## Domain` or `## Conformance` section is absent or empty, **regardless of the note's status** — a `proposed` rule binds nothing yet but is still malformed — evidence: fixture cases absent-Domain, empty-Domain, absent-Conformance, empty-Conformance (each fires, absent and empty named distinctly), the clean case silent, and the `accepted`-status case firing identically; [[TST-0004]], 23 assertions, exit 0.
- [x] A `TST-*` ID named under `## Conformance` that resolves to no note in the repo is reported by the same check; a validator check code or a type named there is accepted as prose and not resolved — evidence: fixture cases dangling-TST (fires, names the ID), resolving-TST via note and via snapshot items (silent), one-dangling-among-resolving (fires once, names the dangling one), check-code-only and type-only (silent); [[TST-0004]].
- [x] Severity is settled under [[ADR-0011]] against a **counted** violation set at landing: zero violations means error on day one ([[ADR-0021]]'s precedent — nothing to migrate); a non-zero count means a warning with its cutover encoded in `PROMOTIONS`, no more than 90 days out, and clause 3 forbids promoting over the debt before it is cleared — evidence: census 2026-08-12, `grep '^## Rule'` over `docs/decisions/*.md` across all 12 fleet repos: two hits (your-health ADR-0020/0021), both conforming, **zero violations → error from day one**; no `PROMOTIONS` entry and no `GRANDFATHERED.yaml` entries, deliberately; count, method and choice recorded in `validate_decision_rule`'s docstring.
- [x] A rule-ADR carrying all three sections validates clean in this repo and in the pilot repo, and the check is present in the bundled copy under `tools/cockpit/` — evidence: new validator run over all 12 repos reports zero `DECISION-RULE` findings, your-health's two pilots positively parsed (Rule seen, sections non-empty, TST-0018/0019 resolved) and its only errors are 2 pre-existing TEST-FIELDS, byte-identical under the HEAD validator; the bundled copy carries the check in project-os's working tree (self-check clean, 23/23 against it) — **applied beside the parallel FEAT-0022 diff and deliberately left uncommitted with it**, recorded loudly in [[TASK-0089]] and both CHG notes.

## Traceability

- Implements: [[FEAT-0023]]
- Decided by: [[ADR-0023]] (the convention), [[ADR-0022]] (why it is a convention and not a type)
- Verified by: `tools/scripts/validate-docs.py` (`DECISION-RULE`) plus the fixture exercising it; a `TST-*` note is created with [[TASK-0089]] rather than up front, because a test note's status is stamped by execution ([[ADR-0010]]) and there is nothing yet to execute.

## Independent review — 2026-08-12, `model:claude-opus-5[1m]`, **changes-requested**

Clean-context pass (fresh session; these notes and the two commits only, no access to the authoring session's reasoning). **Criteria 1 through 5 each reproduce independently.** Criterion 1's five cited line references all resolve as written (`DECISIONS.md:92` is the section heading; `adr.md:23`, `SCHEMAS.md:55`, `adr-authoring/SKILL.md:27`, `issue-intake/SKILL.md:33` are each a pointer). Criteria 2, 3 and 4 were re-verified by re-running the suite (23 assertions, exit 0) and by mutating the check seven ways on a scratch copy — dropping the `Domain` requirement kills 6 assertions, gating the check to `accepted` kills 13, disabling dangling-TST resolution kills 4 — and end-to-end by running `validate-docs.py --repo-root` over a fixture repo with a malformed rule-ADR (2 errors, exit 1). Criterion 5's census reproduces exactly: 12 repos, two `^## Rule` hits, zero `DECISION-RULE` findings, no `PROMOTIONS` and no grandfather entries.

**Finding (blocking). Criterion 6 is ticked, and this requirement is `implemented`, on evidence that exists in no commit.** This note's own `scope:` names "the DECISION-RULE check in validate-docs.py **plus its bundled copy**". A fresh clone of project-os at `6ca15f4` does not contain the check in `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py`; it lives only in that repo's working tree. This is disclosed loudly and in four places, so it is not concealment — but the repo's own doctrine treats exactly this as a named failure class: `validate-docs.sh` grew its `--as-committed` mode because "a file that is present on disk but ignored, untracked, or simply not staged is invisible to every local check and absent in CI", with two recorded instances. Nothing mechanical guards the bundled copy either — TST-0004's recorded `command:` targets the canonical suite, whose harness hard-codes `HERE / "validate-docs.py"` — so if that working tree is discarded, no check, note or test notices. Either narrow the `scope:` and criterion 6 to the canonical validator and carry the bundled copy as separate work, or hold this requirement at `approved` until the file lands in a commit.

**Finding (blocking, handoff). The disposition of that uncommitted file is attributed to a close-out that has already happened.** This criterion, TASK-0089, both change notes and the snapshot entry all say the file rides "beside the parallel FEAT-0022-claimants work whose close-out commits both". That feature is `status: done` and its change note is `merged`, dated 2026-08-04 — its close-out is in the past, not scheduled. Separately verified: the canonical `tools/scripts/validate-docs.py` already carries the claimants fix at `6ca15f4`, so the only thing keeping the bundled copy dirty is a fix that has an open owner elsewhere — the round-three review issue whose blocking finding 1 is precisely *"the compute_metric_counts fix never reached the two bundled validator copies"*, still `open`, together with five later rounds in the same chain. **No note in this feature's record names any of them.** A reader arriving at this requirement with only the notes — which is the handoff test this review exists to apply — is pointed at a completed event and cannot find the open item that actually owes the landing.

**Finding (non-blocking, REQ-0018).** Criterion 1 asserts the linkers "restate none of it", and TASK-0086 states the standard absolutely: *"If any of them restates a sentence of this section, that is the same defect being reintroduced."* Two sentences are restated near-verbatim: `DECISIONS.md:108` "**If the set cannot be named, the rule is not ready to be decided**" reappears at `adr-authoring/SKILL.md:26`, and `DECISIONS.md:111` "one instance is a bug, two is a domain" reappears at `issue-intake/SKILL.md:33`. Both files also link correctly and both duplicated sentences are rationale rather than the gate, so the blast radius is small — but the box is ticked against a standard the work itself states without exception, and if the harvest trigger ever moves off "the second issue", the skill goes stale with nothing comparing prose to prose.

*Further findings on the test itself are recorded in TST-0004.*

## Note on the scope of "names neither"

The originating framing was that the validator should refuse a rule-ADR *"that names neither"* domain nor conformance. This requirement deliberately tightens it to **either**, matching the check as specified in [[TASK-0089]]: both sections are required, so a note carrying one and not the other is reported. Refusing only the both-missing case would let the most common malformation through — a rule with a domain and no discharge, which is exactly the ISS-0005 population.
