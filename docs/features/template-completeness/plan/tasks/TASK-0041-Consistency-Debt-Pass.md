---
type: "[[task]]"
id: TASK-0041
aliases: ["TASK-0041"]
title: "Consistency-debt pass in the project-os template"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-07-17
updated: 2026-07-17
verification_waiver: "docs/tooling change set; verified mechanically — validate-docs 0 errors on template + project-os-dev, negative-test of METRICS check passed, release taxonomy enforced (10 real violations detected in your-trainer)"
source: []
parent: "[[FEAT-0010-Template-Completeness-Program]]"
fixes: []
effort: M
due: ""
depends: []
blocks: [TASK-0042]
related: [REQ-0009]
tests: []
---

# Consistency-debt pass in the project-os template

## Definition of Done

- [x] Release lifecycle unified on `draft → staged → released → rolled-back`: STATUSES.md gains a `[[release]]` section, validate-docs.py gains a release entry in ALLOWED_STATUS, release-prep skill drops `published`, SCHEMAS.md documents `release.md` and `plan.md`, SNAPSHOT.md documents the `releases` collection.
- [x] Hook contracts unified on a single HC-* numbering in HOOKS.md; claude-code adapter and hook script headers cite the same codes; "Codex hook-equivalent" framing replaced by tool-neutral contract language.
- [x] Validator recomputes `metrics.counts` and reports discrepancies (with `--fix-metrics` to rewrite them), making QUALITY.md's claim true.
- [x] `tools/adapters/README.md` rewritten to describe all four adapters; `tools/instructions/README.md` index lists all 16 instruction files; TESTING.md gains standard instruction frontmatter.
- [x] NAVIGATION.base issue grouping uses a real field; Bases no longer filter on statuses outside the taxonomy.
- [x] `sync-project-os.sh` no longer copies `tools/cockpit` twice/unguarded.
- [x] `level: acceptance` added to TAXONOMY.md and the test template; `docs/__templates__/acceptance-tests.md` template created and referenced from TESTING.md.
- [x] LIFECYCLE.md close-out step 1 lists the correct terminal statuses.
- [x] Template repo dogfoods its own adapter: `.claude/settings.json` created from `hooks.json`.
