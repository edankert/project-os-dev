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

### A check is walkable by a stranger

A check is written by someone holding the whole context and walked months later by someone holding none of it. So an acceptance check states four things, under four headings, and a new one is born with them in `../../docs/__templates__/test.md` (project-os-dev ADR-0027):

- **Setup** — the state the walk needs, and *the cheapest way to reach it*. Name the developer toggle, the mock or the bundled fixture that produces it. This is the line that decides whether the check ever gets walked: one check went unwalked for months because its setup sentence asked for hardware to be unplugged, and a developer-settings switch forces the same state in fifteen seconds.
- **Steps** — numbered, one action each, in the order a person performs them.
- **Expect** — what must be observable, one line per assertion, in the words the surface uses. A code symbol may follow the observable name; it may not replace it.
- **Not this check** — the boundary: what a reader might reasonably think this covers, and which check actually covers it.

Provenance — where the check came from, what migration moved it, which audit split it out — goes **below** the procedure under its own heading, or into frontmatter. It is about the note, not about the walk.

**Existing checks are rewritten on contact, never swept.** A check is brought to this shape when it is walked, invalidated, or otherwise edited. Rewriting a whole corpus from note text alone manufactures confident assertions nobody verified; the walk is when a person knows whether the text is true. A check missing its Setup heading prints "Setup: not stated" on the walk sheet ("The walk", rule 5), which is where a corpus comes into contact.

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

## The walk

A release is walked from a **walk sheet**. It is one generated document per release and platform. It opens with the screens the release changed, then lists every owed check in the order to walk them, with each check's setup, steps and expected result printed on the page. Nobody writes it by hand: `python3 tools/scripts/walk-sheet.py --release REL-#### --platform <platform>` prints it from the release ledger, the check notes and the project's walk order. To **walk** a check is to execute it by hand.

Three more words, used on the sheet and below:

- **sitting** — a group of checks that share one setup state, such as one build, one account tier, or one piece of hardware on the bench. They are walked in one go.
- **survey** — the sheet's first section: the surfaces this release changed, and what changed them.
- **walk order** — `docs/tests/acceptance/WALK.md`, one file per project, authored by the person who knows the product. It lists the sittings in product-state order. Its shape is `../../docs/__templates__/walk.md` and its keys are in `SCHEMAS.md`, "Walk order (`WALK.md`)".

Eight rules. They are stated here and nowhere else; the template, the generator, the skills and the cockpit link to this section and restate none of it (project-os-dev ADR-0029, ADR-0024).

**1. The sheet is derived, never stored.** Its rows are exactly the checks the ledger says this platform still owes, restricted to the two manual sections, feature and regression ("The three sections"). No second list of "the checks for this release" exists anywhere. A generated sheet may be committed as a record of what was walked; it is never edited by hand and never read back by tooling. Reason: a maintained list of what a release owes rots, and a computed one cannot.

**2. The survey comes first, and it is derived too.** Before any scripted check, the walker is told which screens this release changed. That list is computed: for every owed check whose latest ledger event is an invalidation, take the check's `area:` and the change and task ids in that event's `invalidated_by:`. Group by surface, name the invalidating notes with their titles, and quote each note's `## Acceptance checks reopened` section where it has one. Reason: looking at what changed is the first thing a person would do, and until this section existed nothing on a check list suggested it.

**3. The order is authored once, in WALK.md, and never inferred.** Sittings appear on the sheet in the order the file lists them. A check joins the first sitting whose `surfaces:` names its `area:`; a sitting may also name check ids in `checks:` to pull them in regardless of area. A sitting with nothing owed is omitted. Checks no sitting claims go to a final sitting labelled "Unplaced", which is the author's worklist. A project with no WALK.md gets one sitting per area in id order, and the sheet says its order is unauthored. Reason: the one previous attempt to order a walk read setup cost out of prose and produced six false positives out of six.

**4. Inside a sitting, `after:` first, then id.** An acceptance check may carry `after: [TST-####]`, the checks that should have passed before this one is walked. The sheet sorts by it. Nothing gates on it, and a cycle prints a warning naming the checks rather than failing the sheet.

**5. Each row is walkable without leaving the sheet.** A row prints the check's id, its title, and its Setup, Steps and Expect sections ("A check is walkable by a stranger"). Where a heading is missing the row says so and prints what the note does have, so the sheet doubles as the worklist for bringing old checks to that shape:

- no `## Setup` prints **"Setup: not stated"**. There is no fallback, and that is the point of the label.
- no `## Steps` falls back to `## Procedure`, and then to the note's own unheaded description — the prose between its title and its first sub-heading — printed under **"Steps: no heading"**. A corpus written before these headings existed keeps its whole procedure there, so printing nothing would make the sheet useless on the repos large enough to need it.
- no `## Expect` falls back to `## Expected results`, and then says the note states no expected result. There is no prose fallback: a check that never said what should happen has nothing to fall back to, which is the finding, not the sheet's failure.

**6. A verdict goes to the ledger, from the sheet.** The sheet is never the store. A walker records each verdict as a ledger event through the cockpit's mark dialog or the ledger write path, with `method: manual`.

**7. One implementation.** `tools/scripts/walk-sheet.py` is the only code that computes a walk. The cockpit bundles that module the way it bundles the validator, so a badge and a sheet cannot disagree about one corpus.

**8. No schedule, and no new obligation.** The generator writes no duration of its own: counts of rows are the only number it produces, and there is no minutes field, no estimate and no burden tag anywhere in the walk. Text it quotes from a note prints verbatim, so a check whose own title says "a 40-minute ride" still reads that way on the sheet — that is the author's sentence, not a schedule the walk invented. And the walk asks nothing new at close-out — the survey reads invalidation events the ledger already refuses to accept without a change id. Reason: both are ways an earlier attempt died. Ordering by inferred setup cost was cancelled for inventing a schedule out of prose, and a close-out acceptance sweep was withdrawn because its common case was "nothing to do, say so".

## Relationship to TST-* notes

- `TST-*` notes, stored per `LIFECYCLE.md` "Test storage", are individual test specifications with frontmatter, procedure and evidence.
- **An acceptance check is a `TST-*` note at `level: acceptance`** (ADR-0031; the retired `check` type is `TAXONOMY.md`, "`check` — retired").
- `level:` is a spectrum: a `unit` test is a pytest module, an `acceptance` test is a thing a person does, and a `command:` moves a note along it.
- An acceptance test rests at `active` (`STATUSES.md` `[[test]]`) and owes no separate review (`QUALITY.md`, "Independent review (clean-context)").
