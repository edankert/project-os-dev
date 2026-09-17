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

Six more words, used on the sheet and below:

- **sitting** — a group of checks that share one setup state, such as one build, one account tier, or one piece of hardware on the bench. They are walked in one go.
- **survey** — the sheet's first section: the screens this release changed, and what changed on each.
- **walk order** — `docs/tests/acceptance/WALK.md`, one file per project, authored by the person who knows the product. It lists the sittings in product-state order. Its shape is `../../docs/__templates__/walk.md` and its keys are in `SCHEMAS.md`, "Walk order (`WALK.md`)".
- **procedure** — a written script for one whole sitting: the setup stated once, then numbered steps. One file per sitting, under `docs/tests/acceptance/walk/`. Rule 9.
- **owed part** — the unit a procedure is counted against: one numbered step of a check this platform still owes. A check whose steps are not numbered is one part. Rule 9.
- **expectation tag** — a label such as `TST-0648.4` on a line of a procedure step, saying that the line satisfies step 4 of check TST-0648.

Nine rules. They are stated here and nowhere else; the template, the generator, the skills and the cockpit link to this section and restate none of it (project-os-dev ADR-0029, ADR-0045, ADR-0024).

**1. The sheet is derived, never stored.** Its rows are exactly the checks the ledger says this platform still owes, restricted to the two manual sections, feature and regression ("The three sections"). No second list of "the checks for this release" exists anywhere. A generated sheet may be committed as a record of what was walked; it is never edited by hand and never read back by tooling. Reason: a maintained list of what a release owes rots, and a computed one cannot.

**2. The survey comes first, and it is built from the change notes.** Before any scripted check, the walker is told which screens this release changed. That list is computed: take every change note added since the last release tag, read its `## Impact` list, and group the `SUR-*` ids those lines name. Under each screen the survey prints the one sentence each change wrote for it, and the picture of the screen at the last release tag beside the picture of the build being walked. A child surface — one whose note carries `parent:` — prints under its parent screen, even when only the child has a change note. In that case the parent is named to show where to open the child; it does not claim the parent changed. **The survey names no check and prints no `TST-` id**: it is a list of places to open and look at, not a list of things to run.

Where the pictures are: `docs/tests/acceptance/gallery/<tag>/<key>.<ext>` holds the screens as they were at the release tagged `<tag>`, and `docs/tests/acceptance/gallery/candidate/<key>.<ext>` holds the build being walked. `<key>` is one of the keys on the surface note's `gallery:` list (`TAXONOMY.md`, "`gallery` (surfaces)"), and `gallery:` in WALK.md is the command that regenerates them. A screen with an after picture and no before one is marked **new**. A screen with neither prints its sentence alone.

Without a reachable release tag — a shallow clone, or a project that has released nothing yet — the survey says so in one line, and the rest of the sheet still prints. It never prints an empty survey silently.

The survey reads what git says was **added** since the tag, so an uncommitted change note is not in it, and neither is an Impact list back-filled onto a note that already existed at the tag. `walk-sheet.py --check` reads every change note in the repo whatever the tag says, which is where a missing Impact list is reported.

Reason: looking at what changed is the first thing a person would do. This rule read the ledger's invalidation events until 2026-09-14, and an invalidation names a check, never a screen — so the survey listed test categories such as "Hardware", which spans five screens, and a change that altered a screen without reopening a check was invisible (project-os-dev ADR-0045 decision 1, amending ADR-0029 rule 2).

**3. The order is authored once, in WALK.md, and never inferred.** Sittings appear on the sheet in the order the file lists them. A check joins the first sitting whose `surfaces:` names its `area:`; a sitting may also name check ids in `checks:` to pull them in regardless of area. A sitting with nothing owed is omitted. Checks no sitting claims go to a final sitting labelled "Unplaced", which is the author's worklist. A project with no WALK.md gets one sitting per area in id order, and the sheet says its order is unauthored. Reason: the one previous attempt to order a walk read setup cost out of prose and produced six false positives out of six.

**4. Inside a sitting, `after:` first, then id.** An acceptance check may carry `after: [TST-####]`, the checks that should have passed before this one is walked. The sheet sorts by it. Nothing gates on it, and a cycle prints a warning naming the checks rather than failing the sheet.

**5. Each row is walkable without leaving the sheet.** A row prints the check's id, its title, and its Setup, Steps and Expect sections ("A check is walkable by a stranger"). This is what a sitting with no procedure prints; a sitting that has one prints that instead (rule 9). Where a heading is missing the row says so and prints what the note does have, so the sheet doubles as the worklist for bringing old checks to that shape:

