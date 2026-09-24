---
type: "[[issue]]"
aliases: ["ISS-0083"]
id: ISS-0083
title: "A repo that edits a shipped skill is told it has diverged, so the only supported way to customise project-os is to stop receiving updates to the file"
status: deferred
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-22
updated: 2026-09-22
source: ["[[Comparable-Systems-Review-2026-07]] listed this unfiled; [[Comparable-Systems-Spec-Kit-2026-09-22]] re-read the mechanism on 2026-09-22"]
reported_by: agent
question: "Should template-owned instructions and skills resolve through layers instead of being one file that either matches the baseline or has diverged? Options: (a) a per-repo overlay directory that wins over the template copy, with declared precedence; (b) compose rather than replace, with append and prepend strategies as Spec Kit has; (c) decline and keep hand-merge, since twelve repos is a scale hand-merge still fits. Recommendation: (a) alone. It is most of the value, and (b) makes a rule's final text something no single file states, which fights [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]."
severity: medium
component: sync
parent: ""
related: ["[[Comparable-Systems-Spec-Kit-2026-09-22]]", "[[Comparable-Systems-Review-2026-07]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[ADR-0001-Tool-Adapter-Architecture]]"]
tests: []
---

# A repo that edits a shipped skill is told it has diverged

## Problem

`tools/sync/MANIFEST.yaml` gives `tools/instructions/`, `tools/skills/`, `tools/agents/` and `tools/adapters/` the ownership value `template`, which it defines as: overwritten when the downstream copy matches the recorded baseline, and where the copy has diverged, skipped and reported for hand-merge. A project that needs one extra step in one skill has two choices. It can leave the file alone and not have the step, or it can edit the file and then reconcile that edit by hand on every future sync, forever.

There is no third option, and the third option is the one most projects actually need.

## Expected

A project states its additions in a file of its own, the template copy keeps updating underneath it, and the sync has nothing to reconcile.

## Actual

Sync ownership is a single value per path. `template` means the template wins unless you diverged; `merge` means divergence is expected and reported as information rather than reconciled; `seed` means copied once and never again; `project` means never touched. Every value describes who owns *the file*. None of them lets two parties own different parts of the same rule set.

This was recorded in [[Comparable-Systems-Review-2026-07]] as a groomable and not filed: "Spec Kit resolves templates through project overrides, presets, extensions and core defaults, so a repo customises without diverging. project-os's MANIFEST detects baseline divergence and treats it as drift to reconcile."

## Evidence

Spec Kit's `docs/reference/artifacts.md` declares four layers in precedence order: project-local overrides in `.specify/templates/overrides/` win, then installed extensions, then installed presets, then built-in assets, which are always present even when nothing overrides them. Commands, templates and scripts resolve winner-takes-all, with index 0 the winning layer. Hooks stack additively instead, so several can be active at once. Composition strategies are `wrap`, `prepend` and `append`.

Since July the layer set has grown a distribution story: `extensions/catalog.json`, `presets/` and `bundles/catalog.json`, each with a `.community.json` counterpart, so a third party can ship a command set without forking. project-os's nearest equivalent is the adapter directory, which varies the *agent* rather than the project.

## Next Actions

- [ ] Decide (see `question:` in the frontmatter).
- [ ] Measure first: count how many of the twelve repos currently carry a local edit to a `template`-owned path, and how often a sync reports one for hand-merge. If that number is near zero the problem is theoretical and this should be declined.
- [ ] Settle the interaction with [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]] before designing anything. An overlay that adds a rule is fine; an overlay that contradicts the template's copy means two files state the rule and the reader has to know the precedence to know which is live.
- [x] Triaged by Edwin on 2026-09-22 and parked in [[PHASE-999-Parking-Lot|PHASE-999]]. Deferred means still wanted: the `question:` above is the decision re-adoption has to make, not one that is waiting on anyone now.
