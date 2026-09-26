---
type: reference
id: TEMPLATES-SCHEMAS
status: active
owner: team:docs
created: 2026-01-27
updated: 2026-07-21
tags: [templates, schema]
---

# Template schemas (frontmatter fields)

This document defines the intended meaning of the frontmatter fields used by the note templates in `docs/__templates__/`.

Conventions (naming, linking, property rules): `../../tools/instructions/OBSIDIAN.md`.

## Common fields (most templates)

- (required) `type` (link string): Obsidian link identifying the note type, e.g. `type: "[[task]]"`.
  - Used by tools/automation to classify notes; the snapshot references these types.
- (required) `id` (string): Stable identifier (should match the filename prefix).
  - Used for traceability and for `SNAPSHOT.yaml` keys.
- (recommended) `title` (string): Human-friendly title for views and summaries.
  - Keep short; no need to repeat the ID.
  - Keep it consistent with `SNAPSHOT.yaml` where possible.
- (required) `status` (string): Lifecycle state; each note type has its own allowed values.
- (optional) `phase` (link or integer): Development phase for milestone grouping. Prefer `[[PHASE-####]]` links when using first-class phase notes; legacy integer values may be used during migration. See `[[PHASES]]` for definitions.
  - Enables machine-filtering, automated progress tracking, and phase grouping.
  - Leave empty/omit for items not tied to a specific phase.
- (required) `owner` (string): Accountable person/team (can be `unassigned`).
  - Values must be defined in `[[OWNERSHIP]]` (or be `unassigned`).
- (required) `created` (date string): Creation date; keep stable.
- (required) `updated` (date string): Last material edit date; bump when meaningfully changed.
- (optional) `related` (list of links/strings): Cross-links to other notes and/or repo paths.
  - Prefer links (`[[...]]`) when pointing to other notes in this docs set.
- (optional) `source` (list of strings/links): Provenance for imported/derived items.
  - Use for links to external trackers, changelogs, or source documents.
- (optional) `origin` (link): The former parent an item was descoped from when it was `deferred`.
  - Set by the deferral procedure (`tools/instructions/STATUSES.md`, "Deferral and re-adoption"); kept as history after re-adoption.
  - Distinct from `source` (import provenance): `origin` records where work was originally scoped inside this project.
- (optional) `verification_waiver` (string): Why a terminal status is set without passing tests; the rule is `tools/instructions/QUALITY.md`, "Verification gating".
- (required with a waiver) `waiver_expires` (date string): When the waiver lapses. A waiver without one, or with a past or unparseable date, is an error (ADR-0010).
- (tool-written) `superseded_by` (link or list) and `amended_by` (list): the notes that replaced or amended this one. `sync-snapshot.py` writes them from the newer note's `supersedes:` or `amends:`; do not write them by hand (ADR-0048). An ADR spells the first one `superseded`.
- (optional) `phases` (list of links) and `workflows` (list of links): `[[PHASE-...]]` and `[[WF-...]]` this note relates to; checked like the other link fields.

## `adr.md` (`type: [[adr]]`)

Purpose: capture “why we chose X” with alternatives and consequences.

Fields:
- (required) `decision` (string): One-sentence decision statement.
- (required) `context` (string): One-sentence reason/background for the decision.
- (optional) `alternatives` (list): Options considered (strings or links).
- (optional) `consequences` (list): Key impacts/tradeoffs (strings or links).
- (optional) `supersedes` (string/link): Link to the ADR replaced by this one (prefer `[[ADR-....]]`).
- (optional) `superseded` (string/link): Link to the ADR that replaces this one. Written by `sync-snapshot.py` from the new ADR's `supersedes:`; do not write it by hand (ADR-0048).
- (optional) `amends` (string/link or list): The ADR(s) this one changes in part, leaving the rest standing.
- (optional) `amended_by` (list): The ADRs that amend this one. Written by `sync-snapshot.py` from their `amends:`; do not write it by hand.