- no `## Setup` prints **"Setup: not stated"**. There is no fallback, and that is the point of the label.
- no `## Steps` falls back to `## Procedure`, and then to the note's own unheaded description — the prose between its title and its first sub-heading — printed under **"Steps: no heading"**. A corpus written before these headings existed keeps its whole procedure there, so printing nothing would make the sheet useless on the repos large enough to need it.
- no `## Expect` falls back to `## Expected results`, and then says the note states no expected result. There is no prose fallback: a check that never said what should happen has nothing to fall back to, which is the finding, not the sheet's failure.

An unscripted acceptance check may declare `walk_readiness_for:` in its frontmatter. The map names a platform and gives `kind: preparation` or `kind: decision`, a plain `reason`, and an optional `issue`. The generated fallback row prints that reason before the check's instructions. The declaration does not change which platforms owe the check or record a verdict. The cockpit asks for preparation to be confirmed before it offers the normal mark control; a decision row offers only the existing release-decision outcomes. The generator rejects malformed declarations.

**6. A verdict goes to the ledger, from the sheet.** The sheet is never the store. A walker records each verdict as a ledger event through the cockpit's mark dialog or the ledger write path, with `method: manual`.

**7. One implementation.** `tools/scripts/walk-sheet.py` is the only code that computes a walk. The cockpit bundles that module the way it bundles the validator, so a badge and a sheet cannot disagree about one corpus.

**8. No schedule, and no new obligation.** The generator writes no duration of its own: counts of rows are the only number it produces, and there is no minutes field, no estimate and no burden tag anywhere in the walk. Text it quotes from a note prints verbatim, so a check whose own title says "a 40-minute ride" still reads that way on the sheet — that is the author's sentence, not a schedule the walk invented. And the walk asks one thing at close-out, and one only: **a change note's `## Impact` list names the screens that change altered**, one sentence each, drafted by an LLM from the diff. That single obligation buys the survey its only input, which is written down nowhere else — measured on the corpus that has the problem (ADR-0045 decision 2, narrowing this rule). Nothing else is added: no sweep over the suite, no per-release run plan, no duration. Reason: both are ways an earlier attempt died. Ordering by inferred setup cost was cancelled for inventing a schedule out of prose, and a close-out acceptance sweep was withdrawn because its common case was "nothing to do, say so".

**9. A sitting may be walked from a written procedure.** A procedure is a script for one whole sitting: the setup stated once, then numbered steps. It removes repetition that per-check rows cannot — on your-trainer's REL-0017 sheet the same "fake a connected trainer" setup printed four times inside one sitting, and the same comparison against a drivable trainer printed in four checks. Where a sitting has a procedure the sheet prints it; where it has none the sheet prints rows, exactly as rule 5 says.

