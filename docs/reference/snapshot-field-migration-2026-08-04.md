---
type: "[[reference]]"
id: REFERENCE-SNAPSHOT-FIELD-MIGRATION
title: "Snapshot field migration record: values replaced when title/goal became derived"
status: active
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
scope: "project"
source: ["FEAT-0022", "TASK-0084", "ADR-0018"]
related: []
---

# Snapshot field migration record

Every `title:`/`goal:` value **project-os-dev**'s `SNAPSHOT.yaml` carried before ADR-0018 made those
fields derived, where it differed from the note that now supplies it. Includes entries
later removed by retention, so this is the complete replaced set, not just the survivors.

Reconstructed from `52328fed~1` after the first pass wrote an incomplete record: the rollout
re-ran the recorder *after* migrating, when there was no drift left to capture.

30 value(s) replaced.

## FEAT-0020 (`goal`)

- **was:** Make every ticked box a machine-readable claim with a strength and a revision — implements ADR-0014. Not yet planned: four open questions in the note, blast radius being the load-bearing one.
- **now:** Make every ticked box in the fleet a machine-readable claim with a strength and a revision, so that 93.9% of claims stop being unrankable prose and a claim can go stale without anyone editing the note.

## FEAT-0007 (`goal`)

- **was:** Relationship model for linking notes. NOTE: the semantic-named-field design (implements/fixes/affects/specifies/validates) was reverted in May 2026; the model in force is specified by REQ-0015
- **now:** Relationship model for linking notes. NOTE: the semantic-named-field design was reverted in May 2026; the model in force is specified by REQ-0015

## FEAT-0009 (`goal`)

- **was:** Three-pane Obsidian layout: left sidebar for navigation (features, phases, issues), center editor, right sidebar for dynamic context (tasks, requirements, tests related to active note)
- **now:** Three-pane Obsidian layout: left sidebar for navigation, center editor, right sidebar for dynamic context using this.file

## FEAT-0010 (`goal`)

- **was:** Close the gaps found by the 2026-07-17 full review: template consistency debt, underused native Claude Code machinery, cockpit verification observability, fleet-blind sync tooling, unwired external tools
- **now:** Close the gaps found by the 2026-07-17 full review of project-os: internal consistency debt, underused native Claude Code machinery, missing verification observability in the cockpit, fleet-blind sync tooling, and unwired external tools

## TASK-0024 (`title`)

- **was:** Update note templates (task, issue, requirement, test, feature)
- **now:** Update note templates with new relationship fields

## TASK-0027 (`title`)

- **was:** Update top-level .base dashboards to reflect renamed fields
- **now:** Update top-level .base dashboards

## TASK-0028 (`title`)

- **was:** Update skills that create/link notes (feature-scaffold, issue-intake, task-breakdown, test-authoring)
- **now:** Update skills that create or link notes

## TASK-0029 (`title`)

- **was:** Update SNAPSHOT.md and migrate existing snapshot entries
- **now:** Update SNAPSHOT.md schema and migrate existing entries

## TASK-0035 (`title`)

- **was:** Update skills to create/reference phase notes instead of integers
- **now:** Update skills to create and reference phase notes

## ISS-0031 (`title`)

- **was:** The startup instruction prescribes one method — read the whole snapshot — for two different needs, and agents comply 5 times in 260
- **now:** The startup instruction prescribes one method — read the whole snapshot — for two different needs, and agents comply with it 5 times in 260; whether the 255 that grep instead are actually oriented is unmeasured

## ISS-0030 (`title`)

- **was:** Retention is a policy nothing performs, configured by three flags no code reads, and its normative rule still names the `closed` status ADR-0008 deleted
- **now:** Retention is a policy nothing performs, configured by three flags no code reads, and its normative rule still names the `closed` status ADR-0008 deleted — so snapshots accumulate until most of what a query matches is finished work

## ISS-0029 (`title`)

- **was:** LIFECYCLE says when a phase is needed, never when one is too small
- **now:** LIFECYCLE says when a phase note is needed and never when one is too small, so an agent under the document-first rule mints a phase per request — measured at nine in a day against nine in the preceding twelve weeks

## ISS-0028 (`title`)

- **was:** Close-out says fix what the validator reports and has no answer for 'cannot fix'
- **now:** Close-out says to run the validator and fix what it reports, and has no answer for 'cannot fix' — which is exactly the case that needs a human and therefore the one that must leave a record

## ISS-0027 (`title`)

- **was:** Nothing re-homes an item's phase at close-out, so delivered work stays in the PHASE-999 parking lot forever
- **now:** Nothing re-homes an item's phase at close-out, so work delivered without a plan stays in the PHASE-999 parking lot forever — 16 of 19 notes naming it in one repo are terminal, and the phase strip draws 16 `delivered` squares inside a phase titled 'Future'

## ISS-0026 (`title`)

- **was:** A TST note's ## Coverage section is hand-written, nothing checks it against the suite, and other notes cite its entries as evidence
- **now:** A TST note's ## Coverage section is a hand-written register of its own suite's assertions that nothing derives or checks, and other notes cite its entries as evidence — one register was wrong in three consecutive review rounds

## ISS-0025 (`title`)