Body sections:
- A decision stating a quantified rule carries `## Rule`, `## Domain` and `## Conformance` in its body — the rule-ADR convention, normative in `tools/instructions/DECISIONS.md` ("A decision that states a rule") and enforced by `DECISION-RULE`.

Where used:
- Referenced from `../decisions/README.md` for organization.

## `change.md` (`type: [[change]]`)

Purpose: durable “what shipped and why” note.

Naming:
- Filename should be `CHG-YYYYMMDD-Short-Description.md`.
- `id` should match the filename without `.md` (same `CHG-...-Short-Description` string).

Fields:
- (optional) `commit` (string): Commit hash.
- (optional) `pr` (string): PR/MR identifier or link.
- (recommended) `impacts` (list of strings): Affected areas/paths/flows (keep short).
- (optional) `issues` (list of links): Issues associated with the change.
- (optional) `features` (list of links): Features associated with the change.
- (optional) `reviewed_by` (string): Independent reviewer identity (`model:...` or `user:...`) when a change note was reviewed; it owes none (`tools/instructions/QUALITY.md`, "Independent review (clean-context)").
- (optional) `review_date` (string/date): Date of the independent review.
- (optional) `review_verdict` (string): `approved | changes-requested`.

Body sections:
- **`## Impact` is a list of the screens this change altered**, and `tools/scripts/walk-sheet.py` parses it to build a release walk's survey (project-os-dev ADR-0045 decision 2). The shape a parser reads: one list item per screen, beginning with a `[[SUR-####]]` link or a bare `SUR-####` id, then a separator (`:`, `—` or `-`), then one sentence in the words a person using the product would use. Everything after the separator is printed verbatim on the sheet. An item may name more than one screen, joined by `and`, `,`, `&` or `+` before the separator, and every screen it names gets that one sentence. Lines inside a fenced block are examples and are not read.
- A change that altered no screen writes one item reading **`No screen changed`** followed by the reason. The parser recognises that phrase and asks for nothing else. A change note with no Impact list at all contributes nothing to the survey and is reported by `walk-sheet.py --check`.
- ~~`## Acceptance checks reopened`~~ — **removed (ADR-0045 decision 1).** The survey no longer reads it. Why a check was reopened is the `reason:` on the ledger's invalidation event, which the ledger refuses to accept without. Old change notes keep the section; nothing parses it.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.changes`) for agent context and linked from change notes.

## `feature.md` (`type: [[feature]]`)

Purpose: a work package describing a capability, with traceability to requirements and tasks.