- **Where it lives.** One file per sitting, `docs/tests/acceptance/walk/<name>.md`, from `../../docs/__templates__/procedure.md`. Its `sitting:` field repeats the `### ` heading in WALK.md word for word, and that is the whole of the link: nothing in WALK.md points back, because a pointer written in two files is a pointer that can disagree. A procedure is written once for the whole product, not once per release, and it aims to cover every live check in its sitting.
- **What a step is.** One numbered item under `## Steps`. Its first line names the screen the step happens on, by `SUR-####` id or by the surface's exact title. Under that line, one line per thing the walker should observe. **A step's number is its position in the list, not the digit written** — markdown renumbers an ordered list and so does the walk, so a procedure written `1.` on every item has steps 1, 2, 3, and that is what a tag names and what the sheet prints. A tag inside a fenced block is an example, not a citation.
- **What an expectation line is.** It quotes one line of the check's own `## Expect` section word for word, then carries one or more expectation tags. Quoting is what lets a tick recorded from a procedure step stand as a verdict on the check itself (project-os-cockpit ADR-0041), so the validator compares the quote against the note and only whitespace may differ.
- **What a tag is.** `TST-####.N`, in backticks, meaning the line satisfies step N of that check: `` `TST-0648.4` ``. ASCII only. A check whose steps are not numbered is cited by its bare id, `` `TST-0648` ``. A line may carry several tags where several checks expect the same thing in the same words.
- **What an owed part is.** One numbered item under a check's `## Steps` (or `## Procedure` where `Steps` is absent), for a check the ledger says this platform still owes, counted by position for the same reason. A check with no numbered steps is one part. Renumbering a check's steps changes what its parts are, and the validator then reports the procedure as no longer covering them; the fix is to regenerate it (`../skills/walk-procedure/SKILL.md`). An agent writing a sitting's procedure numbers a prose-only check's steps in the check note first, and that check then has one part per step.
- **What is checked.** `python3 tools/scripts/walk-sheet.py --check --platform <platform>` fails, naming the check and the step, when an owed part is cited by no step, when an owed part is cited by two different steps, when a backticked `TST-` token is malformed, when a tag names a check at `status: retired`, when a tag names a step number the check does not have, when a tag names a check that another sitting claims, or when a quoted expectation does not match the check's `## Expect` text. A valid tag on the same line does not excuse a malformed one. Covering the owed parts is the requirement; covering every live check is the aim, and the shortfall is reported as a count rather than failed. `validate-docs.sh` runs it for every platform that has a ledger.
- **Declared preparation.** A procedure may add `requires:` in frontmatter, mapping a step's position to earlier step positions it needs. The generator keeps those prerequisite actions transitively and in authored order when a later step is owed. A prerequisite whose own checks have passed is labelled preparation and creates no verdict. An absent, future or cyclic reference fails validation and the sitting falls back to its per-check rows. No dependency is inferred from action prose.
- **Scoped setup.** A procedure may name each `## Setup` bullet as `- [trainer] Connect the trainer.` and map each id to step positions in frontmatter `setup_for:`. A value of `all` means every step; a list such as `[1, 5]` names only those positions. Only items needed by retained steps and their prerequisites print. `setup_platforms:` may limit an item to named platforms. Unannotated procedures keep their full setup. An item with an invalid id, step or platform declaration fails validation. Resolve conflicting setup and sitting state in the authored notes; the generator cannot guess which instruction is right.
- **Platform and state.** `step_platforms:` maps step positions to platform lists such as `[android]` or `[ios]`. `state_for:` maps step positions to a plain statement of the app and equipment state to confirm before that action. The declaration continues through later steps on that platform until another declaration replaces it, including when the declaring step is omitted from the current owed walk. A step unavailable on the selected platform cannot change that platform's state reminder. A platform walk keeps only its applicable steps and checks their owed coverage. A step may depend only on an action available on that platform. Required state is an instruction, not proof that the live app is in that state.
- **Platform action wording.** `action_for:` maps a step position to platform-specific action prose, for example `3: {android: "Open Profile — Connected.", ios: "Open Settings — Integrations."}`. The variant replaces only that step's action after its unchanged bold surface heading; it may not contain a test tag. The validator rejects a variant on a step without a bold surface heading or with tags on its first line. The check's exact expectation lines and owed coverage remain unchanged.
- **Later comparisons and waits.** `capture_for:` maps an earlier step position to the evidence to record there, and `use_capture:` maps a later step position to earlier evidence source positions. The later step must also name each source in `requires:`. The prompt appears only when the later comparison survives filtering. `timer_for:` maps a step position to a positive duration in seconds for an optional user-started timer. Neither capturing evidence nor ending a timer records a verdict. Missing, future or undeclared evidence sources fail validation.
- **Known readiness problems.** `readiness_for:` maps a step position to `{kind: preparation, reason: "...", issue: "ISS-..."}` or `{kind: decision, reason: "..."}`. An optional `platforms: [android]` limits the problem to the named platforms. Use it for a concrete missing fixture, device, developer control or unresolved product decision. The generator prints the reason before the affected action and the cockpit can list it in the session introduction. This label creates no verdict and never drops the step or its owed checks. An absent step or malformed declaration fails validation.
- **What prints.** For a sitting with a procedure the sheet prints relevant setup once, then each owed step and its declared prerequisites, and says how many steps it left out. Display positions are consecutive; source positions remain visible when needed to inspect the procedure. A settled expectation in a retained preparation action does not print or create a verdict. A tag on an owed step whose part is not owed is marked as already passed. A procedure the validator refuses prints that message at the top of its sitting and then per-check rows, so a stale procedure never hides an owed check.

## Relationship to TST-* notes

- `TST-*` notes, stored per `LIFECYCLE.md` "Test storage", are individual test specifications with frontmatter, procedure and evidence.
- **An acceptance check is a `TST-*` note at `level: acceptance`** (ADR-0031; the retired `check` type is `TAXONOMY.md`, "`check` — retired").
- `level:` is a spectrum: a `unit` test is a pytest module, an `acceptance` test is a thing a person does, and a `command:` moves a note along it.
- An acceptance test rests at `active` (`STATUSES.md` `[[test]]`) and owes no separate review (`QUALITY.md`, "Independent review (clean-context)").
