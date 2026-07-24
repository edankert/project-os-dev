---
type: "[[feature]]"
id: FEAT-0006
aliases: ["FEAT-0006"]
title: "First-class release tracking"
status: done
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
goal: "Add REL-* note type for full release records plus a lightweight releases section in SNAPSHOT.yaml for agent access"
tags: [release-tracking]
---

# First-class release tracking

## Goal
Add a `[[release]]` note type (REL-*) that captures what was shipped, when, and with what verification — plus a lightweight `releases` section in SNAPSHOT.yaml so agents can instantly see the latest release without scanning notes.

## Design (Option D)
- REL-* notes for the full record (features, changes, tests verified, previous release link)
- `releases.latest` + `releases.history` in SNAPSHOT.yaml for quick agent access
- Release-verification skill creates REL-* notes as part of the gating workflow
- Releases dashboard and base for human visibility
