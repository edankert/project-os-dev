---
type: "[[adr]]"
id: ADR-0022
aliases: ["ADR-0022"]
title: "Conventions before types: a new note kind is minted only when an existing kind demonstrably cannot carry the semantics, and a convention that stands in for one must name its discharge"
status: accepted
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["user decision 2026-08-12", "downstream:project-os-cockpit FEAT-0091", "[[ISS-0005-Feature-Less-Requirement-Triage]]", "[[FEAT-0019-Design-Note-Type]]"]
decision: "Option 2. A new first-class note kind — ID prefix, collection, status table, counter, validator entries — is created only when an existing kind demonstrably cannot carry the semantics, evidenced by at least two concrete instances where a convention was tried and failed structurally rather than aesthetically. Until then new semantics ride inside an existing kind as a marked convention: a section convention, a role field, or a manifest. A convention standing in for a type must name the check that discharges it."
context: "This system has refused a new kind twice on the same reasoning and written the reasoning down neither time, while `SNAPSHOT.md` line 46 invites projects to add collections nothing validates."
alternatives:
  - "Mint a kind whenever the semantics feel new — rejected: the cost of a kind is permanent and paid by every downstream surface, while the feeling is momentary; this is the status quo, and it is a status quo held only by whoever happens to be arguing"
  - "A generic extension kind that projects specialise — rejected: it is a kind with the discipline removed, and `SNAPSHOT.md` line 46 already shows what that produces — a permission with no validator behind it"
supersedes: ""
superseded: ""
related: [ADR-0008, ADR-0023, ISS-0005, FEAT-0019]
decided_option: "2"
---

# Conventions before types

## Context

Twice in three weeks this system was asked for a new note kind, refused, and reached for the same argument both times. Neither time was the argument written down, so both times it had to be reconstructed.

**`project-os-cockpit` FEAT-0091**, 2026-08-10, on the eight one-per-project standing documents. Under *Out of scope*: *"**A new note type.** REQ-0033 records why: a type is for an open population, and there will never be a second glossary."* What shipped instead was a manifest — the base set template-owned, project extensions declared in `SNAPSHOT.yaml`'s `docs_system` block. Extensible, checked, and not a type.

**`ISS-0005` here**, 2026-07-24, closing out ADR-0007's deferred residue question: 23 requirements named no feature, and after triage 5 were policies and 3 were conventions. The finding: *"All 8 open non-deliverable notes have a natural home — ADR for the 5 policies, styleguide for the 3 conventions. No `kind:` field, and certainly no `constraint` type, is warranted."*

Two refusals, one reason, zero records. The next person asking gets to re-run the argument from scratch, and the argument only holds while someone is willing to run it.

**The counter-case is instructive rather than embarrassing.** [[FEAT-0019-Design-Note-Type|FEAT-0019]] *did* mint a kind — `DES-*` — and its own note states the bar this ADR generalises: *"Downstream started on `reference` + `scope: design-input` precisely to avoid this change — and then wanted the lifecycle, which is the signal that the type is real rather than convenient."* A convention was tried; it failed on something a convention cannot supply; the type followed. That is the shape.

**And the cautionary precedent is already in the template.** `tools/instructions/SNAPSHOT.md`, line 46: *"Projects may add collections (e.g. `epics`, `milestones`) if rules are documented and applied consistently."* Nothing validates a collection added under that permission — not its statuses, not its IDs, not its links. It is an invitation to produce data wearing a kind's clothes, and it has sat there unexercised, which is the only reason it has cost nothing yet.

## Options

1. **Mint a kind whenever the semantics feel new.** The status quo. It costs nothing at the moment of minting and everything afterwards, and it has no defender — nobody chose it; it is what happens when nothing is written down.
2. **Conventions first, with a named conformance check.** New semantics ride inside an existing kind as a marked convention until two instances show the convention failing structurally. The convention must name what checks it, or it is a preference. **Chosen.**
3. **A generic extension kind that projects specialise.** One `EXT-*` type with a `kind:` discriminator, so a project can declare its own semantics without touching the template. Rejected: it is minting with the discipline removed, and `SNAPSHOT.md` line 46 is the same idea already in the codebase — a permission with nothing behind it.

## Decision

**Option 2.**

