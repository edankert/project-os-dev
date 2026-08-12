---
type: "[[adr]]"
id: ADR-0023
aliases: ["ADR-0023"]
title: "A quantified rule is a decision: a rule of the form \"every member of DOMAIN satisfies P\" is recorded as an ADR carrying `## Rule`, `## Domain` and `## Conformance`"
status: accepted
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["user decision 2026-08-12", "three-repo survey 2026-08-12 (project-os, project-os-cockpit, your-health)", "[[ISS-0005-Feature-Less-Requirement-Triage]]", "downstream:your-health ADR-0006"]
decision: "Option 4. A rule quantified over a domain is recorded as an ordinary ADR carrying three additional sections: `## Rule` (one testable normative sentence), `## Domain` (the enumerable set the rule ranges over), `## Conformance` (the named discharge, plus which side is authoritative when rule and artifact disagree). The presence of `## Rule` is what marks a rule-ADR; no new note kind, per ADR-0022."
context: "project-os has no surface for a project-authored quantified rule: REQ, ADR and RISK are all singular, a cross-cutting REQ is permitted and then gated by nothing, and the only quantified rules in the system are the validator's own checks, which are closed to projects."
alternatives:
  - "A cross-cutting requirement (`implements: \"\"`) — rejected: already permitted, already gated by nothing, and its lifecycle describes a thing built once rather than a law in force"
  - "A standing prose document — rejected as the primary home: no per-rule lifecycle, no supersession record, and nothing dates or checks an individual rule inside it"
  - "A new POL-*/INV-* note kind — rejected under ADR-0022: no instance yet shows a convention inside `[[adr]]` failing structurally"
supersedes: ""
superseded: ""
related: [ADR-0022, ADR-0007, ADR-0011, ADR-0021, ISS-0005, REQ-0025]
decided_option: "4"
---

# A quantified rule is a decision

## Context

Every note kind in project-os is **singular**. A requirement is a thing to build. An ADR is a choice that was taken. A risk is a hazard that might happen. Not one of them is shaped like *"every member of this set satisfies P"* — and that is the shape most of a mature project's hard-won knowledge eventually takes.

