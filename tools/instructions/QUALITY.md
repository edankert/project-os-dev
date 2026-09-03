---
type: instruction
id: INSTR-QUALITY
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-03
tags: [instructions, quality]
---

# Quality and close-out rules

These rules define what "done" means for work tracked in this documentation system.

> **State vocabulary and per-type gates are normative in `STATUSES.md`**, which also records who writes each status. This file describes the close-out process; where the two disagree, `STATUSES.md` wins and the disagreement is a bug to file.

## Minimum close-out for any implemented task
- Set the task note to `done`; the snapshot follows through the sync script.
- Update `focus` (clear it or move to the next task) and the statuses of related items (issue fixed, feature progressed).
- If behaviour, paths or contracts changed, create a `CHG-*` note and link it.

## Documentation Fidelity
- `metrics.counts` in `../../SNAPSHOT.yaml` must match the computed counts (definitions in `SNAPSHOT.md`); `bash tools/scripts/validate-docs.sh --fix-metrics` rewrites the block when it drifts.
- Every snapshot item's `file` path must exist on disk.
- A discrepancy between the filesystem and the snapshot is a build failure: `tools/scripts/validate-docs.sh` exits non-zero on it at the session Stop hook, at pre-commit (`tools/scripts/install-git-hooks.sh`) and in CI (`.github/workflows/validate-docs.yml`). It checks snapshot-to-filesystem agreement, frontmatter and status consistency, counter integrity, link-graph integrity and the verification invariant. Reason: convention-only rules get skipped under context pressure; the validator does not. Reconcile drift with `../skills/snapshot-sync/SKILL.md`; `../skills/docs-audit/SKILL.md` covers what the validator cannot.

## Verification gating (tests)
- The gate on each terminal status (task `done`, issue `fixed`, feature `done`, requirement `implemented`) is stated once in `STATUSES.md`, "The contract at a glance". This section says how to satisfy it.
- Verification is an automated test linked and `passing`, or a manual `[[test]]` note with a clear procedure that a human has run and whose result the note records.
- Do not tick an acceptance criterion the delivered system does not satisfy. If the work departed from a criterion, amend, narrow or supersede it with recorded rationale (`../skills/close-out/SKILL.md`, step 3 "Requirement advancement"); ticking to fit is a fake `done`.
- A `deferred` task never resolves a feature's scope: descope it through the deferral procedure (`STATUSES.md`, "Deferral and re-adoption"); never flip it to `done` or drop it from the list.
- If a terminal status must be set without passing tests (a docs-only or config-only change), record `verification_waiver: <reason>` in the note frontmatter. The validator reports the waiver as a warning; a silent skip is a build failure.

## Independent review (clean-context)
- **The gate is keyed on a status, not on a note being touched**: a `TST-*` reaching `passing`, a requirement reaching `implemented`, a feature reaching `done`. Each requires an independent review pass per `../skills/independent-review/SKILL.md`.
- **Independent means a clean context**: a session that starts from the notes and the diff alone, never the author's reasoning trace, and is not the session that authored the work. A human pass also satisfies this and remains the strongest option. Self-review is forbidden.
- Model family is not the gate (ADR-0013 records the experiment). The boundary is session and context, not vendor.
- **A `CHG-*` note does not owe a review** (ADR-0019): the change itself is reviewed at the three gates above while the work is live, and reviewing the note later reviews the prose.
- **An acceptance test does not owe a review either.** It rests at `active` and never reaches `passing` (`STATUSES.md` `[[test]]`); the review of an acceptance test is the walk, and gating it would ask for the same evidence twice.
- Record the outcome in the reviewed note's frontmatter (`reviewed_by`, `review_date`, `review_verdict`).

## Verification expectations (generic)
- Prefer a reproducible command, test or check that demonstrates the change.
- If verification is manual, record the exact steps and expected outputs in the task or workflow note.
- For a test guarding a fix, record adequacy evidence (does the test fail when the fix is broken?): `TESTING.md`, "Test adequacy".
- The message the user reads is held to the same rule as the notes: before reporting progress, audit each claim against a tool result from this session, and report only work you can point to evidence for. If a test fails, say so with its output; if a step was skipped, say that; if something is not yet verified, say so. Reason: an evidence-free claim in chat is the fake `done` that ticked-with-evidence criteria keep out of notes.
