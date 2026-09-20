---
type: "[[issue]]"
id: ISS-0074
aliases: ["ISS-0074"]
title: "A feature scaffolded from the template has no acceptance or design gate, and no place to record its review"
status: open
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-20
updated: 2026-09-20
source: ["The FEAT-0034 review of 2026-09-20, via fleet-file-drift.py", "project-os-cockpit .project-os-sync: 'Drop this line when the template carries them'"]
reported_by: review
question: ""
severity: medium
component: "docs/__templates__"
parent: ""
related: ["[[TASK-0146-The-Four-Findings-Round-One-Left]]", "[[FEAT-0037-Every-Repo-Can-Take-The-Template-Again]]"]
tests: []
---

# A feature scaffolded from the template has no acceptance or design gate, and no place to record its review

## Problem

Anyone starting a feature from `docs/__templates__/feature.md` gets a note with no `acceptance:`, no `design:`, and no `reviewed_by:` or `review_date:`. `project-os-cockpit` added all four to its own copy and has carried a `keep_local:` exception ever since, so its features cannot be scaffolded from the template the rest of the fleet uses. The exception's own note says what is owed: *"Drop this line when the template carries them."*

`QUALITY.md` tells an author to record a review verdict in the reviewed note's frontmatter, and the template a feature is scaffolded from offers no field for it. Every feature note in this repo that carries `reviewed_by:` has it because someone typed it in by hand.

## Evidence

`project-os-cockpit/.project-os-sync`:

> `docs/__templates__/feature.md` — keeps the `acceptance:` gate (FEAT-0064) and `design:` fields the template lacks (project-os-dev TASK-0135). Drop this line when the template carries them.

`diff` against the template, 2026-09-20: the cockpit's copy has ten lines the template does not, covering `acceptance:` (the FEAT-0064 gate, stamped `requested` at close-out and `accepted` only by a completed acceptance run) and `design:` (the FEAT-0070 gate, which warns rather than blocks when a feature leaves the pending band against an unaccepted design), plus `reviewed_by:` and `review_date:`.

Found by `tools/scripts/fleet-file-drift.py` on 2026-09-20. It was already recorded as a kept divergence by [[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template|TASK-0142]] on 2026-09-19; what nobody had was an item that would come back.

## Why it matters

The divergence is invisible in the ordinary run of things. A `keep_local:` line reads as settled, and the work it defers has no note, no owner and no status. This one has waited since FEAT-0064.

It also means the two repos disagree about what a feature *is*. A feature scaffolded in the cockpit can carry an acceptance gate; the same feature scaffolded anywhere else cannot.

## What a fix looks like

Carry the cockpit's four fields into the template's `feature.md`, with the comments that explain them, check that the validator's `DESIGN-GATE` and acceptance checks read them the same way in both repos, then drop the `keep_local:` line from `project-os-cockpit/.project-os-sync` and let the next sync take the template's copy.

The fields are optional and default to empty in the cockpit's copy, so adding them should change nothing for a repo that ignores them — but that is a claim to verify, not to assume, because the validator's gates key on them.
