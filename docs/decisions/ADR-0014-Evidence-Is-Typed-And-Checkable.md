---
type: "[[adr]]"
id: ADR-0014
aliases: ["ADR-0014"]
title: "Evidence is typed and checkable, and the requirement is not confined to requirements"
status: proposed
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
source: ["fleet measurement 2026-07-29: 4,833 ticked claims across 12 repos"]
decision: "A ticked box on any note type is a claim, and a claim carries a typed evidence token naming what was done and at which revision. The token vocabulary is closed and machine-readable (`test:`, `mutation:`, `runtime:`, `human:`, `asserted:`); `asserted:` is legal, visible, and blocks nothing except terminal transitions. The REQ-BOXES check generalises to every note type that carries ticked claims"
context: "ADR-0006 required evidence pointers on requirement acceptance criteria and the validator enforces it as REQ-BOXES. Measured across 12 repos: requirements carry evidence on 60.3% of ticked boxes, tasks on 5.1%, tests on 0%. The mechanism works. It was scoped to the note type holding 209 claims and never extended to the one holding 2,921"
alternatives:
  - "Require evidence prose on task DoD lines without typing it — rejected: 36% of the evidence that already exists is prose only, which no validator can check and no reader can rank. Adding more unrankable prose is the current state at greater volume"
  - "Extend REQ-BOXES to tasks unchanged — rejected: it checks that a pointer is present, not that it is true or current. Presence is satisfied by the word 'evidence' followed by anything"
  - "Forbid `asserted:` and require every claim to be machine-verified — rejected: it produces the fake automation ADR-0010 rejected for manual tests. Some claims are genuinely judgement, and the useful move is making them visible and rankable, not illegal"
  - "Infer evidence strength with an LLM at close-out — rejected: it re-creates the conflict of interest ADR-0010 removed, with the party seeking the transition also grading the proof"
  - "Do nothing until the hosted platform exists — rejected: this pays off in eleven repos on the day it lands and needs no service, and ADR-0015 may never be accepted"
consequences:
  - "Every ticked box in the fleet becomes machine-readable as a claim with a strength; today 93.9% of them are unrankable"
  - "`asserted:` will be the honest answer for a large share of existing boxes, and the first fleet run will look worse than the current silence. That is the true state being made visible, as with ADR-0010"
  - "Evidence gains a revision, so a claim can go STALE when its blast radius changes — the first check in the system that can invalidate a claim without anyone editing the note"
  - "The task template, SCHEMAS.md and close-out gain a step; task DoD lines get longer"
  - "`project-os-bench` gains an objectively gradable dimension, since evidence tokens are checkable without an LLM judge"
  - "Retrofitting is not required: the rule applies to boxes ticked after adoption, and untyped historical boxes read as `asserted:`"
related: [ADR-0006, ADR-0010, ADR-0008, REQ-0006]
supersedes: ""
superseded: ""
---

# Evidence is typed and checkable

## Context

[[ADR-0006-Requirement-Advancement-On-Evidence|ADR-0006]] established the rule: tick a box only with *"an evidence pointer (path, command, or note ID)"*. `validate-docs.py` enforces it as `REQ-BOXES`. It is a good rule and it works.

Measured across all 12 project-os repos, counting only **ticked** boxes — an unticked box is a plan, a ticked one is a claim that something is true:

| note type | ticked claims | carry evidence | |
|---|---:|---:|---:|
| requirement | 209 | 126 | **60.3%** |
| phase | 188 | 15 | 8.0% |
| feature | 32 | 2 | 6.2% |
| task | **2,921** | 148 | **5.1%** |
| issue | 197 | 5 | 2.5% |
| test | 305 | 0 | **0.0%** |
| **total** | **4,833** | **296** | **6.1%** |

The shape of the finding is the opposite of the usual one. This is not a rule nobody follows — it is a rule that is followed **twelve times more often where a validator checks it**, and the validator only checks the note type holding 4% of the claims. The instrument works and is aimed at the wrong place: 2,921 task DoD claims are governed by nothing at all, and 305 ticked boxes on `TST-*` notes carry no evidence whatsoever, which is a peculiar thing for a test to be short of.

