---
type: instruction
id: INSTR-DECISIONS
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-03
tags: [instructions, decisions]
---

# Decision records (ADRs)

Use ADRs (`../../docs/decisions/ADR-####-*.md`) for durable decisions that affect more than one file or flow.

## When to create an ADR
- A convention or contract changes (schemas, status models, directory layout).
- There are real alternatives with tradeoffs.
- A choice affects more than one workflow or team.

## How to record ADRs
1. Create the note from `../../docs/__templates__/adr.md`.
2. Add or update the entry under `items.decisions` in `../../SNAPSHOT.yaml`.
3. Link the ADR to the items it affects via `related`.

## Superseding
- If ADR B replaces ADR A: B sets `supersedes: [[ADR-A]]`; A sets `superseded: [[ADR-B]]` and its status becomes `superseded`.

## A decision that is not a yes/no

An ADR that leaves threads open in its own consequences gets an `## Acceptance` section with one criterion per thread. Reason: accepting stamps every thread at once, so a decision with unanswerable threads sits `proposed` for months; criteria are tickable one at a time, with evidence, through the machinery a feature's criteria already use.

```markdown
## Acceptance

- [ ] **The read-only digest:** decided, or deferred with a home and a reason.
- [ ] **`Recent`:** kept in both surfaces or dropped from both. Say which.
```

Accepting with a criterion still open is allowed; the record shows the residue rather than preventing the decision. Most ADRs are a genuine yes/no and need none of this.

## Recording why, not only what

Every human verb (accept, approve, decline, supersede, triage) may carry a note, appended to the decided note under a single `## Decision record` heading as an Obsidian callout:

```markdown
## Decision record

> [!note] Accept — 2026-08-12 (user:edwin)
> Option 3, but consequence 3 needs the digest question settled first.
```

It is a callout so Obsidian and the cockpit both render it; it appends, so a second decision adds a second callout and the first is never edited; the prose is quoted line by line, so a note containing `---` or a heading cannot alter the file. Reason: without this a project records *that* a human decided and never *why* (ADR-0020 holds the measurement).

## A decision that offers options

If the decision is a choice between paths, put them under `## Options`, numbered `1..N`, either as a numbered list or as `### N. Title` subsections, and name the one you propose in `## Decision` ("Option 3") so a surface can default to it.

**This is checked.** `DECISION-OPTIONS` is an error when an `## Options` section yields fewer than two readable options or they do not number `1..N`. Reason: a control can only offer what a document declares, and a convention nobody validates drifts per author until the control stops appearing. An error rather than a dated warning because the convention landed with no debt to grandfather (ADR-0011).

Recording a choice writes `decided_option:` in the frontmatter and names it in the decision-record callout. Accepting without choosing stays legal: demanding a choice would turn an offer into a gate.

## A decision that states a rule

A quantified decision, **every member of DOMAIN satisfies P**, is an ordinary ADR carrying three more sections. A section convention, not a new note kind (ADR-0023; the bar a new kind must clear is ADR-0022's). **The `## Rule` heading's presence marks a rule-ADR**, so do not use that heading as prose scaffolding in a decision that is not a rule.

```markdown
## Rule
One testable normative sentence.

## Domain
The enumerable set the rule ranges over.

## Conformance
The named discharge, and which side is authoritative on disagreement.
```

- **`## Rule`**: one testable normative sentence. A paragraph is two rules or not yet a rule.
- **`## Domain`**: the enumerable set the rule ranges over: a type enum, a directory, a manifest, a table. If the set cannot be named, the rule is not ready; naming the domain often forces the missing registry into existence, which is most of the rule's value.
- **`## Conformance`**: the named discharge (one or more `TST-*` notes, a type that makes the violation unrepresentable, or a validator check code) plus one sentence naming which side is authoritative when the rule and an artifact disagree. Reason: without that sentence a violation has no defined resolution and the rule becomes advisory on first contact.

**Provenance.** A harvested rule cites the nominating issue family in its `## Context`. The trigger is the second issue of a kind, not the first: one instance is a bug, two is a domain (the sibling search in `../skills/issue-intake/SKILL.md` is where the second gets noticed). A rule from principle says so and lands its conformance the same day.

**Landing a rule over an existing corpus.** The rule's check lands warning-first with a dated promotion (`PROMOTIONS` in `../scripts/validate-docs.py`) and the instances already violating are listed by ID, with reasons, in `../GRANDFATHERED.yaml` (`STATUSES.md`, "Grandfathering"). ADR-0011 applies unweakened: the cutover is encoded in code, no more than 90 days out, and promotion over unpaid debt is forbidden. A corpus with zero violations skips the warning and errors from day one.

**Options.** A rule-ADR carries `## Options` under the rule above whenever it rejected something specific: a threshold, a default, a type deferred in favour of the check.

**This is checked.** `DECISION-RULE` is an error when a decision note carries `## Rule` and its `## Domain` or `## Conformance` is missing or empty, at any status, because a `proposed` rule is malformed the same way. `TST-*` IDs under `## Conformance` must resolve; a check code, a type name or prose there is never a dangling link. Headings inside fenced code blocks or HTML comments do not count, which is why the commented block in `../../docs/__templates__/adr.md` cannot arm the check. An error from day one for the same reason as `DECISION-OPTIONS`: zero violations at landing (ADR-0011).
