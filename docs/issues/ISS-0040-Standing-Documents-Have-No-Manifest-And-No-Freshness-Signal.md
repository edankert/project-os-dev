---
type: "[[issue]]"
aliases: ["ISS-0040"]
id: ISS-0040
title: "Every project-os repo ships eight one-per-project documents, 94% of them are stale or undated fleet-wide, and nothing names the set, checks it is complete, or reports its freshness"
status: open
severity: medium
owner: user:edwin
created: 2026-08-10
updated: 2026-08-10
component: tooling
source: ["project-os-cockpit ISS-0125 / REQ-0033 / FEAT-0091", "fleet measurement over 12 repos, 2026-08-10"]
phase: "[[PHASE-999]]"
parent: ""
related: [ISS-0026]
tests: []
---

# Standing documents have no manifest and no freshness signal

## The class

The template ships eight documents that are **one per project, carry no lifecycle, and are written for a human to read**: `README`, `INDEX`, `ARCHITECTURE`, `GLOSSARY`, `OWNERSHIP`, `DESIGN`, `STYLEGUIDE`, `PHASES`.

They are not work, not decisions, not a record of something that happened. They are the standing answer to *what is this project*.

## Measured across all twelve repos, 2026-08-10

| | |
|---|---|
| documents present | **90** of a possible 96 |
| stale (`updated` > 90 days) | 74 |
| carrying no `updated:` at all | 11 |
| **stale or undated** | **85 of 90 — 94%** |
| still recognisably template stubs | 12 |
| repo missing five of the eight | `yourtrainer-mcp` |

Every repo tells the same story: seven or eight present, seven stale. `obsidian-supernote-sync` has eight present and eight stale.

**So the set is not missing — it is present and abandoned.** Nothing names it, nothing checks it, nothing shows it, and a document nobody is ever asked about is a document nobody updates.

## Three defects, one cause

**1. They carry a lifecycle status they do not have.** `active` is in the **work-in-flight band**, so these documents are coloured, sorted and counted as work somebody is doing. In `project-os-cockpit` that made 19 of the 44 rows its Active view called `Doing` into references and a glossary. A status field on a document with no lifecycle can only say something false or say nothing.

**2. Their `updated:` dates lie, in a specific and repeatable way.** Two of the eight carried dates predating content they visibly contain — edited without the date being touched. That is not carelessness; it is what happens when no surface ever reads the field.

**3. `reference` does three unrelated jobs.** Of 21 `reference` notes in one repo: five are these singletons, nine are container-directory `README.md` signposts, four are templates, and one is a genuine reference document.

## Proposed

**A manifest, not a type.** A type models an open population — there will be a ninth feature, a fortieth issue. There will never be a second glossary. The set is fixed and small, so it is data.

**Two layers, and the split is a requirement of the sync rather than a preference.** `sync-project-os.sh` copies `tools/instructions/`, `tools/skills/`, `docs/__templates__/` and `docs/__bases__/` **wholesale** — so a project-specific entry living in any of those is silently destroyed at the next sync. The base set must therefore be template-owned, and **project extensions must live in `SNAPSHOT.yaml`**, which is never synced and sits in the repo being described.

`SNAPSHOT.yaml` already has a `docs_system:` block carrying `source_of_truth`, `instructions` and `references` — and nothing reads it. `docs_system.standing` gives it a first consumer rather than inventing a place beside it.

**Singularity is a check, not an assumption.** "Only one appears in the repo" is the defining property, so it is the one worth asserting. An entry resolving to two files means the set has quietly become a type. A resolver returning the first match would hide that forever.

**No lifecycle status; `updated:` is the state.** This also answers, in the other direction, whether `reference` / `glossary` / `architecture` / `dashboard` need entries in the validator's status table: they need to be recorded **status-free**.

**Four findings, reported distinctly** — missing · ambiguous · still-a-stub · stale. Collapsing them loses the only useful part, since what to do about each differs completely.

**Staleness warns and never blocks.** The pattern ADR-0011 established for independent review. A build that fails because a glossary is old gets the check disabled within a week, which is worse than a warning occasionally skipped.

## Reference implementation

`project-os-cockpit` has this working: `src/project_os_cockpit/standing.py` (manifest, resolver, checks) and `tests/test_standing_documents.py` (13 assertions, property-based rather than membership-based). Its `STALE_AFTER_DAYS = 180` carries its reasoning — these do not decay like a manual test at 60 days; what is worth catching is abandonment, and 180 flags the two documents untouched since creation while leaving one revisited twice a year alone.

The rule lives in the app there rather than in `validate-docs.py` because that file is template-owned and held byte-identical (ISS-0026) — guarded locally, proposed here, which is the split ISS-0069 and the PHASE-999 rule both took.

## Why this belongs upstream

`project-os-cockpit` holds **8 of the 90** documents. Fixing only those leaves 82 stale in eleven other repos, and the validator logic that would report them is template-owned. A local-only fix is both the smaller win and the one that drifts at the next sync.

## Re-measure after

85 of 90 stale or undated is the **before**. The proposal is only worth adopting if that number moves.
