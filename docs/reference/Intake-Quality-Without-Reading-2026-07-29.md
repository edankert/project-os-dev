---
type: "[[reference]]"
id: REFERENCE-INTAKE-QUALITY-WITHOUT-READING
aliases: ["Quality-without-reading intake"]
title: "Intake and verification record: project-os gaps against the quality-without-reading thesis (2026-07-29)"
status: active
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
scope: "project"
source:
  - "intake from the articles repo, 2026-07-29, against project-os template commit abc3ae3"
related: [ADR-0017, ISS-0019, ISS-0020, ISS-0021, ADR-0009, ADR-0010, ADR-0014]
---

# Intake: quality without reading the code (2026-07-29)

## Purpose

The disposition record for an eight-finding intake received 2026-07-29, assessing project-os against a seven-layer model of quality-without-reading-the-code developed in the `articles` repo. Kept because the verification work behind each disposition is more expensive than the filing, and because four findings were verified real and then **deliberately not adopted** — a decision that is worthless if the reasoning is not recoverable.

## Baseline

The intake reviewed a downstream synced copy at template commit `abc3ae3`. Verified: `abc3ae3` is the immediate parent of `40b2649`, which is this repo's own `.project-os-sync` baseline. The single intervening commit is *"The project inbox, and the cockpit release that fills it"* and touches none of the eight areas. **No finding needed discounting for staleness.**

The intake's `:file:line` references were flagged by its author as untrusted (taken from a downstream copy). Verified: every one resolved correctly against this tree. One trivial drift — `previous_release` was cited in `SCHEMAS.md`, and is at `SNAPSHOT.md:79` here.

## Scoping decision

**Partial.** project-os adopts the derivation principle and the extensions that ride on mechanisms already in force. It does not adopt the four layers that would require it to model the running system.

The reasoning is in [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]], including the four non-goals with the verified evidence for each. The short form: project-os can *record* a claim about the running system but cannot *derive* one, because it does not execute the project's code — and recording without deriving is what the principle forbids.

## Disposition, all eight

| # | Finding | Verified | Disposition |
|---|---|---|---|
| 1 | Derivation principle implemented twice, never stated | Confirmed. No statement anywhere; `ADR-0009:50` notices the habit without naming it | **Filed** — [[ADR-0017-Claims-About-Working-Software-Are-Derived\|ADR-0017]], with the intake's phrasing rejected as too strong (see below) |
| 2 | Nothing requires a test to be executable; no ratio | Confirmed. `validate-docs.py:1457-1462` nudges as an alternative remedy; `SNAPSHOT.md:96` counts by status only | **Filed** — [[ISS-0020-Nothing-Requires-A-Test-To-Be-Executable\|ISS-0020]], scoped to the metric only; requiring `command:` explicitly out of scope |
| 3 | No gate manifest | Confirmed. Three `WF-*` notes, all project-os operations | **Non-goal**, ADR-0017 |
| 4 | No observability representation | Confirmed. No SLO/telemetry/alerting/canary/flag vocabulary; `monitoring` at `STATUSES.md:106` is a *rejected* risk status, written "never … across 5,890 fleet status writes" | **Non-goal**, ADR-0017 — adding a vocabulary with zero observed demand inverts ADR-0008 |
| 5 | Reversibility not a designed property | Confirmed, narrower than written: `CHG-*` also has `merged → reverted`, not only `REL-*` | **Non-goal**, ADR-0017 — pre-commitment reversibility is a prediction, so clause 3 forbids its author writing it |
| 6 | No code-contract artifact | Confirmed | **Non-goal**, ADR-0017 — strongest of the four; revisit with [[ISS-0018-Traceability-Stops-At-The-Docs-Boundary\|ISS-0018]], whose mechanism it shares |
| 7 | Absence is invisible | Confirmed, and **sharper than written** — see below | **Filed** — [[ISS-0019-Verify-Is-Blind-To-Tests-That-Were-Never-Linked\|ISS-0019]], severity high |
| 8 | Waiver has no budget, expiry, or ageing | **Half stale.** Expiry exists and errors (`validate-docs.py:1380-1393`, ADR-0010, TASK-0068). Budget half survives | **Filed narrowed** — [[ISS-0021-Verification-Waivers-Have-No-Budget\|ISS-0021]], severity low |

## The two places verification changed the finding

**Finding 7 was upgraded.** As written it was conceptual — nothing records where there are *no* tests — and in that form it is about untested regions of code, which project-os cannot see (hence a non-goal). But the mechanical instance is live and severe: `validate-docs.py:1397` iterates `for tst in sorted(linked_tests)`, so with an empty list every finding the gate can produce is skipped. An item reaches terminal with no test and no waiver in total silence, against QUALITY.md's explicit *"silent skips are a build failure."* Measured here: **52 registered terminal items** (40 tasks, 7 issues, 5 features) in that state, a floor because retention prunes closed items out of the snapshot the walk starts from. `REQ-0006`'s own wording — *"when linked tests are not passing"* — encodes the same blind spot, so requirement and implementation agree with each other and both disagree with QUALITY.md.

**Finding 1's phrasing was rejected.** The intake proposed: *"Any claim about whether the software works must be derived from execution, never asserted by an agent."* That outlaws manual tests, which ADR-0010 deliberately preserved, and outlaws `human:`/`asserted:` evidence tokens, which ADR-0014 deliberately made legal — so it cannot be the rule those two decisions were following. ADR-0017 states it in three clauses instead, of which the third (*never written by the party seeking the transition it gates*) is the invariant that actually unifies ADR-0009, ADR-0010, ADR-0014 and ISS-0017.

## Sequencing constraint worth preserving

ISS-0019 and ISS-0021 interact and must not be worked independently. ISS-0019's likely disposition for many of its 52 items is a waiver, which would take this repo from 15 outstanding waivers to roughly 67 — so arming a waiver budget before ISS-0019 lands would cap the honest exit while the silent one stays open. ISS-0019 first. Both notes record this.

## What was right about the intake

Its two cautions were the load-bearing content. *"Don't let this expand the system for its own sake"* is why four verified-real findings are non-goals, and *"the scoping decision is the real work; the tickets are the easy part"* was accurate — the scoping question took longer to answer than all four notes took to write. An intake that names its own failure modes and asks to be checked against the tree is the shape that made this cheap to act on.

## Maintenance

Superseded by events, not edits. If any non-goal is revisited, amend ADR-0017's non-goals table (the normative record) and leave this note as the intake's history.
