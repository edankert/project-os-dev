---
type: "[[task]]"
id: TASK-0044
aliases: ["TASK-0044"]
title: "Sync manifest with baseline divergence detection + fleet-wide validator"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-07-17
updated: 2026-07-17
verification_waiver: "docs/tooling change set; verified mechanically — dry-run against project-os-dev (baseline resolution: 11 diverged files fast-forward with --baseline 77b4d5e), validate-fleet table over 10 repos"
source: []
parent: "[[FEAT-0010-Template-Completeness-Program]]"
fixes: []
effort: L
due: ""
depends: [TASK-0041]
blocks: []
related: []
tests: []
waiver_expires: 2026-10-23

---

# Sync manifest + fleet validator

## Definition of Done

- [x] `tools/sync/MANIFEST.yaml` (or equivalent) declares per-path ownership: template-owned, project-owned, merge-required.
- [x] `sync-project-os.sh` consumes the manifest: byte-match against the recorded baseline template SHA ⇒ safe overwrite; local divergence ⇒ skip + report (mechanizing the hand recipe from the 2026-07-05 rollout); baseline SHA recorded per repo after sync.
- [x] `tools/scripts/validate-fleet.sh` runs the docs validator across all SNAPSHOT-bearing repos under a root and prints an aggregate per-repo summary (errors/warnings/waivers).
- [x] SYNCING.md rewritten around the manifest; clobber-hazard list from the fleet memory encoded in the manifest rather than tribal knowledge.
