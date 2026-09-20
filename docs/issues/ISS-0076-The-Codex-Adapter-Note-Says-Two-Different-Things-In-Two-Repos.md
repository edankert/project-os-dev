---
type: "[[issue]]"
id: ISS-0076
aliases: ["ISS-0076"]
title: "The Codex adapter is documented two different ways, and the fleet drift check will read red until one wins"
status: open
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-20
updated: 2026-09-20
source: ["tools/scripts/fleet-file-drift.py, 2026-09-20", "[[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template]]: 'Another session is editing it. Out of scope in FEAT-0037.'"]
reported_by: review
question: ""
severity: medium
component: "tools/adapters/codex"
parent: ""
related: ["[[TASK-0146-The-Four-Findings-Round-One-Left]]", "[[FEAT-0032-Codex-Native-Project-Adapter]]", "[[ISS-0074-The-Feature-Template-Lacks-The-Acceptance-And-Design-Fields-The-Cockpit-Uses]]", "[[ISS-0075-Two-Test-Runners-Are-Maintained-Against-Two-Decisions]]"]
tests: []
---

# The Codex adapter is documented two different ways, and the fleet drift check will read red until one wins

## Problem

Someone setting up Codex reads `tools/adapters/codex/ADAPTER.md` and gets different instructions depending on which repo they opened. The template's copy (46 lines) documents the generated files — `.agents/skills/`, `.codex/agents/*.toml`, `.codex/hooks.json` — and how `generate-adapters.py --install-hooks` writes them. `project-os-cockpit`'s copy (55 lines) documents the instruction layer instead — `AGENTS.md` as a cross-tool convention, `LLM_BRIEF.md`, `CONTEXT.md`, the `tools/agents/*.sh` scripts — and says nothing about the generated files.

Neither is stale in the usual sense. Both were edited after they split: the cockpit's in commit `1d16f08` on 2026-09-19, as part of its Codex parity work, and the template's when the native adapter landed.

## Why this one cannot just sit there

This is the only file in the fleet that `tools/scripts/fleet-file-drift.py` reports as real drift, so that check now exits 1 every time anyone runs it. A check that is permanently red is a check people stop reading, which is the failure [[ADR-0011]] ended the permanent warning tier over. The other four divergences it used to report are recorded decisions and are now shown as kept; this one has no decision behind it, only a deferral.

[[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template|TASK-0142]] saw it on 2026-09-19 and left it alone for a good reason at the time — another session had the file open. That reason has expired: the cockpit's copy is committed and its working tree is clean.

## What a fix looks like

Decide what the file is for. The two versions are not competing drafts of the same document; they answer different questions, and both answers are wanted:

- what Codex reads to learn the project (the cockpit's version), and
- what the generator writes and how to install the hooks (the template's version).

The likely resolution is one document covering both, in the template, with the cockpit's instruction-layer sections merged in and its `generate-adapters` sections kept. Then the cockpit takes the template's copy at the next sync and the drift check goes quiet.

If instead the cockpit's version is deliberately its own, it belongs in `keep_local:` in `project-os-cockpit/.project-os-sync` with the reason written down — the same treatment the four other divergences have. What it must not stay is undeclared.
