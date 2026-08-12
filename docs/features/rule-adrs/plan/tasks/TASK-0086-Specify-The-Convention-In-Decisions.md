---
type: "[[task]]"
id: TASK-0086
aliases: ["TASK-0086"]
title: "DECISIONS.md specifies the three sections, the harvest trigger and the landing pattern — once, and everything else links to it"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[REQ-0025]]"]
parent: "[[FEAT-0023]]"
effort: M
due: ""
depends: []
blocks: ["[[TASK-0087]]", "[[TASK-0088]]", "[[TASK-0089]]"]
related: ["[[ADR-0022]]", "[[ADR-0021]]", "[[ADR-0011]]"]
tests: []
---

# The specification

## What

Add a section to `~/Dev/repos/project-os/tools/instructions/DECISIONS.md` specifying the rule-ADR convention. This is the **only** place the convention is stated; the template, `SCHEMAS.md` and both skills link here.

`DECISIONS.md` already has the right shape for it — it grew three sections in the last week for [[ADR-0020]]'s decision record and acceptance criteria and [[ADR-0021]]'s options, each written as *what to put in the note* followed by *why it is that way*. Match that register.

## What it must specify

**The three sections.**

- **`## Rule`** — one testable normative sentence of the form *every member of DOMAIN satisfies P*. If it takes a paragraph it is two rules or not yet a rule. **Its presence is the marker**: there is no `kind:` field and no new note type, per [[ADR-0022]].
- **`## Domain`** — the enumerable set or registry the rule ranges over: a type enum, a directory, a manifest, a table. If the set cannot be named, the rule is not ready to be decided.
- **`## Conformance`** — the named discharge (a `TST-*` note, a type that makes the violation unrepresentable, or a validator check code) **plus one sentence naming which side is authoritative** when rule and artifact disagree.

**The provenance convention.** A harvested rule cites the nominating issue family in `## Context`, and **the trigger is the second issue of a kind, not the first** — one instance is a bug, two is a domain. An up-front rule says "from principle" and **must land its conformance the same day**, because it has no scars keeping it honest.

**The landing pattern.** A new rule over an existing corpus lands warning-first with a dated promotion (`PROMOTIONS` in the validator) plus grandfathered instances listed with reasons (`tools/GRANDFATHERED.yaml`) — the existing [[ADR-0011]] machinery, reused rather than reinvented, and its three clauses unweakened.

**Whether rule-ADRs carry `## Options`.** [[ADR-0021]] makes options required only when the decision offers a choice. State whether a rule-ADR is expected to carry them or inherits "available, not required" unchanged. This is a real question — most good rules rejected a specific alternative threshold or default — and leaving it open means two authors will answer it differently.

## Why this file and not a new one

REQ-0018 is the rule: state it once, link from everywhere else. [[ISS-0006]] is what the alternative costs — requirement advancement was stated in four files, ADR-0007 was amended, three were corrected and `status-transition/SKILL.md` was not, leaving **every repo in the fleet** instructing agents to apply a gate the ADR had just reverted. Nothing detected it, because no check compares prose to prose.

Three files will link here. If any of them restates a sentence of this section, that is the same defect being reintroduced.

## Definition of Done

- [x] `tools/instructions/DECISIONS.md` in `~/Dev/repos/project-os` carries the specification: three sections with semantics, the second-issue harvest trigger, the from-principle exception, the landing pattern, and the `## Options` answer — evidence: project-os `6ca15f4`, "A decision that states a rule". The Options answer: a rule-ADR inherits "A decision that offers options" unchanged — required when the decision offers a choice, with the observation that most real rules did reject something specific.
- [x] The section links to [[ADR-0023]] for the decision and [[ADR-0022]] for why it is a convention rather than a kind — evidence: its opening paragraph cites both, in the file's existing prose-ID convention for this repo's ADRs (as it already cites ADR-0011 in the Options section).
- [x] No other file added by this feature restates any of it — evidence: read against the TASK-0087/TASK-0088 diffs in `6ca15f4`; the template comment carries the three headings and a pointer, SCHEMAS.md carries one pointing sentence, both skills link to the section by name and add only the behaviour that is theirs (domain-first stop rule; bounded sibling search).
- [x] `bash tools/scripts/validate-docs.sh` clean in `project-os` after the edit — evidence: pre-commit run on `6ca15f4`, exit 0 (one pre-existing BRIEF-PLACEHOLDER warning, unchanged from baseline).

## Notes

`DECISIONS.md` is template-owned and syncs to eleven downstream repos via `tools/scripts/sync-project-os.sh`. Write it so it reads correctly in a repo that has never heard of `your-health` — the pilot is evidence for the convention, not part of it.