Of the 296 evidence clauses that do exist, only **23% name a test** — the one shape a machine can re-run. 36% are prose. So even inside the well-governed 60%, most evidence cannot be checked by anything except a reader who already knows the answer.

The failure this produces is documented and recurrent. In one session on 2026-07-28, six separate claims in `project-os-cockpit` asserted more than the code did — a placeholder scrub whose own test name promised a field it never touched; a size limit advertised at 25 MB that a shared body reader capped at 2 MB; a token-parity claim with no parity; and *"thumbnail rendered"* for images that a Content-Security-Policy had blocked from ever painting. Every one was caught by a person or by accident. None was catchable, because *"verified over real HTTP"* and *"measured in the running app at 28×22"* and *"I believe this works"* are the same string as far as every tool in the system is concerned.

## Decision

### 1. A ticked box on any note type is a claim, and carries a typed evidence token

```
- [x] <claim> — evidence: test:test_a_dropped_file_lands@2011420
- [x] <claim> — evidence: mutation:test_the_store_endpoint_is_loopback_only@2011420
- [x] <claim> — evidence: runtime:"thumb naturalWidth 1301, box 28x22"@85fa50c
- [x] <claim> — evidence: human:edwin@2026-07-28
- [x] <claim> — evidence: asserted:"reviewed the diff, did not execute"
```

The vocabulary is **closed** — five tokens, ordered by strength:

| token | means | who can write it |
|---|---|---|
| `mutation:` | a test that provably fails when its guard is removed | the runner |
| `test:` | a named test that passed at that revision | the runner |
| `runtime:` | observed in the shipped artifact, with the observation quoted | an agent or human, quoting what was measured |
| `human:` | a person looked and judged | a person |
| `asserted:` | nobody checked | anyone |

A closed vocabulary is the whole point. `path`, `command`, or `note ID` — ADR-0006's phrasing — describes *where to look*, not *what was done*, which is why 36% of the results are prose. Strength is what a reader and a validator both need, and it is the one thing free-form pointers cannot express.

### 2. Evidence names a revision, so it can go stale

`test:foo@abc123` is a claim about `abc123`. When the files that claim depends on change, the claim is **stale** — not false, not failing, stale — and a stale claim does not satisfy a terminal transition.

Staleness is a **finding, not a status**, exactly as [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] ruled for tests. Adding a status value would regrow the taxonomy [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]] cut, and would let an agent clear it by hand.

This is the first mechanism in project-os that can invalidate a claim **without anyone editing the note**. Today a DoD line written in March still reads as true in July with no code left standing behind it.

### 3. `asserted:` is legal

It is legal, it is visible, and it blocks only terminal transitions. Making unverified claims *illegal* produces the fake automation ADR-0010 rejected — a `command:` wrapped round a judgement to get past a gate. Making them *countable* produces a number a human can act on: "this feature rests on nine assertions and two tests" is a sentence worth reading at close-out.

The first honest fleet run will report thousands of `asserted:` boxes. That is not a regression introduced by this ADR. That is 93.9% of the fleet's ticked claims, described accurately for the first time.

### 4. `REQ-BOXES` generalises

The check becomes `CLAIM-EVIDENCE` and applies to every note type carrying ticked boxes. Requirements keep the behaviour they already have; tasks, tests, phases, features and issues acquire it.

## Why this and not more enforcement

The tempting move is to demand better discipline about evidence prose. That is precisely ADR-0006's rule, and it has produced 296 clauses across 4,833 claims, 108 of them unrankable prose.

The pattern across ADR-0007, ADR-0008, ADR-0010 and this decision is one pattern: *when a rule is followed only where it is mechanically checked, the fix is to extend the mechanism, not to restate the rule.* Here the extension is small — a closed token vocabulary and a revision — and it is what turns a sentence a reader must trust into a fact a validator can refuse.

## Consequences

See frontmatter. The load-bearing one: **this is useful with no other change.** It needs no service, no platform, and no new tool beyond a validator rule, and it lands in eleven repos the day it is upstreamed. [[ADR-0015-Intent-Layer-Not-A-Git-Host|ADR-0015]] may never be accepted; this stands regardless, and is the prerequisite if it ever is.
