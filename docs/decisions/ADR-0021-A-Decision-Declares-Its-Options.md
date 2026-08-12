---
type: "[[adr]]"
id: ADR-0021
aliases: ["ADR-0021"]
title: "A decision declares its options in a form the tool can read, and the validator keeps it that way"
status: accepted
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["Edwin 2026-08-12: 'why for ADR-0010 do I not have a way to select an option? (how can we make sure the LLM formats the document correctly for me to be able to make these decisions?)'"]
decision: "A decision offering a choice states it under `## Options`, in either of two readable forms, numbered 1..N, naming the proposed one in `## Decision`. `DECISION-OPTIONS` errors on a section that cannot be read. Recording a choice writes `decided_option:` and names it in the decision-record callout."
context: "Three ADRs in one corpus carried an Options section in two different forms; a person opening one to decide it was offered Accept and Supersede, and which option they chose was not recordable."
alternatives:
  - "One canonical form, migrate the rest — rejected: both observed forms are unambiguous, and a convention that invalidates notes already written is a migration wearing a convention's clothes"
  - "Let the surface parse loosely and offer whatever it finds — rejected: the shape then drifts per author until the control silently stops appearing, which is the state this fixes"
  - "A dated warning first — rejected: ADR-0011 permits a warning only as a migration state, and a new convention has nothing to migrate"
  - "Require a choice before Accept — rejected: a decision may be taken as proposed, and demanding a choice turns an offer into a gate"
supersedes: ""
superseded: ""
related: [ADR-0011, ADR-0020]
---

# A decision declares its options

## Context

[[ADR-0020]] made a judgment able to carry its reasoning. It did not make a judgment able to carry **what was judged**.

A decision that lists three options and records only `accepted` has lost the answer — and choosing a path other than the proposed one was not expressible at all. Measured 2026-08-12 in `project-os-cockpit`: three decisions carried an `## Options` section in **two** forms, `N. **Label.**` in two and `### N. Label` in the third, because nothing had ever said which was right.

**A control can only offer what a document declares**, which is the whole of Edwin's second question: *"how can we make sure the LLM formats the document correctly for me to be able to make these decisions?"* Writing the convention down is half an answer; the other half is checking it.

## Decision

1. **Options go under `## Options`**, in either readable form, numbered `1..N`.
2. **The proposed one is named in `## Decision`** — "Option 3" — so a surface defaults to what the note says rather than to a guess.
3. **`DECISION-OPTIONS` is an error** when the section yields fewer than two readable options, or when they do not number from 1.
4. **A recorded choice writes `decided_option:`** and names the option in the decision-record callout — machine-readable and human-readable, from one act.
5. **Accepting without choosing stays legal.**

## Why both forms

Because both were already in use and neither is ambiguous. The check is not *which syntax* but *can this be read*, which is the difference between a convention and a preference. A rule that reds existing notes on the day it lands teaches people to route around the validator.

## Why an error on day one

[[ADR-0011]] permits `warn` only as a dated migration state. A brand-new convention has **nothing to migrate**: no repo has an `## Options` section written against it, so there is no debt, and a warning would be the permanent tier that ADR forbids.

## Consequences

- The ADR template carries the section, so the shape is where an author starts rather than something they are told afterwards.
- A surface offering the options never parses markdown itself; it receives them, or there are two parsers to keep in step.
- The validator ships a second, standalone reader on purpose — the check must not depend on the cockpit being installed.