- **was:** review_verdict is checked for presence but never for a defined value, so any string reads as a satisfied review
- **now:** The validator checks that review_verdict is PRESENT but never that it is a DEFINED value, so any string reads as a satisfied review — 10 notes in one repo carried `CLOSE`, which QUALITY.md does not define

## ISS-0023 (`title`)

- **was:** Round two on ADR-0017: the three-question test still asks who writes the field, two notes quote the superseded clause 3, and ISS-0021's provenance paragraph mis-cites TASK-0070
- **now:** Round two on ADR-0017: the frontmatter three-question test still asks who writes the field, which the amended clause 3 abandoned, so it fails the two mechanisms the body calls compliant; two notes still quote the superseded clause; and ISS-0021's new provenance paragraph mis-cites TASK-0070 and claims months of drift where the tree shows three days

## ISS-0022 (`title`)

- **was:** ADR-0017 review findings: it ratifies ADR-0014 while that is only proposed, clause 3 has no stated subject, and a consequence names ISS-0020 for ISS-0019's defect
- **now:** ADR-0017 is accepted while ratifying ADR-0014, which is only proposed; clause 3 has no stated subject, so read literally it forbids the waiver and manual-test paths the same ADR says it preserves; and a consequence names ISS-0020 for ISS-0019's defect

## ISS-0021 (`title`)

- **was:** Verification waivers expire individually but nothing bounds how many are outstanding; all 19 in this repo expire 2026-10-23, the migration default
- **now:** Verification waivers expire individually but nothing bounds how many are outstanding, and a batch stamped with one date is indistinguishable from waivers considered one at a time — all 19 in this repo expire 2026-10-23, the migration default no waiver has diverged from since

## ISS-0020 (`title`)

- **was:** Nothing requires a TST-* to carry a command:, and no metric distinguishes executable from manual tests
- **now:** Nothing requires a `TST-*` to carry a `command:`, and no metric distinguishes executable from manual tests — so the project cannot report how much of its verification actually runs

## ISS-0019 (`title`)

- **was:** VERIFY iterates only over tests that exist, so terminal items with zero linked tests and no waiver pass silently — 52 registered items in this repo
- **now:** VERIFY iterates only over tests that exist, so an item reaching terminal with zero linked tests and no waiver passes silently — 52 registered items in this repo did exactly that, against QUALITY.md's stated rule

## ISS-0018 (`title`)

- **was:** The link graph stops at the docs boundary: no requirement names the code that implements it, so `implemented` is asserted rather than covered
- **now:** The link graph stops at the docs boundary: no requirement names the code that implements it, so `implemented` is asserted by the agent seeking the transition and an unimplemented requirement is undetectable

## ISS-0017 (`title`)

- **was:** A review verdict never expires: reviewed_by/review_date survive any later edit to the note they approved
- **now:** A review verdict never expires: `reviewed_by`/`review_date`/`review_verdict` survive any later edit to the note they approved, so an approved note and a rewritten-since-approval note are indistinguishable

## ISS-0016 (`title`)

- **was:** Completeness registry keyed on id() (defeated by CPython constant dedup); total metrics skipped their prefix check
- **now:** The completeness registry was keyed on id(), which CPython constant-dedup defeats; and every total metric skipped its prefix check, so a mistyped prefix silently read zero

## ISS-0014 (`title`)

- **was:** validate-docs.py ships its own second half twice: lines 1560-2560 duplicate 556-1556 verbatim, fleet-wide; the 'no inline status literal remains' claim is false; the walker's boundary prose still overclaims on dict, underscore names and nesting
- **now:** validate-docs.py ships its own second half twice: lines 1560–2560 duplicate 556–1556 verbatim, fleet-wide; the 'no inline status literal remains' claim is false; the walker's boundary prose still overclaims on dict, underscore names and nesting

## REQ-0009 (`title`)

- **was:** Releases must be tracked as first-class notes with traceability to features, changes, and tests
- **now:** Releases must be tracked as first-class notes with traceability

## REQ-0010 (`title`)

- **was:** Child notes must use semantic named relationship fields that support multiple values and are filterable by Obsidian Bases
- **now:** Named relationship fields with multi-parent support and Bases filterability

## REQ-0011 (`title`)

- **was:** Phases must be navigable first-class notes with contextual dashboards showing all items in that phase
- **now:** Phases must be navigable first-class notes with contextual dashboards

## CHG-20260725-State-Model-Simplification (`title`)

- **was:** PHASE-0002 complete: taxonomy collapsed 64 to 53 and migrated across 10 repos; snapshot status derived from notes; test status stamped by execution; grandfather ledger replaces date-based gating
- **now:** PHASE-0002 complete: status taxonomy collapsed 64→53 and migrated across 10 repos; snapshot status derived from notes; test status stamped by execution; grandfather ledger replaces date-based gating

## ADR-0017 (`title`)

- **was:** A claim about whether the software works is derived from execution where possible, labelled and dated where not, and never written by the party seeking the transition it gates
- **now:** A claim about whether the software works is derived from execution where execution is possible, labelled and dated where it is not, and in neither case trusted on the unmarked word of the party seeking the transition it gates

