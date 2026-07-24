---
type: "[[change]]"
id: CHG-20260724-Verification-Record-Backfill
title: "Requirement verification records made machine-readable — criteria of record in frontmatter, criteria as checkboxes, `tests:` key present"
status: merged
owner: user:edwin
created: 2026-07-24
updated: 2026-07-24
source: ["downstream:your-sudoku"]
commit: ""
pr: ""
impacts: ["docs/requirements/"]
issues: []
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# Verification record backfill

## Why

Raised in `../your-sudoku`, where 97 requirements sat at `implemented` and looked stuck. Two causes: the cockpit rendered `implemented` as if it were done (fixed separately — `../project-os-cockpit` ISS-0023, now synced here), and the requirement notes held their acceptance criteria as prose bullets that no tool could read. The validator's REQ-BOXES check keys off `acceptance:` frontmatter, so criteria living only in the body were invisible to it. This pass applies the same correction here.

## What changed

- **4 requirement notes** touched.
- **0** gained an `acceptance:` frontmatter list — **0 criteria of record** lifted out of prose.
- **0** body bullets became checkboxes, so a criterion can now be ticked individually against evidence.
- **4** notes gained the `tests:` key so a covering `[[test]]` can be linked.

Requirements already at `verified`, `retired`, `superseded`, `cancelled`, or `deferred` were **skipped**: reopening their criteria as unticked boxes would misrepresent work that has already been through close-out.

No criterion was ticked. Ticking requires naming evidence per criterion, which is per-requirement work for whoever knows the coverage — `close-out/SKILL.md`: *"A criterion with no evidence does not get ticked."*

## Impact

Documentation metadata only. No code, no behaviour, no status transitions. `bash tools/scripts/validate-docs.sh` reports no errors.

## Findings

Nearly nothing to do: this repo already kept criteria of record in frontmatter *and* ticked them as checkboxes — it is the reference implementation of the pattern. Only the `tests:` key was missing on 4 notes. 10 further notes were touched and then reverted because the only change would have been an `updated:` date bump with no substantive edit.

No `TST-*` notes were authored: the repo is docs and tooling with no application test surface, and its 15 terminal items already carry explicit `verification_waiver` entries — which is the correct project-os instrument for docs-only work, and it is already in use.

## Documentation Coverage (All Types Considered)

- features / requirements: requirements updated (structure only, no status changes)
- tasks / issues / tests / workflows / decisions / risks: not-applicable
- changes: new
- snapshot: not-applicable (no tracked item changed status)

## Follow-ups

- [ ] Tick criteria against evidence, and link `TST-*` notes, per requirement.
- [ ] Independent review of this change is owed per `QUALITY.md`.
