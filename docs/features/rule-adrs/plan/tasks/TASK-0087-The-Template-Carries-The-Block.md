---
type: "[[task]]"
id: TASK-0087
aliases: ["TASK-0087"]
title: "The ADR template carries an optional Rule/Domain/Conformance block, and SCHEMAS.md gains one sentence"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["[[ADR-0023]]", "[[REQ-0025]]"]
parent: "[[FEAT-0023]]"
effort: S
due: ""
depends: ["[[TASK-0086]]"]
blocks: []
related: ["[[ADR-0021]]"]
tests: []
---

# The template carries the block

## What

Two small edits in `~/Dev/repos/project-os`:

1. `docs/__templates__/adr.md` — an **optional, commented** Rule/Domain/Conformance stanza, so an author writing a rule starts from the shape instead of being told about it afterwards.
2. `docs/__templates__/SCHEMAS.md` — one sentence naming the convention and pointing at `DECISIONS.md`.

## Why commented and optional

Because most ADRs are not rules, and a template that ships three sections every decision must delete is a template people stop starting from.

[[ADR-0021]] took the opposite call for `## Options` and was right to: an options section is required of any decision that offers a choice, so it belongs in the template uncommented. A `## Rule` section is required of a *subset* of decisions and is meaningless on the rest — and worse, **the heading's presence is the marker** under [[ADR-0023]]. An uncommented `## Rule` heading in the template would mark every ADR authored from it as a rule-ADR, and `DECISION-RULE` would then report every one of them. The comment is not a stylistic preference; it is what stops the template from arming the check against its own output.

## Definition of Done

- [ ] `docs/__templates__/adr.md` carries the three headings inside an HTML comment, with a one-line pointer to `tools/instructions/DECISIONS.md` for the semantics — and restates none of them.
- [ ] `docs/__templates__/SCHEMAS.md` carries one sentence naming the convention and linking to `DECISIONS.md`.
- [ ] An ADR authored from the template **without** using the block produces zero new validator findings, verified against a fixture note rather than asserted.
- [ ] An ADR authored from the template **with** the block uncommented and filled in also validates clean.
- [ ] `bash tools/scripts/validate-docs.sh` clean in `project-os`.

## Notes

Both files are template-owned and sync downstream, so the fixture check matters more than it looks: a template that emits a note the validator dislikes breaks eleven repos at once, and the first one to notice will be whichever repo authors its next ADR.

Check whether the ADR template in `project-os-dev`'s own `docs/__templates__/adr.md` is the same file — it is currently the older version, carrying `## Alternatives` and no `## Options`, which is a symptom of this repo being a sync behind rather than a second thing to edit. Do not fix it here; it arrives via `sync-project-os.sh`.