**There is one place quantified rules do live, and projects cannot reach it.** `tools/scripts/validate-docs.py` is 40 distinct check codes as of 2026-08-12 (counted as the distinct first argument to `report.error` / `report.warn` / `emit`; 44 in `project-os-cockpit`'s deliberately diverged superset, 39 here — this repo is a sync behind and is missing `DECISION-OPTIONS`). Every one of them is a rule quantified over a domain: *every requirement names at most one feature*, *every plan's status follows its feature*, *every terminal item resolves its criteria*. They are template-owned. A project gets exactly three levers over them — the `STATUSES.md` overlay, the `tools/GRANDFATHERED.yaml` ledger, and `verification.staleness_days` — and **all three subtract**. There is no way for a project to *add* a rule of its own.

**So projects reach for a cross-cutting requirement, and the model lets them.** `STATUSES.md` is explicit: a requirement's `implements:` names at most one feature, and *"Zero is permitted (an unowned or cross-cutting requirement gates no feature)."* [[ISS-0005-Feature-Less-Requirement-Triage|ISS-0005]] then measured what that produces. Of 23 feature-less requirements across the fleet, after triage **5 were policies and 3 were conventions**, and the note is blunt about both halves of the problem:

> They are ADR-shaped: each is a decision with consequences and rejected alternatives.

> Note the 5 policies are *already* effectively feature-exempt with no mechanism at all: they name no feature, so the FEATURE-REQ gate never inspects them and they block nothing.

**Permitted, and gated by nothing.** ISS-0005 recommended converting them to ADRs and has sat `open` awaiting sign-off since 2026-07-24 — because "make it an ADR" was a filing answer, and nothing said what an ADR does to keep a rule's teeth once it gets there.

**Meanwhile the fleet is already using ADRs as rule statements, without saying so.** `your-health` ADR-0006 — *"One permanent hue per metric; level is encoded as a shade of that hue"* — is a universally quantified statement over an enumerable set, and it is enforced by a loop test over every `WidgetType`. It has a rule, a domain and a conformance check. It just has them implicitly, so nothing can tell it apart from an ADR that is genuinely a one-off choice.

**And the cost of not having the shape is measurable.** In `your-health` (85 requirements and 82 issues, both re-counted 2026-08-12), the survey found ~41% of requirements and ~44% of issues naming one specific metric, with at least 15 issues falling into four cross-cutting families — null-versus-zero, day-attribution, comparator-includes-today, rounding. Each was filed retail. Each family is one sentence that would have covered every member of it. *(Family membership is the survey's classification and the one figure here not re-derived independently; [[TASK-0086]] and the pilot restate it with a stated method or drop it.)*

## Options

1. **A cross-cutting requirement — `REQ-*` with `implements: ""`.** Costs nothing to adopt; it is already legal. Rejected on two counts. It is gated by nothing — ISS-0005 measured exactly this and found the FEATURE-REQ gate never inspects such a note. And its lifecycle is wrong: `draft → approved → implemented` describes a thing that gets built once and is then finished, where a rule is in force or repealed and is never *done*.
2. **A standing prose document** — one `RULES.md` per project, or a section inside `STYLEGUIDE.md`. This is ISS-0005's answer for its 3 conventions and remains right for them. Rejected as the primary home for rules: a document has one `updated:` date for N rules, no supersession record, and no way to say *this clause was replaced on this date because of this evidence*. It drifts silently, which is precisely the failure `FEAT-0091` measured across the standing set — 94% stale or undated.
3. **A new `POL-*` / `INV-*` note kind.** Honest about the semantics being new. Rejected under [[ADR-0022]]: no instance yet shows a convention inside `[[adr]]` failing *structurally*, and the permanent cost of a kind is paid by every downstream surface. If two such instances appear, this is the proposal to revive — and they should be named here when they do.
4. **A rule-ADR: an ordinary ADR carrying `## Rule`, `## Domain` and `## Conformance`.** **Chosen.**

## Decision

**Option 4.** A rule of the form *"every member of DOMAIN satisfies P"* is recorded as an ordinary ADR carrying three additional sections.

**`## Rule`** — the normative statement, **one testable sentence**. If it takes a paragraph it is either two rules or not yet a rule. Its presence is what marks the note as a rule-ADR; there is no `kind:` field and no new type.

**`## Domain`** — the enumerable set or registry the rule ranges over: a type enum, a directory, a manifest, a table. **If the set cannot be named, the rule is not ready to be decided.** A rule over "everything relevant" cannot be conformed to and cannot be checked, and writing "all metrics" where no list of metrics exists is how a rule becomes a slogan.

**`## Conformance`** — the named discharge: a `TST-*` note, a type that makes the violation unrepresentable, or a validator check code. Plus **one sentence naming which side is authoritative when the rule and the artifact disagree** — whether a conflict means the code is wrong or the rule has been overtaken. Without that sentence a violation has no defined resolution, and the rule quietly becomes advisory on first contact.

Everything else about the note is unchanged: it is a decision, it takes `proposed` / `accepted` / `superseded`, and [[ADR-0021]]'s `## Options` discipline applies to it exactly as to any other.

## Why an ADR and not a requirement

**Lifecycle fit, and it is not a close call.** `accepted` and `superseded` already mean *in force* and *repealed*, which is what laws do. A requirement's `draft → approved → implemented` describes a deliverable, and [[ADR-0007]] made `implemented` terminal and gated it on acceptance criteria — so a rule filed as a requirement reads `implemented` the moment its first instance ships, while it must still bind everything built afterwards. `your-health` REQ-0028 already works around this in prose, listing its features under **"Reinforced by"** rather than "implemented by" (ISS-0005, category C).

**Supersession preserves case history.** A rule that changes leaves a chain: the old note stays, `superseded_by:` points forward, and the reason for the change is in the successor's Context. That is exactly how a body of law records why it is what it is, and requirements have no equivalent — an amended requirement's previous text is only in git.

**ADR-0021's options discipline keeps rules honest.** A rule that had to declare at least two readable options is a rule someone chose over an alternative. Without that pressure, quantified statements drift toward platitude — "every metric should be consistent" — which is unfalsifiable and therefore unconformable.

## Provenance: harvested rules and up-front rules

**A harvested rule cites the issue family that nominated it, in `## Context`. The trigger is the *second* issue of a kind, not the first.** One instance is a bug; two is a domain. Filing the third one-off instead of proposing the rule is the failure this convention exists to catch, and it is what produced `your-health`'s four families.

**An up-front rule says "from principle" and must land its conformance the same day.** A rule with no scars has nothing keeping it honest — no instance forced it to be precise, and nothing yet proves the domain is enumerable. Requiring the check immediately is the substitute for the evidence it does not have.

## Landing a rule over an existing corpus

Reuse the machinery, do not reinvent it. A new rule over a corpus that predates it lands **warning-first with a dated promotion** — `PROMOTIONS` in `validate-docs.py`, the shape [[ADR-0011]] already defines — plus **grandfathered instances listed by ID with reasons**, in `tools/GRANDFATHERED.yaml`.

ADR-0011's three clauses apply unchanged and unweakened: the cutover is encoded in code, it is no more than 90 days out, and **clause 3 forbids promoting over debt**. Its corollary bites here in both directions: a rule landing over a corpus with *zero* violations has nothing to migrate, and per ADR-0021's precedent it should be an error on day one rather than a warning nobody reads.

## Consequences

- **Naming a Domain forces registries into existence, and that is rule zero of the whole scheme.** "Every metric" is not a domain until something enumerates the metrics. Most of the value of a rule-ADR is extracted before it is accepted, by the act of being made statable.
- **A rule that binds nothing should eventually be refused by the validator**, not merely discouraged — [[REQ-0025]] and `DECISION-RULE`. Until that check exists the convention is prose, and per [[ADR-0022]] a convention with no named discharge is a preference.
- **Fleet-level rules get stated once upstream and cited downstream**, rather than copied into eleven repos where eleven copies drift. Which rules are template-owned and which are project-owned is a filing question this ADR does not settle; the sync mechanism already carries the template-owned ones.
- **`## Rule` becomes load-bearing syntax in a decision note.** A note that uses the heading casually — as prose scaffolding rather than as the marker — will be checked as a rule-ADR and will fail. That is the cost of a section convention doing a type's job, and it is the cheaper cost.
- **ISS-0005's five policies now have a mechanism, not just a destination.** Whether to convert them is still Edwin's call and still needs sign-off; what changes is that "make it an ADR" now means something specific about what the ADR must carry.
- **This is [[ADR-0022]]'s second application and its first test.** If rule-ADRs turn out to need a lifecycle `[[adr]]` cannot express — a rule in force for one repo and not another, say, or a rule with a scheduled repeal — that is one of the two structural failures ADR-0022 requires before `POL-*` is proposed again. Record it here if it happens.

> [!note] Accept — option 4: A rule-ADR — an ordinary ADR carrying `## Rule`, `## Domain` and `## Conformance` — 2026-08-12 (user:edwin)
> Accepted with [[ADR-0022]] and the two pilot rule-ADRs (your-health ADR-0020/0021). Implementation starts the same day: [[FEAT-0023]] upstream ([[REQ-0025]], `DECISION-RULE`), the registry and the conformance loops in your-health.