Fields:
- (required) `goal` (string): Short outcome statement.
- (optional) `requirements` (list of links): `[[REQ-...]]` links implemented by this feature.
- (optional) `tasks` (list of links): `[[TASK-...]]` links that deliver the feature — the feature's **current scope**; its completeness gate is `tools/instructions/STATUSES.md` `[[feature]]`.
- (optional) `fixes` (list of links): `[[ISS-...]]` issues this feature fixes. An issue whose `parent:` names the feature must appear here or in `issues:` (validator `PARENT-BACKLINK`).
- (optional) `deferred` (list of links): `[[TASK-...]]` links descoped out of the feature via the deferral procedure (each keeps `origin` pointing back here). Not part of completeness.
- ~~`tests`~~ — **removed (ADR-0032).** A feature does not list its tests. The verification link has one direction and one encoding: the test's `covers:`. A feature's tests are rendered from a reverse index over that field, so the list is derived and cannot drift — where the field could only ever be as correct as the last person to edit both sides, and a third of the fleet's feature→test edges disagreed when it was measured.

  *The same reverse encoding still exists on `task`, `issue` and `requirement` (330 live edges fleet-wide against the feature's 62). Normalising those is decided in principle and not yet done; until then `VERIFY` ignores any linked test at `level: acceptance` so the merged type cannot trip the gate from those three.*
- (optional) `release` (string): Milestone/release label.
- (optional) `acceptance_exception` (string): Why this feature can never have an acceptance check — an engine with no user-facing surface, a phase of work, a repo that ships prose. **Said once, at scaffold time, when the reason is known.** Non-empty silences `FEATURE-UNCOVERED` for this feature permanently; empty (the template's default) means the feature is expected to be covered by the time it is `done`. This is an escape, not a switch: a reason that is not true is worse than the warning it removes.
- (optional) `reviewed_by`, `review_date`, `review_verdict` (strings): the independent review of this feature reaching `done` (`tools/skills/independent-review/SKILL.md`). The same review records them on each linked test it checked.
- (optional) `review_round` (integer, `1` or `2`): which round produced the verdict. A gate runs at most two rounds (`tools/instructions/QUALITY.md`); the validator refuses any other value (`REVIEW-ROUND`).

Body sections:
- `## Acceptance`: the observable criteria. `tools/scripts/review-packet.py` copies them word for word into the review packet, so write each as a claim a reviewer can refute.
- `## Verification`: the author's last full test run before the review, as the command, the date and the result count. The packet carries it so the reviewer does not re-run the suite.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.features`) for agent context and linked from feature notes.

## `phase.md` (`type: [[phase]]`)

Purpose: define a delivery milestone with explicit scope, linked work, and exit criteria.

Naming:
- Filename should be `PHASE-####-Short-Name.md`.
- `id` should match the filename prefix.

Fields:
- (required) `order` (integer): Sort order for roadmap sequencing.
- (required) `goal` (string): Short outcome statement for the milestone.
- (optional) `features` (list of links): Features planned for this phase.
- (optional) `requirements` (list of links): Requirements introduced or verified in this phase.
- (optional) `tasks` (list of links): Active or key tasks in this phase.
- (optional) `issues` (list of links): Issues tied to this phase.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.phases`) for agent context and linked from phase-aware items.

## `issue.md` (`type: [[issue]]`)

Purpose: canonical problem report / gap / bug.

Fields:
- (required) `severity` (string): e.g. `low|medium|high|critical` (project-defined).
- (recommended) `component` (string): Subsystem/area label (project-defined).
- (optional) `parent` (string/link): Link to a parent feature/epic note.
- (optional) `tests` (list of links): `[[TST-...]]` links used to reproduce/verify the issue.
- (required from 2026-09-19 on an open issue) `reported_by` (string): `user:<name>`, `review` or `agent` (validator ISSUE-REPORTER, ADR-0047).
- (optional) `question` (string): when the issue waits on the owner, the question, its options and a recommendation. An open issue that says it waits on the owner without one draws ISSUE-QUESTION.

The title and the first sentence of `## Problem` name what a user would notice (`tools/instructions/WRITING.md`). Before filing at all, apply the filing bar in `tools/instructions/QUALITY.md`.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.issues`) for agent context and linked from issue notes.

## `requirement.md` (`type: [[requirement]]`)

Purpose: acceptance criteria that features/tasks must satisfy.

Fields:
- (required) `priority` (string): e.g. `low|medium|high` (project-defined).
- (optional) `scope` (string): Short scoping label (area/domain).
- (required) `acceptance` (list): Acceptance criteria statements (strings). This list is the **criteria of record** — the machine-readable contract other notes and tooling refer to.
  - The body `## Acceptance Criteria` checkboxes are the **verification record**: one box per criterion, ticked only with an evidence pointer (path, `path:line`, command, or note ID) at feature close-out.
  - Both surfaces must describe the same criteria; where they diverge, frontmatter wins and the body is corrected. Departures from a criterion are amended/superseded with rationale (an `## Amendments` section), never ticked to fit — see `../../tools/skills/close-out/SKILL.md`, step 3 "Requirement advancement".
- (optional) `implements` (link): The feature implementing this requirement. Direction note: this names the feature that implements *this requirement* (the inverse-named back-reference), and it holds **at most one** feature (`tools/instructions/STATUSES.md` `[[requirement]]`, Ownership).
- (optional) `verifies` (list of links/paths): Proof/verification pointers (workflows/tests/repo paths).
- (optional) `tests` (list of links): `[[TST-...]]` links that verify this requirement.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.requirements`) for agent context and linked from requirement notes.

## `reference.md` (`type: [[reference]]`)

Purpose: durable explanatory, registry, or background material that supports project understanding but is not itself a task, feature, workflow, decision, test, issue, requirement, phase, risk, or change.

Fields:
- (recommended) `scope` (string): Short scope label such as `project`, `docs`, `tooling`, or a domain-specific area.
- (optional) `related` (list of links/strings): Related notes or repo paths.
- (optional) `source` (list of strings/links): Provenance or upstream/source documents.

Where used:
- Surfaced by the cockpit project mode under References and by `/index/references`.
- Not normally tracked in `SNAPSHOT.yaml` unless a downstream project deliberately promotes a reference collection into active state.

## `risk.md` (`type: [[risk]]`)

Purpose: track hazards + mitigations.

Fields:
- (required) `likelihood` (string): e.g. `low|medium|high` (project-defined).
- (required) `impact` (string): e.g. `low|medium|high` (project-defined).
- (recommended) `mitigation` (list): Mitigation actions (strings or links to tasks).
- (optional) `mitigation_tasks` (list of links): `[[TASK-...]]` tasks that carry out the mitigations; checked like the other link fields.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.risks`) for agent context and linked from risk notes.

## `task.md` (`type: [[task]]`)

Purpose: actionable unit of work with a Definition of Done.

Fields:
- (required) `parent` (link): Link to a feature or issue note this task belongs to.
- (optional) `effort` (string): Size label (e.g. `XS|S|M|L`).
- (optional) `due` (string/date): Due date.
- (optional) `depends` (list of links): Tasks/issues that must complete first.
- (optional) `blocks` (list of links): Tasks/issues blocked by this task.
- (optional) `tests` (list of links): `[[TST-...]]` links used to verify completion.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.tasks`) for agent context and linked from task notes.

## `test.md` (`type: [[test]]`)

Purpose: describe how to verify behavior (manual or automated) and provide durable coverage mapping.

Fields:
- (required) `scope` (string): values in `tools/instructions/TAXONOMY.md`, "`scope` (tests)"; it decides where the note is stored (`tools/instructions/LIFECYCLE.md`, "Test storage").
- ~~`kind`~~ — **removed (ADR-0034 decision 4).** `command:` answers who runs a test: present, the runner owns it; absent, a person does. Two fields answering one question is how the reader and the registry came to disagree about 8 of 788 notes.
- (recommended) `level` (string): values in `tools/instructions/TAXONOMY.md`, "`level` (tests)".
- (optional) `entrypoint` (string): Repo-relative command/script to run (or blank for purely manual tests).
- (optional) `command` (string): A runnable check. **When present the note records no verdict** (project-os-dev ADR-0025; `tools/instructions/STATUSES.md` `[[test]]`): it rests at `active`, CI runs it, and the validator's COMMAND-VERDICT reports a `ready`/`passing`/`failing` or a `last_run`/`exit_code` written on it. The reason ADR-0010 gave still holds, the party seeking a transition must not certify it; this closes it by leaving nothing on the note to certify. A hand-edited `status` on a note carrying a `command` was a validator error.
- (required for manual tests) `last_verified` (date): When a human last performed the procedure. A manual test past the project's staleness window stops satisfying the verification gate — verification that was true a year ago is not evidence about today's system.
- `status`: the values, who writes them and what a `command:` changes are `tools/instructions/STATUSES.md` `[[test]]`.
- (recommended) `requirements` (list of links): Requirements verified by this test (`[[REQ-...]]`).
- (required where the test verifies anything in particular) `covers` (list of links): **the single encoding of what this test verifies** — `[[FEAT-...]]`, `[[ISS-...]]`, `[[REQ-...]]` (ADR-0032). Resolvable through the index. A system-wide test that verifies nothing in particular leaves it empty, deliberately.
- (optional) `issues` (list of links): Related issues (`[[ISS-...]]`) — context, not verification. What the test *verifies* goes in `covers`.
- (optional) `tasks` (list of links): Related tasks (`[[TASK-...]]`).
- (optional) `artifacts` (list): Expected artifacts/logs.
- (optional) `evidence` (list): Evidence from the last run (paths/log excerpts).
- ~~`last_run`~~, ~~`exit_code`~~ — **removed (ADR-0025).** The runner wrote them; it no longer writes to a note.
- (optional) `adequacy` (string): Evidence the test actually guards (see `tools/instructions/TESTING.md`, "Test adequacy").
- (optional) `mutation_score` (string): Mutation-testing score for the code this test guards, when measured.
- (optional) `reviewed_by` (string): Independent reviewer identity (`model:...` or `user:...`), per `tools/skills/independent-review/SKILL.md`.
- (optional) `review_date` (string/date): Date of the independent review.
- (optional) `review_verdict` (string): `approved | changes-requested`.
- (optional) `review_round` (integer, `1` or `2`): which round produced the verdict (`REVIEW-ROUND`).

### Acceptance fields (`level: acceptance` only)

An acceptance test is the thing a person walks. It carries the fields below and rests at `status: active` (`tools/instructions/STATUSES.md` `[[test]]`); every one of them is meaningless on an executable test and the validator does not require them there.

**The note holds intent. The verdict is not on it** (ADR-0037; why is `tools/instructions/TAXONOMY.md`, "Acceptance outcomes (the ledger's vocabulary)"). It lives as a dated, attributed event in `docs/releases/ledgers/`, whose README gives the file format with an example.

**Twelve fields were removed**: `mark`, `verdict_date`, `verdict_reason`, `invalidated_by`, `automation`, `covered_by`, `evidence`, `section`, `ordinal`, `migrated_from`, `merged_from` and `burden`. Do not write them on a new note. In a repo that keeps ledgers the validator reports each one as `LEDGER-FIELD`, a warning until 2026-12-17 and an error after it. A repo with no ledger is untouched and keeps reading its scalar marks, because a schema change that broke every repo that had not migrated yet would be a worse failure than the one it fixes.

- ~~`tier`~~ — **removed (ADR-0034).** There is no tier system: a check's section is derived from `covers:` and `command:` (`tools/instructions/TESTING.md`, "The three sections"). Readers still accept the field on legacy notes and ignore it.
- ~~`burden`~~, ~~`migrated_from`~~, ~~`merged_from`~~ — **removed (ISS-0233).** Provenance of migrations that are finished, plus a field empty on every check in the fleet. Git holds the first two, with the shas ADR-0030 and ADR-0031 name; a field is the wrong place for a fact already immutable somewhere better.
- (required) `area` (string): the human grouping — "The navigator", "Agents and sessions". One walk's worth of related checks.
- (optional) `after` (list of check ids): the checks that should have passed before this one is walked — `after: ["TST-0044"]`. Read by `tools/scripts/walk-sheet.py` to order rows inside a sitting (`tools/instructions/TESTING.md`, "The walk", rule 4). It gates nothing: a check whose prerequisite has not passed still appears on the sheet and still blocks the release, it is simply printed later.
- ~~`section`~~, ~~`ordinal`~~ — **removed (ISS-0224).** They were a check's position in `ACCEPTANCE_TESTS.md`, a document that exists in no migrated repo. Order is `id` and grouping is `area` alone. Measured before the removal, ordering by tier-then-id reproduced the old section order byte-for-byte in every repo, and no area spanned two sections anywhere; ADR-0034 then removed `tier` as well, leaving `id`.

Where NOT used:
- The obligation registry and the independent-review gate: neither engages for an acceptance test, by construction (`tools/instructions/STATUSES.md` `[[test]]`).
- `SNAPSHOT.yaml` `items.tests`: a repo can hold hundreds of acceptance tests and the snapshot is active-and-recent context. Executable tests are tracked as before.


Where used:
- Tracked in `SNAPSHOT.yaml` (`items.tests`) for agent context and linked from test notes.

## `design.md` (`type: [[design]]`)

- (optional) `asset` (path): An HTML page showing the design, relative to the note. A design past `draft` must show something, in pictures or in `asset:` (validator `DESIGN-ASSET`); the rules are `tools/instructions/TRACEABILITY.md`, "`[[design]]` links".

## `surface.md` (`type: [[surface]]`)

Purpose: name one place in the product once, so every check that touches it can say `area:` and mean the same place.

Naming:
- Filename should be `SUR-####-Short-Name.md`; `id` should match the `SUR-####` prefix.
- `title` is the string a check's `area:` matches, so it is the part that must not drift. Renaming a surface and its checks happens in one commit (project-os-cockpit ISS-0250).

Fields:
- (required) `kind` (string): values in `tools/instructions/TAXONOMY.md`, "`kind` (surfaces)". **A surface is a screen unless this says otherwise**, and the four rules for the cases that get it wrong are stated there (project-os-dev ADR-0044).
- (optional) `platforms` (list of strings): the platforms this surface exists on. Empty means all of them.
- (optional) `parent` (link or string): the screen this one opens from. A dialog, sheet, panel or section carries it; a top-level screen does not.
- (optional) `gallery` (list of strings): the screenshot keys that capture this surface — `key`, or `key:state` where that key captures it in one state, for example `gallery: [equipment-hub, "equipment-hub-dataonly:data-only"]`. Read by `tools/scripts/walk-sheet.py` to put a before and an after picture in the walk sheet's survey; where it looks for the image files is `tools/instructions/TESTING.md`, "The walk", rule 2.

Where NOT used:
- A `## Coverage` list of checks. The checks covering a surface are derived from their `area:` (ADR-0032).

## `walk.md` — the walk order (`WALK.md`)

Purpose: the one file per project that says in what order a release is walked. Instantiated from `walk.md` to `docs/tests/acceptance/WALK.md`, typed `[[reference]]`, resting at `active` (or `deprecated`). What a walk sheet does with it is stated once in `tools/instructions/TESTING.md`, "The walk"; this entry is the syntax alone.

Frontmatter: the standing-document fields (`type`, `title`, `status`, `owner`, `created`, `updated`), plus one optional key:

- (optional) `gallery` (string): a command that regenerates the project's screen gallery. The walk sheet prints it at the top of the survey, as the thing to run and compare before walking anything.

Body: prose the walker reads once, then **one `### ` heading per sitting with one fenced `yaml` block under it**. The heading is the sitting's name as the sheet prints it. The block's keys:

| key | required | what it holds |
|---|---|---|
| `surfaces` (list) | one of the two | The `area:` strings this sitting claims, or `SUR-*` ids whose note title is that area string. A check joins the **first** sitting in file order that claims its area. |
| `checks` (list) | one of the two | Check ids pulled into this sitting regardless of area. |
| `state` (string) | recommended | The product state the sitting needs and the cheapest way to reach it, in the same register as a check's Setup line. |
| `bench` (list) | recommended | What must be physically present, signed in or installed before the sitting starts, one line each. |

A sitting block with neither `surfaces` nor `checks` claims nothing, and the generator reports it. No key carries a duration.

## `procedure.md` — a sitting's procedure (`docs/tests/acceptance/walk/`)

Purpose: the written script for one sitting of a release walk — the setup stated once, then numbered steps, each expectation tagged with the check step it satisfies. Instantiated from `procedure.md` to `docs/tests/acceptance/walk/<name>.md`, typed `[[reference]]`, resting at `active`. What a procedure is for, what the validator refuses and what the sheet prints are stated once in `tools/instructions/TESTING.md`, "The walk", rule 9; this entry is the shape a parser reads.

Frontmatter: the standing-document fields (`type`, `title`, `status`, `owner`, `created`, `updated`), plus one required key:

- (required) `sitting` (string): the `### ` heading in `docs/tests/acceptance/WALK.md` this procedure walks, word for word. It is the only link between the two files, and a value naming no sitting is reported by `walk-sheet.py --check`.

Body:

| part | what a parser reads |
|---|---|
| `## Setup` | Everything under the heading, printed verbatim once at the top of the sitting. |
| `## Steps` | The numbered items under it. A line matching `N.` at the start of a line begins a step; everything until the next such line belongs to it. **The step's number is its position, not the digit written** — `1.` on every item gives steps 1, 2, 3, which is what markdown renders. Lines inside a fenced block belong to the step and are not read for tags. |
| a step's first line | The screen: the first `SUR-####` id on it, or failing that the first surface title that matches a `SUR-*` note exactly. A step naming no screen is reported, not refused. |
| an expectation line | Any line inside a step carrying at least one expectation tag. Strip the list marker and the tags; what remains is the quote. |
| an expectation tag | `` `TST-####.N` `` or `` `TST-####` ``, in backticks, ASCII. `N` is the position of the cited check's step, counted the same way; the bare form cites a check whose steps are not numbered. Several tags on one line mean several checks expect the same thing in the same words. |
| the quote | Compared against the lines of the tagged check's `## Expect` section after stripping list markers and collapsing whitespace. Nothing else may differ. |

Any heading other than `## Setup` and `## Steps` is prose for the reader and is not parsed — `## Not covered here` is the conventional place to say which checks in the sitting the procedure does not yet reach.

## `check.md` — removed (ADR-0031)

There is no `check` type and no `check.md` template; an acceptance check is a `[[test]]` at `level: acceptance`, its fields documented under `test.md` above. Why the type was retired is stated once in `tools/instructions/TAXONOMY.md`, "`check` — retired". See `project-os-cockpit` ADR-0031, which supersedes ADR-0030.

## `release.md` (`type: [[release]]`)

Purpose: first-class release record with traceability to shipped features, changes, and verified tests.

Naming:
- Filename should be `REL-####-v<version>.md`; `id` should match the `REL-####` prefix.

Fields:
- (required) `version` (string): Human version string (e.g. `1.4.0`).
- (required) `tag` (string): VCS tag for the release (e.g. `v1.4.0`).
- (required) `date` (date string): Release (or planned release) date.
- (optional) `platform` (string): Target platform/channel when the project ships more than one.
- (recommended) `features` (list of links): `[[FEAT-...]]` shipped in this release.
- (recommended) `changes` (list of links): `[[CHG-...]]` notes included in this release.
- (recommended) `tests_verified` (list of links): `[[TST-...]]` verified for this release (see `../../tools/skills/release-verification/SKILL.md`).
- (recommended) `previous_release` (string/link): The prior `REL-*` for rollback targeting.
- (optional) `preparing` (boolean): `true` while this draft release is the one being prepared to ship. Two drafts may exist; only a `preparing` one is treated as in preparation.
- (optional) `ledgers` (list of `{file, sha}`): The verdict ledgers sealed into this release, each with the hash of its bytes; the validator checks each hash against the file.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.releases`) and summarized in the optional `releases.latest`/`releases.history` block.

## `plan.md` (`type: [[plan]]`)

Purpose: per-feature implementation plan living at `docs/features/<slug>/plan/PLAN.md`; the checklist of tasks that deliver the parent feature.

Fields:
- (required) `parent` (link): The `[[FEAT-...]]` this plan delivers. (Feature-scaffold generated plans may use `parent` only; the template's `id`/`implements` fields are optional for plans.)
- (optional) `implements` (list of links): Requirements the plan addresses.

Where used:
- Not tracked in `SNAPSHOT.yaml`; discovered via its parent feature's directory.

## `workflow.md` (`type: [[workflow]]`)

Purpose: canonical “front door” for a repo activity (what to run, inputs/outputs).

Fields:
- (recommended) `entrypoints` (list): Main scripts/commands (repo-relative).
- (optional) `prereqs` (list): Prerequisite tools/env/licenses (strings or links).
- (optional) `inputs` (list): Required inputs (paths/links).
- (optional) `outputs` (list): Expected outputs/artifacts/log locations.

Where used:
- Tracked in `SNAPSHOT.yaml` (`items.workflows`) for agent context and linked from workflow notes.