1. **A new first-class note kind is created only when an existing kind demonstrably cannot carry the semantics.** A kind means all of it: an ID prefix, a collection, a status table, terminal-status decisions, `COLLECTION_TYPE` / `ID_PREFIXES` / metrics entries in the validator, template, taxonomy, traceability, adapters, and an obligation-and-ownership answer in every downstream surface that renders notes.
2. **The evidence is at least two concrete instances where a convention was tried and failed structurally, not aesthetically.** Structural means the existing kind cannot express the thing at all — FEAT-0019's *"then wanted the lifecycle"* is structural; *"it would read better with its own prefix"* is aesthetic. Name the instances in the ADR that proposes the kind.
3. **Until then, new semantics ride inside an existing kind as a marked convention.** Three shapes, in rough order of preference: a **section convention** (a named heading whose presence is the marker), a **role field** (`scope:`, `kind:`, a discriminator on an existing type), or a **manifest** (a declared, extensible set — FEAT-0091's shape).
4. **A convention standing in for a type must name its discharge.** What check, in what file, reports a note that claims the convention and does not satisfy it. A convention with no named check is a preference, and preferences do not survive contact with a corpus.

## Why the cost of a kind is the argument

Because it is permanent and it is paid by parties who were not in the room.

Counters never reuse IDs — allocating is not owning, and deleting a note never frees its number (`LIFECYCLE.md`, "Counter Integrity"). So a kind that turns out to be wrong cannot be withdrawn; it can only be deprecated, which is a second permanent artifact. Every kind then needs a status table and terminal-status decisions, which is what ADR-0008 spent a phase contracting after measuring that several declared values had never been written once. Every kind needs entries in the validator's type tables, and the `--self-check` guard exists precisely because a type added to one table and not another is invisible (ISS-0016, exercised for the first time by FEAT-0019). And every downstream surface that renders project-os notes has to answer what the kind means for obligations, for ownership, and for whether it counts as work in flight.

A convention costs a heading and a check. That asymmetry is the whole decision.

## Why the discharge clause is not optional

Because without it this ADR is a licence to leave rules unenforced, which is worse than the type-minting it prevents.

`QUALITY.md` states the operating theory in one line: **"Convention-only rules get silently skipped under context pressure; the validator does not."** ADR-0004 is the same finding measured — conditional skill steps were skipped by agents deciding the condition did not apply, *even when it did*, which is why risk scans, verification gating and impact analysis were made mandatory with explicit triggers.

So "ride as a convention" is only honest paired with "and name what checks it". The two clauses are one rule.

## What this is not

- **Not retroactive.** `DES-*` stands; so does every other kind in the vocabulary. This is the bar a *fourth* type has to argue past, not a re-litigation of the third.
- **Not a ban on structure.** A manifest, a role field and a section convention are all structure. What is rationed is the *kind*, because that is the thing with the permanent tail.
- **Not about status values.** ADR-0008 already governs those, and FEAT-0019's *"this adds a type, not a vocabulary"* shows the two questions are separable. A proposal may clear ADR-0008 and still fail here.

## Consequences

- The type table stays small enough that every entry means something, which is the property that makes `COLLECTION_TYPE` readable at all.
- **The price is real: a convention must carry a check, and writing the check is the work.** A project that adopts a convention and skips its discharge has not applied this ADR, it has skipped one — and by QUALITY.md's own theory that convention will be quietly ignored inside a quarter.
- The bar is now written down, so the next refusal costs a link instead of an argument, and the next *acceptance* has to show its two instances in public.
- `SNAPSHOT.md` line 46 is now visibly in tension with this decision: it permits collections that nothing validates. Left standing and named here rather than silently amended — whether it is narrowed, given a check, or deleted is its own decision with its own evidence, and this ADR is not the place to take it.
- [[ADR-0023]] is the first application: a quantified rule rides inside `[[adr]]` as a section convention, with `DECISION-RULE` as its named discharge.

> [!note] Accept — option 2: Conventions first, with a named conformance check — 2026-08-12 (user:edwin)
> "accept the four ADRs and start the implementation" — accepted in one act with [[ADR-0023]] and the pilot's first two rule-ADRs (your-health ADR-0020/0021): the law and its first applications enter force together.
