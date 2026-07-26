---
type: "[[task]]"
id: TASK-0066
aliases: ["TASK-0066"]
title: "Add command, last_run, last_verified and waiver_expires to the test schema and templates"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0016-Executable-Verification]]"
effort: S
due: ""
depends: []
blocks: [TASK-0067, TASK-0068]
related: [REQ-0022, REQ-0023, ADR-0010]
tests: []
---

# Test command schema

## Definition of Done

- [ ] `command:` (optional), `last_run:`, `exit_code:` added to `docs/__templates__/test.md` and `SCHEMAS.md`.
- [ ] `last_verified:` added, required when `command:` is absent.
- [ ] `waiver_expires:` added alongside `verification_waiver:`.
- [ ] `test-authoring/SKILL.md` gains the step: declare a command where one exists, otherwise record `last_verified:` and why the check is manual.
- [ ] `SCHEMAS.md` states plainly that `status` on a test with a `command:` is written by the runner, not by the author.
- [ ] Field names checked against existing frontmatter fleet-wide for collisions.

## Steps

- [ ] Add the fields to the template and `SCHEMAS.md`.
- [ ] Update `test-authoring/SKILL.md`.
- [ ] Grep the fleet's 80 `TST-*` notes for existing uses of these names.
- [ ] Decide the manual-test backfill baseline with TASK-0068 (it is one decision, not two).

## Notes

**Prefer single-word field names** where the meaning survives it — `command`, `expires` — consistent with existing convention in this repo. `last_run` and `last_verified` keep their qualifiers because `run` and `verified` alone would be ambiguous next to `status`.

This task is deliberately schema-only. The runner (TASK-0067) and the expiry rules (TASK-0068) both depend on it, and splitting the schema out means the field names can be settled once, cheaply, before two implementations bake them in.
