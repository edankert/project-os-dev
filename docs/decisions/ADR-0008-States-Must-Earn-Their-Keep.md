---
type: "[[adr]]"
id: ADR-0008
aliases: ["ADR-0008"]
title: "States must earn their keep: collapse the status taxonomy to observed usage, one terminal status per work-item type"
status: accepted
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: ["review:2026-07-25-fleet-state-audit"]
decision: "Delete every status value with no observed use across the fleet; give each work-item type exactly one terminal status (merging issue `closed` into `fixed`); model blocked-ness as a relationship (`depends:`) rather than a state; and treat reopening as a plain transition back to `open`. Whether `approved` survives on requirements is deliberately left to the implementing task, decided against the fleet numbers"
context: "Across 10 project-os repos and 3,775 notes, 5,890 `status:` writes were reconstructed per-note from git history. 13 note types declare 64 status values; 12 of those values were written fewer than 10 times and 6 were never written at all. 53% of tasks only ever carry one status and 39% are born `done`; 67% of issues carry one status and 55% are born terminal; `fixed → closed` has 3% follow-through (324 issues reached `fixed`, 10 reached `closed`)"
alternatives:
  - "Keep the taxonomy and enforce it harder — rejected for the reason ADR-0007 gave about `verified`: uniform non-use across every repo over months is evidence about the instrument, not about ten negligent repos. `next` was written 8 times and `blocked` 3 times in 5,890 writes; no amount of enforcement turns those into states people think in"
  - "Add the drifted vocabulary instead of deleting states (`pending` 166 writes, `todo` 79, `fulfilled` 80, `resolved` 20) — rejected: every one is a synonym for a state that already exists (`backlog`, `backlog`, `implemented`, `fixed`). Admitting synonyms grows the taxonomy without adding a single distinction"
  - "Per-project taxonomies — already supported (`load_allowed_status` reads each repo's own STATUSES.md) and deliberately not made the default: it forces every agent to establish a repo's dialect before it can read a status, which is the cost the fleet-wide vocabulary is paying for"
  - "Keep `closed` and enforce the `fixed → closed` step — rejected: the step encodes 'implemented' vs 'verified', a distinction the test gate and TST-* notes already carry with evidence attached. Recording it a second time as a status word is what ADR-0007 retired `verified` for"
consequences:
  - "The taxonomy drops from 64 declared values to roughly 45; six values that were never written once (`failing` excepted — see below) disappear entirely"
  - "`failing` is retained on tests despite zero observed writes. It is not dead vocabulary, it is an unreachable state under the current authoring model, and ADR-0010 makes it reachable by stamping test status from execution. Deleting it would remove the outcome the gate exists to detect"
  - "Issues gain a single terminal status. `metrics.issues_open` must be redefined in the same change or 313 fleet-wide `fixed` issues stay invisible (ISS-0008)"
  - "Blocked-ness moves to `depends:`, which already exists and already carries which item does the blocking — strictly more information than the `blocked` status it replaces"
  - "Migration touches roughly 250-300 notes carrying statuses that are already illegal today: 71 tasks at `superseded`, 50 issues at `done`, 30 at `pending`, 8 tests at `active`, plus phase and reference drift. ISS-0009 tracks the existing drift; the merge of `closed` into `fixed` adds 54 more"
  - "`NOTE-STATUS` graduates from warning to error once migration completes — its code comment already anticipates this ('Graduate to report.error once the fleet is migrated')"
  - "The cockpit's status bands (`project_os_cockpit/statuses.py`) need the collapsed vocabulary, as they did for ADR-0007"
  - "One-time cost, paid fleet-wide: the `verified → implemented` and `fulfilled → implemented` migrations under ADR-0007 account for ~160 of the 5,890 writes measured here. A vocabulary change is not free and should be made once, deliberately, rather than incrementally"
supersedes: ""
superseded: ""
related: [ADR-0007, ADR-0006, ADR-0005, FEAT-0013]
---

# States must earn their keep

## Context

The status taxonomy has been extended several times (deferral in FEAT-0011, requirement lifecycle in FEAT-0012, terminality in ADR-0007) and never contracted. This decision is the contraction, argued from usage rather than from taste.

The measurement covers all 10 project-os repos on this machine: 3,775 notes, and every `status:` value ever written to a note in `docs/`, reconstructed per-note from git history so that intermediate states are not hidden by the current value. That is 5,890 writes.

**1. Twelve of the 64 declared values are dead or vestigial.**

| Value(s) | Writes across 5,890 |
|---|---|
| `failing`, `deprecated`, `monitoring`, `staged`, `rolled-back`, `rejected` | **0** |
| `mitigating`, `reverted` | 1 each |
| `blocked` (task/issue/test), `reopened` | 3 each |
| `next` (task) | 8 |
| `retired` | 9 |

