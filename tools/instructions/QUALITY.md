---
type: instruction
id: INSTR-QUALITY
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, quality]
---

# Quality and close-out rules

These rules define what “done” means for work tracked in this documentation system.

## Minimum close-out for any implemented task
- Update the task note status to `done`.
- Update `../../SNAPSHOT.yaml`:
  - set task status to `done`
  - update `focus` (clear or move to next task)
  - update related item statuses if appropriate (issue fixed/closed, feature progressed)
- If behavior/paths/contracts changed, create a `CHG-*` note and link it.

## Documentation Fidelity
- Ensure `metrics` in `../../SNAPSHOT.yaml` accurately reflect the count of `done` features and tasks.
- Verify that every item in the snapshot has a valid `file` path that exists on disk.
- Discrepancies between the filesystem and the snapshot are considered a build failure — literally: `tools/scripts/validate-docs.sh` exits non-zero on them and runs at three mechanical layers (session Stop hook, git pre-commit via `tools/scripts/install-git-hooks.sh`, and CI via `.github/workflows/validate-docs.yml`).
- **Mechanical enforcement:** run `bash tools/scripts/validate-docs.sh` to check snapshot↔filesystem agreement, frontmatter/status consistency, counter integrity, link-graph integrity, and the verification invariant. Convention-only rules get silently skipped under context pressure; the validator does not.
- **Reconciliation:** Use the `snapshot-sync` skill (`../skills/snapshot-sync/SKILL.md`) to reconcile any drift the validator reports; use `../skills/docs-audit/SKILL.md` for the semantic (cross-document) consistency the validator cannot check mechanically.

## Verification gating (tests)
- Do not mark an implementation task `done` unless verification is complete:
  - If verification is automated: link to the relevant `[[test]]` and ensure it is `status: passing` (and record evidence in the test note).
  - If verification is manual: the LLM must create a `[[test]]` note with a clear procedure; a human runs it and reports results; the LLM then updates the test to `passing`/`failing` with evidence.
- Do not mark an issue `closed` unless the verifying test(s) are `passing` (use `fixed` for “implemented but not yet verified”).
- Do not mark a requirement `verified` unless the verifying test(s) are `passing`.
- Do not mark a feature `done` unless its required tasks are `done` and required tests are `passing`.

- If a terminal status must be set without passing tests (docs-only chore, config-only change), record an explicit `verification_waiver: <reason>` in the note frontmatter. The waiver is a logged artifact (the validator reports it as a warning); silent skips are a build failure.

## Independent review (different-model)
- Any change that creates or updates a `TST-*` or `CHG-*` note, and any transition to requirement `verified` or feature `done`, requires an independent review pass per `../skills/independent-review/SKILL.md` — a different model family or a human, never a second pass by the authoring model.
- Record the outcome in the reviewed note frontmatter (`reviewed_by`, `review_date`, `review_verdict`).

## Verification expectations (generic)
- Prefer a reproducible command, test, or check that demonstrates the change.
- If verification is manual, record exact steps and expected outputs in the task/workflow note.
- For tests guarding fixes, record adequacy evidence (does the test fail when the fix is broken?) — see `TESTING.md`, "Test adequacy".
