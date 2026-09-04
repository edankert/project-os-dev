---
type: instruction
id: INSTR-TAXONOMY
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-03
tags: [instructions, taxonomy]
---

# Taxonomy (allowed values)

This file defines default allowed values for common fields so multiple agents/LLMs stay consistent.

Projects may override; if you do, update templates and any automation that assumes these values.

## `kind` (surfaces)
- `screen` — a place a person navigates to
- `flow` — a sequence across screens, named because it is walked as one thing
- `subsystem` — a behaviour with no single screen (sync, licensing, physics)
- `surface-less` — the honest answer where a check is about the record, the build or the repo rather than the product

A `SUR-*` names a place in the product; a check's `area:` names one of these. **The name is written once, in the surface note, instead of retyped on every check that touches it** — 94 distinct `area:` strings across one repo's 581 checks is what the type exists to end.

## `status` (surfaces)
- `active`, `retired`, `superseded`

A surface is not *done*: it exists until the product stops having it. `retired` says the place is gone; `superseded` says another surface took it over and names which.

## `owner` (all notes)
See `OWNERSHIP.md` for allowed formats and the canonical registry.

## `severity` (issues)
- `low`, `medium`, `high`, `critical`

## `priority` (requirements)
- `low`, `medium`, `high`

## `order` (phases)
Positive integer sort order for roadmap sequencing.

## `effort` (tasks)
- `XS`, `S`, `M`, `L`, `XL`

## `likelihood` (risks)
- `low`, `medium`, `high`

## `impact` (risks)
- `low`, `medium`, `high`

## `component` (issues)
Project-defined free text label, but keep it stable. Examples:
- `docs`, `build`, `tests`, `tooling`, `runtime`, `ui`, `api`

## `kind` (tests) — removed (ADR-0034)
- There is no `kind` field. `command:` answers who runs a test: present, the runner; absent, a person (`../../docs/__templates__/SCHEMAS.md`, `test.md`).

## `level` (tests)
- `unit`, `integration`, `system`, `e2e`, `acceptance`
- **`acceptance` is the discriminator of the merged type (ADR-0031)**: a test at this level is the thing a person walks — it rests at `status: active`, its verdict is in the release ledger ("Acceptance outcomes (the ledger's vocabulary)" below), and it carries the acceptance fields below. Everything else on the scale is executable. The field has always been here; since ADR-0031 it carries the distinction the retired `check` type used to.
- A test moves along the scale rather than between types; how a walk becomes automated is stated once in `TESTING.md`, "When to create", rule 3. (`covered_by:` was removed with the ledger model; `SCHEMAS.md`, "Acceptance fields".)

## `scope` (tests)
- `feature`, `system`

## Acceptance outcomes (the ledger's vocabulary)

The verdict on an acceptance test is **an event in a per-release, single-platform ledger**, not a field on the note (ADR-0037). It is a fact about *(check × platform × release)* and a scalar cannot hold a three-tuple — measured before deciding: 579 of `your-trainer`'s 581 acceptance notes carried no platform at all, while every one of its 513 passes was earned on Android.

| mark | means | gate | survives the seal |
|---|---|---|---|
| `pass` | walked, and it held | clears | yes, until invalidated |
| `partial` | some clauses hold, some do not | clears | yes, until invalidated |
| `na` | **cannot apply here** — no such surface on this platform | clears | yes, until invalidated |
| `excused` | **not done this cycle, by decision** — out of scope, low risk, no time | clears | **no — expires with its release** |
| `blocked` | **could not be run right now** — rig down, device unavailable | **blocks** | no |
| `question` | walked, and the *check* is not understood | **blocks** | no |
| `fail` | walked, and it failed | **blocks** | no |
| *(no entry)* | nobody has run it on this platform | **blocks** | — |

**Every mark but `pass` is refused without a reason.** A check that clears the gate without being run, or blocks it after being run, is a claim about the release; the claim carries its evidence or it is refused.

**"Not run" is three answers, not one, and only two of them clear.** `na` and `excused` are *decisions* somebody made about this release; `blocked` is an *accident* that will be gone next week, and a gate that clears because the rig was down clears on whatever happens to be broken that day.

**`na` and `excused` differ in exactly one property and it is the one that matters: whether the exception comes back.** `na` is about the check and the platform, so re-asking it every release is the maintained-matrix failure this design removes. `excused` is about the check, the platform **and this release** — and a field on a note cannot hold *"expires with its release"* at any price, which is how ADR-0029's per-release exception silently became permanent when its mark moved from `[!]` to `[-]`.

**There is no "not yet walked" value.** You do not record that you did not do something: no entry for a platform means owed on that platform, so adding a platform makes every check immediately owed there with no schema change and no backfill.

**An invalidation is an event, not a mark.** `{check, invalidated_by, date}` sitting after the verdict it overtakes — which is why `rerun` is not in this table.

### Legacy values, read forever and never written

Two earlier vocabularies stay **readable** so that a repo mid-migration keeps working; neither is current, and nothing writes them.

| era | values |
|---|---|
| ADR-0029 — [Minimal's alternate checkboxes](https://minimal.guide/checklists) | `" "` `x` `/` `-` `!` `?` |
| ADR-0034 — the same distinctions as words | `todo` `done` `incomplete` `canceled` `important` `question` `rerun` |

The mapping into the ledger is `done`→`pass`, `incomplete`→`partial`, **`canceled`→`na` (never `excused`)**, `important`→`fail`, `question`→`question`, `todo`→*no entry*, `rerun`→*an invalidation*.

`canceled` gets a written rule because one old value has two successors: a migration that guessed would either make a permanent exception expire or make a per-release one permanent. `na` is right for a backfill — nothing in the old field said which release it belonged to, and `excused` is precisely the value that claims one.

**`mark:` is not `status:`.** An acceptance test's lifecycle is `status:` — it rests at `active`, and `retired` is terminal. Its verdict is not on the note at all. That is what keeps it outside the runner-only rule, the independent-review gate and the `Run` obligation — see `STATUSES.md` `[[test]]`.

## `check` — retired (ADR-0031)

**There is no `check` type.** An acceptance check is a `[[test]]` at `level: acceptance`; a note that carried `type: "[[check]]"` was migrated, keeping its old id as an alias.

*(This heading read "`check` versus `level: acceptance` on a test — Both exist and they are not the same thing…" until 2026-08-19. It survived ADR-0031 by nobody reading past the mark table, and was then copied into two more repos by the same sync that was fixing [[ISS-0217]]. The ISS-0218 drift check reads the mark TABLE and cannot see prose, which is why this one needed a person.)*