**2. The lifecycles are mostly fiction, because notes are written after the work.**

| Type | Only ever one status | Born terminal | Dominant path |
|---|---|---|---|
| Task (1,638) | 53% | 39% | `done` (39%), `backlog→done` (24%) |
| Issue (505) | 67% | 55% | `fixed` (41%) |
| Test (77) | 99% | 78% | `passing` (78%) |
| Feature (275) | 40% | 19% | `done` / `backlog` / `backlog→done` |

Around 5% of tasks ever pass through `doing`. A seven-state task machine is being used as two and a half.

**3. `fixed → closed` has 3% follow-through.** 324 issues reached `fixed`; 10 went on to `closed`. Because `metrics.issues_open` counts only `{open, in-progress, blocked, reopened}`, those 313 stalled issues are invisible in every metric the system reports — the backlog looks clean precisely because the second step is never taken. That is tracked separately as [[ISS-0008-Issues-Open-Metric-Excludes-Fixed|ISS-0008]].

**4. The gap is filled by invented vocabulary.** ~370 writes used values outside the taxonomy: `pending` (166), `fulfilled` (80), `todo` (79), `verified` (79, post-retirement), `resolved` (20), `completed` (12), `published` (11), `met` (7). 71 tasks currently sit at `superseded`, which has never been a legal task status. The system's own validator reports 164 of these as warnings and none as errors.

## Decision

### 1. A status value with no observed use is deleted

Concretely, subject to the migration in [[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]]:

| Type | Now | Proposed |
|---|---|---|
| task | 7 | `backlog, doing, done, cancelled, deferred` |
| issue | 9 | `triage, open, fixed, wont-fix, deferred` |
| feature | 8 | `backlog, in-progress, done, cancelled, superseded, deferred` |
| requirement | 7 | `draft, implemented, superseded, cancelled, deferred` |
| test | 6 | `passing, failing` |
| risk | 4 | `open, closed` |
| release | 4 | `released, rolled-back` |

`failing` is the deliberate exception to the usage rule, for the reason recorded in the consequences: it is unreachable rather than unwanted, and [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] makes it reachable.

### 2. One terminal status per work-item type

Issue `closed` is merged into `fixed`. Every other type already has one terminal word (`done`, `implemented`) plus the descoping outcomes (`cancelled`, `superseded`, `wont-fix`), which resolve scope without claiming delivery and are kept.

### 3. Blocked-ness is a relationship, not a state

`blocked` is deleted from task, issue, and test. An item waiting on another records `depends: [ID]` — which already exists, is already link-checked, and names *what* is blocking rather than merely asserting that something is. An item can be blocked and in `doing` at the same time, which the status model cannot express and the relationship model can.

### 4. Reopening is a transition, not a status

`reopened` (3 writes) is deleted. A regression sets the issue back to `open`; git holds the history, and the note body records why.

### 5. Deliberately not decided here: whether `approved` survives

`approved` (99 writes) is the one value where the evidence cuts both ways. Against it: `draft → implemented` (51 notes) outnumbers `approved → implemented` (36), and the gate it powers — `REQ-PREMATURE` — fires 3 times across the whole fleet. For it: it is the only marker of "criteria agreed, features may now implement against this", which is a real checkpoint in `feature-scaffold` and the only thing standing between a draft requirement and code written against it.

Deleting it would also reopen a question ADR-0006 settled ("approval precedes implementation"). That is a larger decision than a vocabulary trim, so it is scoped to [[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]], to be settled with the numbers in hand and recorded as an amendment here.

## Consequences

See frontmatter. The load-bearing ones: the taxonomy shrinks by roughly a third and every surviving value is one someone actually writes; blocked-ness gains an object; and the `fixed`/`closed` split stops silently hiding 313 issues.

The cost is a fleet-wide data migration ([[RISK-0001-Fleet-Status-Migration|RISK-0001]]) and the loss of two glance-level distinctions — "implemented vs verified" on issues and "queued vs next" on tasks. The first survives in the test gate and TST links, where it carries evidence. The second was written 8 times in 5,890 and is not a distinction anyone was making.

## Amendment (2026-07-25) — decisions taken at implementation, and three corrections

Implementing this ADR under the constraint *"completed states must not change"* forced its open questions closed and corrected three of its claims. All figures re-derived from the 3,826-note fleet baseline captured before migration (`baseline.json`), not from the draft table above.

### 1. The deletion rule, made precise

The ADR said "delete every status value with no observed use". Implementation needed a threshold that could not silently relabel finished work, so the operative rule is:

> **Delete a value iff it has fewer than 10 writes fleet-wide AND zero notes currently hold it.**

