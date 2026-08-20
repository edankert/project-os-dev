---
type: instruction
id: INSTR-TESTING
status: active
owner: group:maintainers
created: 2026-03-16
updated: 2026-07-17
tags: [instructions, testing]
---

# Acceptance test rules

This document defines the three acceptance test sections, their lifecycle rules, and release gating requirements. There is no tier system: a check's section is derived from what it covers and who executes it.

## The three sections

A check is **not filed** into a section. Its section is computed from two fields it already carries: `covers:` says what the check is about, `command:` says who executes it (ADR-0034). Nothing else selects a section.

**Precedence, in order.** A non-empty `command:` makes it an automated test. Otherwise a `covers:` naming an `ISS-*` makes it a regression test. Otherwise it is a feature test.

### Feature tests — re-checked when behaviour changes

- The check asserts *the system does X*: a standing claim about current behaviour.
- `covers:` names a `FEAT-*`.
- Never removed, and **invalidated when a change overlaps its scope**. This is the only section that is.

### Regression tests — completed once

- The check asserts *this defect was fixed*: a claim about a past event.
- `covers:` names the `ISS-*` that created it.
- Discharged one of two ways, and then it is done: **completed once** by a person, or **given a `command:`**, after which it is an automated test.
- A later change does **not** re-open it. Nothing a change does can falsify a claim about the past, so *never re-checked* is a property of what the check asserts rather than a policy applied to it.
- **A check that is not a standing behaviour claim must name the `ISS-*` it verifies.** Without that link it cannot be told apart from a behaviour claim, and is treated as one.

### Automated tests — executed by CI

- The check carries a non-empty `command:`.
- **Filed by nobody.** It appears here because a machine executes it, and leaves when it stops carrying a command. It does not matter why it was automated.
- **Permanent.** Nothing removes it. A kept check whose command stops resolving reports itself; a deleted one is a one-way door that cannot notice a covering test being renamed.
- **It carries no verdict** — no `ready`, `passing` or `failing`, no `last_run:`, no `exit_code:`. CI is the verdict, and a red automated test is a broken build rather than a state anybody records.

## Lifecycle rules

### When to create
1. **New feature implemented** → create a feature test covering the user-visible behaviour, naming the `FEAT-*` in `covers:`.
2. **Bug fixed** → create a regression test that reproduces the original bug and verifies the fix, **naming the `ISS-*` in `covers:`**.
3. **A check a machine can execute** → give it a `command:`. That is the whole of automating a check; nothing is moved and nothing is re-filed.

### When to invalidate (mark for re-check)
- **Feature tests only.** A code change invalidates the feature tests whose scope overlaps it.
- Use judgment: a change to `WorkoutViewModel` invalidates workout checks, not Bluetooth checks.
- **Say which change did it, in the same action.** This half of the rule is the one that does not get done: measured across the fleet, 54 rows carried a hand-written `RE-RUN (…)` annotation and **all 54 were still ticked**, because clearing the tick destroyed the only record that the check had ever passed and there was nowhere to say why. In note form that record is `invalidated_by:` — the change id, the reason and the date — written in the same act that clears the mark, and refused without a change id.
- Best done **at the close-out of the work that caused it**, not saved up for release time: a sweep over the areas a feature touched, adding the checks it needs and invalidating the ones it overtook, in one commit.
- A regression test is **not** invalidated by a later change. A person may still re-open one explicitly if the defect returns — which files a new issue.

### When to remove
- **Nothing removes a check.** A check whose subject is gone goes `retired`; a check a machine now covers gets a `command:`. Deleting one is a one-way door: it cannot report that its covering test was renamed, and the check is silently no longer verified by anything.

### Unit test replacement
- When unit tests are written that cover the same logic as a check, **give the check their `command:`**. It becomes an automated test from that moment, with no move and no removal date.
- If the command later stops resolving, the check reports itself as a broken command and returns to the manual list on its own.

## Where the acceptance suite lives

**Two shapes, split by time.** A repo stores its acceptance suite one way or the other, never both.

**Notes (current).** One check per note, `type: [[test]]` with `level: acceptance`, id `TST-*`, at `docs/tests/acceptance/TST-####-Slug.md`, scaffolded from `../../docs/__templates__/test.md`. `status:` is the lifecycle (`draft`/`active`/`retired`) and **`mark:` is the verdict** — ticking never touches status, which is what keeps an acceptance test outside the verdict rules and the independent-review gate. `area:` is a field; the section is derived from `covers:` and `command:` and is never written down. The suite is read as a generated list rather than as a document. See `SCHEMAS.md` `test.md` ("Acceptance fields") and `STATUSES.md` `[[test]]`.

