---
type: "[[adr]]"
id: ADR-0011
aliases: ["ADR-0011"]
title: "Every validator rule is an error or is deleted — no permanent warning tier"
status: accepted
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: ["review:2026-07-25-fleet-state-audit"]
decision: "Every check in validate-docs.py is either an error or is removed. `warn` survives only as a dated migration state: a warning must name the cutover date at which it becomes an error, that date must be encoded in the code (the FEATURE_REQ_GATE_FROM pattern) and be no more than 90 days out. A check with no cutover is promoted or deleted"
context: "All 10 project-os repos currently exit 0 — `validate-docs: OK` — while carrying roughly 600 warnings between them: 206 REVIEW (independent review never ran), 271 REQ-BOXES, 54 FEATURE-REQ, 164 NOTE-STATUS, 47 VERIFY-WAIVED, plus PATH-ALIAS and REQ-PREMATURE. No repo's build has ever failed on any of them and no backlog tracks them"
alternatives:
  - "Keep warnings as informational output — rejected: 600 unread warnings across ten green repos is the operational definition of non-informational. Warnings that never change anyone's behaviour are worse than absent, because they train readers to skim past the errors printed beside them"
  - "Route warnings to a dashboard or report instead of the validator — rejected: relocating output that nobody acts on moves the ignoring without reducing it, and adds a surface to maintain"
  - "Promote everything to error immediately — rejected: it reds every repo's CI on the next commit for debt the tooling itself permitted, which is the objection ADR-0007 already sustained when it made FEATURE-REQ forward-only"
  - "Add a severity config so each repo picks its own enforcement level — rejected for the reason ADR-0007 gave against a per-project verification switch: it formalises the drift instead of resolving it, and makes a rule's meaning depend on which repo you are standing in"
consequences:
  - "Each existing warning code gets an explicit disposition — promote (with a dated cutover) or delete — recorded in TASK-0069; no code may end that triage still warning without a date"
  - "The fleet's existing debt must be cleared before promotion, not after: ~325 REQ-BOXES/FEATURE-REQ findings and 164 NOTE-STATUS findings are prerequisites (TASK-0070), and NOTE-STATUS is already gated behind the ADR-0008 migration"
  - "REVIEW is the hardest case: 206 findings means independent review is effectively not running. It is either wired into close-out so it does run, or its scope narrows to CHG-* notes where the cost is justified. Promoting it as-is would fail every repo"
  - "VERIFY-WAIVED stays a warning under an exemption this ADR grants explicitly: a waiver is a logged artifact by design (QUALITY.md), so the finding is the log entry rather than a defect. ADR-0010 gives waivers an expiry, and an *expired* waiver is an error"
  - "The FEATURE_REQ_GATE_FROM pattern becomes the standard mechanism for every promotion, so grandfathering is uniform and visible in one place rather than reinvented per check"
  - "The 90-day ceiling means a migration that stalls fails the build rather than dissolving into permanent warning noise — which is what happened to every warning currently in the fleet"
supersedes: ""
superseded: ""
related: [ADR-0004, ADR-0007, ADR-0008, FEAT-0017]
---

# No permanent warning tier

## Context

`validate-docs.py` has two severities. Errors exit non-zero and fail the pre-commit hook and CI. Warnings print and are ignored — structurally, since `main()` returns 0 regardless, and `--quiet` suppresses them entirely.

Current fleet state, with every repo reporting `validate-docs: OK`:

| Code | Findings | What it means |
|---|---|---|
| `REQ-BOXES` | 271 | Terminal requirements with unresolved acceptance criteria |
| `REVIEW` | 206 | Settled tests/changes with no independent review recorded |
| `NOTE-STATUS` | 164 | Notes carrying statuses outside the taxonomy |
| `FEATURE-REQ` | 54 | Features closed over unresolved requirement criteria |
| `VERIFY-WAIVED` | 47 | Terminal status under a recorded waiver |
| `PATH-ALIAS`, `REQ-PREMATURE` | 7 | Legacy field form; implementing against a draft requirement |

`ADR-0004` made risk scans, verification gating and impact analysis *mandatory* precisely because "convention-only rules get silently skipped under context pressure" — the sentence is in QUALITY.md. A warning is a convention-only rule with extra steps: it prints, and then the build passes.

Two of these deserve specific note.

**`REVIEW` at 206** means the independent-review rule in QUALITY.md — "any change that creates or updates a `TST-*` or `CHG-*` note, and any transition to requirement `implemented` or feature `done`, requires an independent review pass" — is not running. An `independent-reviewer` subagent exists and is wired into the Claude adapter; the rule is simply not reached in practice.

**`NOTE-STATUS` at 164** is warned rather than errored on purpose, and the code says so: *"Failing those builds outright would punish repos for drift the tooling allowed. Graduate to `report.error` once the fleet is migrated."* That is exactly the right instinct — and it is also the pattern this ADR wants to make universal and time-bounded, because "once the fleet is migrated" with no date attached is how a temporary warning becomes a permanent one.

