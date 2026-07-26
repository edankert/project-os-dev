---
type: "[[requirement]]"
id: REQ-0009
aliases: ["REQ-0009"]
title: "Releases must be tracked as first-class notes with traceability"
status: implemented
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
owner: user:edwin
created: 2026-03-08
updated: 2026-07-24
priority: medium
acceptance:
  - REL-* notes capture version, tag, date, included features, changes, and verified tests
  - Each release links to its previous release for continuity
  - SNAPSHOT.yaml carries a lightweight releases.latest/releases.history block for agent quick-lookup (ships commented out in the template; uncommented at first release)
  - Release-verification skill creates REL-* notes as part of the gating workflow
implements: ["[[FEAT-0006]]"]
tags: [release-tracking]
tests: []
---

# Release tracking requirement

Releases must be tracked as first-class documentation notes (REL-*) with full traceability to features, changes, and verified tests. The SNAPSHOT.yaml must provide a lightweight `releases` section so agents can determine the current release state without scanning notes.

## Acceptance Criteria

- [x] `REL-*` notes capture version, tag, date, features, changes and verified tests — evidence: `docs/__templates__/release.md` frontmatter (`version`, `tag`, `date`, `features`, `changes`, `tests_verified`), schema at `docs/__templates__/SCHEMAS.md` with `tag`/`date` required.
- [x] Each release links to its previous release — evidence: `previous_release` field in the release template and `SCHEMAS.md` ("the prior `REL-*` for rollback targeting"); consumed by the rollback procedure in `release-verification/SKILL.md`.
- [x] `SNAPSHOT.yaml` carries a lightweight `releases.latest`/`releases.history` block for agent quick-lookup — evidence: the block ships commented out in the template snapshot under "Latest release context for agents", is now documented in `tools/instructions/SNAPSHOT.md` ("Required top-level keys"), and is uncommented at the first release by `release-verification/SKILL.md`.
- [x] The release-verification skill creates `REL-*` notes as part of the gating workflow — evidence: `tools/skills/release-verification/SKILL.md` step 9 "Create/update release note" (allocates from `counters.REL`, creates the note, sets `status: staged`, updates `items.releases` and `releases.latest`), gated behind steps 6 and 8.

## Amendments (2026-07-21)

**Criterion 3** was narrowed: the `releases.latest` block ships **commented out** in the template rather than as an active key, because a template has no releases to describe. The verification also found it was documented *nowhere* — `SNAPSHOT.md` described `items.releases` and `releases_total` but never the `releases.latest`/`releases.history` block. That documentation gap was closed as part of this backfill rather than amended away.

This note previously had **no `## Acceptance Criteria` section at all** (a 3-sentence prose body only), so the four frontmatter criteria had no verification record. The section above was created during this backfill.