**One document (older).** `docs/tests/ACCEPTANCE_TESTS.md`, scaffolded from `../../docs/__templates__/acceptance-tests.md`, with the structure below. A repo that has not migrated keeps using it and everything in this file still applies; a repo that migrates **deletes** it in the migration commit rather than keeping a copy, because two records of one thing is a source of drift and git holds the file at every earlier ref.

The document form:

```markdown
# Acceptance Test Suite: <Project> v<version>

## Sections
<!-- Section definitions and rules summary -->

## Rules
<!-- Numbered rules for create/uncheck/remove/gate -->

---

# Feature tests

## <Area> (<FEAT-IDs>)
- [x] **Test Name:** Test procedure and expected result.

---

# Regression tests

## <Bug Area> (<ISS-ID>)
- [x] **Test Name:** Test procedure and expected result.

---

# Automated tests
<!-- Checks carrying a `command:`. Executed by CI. No checkbox, no verdict. -->

---

# Test Execution Notes
<!-- Prerequisites, environment setup -->

# Release History
<!-- Build notes per version -->
```

## Test adequacy (who verifies the tests?)

A guarding test that cannot fail does not guard: LLM-authored test suites cluster their blind spots in the same places the LLM-authored fix does. Every regression test (and any `TST-*` gating a terminal status) should carry adequacy evidence in its note:

- **Minimum bar (cheap, always possible):** demonstrate the test fails when the fix is reverted or deliberately broken, and record that in the `TST-*` note's Adequacy section (or `adequacy` frontmatter field).
- **Stronger bar (when tooling exists):** run mutation testing over the code the test guards and record the score in `mutation_score`. A surviving mutant in the guarded code means the test does not actually guard it. Per-stack tools: `mutmut` (Python), Stryker (`stryker-js`/`stryker-net` for JS/TS/C#), `cargo-mutants` (Rust), PIT/`pitest` (JVM/Kotlin/Android), `muter` (Swift/iOS); record the tool and command in the test note's evidence so runs are reproducible.
- **Independence:** tests created alongside the fix they guard should get an independent review pass (`../skills/independent-review/SKILL.md`) — the author of a fix must not be the sole judge of its guarding test.
- **Cadence threshold:** if mutation scores on guarding tests are consistently above ~80%, reduce the adequacy-check cadence; below that, keep checking every guarded fix.

## Release gating

- A release is **blocked** if any **manual** check is not settled.
- **An automated test never enters the manual list.** CI gates it, and a red automated test blocks the build rather than the release note.
- A **broken command** — an automated test whose `command:` no longer resolves — returns to the manual list, because nothing is verifying it.
- A test may be marked as a **release exception** if it cannot be completed (e.g., third-party API key unavailable). Exceptions must be documented in the release note with justification.

## Relationship to TST-* notes

- `TST-*` notes in `docs/tests/` or `docs/features/<slug>/plan/tests/` are individual test specifications with frontmatter, preconditions, procedures, and evidence.
- **An acceptance check is a `TST-*` note at `level: acceptance`** (ADR-0031). There is no separate `check` type and no `CHK-*` id; notes that carried one were migrated, keeping the old id as an alias. In a repo that has not migrated at all, an acceptance check is still a line in `ACCEPTANCE_TESTS.md`.
- **`level:` is the whole distinction, and it is a spectrum rather than a boundary.** A `unit` test is a pytest module; an `acceptance` test is a thing a person does. The same note can move between them, which is the point: **adding a `command:` to an acceptance test is how it becomes automated** — and from that moment nothing writes a verdict into the note at all, because CI answers that question and answers it better.
- **What used to be a type boundary is now a status one, and it is still load-bearing.** An acceptance test rests at `active`, so the verdict rules (`STATUSES.md` `[[test]]`), the independent-review gate (`QUALITY.md`) and the `Run` obligation — keyed on `passing`, `passing` and `ready` respectively — never engage. **The review of an acceptance test is doing it.** A suite is hundreds of rows that re-arm on every overlapping change, and counting them individually is a badge that never empties.
- **A check carrying a `command:` is settled by CI**, with no human mark. That is what the shared type buys: before it, automating a check bought nothing and the check stayed owed.