The second clause is what protects the invariant. A value with live notes cannot be deleted without rewriting those notes, and where they are terminal that rewrites the record of what was completed.

### 2. `approved` survives (clause 5 resolved)

99 writes, 10 live notes. It passes the rule on both counts, so keeping it is what this ADR's own principle *requires* — not an exception to it. The conflict with [[REQ-0014-Requirement-Lifecycle-Advancement|REQ-0014]]'s third criterion and ADR-0006's approval-precedes-implementation clause therefore **does not arise**, and `REQ-PREMATURE` stays.

### 3. Three values are ADDED, not deleted

The draft table treated these as drift. They are gaps in the taxonomy:

- **`superseded` on `task`** — 71 notes (your-trainer), every one carrying `superseded_by: [[FEAT-0098-iOSParity]]`. The work was *absorbed into a successor feature*, not abandoned. `cancelled` would misrecord it as dropped and `done` would claim it shipped. Features and requirements already have `superseded`; tasks get superseded too.
- **`superseded` on `phase`** — 1 note (PHASE-012, `superseded_by: [[PHASE-019-iOSParity]]`). Same shape.
- **`ready` on `test`** — 11 writes, and the only honest home for the 8 manual tests currently at `active`. The draft's `{passing, failing}` has no state for *defined but not yet run*: mapping those to `passing` fabricates a verification result — precisely what [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] exists to stop — and `failing` asserts a failure that never happened. `ready` is also the correct initial state for a test the runner has not yet executed.

### 4. `retired` is kept

9 writes, 9 live notes, all terminal requirements. Below the write threshold but failing the zero-live clause. Folding it into `superseded` would rewrite 9 completed records to say something different about why they ended.

### 5. Corrected outcome: 64 → 53, not 64 → ~45

| Type | Was | Now | Change |
|---|---|---|---|
| task | 7 | 6 | −`next`, −`blocked`, +`superseded` |
| issue | 9 | 5 | −`in-progress`, −`blocked`, −`reopened`, −`closed` (merged into `fixed`) |
| feature | 8 | 8 | unchanged — `planned` (145 writes) and `in-review` (90) both pass the rule |
| phase | 4 | 5 | +`superseded` |
| requirement | 7 | 7 | unchanged — `approved` and `retired` both kept |
| risk | 4 | 2 | −`mitigating`, −`monitoring` |
| workflow | 3 | 3 | unchanged — see "needed terminals" below |
| adr | 4 | 3 | −`rejected` |
| test | 6 | 3 | −`draft`, −`blocked`, −`deprecated`, +`ready`; `{ready, passing, failing}` |
| release | 4 | 3 | −`staged` only |
| change / plan / reference | 8 | 8 | unchanged |
| **Total** | **64** | **53** | **−11 net (14 deleted, 3 added)** |

### 5a. Needed terminals are kept despite zero writes

Three values have never been written and are nonetheless retained, because deleting them would leave a type with **no way to record an outcome that can genuinely occur**:

- `deprecated` on `workflow` and `reference` — the only retirement state either type has.
- `rolled-back` on `release` — a rollback is a real event; `staged` is deleted because it is redundant with `draft`, but a release that reverted needs somewhere to land.
- `failing` on `test` — unreachable only because nothing executes tests today, which [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] fixes.

This is the same category as `failing` in the original consequences, generalised: **zero writes plus no alternative destination means unreachable, not unwanted.** Zero writes plus an existing synonym means dead, and those are the ones deleted.

The draft's ~45 assumed `approved`, `retired`, `planned` and `in-review` would go. Each is written by the fleet, and three have live terminal notes. **A 17% cut that preserves every completed record is the correct outcome; a 30% cut that rewrites finished work is not.** The ADR's thesis is unchanged — states must earn their keep — but "earning it" is measured against the whole write history and the live corpus, not a draft table.

### 6. Migration is completion-preserving by construction

Of the 2,808 terminal notes in the baseline, the migration touches the status word of **54** (issue `closed` → `fixed`) and **0** others. Both words are terminal before and after, in the validator and in the cockpit's `DONE_BY_TYPE`. Every other terminal note is byte-identical. Non-terminal remappings (`pending`→`open`, phase `draft`→`planned`, plan/reference tidy-ups) change no completion state.

Two changes **do** alter how an item reads, and are called out rather than buried:

- **50 issues at `done` → `fixed`.** `done` was never a legal issue status and is absent from the cockpit's `DONE_ISS`, so these render as *not complete* today despite their authors marking them finished. Migration makes them complete. This is a correction of a display bug, but it is a visible change and is recorded here as one.
- **3 change notes at `active`/`draft`/`in-review` → `merged`.** All three are dated and landed; `{merged, reverted}` has no pre-merge state.
