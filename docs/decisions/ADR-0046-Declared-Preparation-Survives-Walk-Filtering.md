---
type: "[[adr]]"
id: ADR-0046
aliases: ["ADR-0046"]
title: "Declared preparation survives filtering of settled walk checks"
status: accepted
decided_option: "2"
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
decided: 2026-09-16
source: ["Your Trainer FEAT-0122 and Edwin's 2026-09-16 instruction to implement it fully"]
decision: "Amend ADR-0045's step-filtering rule: a procedure may declare earlier prerequisite steps, setup tied to steps, and platform variants. The generator retains the transitive prerequisite actions for owed steps in authored order. Preparation contributes no verdict. The validator reports invalid declarations; the owed check set remains the ledger's set. No dependency is inferred from prose."
context: "Filtering a procedure to steps that cite owed checks can remove the workout start and finish actions required to reach later owed observations. Printing full setup also asks for equipment used only by omitted work."
alternatives: ["Keep every step and all setup", "Infer required actions from prose at generation time"]
consequences: ["Procedure authors must declare dependencies and setup scope where selective filtering matters", "The sheet and cockpit receive preparation actions without adding check verdicts", "Invalid declarations require a visible fallback or readiness problem", "Existing unannotated procedures retain their current behavior until corrected"]
supersedes: ""
superseded: ""
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]", "[[REQ-0031-Preparation-Is-Declared-And-Validated]]"]
---

# Declared preparation survives filtering of settled walk checks

## Context

ADR-0045 prints only the procedure steps that cite owed test parts. The FREE-rides sitting can therefore retain a resistance check and a summary check while losing the actions that start and finish the workout. A full sitting setup can also demand an AI key when only a language sweep remains.

## Options

1. **Keep all steps and setup.** This preserves the route but asks for unrelated work and equipment.
2. **Declare prerequisites and setup scope.** The generator follows authored links and keeps the ledger's owed set unchanged.
3. **Infer prerequisites from prose.** This hides decisions in a heuristic the author cannot validate.

## Decision

Use option 2. A procedure is still authored once for the product. Its numbered order remains authoritative. A prerequisite link names an earlier step; it never schedules a future step or creates a verdict. The validator reports a missing or cyclic link. A broken declaration cannot silently remove an owed observation.

Setup and platform variants are authored with the procedure and validated there. The generator does not combine conflicting instructions at runtime. The full procedure remains available, while the current walk shows only the setup needed by retained steps and their prerequisites.

## Consequences

The upstream generator, validator, template and rules change together. Consumer copies are synced from upstream. Project-specific procedures need annotation where the current filter removes necessary actions or carries irrelevant setup.

## Clarification, 2026-09-16: required state between actions

The authored `state_for:` value applies before its named step and each later step on that platform until another `state_for:` value replaces it. The generator follows this declaration even when an intervening step is omitted from the current owed walk. A step that is unavailable on the selected platform does not change that platform's required state. This makes a resumed step show the state the author says to restore. It does not confirm that the app or equipment is currently in that state, and it does not infer state from action prose. A procedure with no declaration keeps its current behavior.