## Decision

### 1. Two dispositions only

Every check is an **error**, or it is **deleted**. A check nobody will fix is not a standard; it is commentary, and it belongs in the instructions rather than in the tool.

### 2. `warn` is a migration state with a date

A warning is legal only when the code names the cutover at which it becomes an error, following the existing `FEATURE_REQ_GATE_FROM` pattern:

```python
FEATURE_REQ_GATE_FROM = "2026-07-25"   # warning before, error on/after
```

The cutover must be **no more than 90 days** from the day the warning is introduced. Past it, the check errors — for everyone, with grandfathering keyed on the note's `updated:` date exactly as ADR-0007 specified.

### 3. Debt is cleared before promotion, not after

A check is promoted only once the fleet finding count for it is zero. That ordering is what makes the promotion a no-op at the moment it happens, and it is the reason [[TASK-0070-Fleet-Backfill-Before-Cutover|TASK-0070]] blocks [[TASK-0069-Triage-Validator-Warnings|TASK-0069]]'s promotions rather than following them.

### 4. One standing exemption: `VERIFY-WAIVED`

A waiver is *designed* to be a logged artifact — QUALITY.md requires the log entry and forbids the silent skip. Reporting it is therefore correct behaviour, not deferred enforcement. It stays a warning permanently. Under [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] waivers gain an expiry, and an expired waiver is an error.

## Relationship to the live cutover

`FEATURE_REQ_GATE_FROM` is set to **2026-07-25** — today. The `FEATURE-REQ` and terminal `REQ-BOXES` gates arm now, keyed on each note's `updated:` date, which means the 325 findings currently sitting in the fleet convert to build failures the moment those notes are touched for any reason. Under this ADR's clause 3 that ordering is backwards: the debt should have been cleared first.

That is a live operational decision rather than a hypothetical, and it is tracked as [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] — the first real test of the policy this ADR proposes.

## Consequences

See frontmatter. The honest summary: this ADR converts ~600 pieces of ignored output into either work or deletions. Some of it will be deletions, and that is a success rather than a retreat — a rule the fleet has declined to follow for months, uniformly, is a rule the system does not actually hold.

## Amendment (2026-07-25) — the mechanism is a ledger, not a date

Clause 2 above specified the `FEATURE_REQ_GATE_FROM` pattern — a cutover date in code, compared against each note's `updated:`. Implementing it revealed the pattern is the wrong instrument, for a reason its own code comment already admitted:

> editing a grandfathered note for any reason re-arms the gate on it

A date compared against `updated:` measures **when a note was last edited**, not when the item closed. Two failure modes follow, and both were live:

1. **Edit-triggered failure.** Fixing a typo in a grandfathered note converts a warning into a build failure, in a repo whose owner has no context on the decision. A routine template sync — which touches `updated:` across many notes at once — could detonate dozens at a time.
2. **Silent permanent exemption.** A stale or malformed `updated:` was treated as grandfathered, so the gate never fired on notes it could not date.

**Replaced by `tools/GRANDFATHERED.yaml`**: an explicit, ID-named list of the items that were already violating a gate at the moment it was promoted. Listed items warn; everything else errors, immediately, with no dependence on dates. The ledger only shrinks — an entry is deleted when its debt is paid, and a stale entry is inert rather than dangerous. `tools/scripts/grandfather.py --write --refresh` regenerates it.

This also resolves [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]]: there is no longer a cutover to arm.

### Ledger at promotion (2026-07-25)

| Repo | VERIFY | REQ-BOXES | FEATURE-REQ |
|---|---|---|---|
| your-trainer | 3 | 121 | 30 |
| your-sudoku | — | 74 | 15 |
| your-health | — | 39 | 1 |
| your-applications.com | — | 21 | 6 |
| edankert.com | — | 10 | 1 |
| obsidian-supernote-sync | — | 4 | — |
| project-os-cockpit | — | 1 | 1 |
| **327 entries; project-os, project-os-dev and yourtrainer-mcp carry none.** |

The `VERIFY` entries are new debt made *visible*, not new debt created: ADR-0008 made issue `fixed` terminal, which gated ~360 fleet-wide issues that had been sitting in the old `fixed` limbo ungated. Three of them link a test that has never passed.

### What is genuinely implemented, and what is not

- **Done:** `NOTE-STATUS` promoted to error at zero findings (clause 3 honoured — the migration cleared it first) and extended to registered notes; the ledger mechanism; `ITEM-STATUS`/`COUNTER`/`METRICS` retained deliberately (see [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]'s amendment).
- **Not done:** the full per-code triage ([[TASK-0069-Triage-Validator-Warnings|TASK-0069]]) and the `REVIEW` disposition ([[TASK-0071-Independent-Review-Wiring|TASK-0071]]). **589 warnings remain fleet-wide**, of which 206 are `REVIEW`. Clause 1 is therefore *not yet satisfied* — this ADR is accepted as a decision, not as a completed state.
