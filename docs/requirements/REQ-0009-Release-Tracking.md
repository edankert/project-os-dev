---
type: "[[requirement]]"
id: REQ-0009
title: "Releases must be tracked as first-class notes with traceability"
status: approved
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
priority: medium
acceptance:
  - REL-* notes capture version, tag, date, included features, changes, and verified tests
  - Each release links to its previous release for continuity
  - SNAPSHOT.yaml provides lightweight releases.latest for agent quick-lookup
  - Release-verification skill creates REL-* notes as part of the gating workflow
implements: ["[[FEAT-0006]]"]
tags: [release-tracking]
---

# Release tracking requirement

Releases must be tracked as first-class documentation notes (REL-*) with full traceability to features, changes, and verified tests. The SNAPSHOT.yaml must provide a lightweight `releases` section so agents can determine the current release state without scanning notes.
