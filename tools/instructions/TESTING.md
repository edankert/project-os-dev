---
type: instruction
id: INSTR-TESTING
status: active
owner: group:maintainers
created: 2026-03-16
updated: 2026-09-03
tags: [instructions, testing]
---

# Acceptance test rules

The three acceptance test sections, their lifecycle, and release gating. There is no tier system: a check's section is derived from what it covers and who executes it.

## The three sections

A check is not filed into a section. Its section is computed from two fields it carries: `covers:` says what it is about, `command:` says who executes it (ADR-0034). **Precedence:** a non-empty `command:` makes it an automated test; otherwise a `covers:` naming an `ISS-*` makes it a regression test; otherwise it is a feature test.

### Feature tests — re-checked when behaviour changes
- Asserts *the system does X*, a standing claim about current behaviour; `covers:` names a `FEAT-*`.
- Never removed, and **invalidated when a change overlaps its scope**. The only section that is.

### Regression tests — completed once
- Asserts *this defect was fixed*, a claim about a past event; `covers:` names the `ISS-*`.
- Discharged once, by a person completing it or by a `command:` that makes it automated. A later change does not re-open it: nothing a change does can falsify a claim about the past. Without the `ISS-*` link it is read as a feature test.

### Automated tests — executed by CI
- Carries a non-empty `command:`; it is here because a machine executes it, and leaves when the command is removed.
- **Carries no verdict** (`STATUSES.md` `[[test]]`); a red run is a red build.

## Lifecycle rules

### When to create
1. **New feature implemented**: a feature test on the user-visible behaviour, naming the `FEAT-*` in `covers:`.
2. **Bug fixed**: a regression test that reproduces the bug and verifies the fix, naming the `ISS-*` in `covers:`.
3. **A check a machine can execute**: give it a `command:`. That is the whole of automating it; nothing is moved or re-filed.

### When to invalidate (mark for re-check)
- Feature tests only, and only those whose scope the change overlaps: a change to `WorkoutViewModel` invalidates workout checks, not Bluetooth checks.
- **Say which change did it, in the same action**: the invalidation is a dated event in the release ledger naming the check and the change (`TAXONOMY.md`, "Acceptance outcomes (the ledger's vocabulary)"), and it is refused without a change id; no field on the note records it (ADR-0037). Reason: clearing a tick otherwise destroys the only record the check ever passed, and the re-check never happens (measured in project-os CHG-20260903-Instruction-Weight).
- Best done at the close-out of the work that caused it, as one sweep over the areas touched.
- A regression test is not invalidated by a later change; a returned defect files a new issue.

### When to remove
- **Nothing removes a check.** A check whose subject is gone goes `retired`; one a machine now covers gets a `command:`. Reason: a deleted check cannot report that its covering test was renamed.

### Unit test replacement
- When unit tests cover a check's logic, give the check their `command:`. If it later stops resolving, the check reports itself as broken and returns to the manual list.

## Where the acceptance suite lives

A repo stores its suite one of two ways, never both.

**Notes (current).** One check per note: `type: [[test]]`, `level: acceptance`, id `TST-*`, stored per `LIFECYCLE.md` "Test storage", from `../../docs/__templates__/test.md`. `status:` is the lifecycle (`draft`/`active`/`retired`); the verdict is not on the note (`STATUSES.md` `[[test]]`). The section is derived and never written down. See `SCHEMAS.md` `test.md` ("Acceptance fields") and `STATUSES.md` `[[test]]`.

**One document (older).** `docs/tests/ACCEPTANCE_TESTS.md`, from `../../docs/__templates__/acceptance-tests.md`: `# Feature tests`, `# Regression tests` and `# Automated tests`, grouped by area, one `- [x] **Test Name:** procedure and expected result` row per check (automated rows have no checkbox). Everything in this file applies to it. A repo that migrates to notes deletes the document in the migration commit, because two records of one thing drift and git holds the old one.

## Test adequacy (who verifies the tests?)

A guarding test that cannot fail does not guard, and LLM-authored tests share the blind spots of the LLM-authored fix. Every regression test, and any `TST-*` gating a terminal status, carries adequacy evidence in its note:

- **Minimum bar:** show the test fails when the fix is reverted or broken, in the note's Adequacy section or `adequacy:` field.
- **Stronger bar (when tooling exists):** mutation testing over the guarded code, score in `mutation_score:`, tool and command in the evidence (`mutmut`, Stryker, `cargo-mutants`, PIT, `muter` by stack).
- **Independence:** a test created alongside the fix it guards gets an independent review (`../skills/independent-review/SKILL.md`).
- **Cadence:** mutation scores consistently above about 80% justify checking less often; below that, check every guarded fix.

## Release gating

- A release is **blocked** while any manual check is unsettled.
- An automated test never enters the manual list; CI gates it. A **broken command** returns its check to the manual list, because nothing is verifying it.
- A check that cannot be completed (a third-party key unavailable, for example) may be a **release exception**, documented in the release note with justification.

## Relationship to TST-* notes

- `TST-*` notes, stored per `LIFECYCLE.md` "Test storage", are individual test specifications with frontmatter, procedure and evidence.
- **An acceptance check is a `TST-*` note at `level: acceptance`** (ADR-0031; the retired `check` type is `TAXONOMY.md`, "`check` — retired").
- `level:` is a spectrum: a `unit` test is a pytest module, an `acceptance` test is a thing a person does, and a `command:` moves a note along it.
- An acceptance test rests at `active` (`STATUSES.md` `[[test]]`) and owes no separate review (`QUALITY.md`, "Independent review (clean-context)").
