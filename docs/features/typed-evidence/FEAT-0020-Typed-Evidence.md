---
type: "[[feature]]"
id: FEAT-0020
aliases: ["FEAT-0020"]
title: "Typed evidence on every ticked claim"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
source: ["[[ADR-0014-Evidence-Is-Typed-And-Checkable]]", "fleet measurement 2026-07-29"]
goal: "Make every ticked box in the fleet a machine-readable claim with a strength and a revision, so that 93.9% of claims stop being unrankable prose and a claim can go stale without anyone editing the note."
requirements: []
tasks: []
release: ""
related: ["[[ADR-0014-Evidence-Is-Typed-And-Checkable]]", "[[ADR-0006-Requirement-Advancement-On-Evidence]]", "[[ADR-0010-Test-Status-Stamped-By-Execution]]"]
tests: []
---

# Typed evidence on every ticked claim

## Goal

Implement [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]]: a closed evidence-token vocabulary, a revision on every token, and a validator check that applies to every note type carrying ticked boxes — not only requirements.

The measured starting point, across 12 repos, counting ticked boxes only:

| | ticked claims | carry evidence |
|---|---:|---:|
| requirement (governed by `REQ-BOXES`) | 209 | **60.3%** |
| everything else | 4,624 | **3.7%** |
| task alone | 2,921 | 5.1% |
| test | 305 | 0.0% |

## Why this is worth doing before anything else

It is the only part of the 2026-07-29 design conversation that pays off with **no service, no platform, and no new tool** beyond a validator rule. It lands in eleven repos the day it is upstreamed, and it is the prerequisite for [[ADR-0015-Intent-Layer-Not-A-Git-Host|ADR-0015]] if that is ever accepted — while standing entirely on its own if it is not.

It also converts a documented, recurring failure into a catchable one. Six claims in `project-os-cockpit` on 2026-07-28 asserted more than the code did, including *"thumbnail rendered"* for images a CSP had blocked from ever painting. Every one was caught by a person. None was catchable, because a validator cannot tell *"verified over real HTTP"* from *"I believe this works"*.

## Scope

**In:**
- The token vocabulary (`mutation:`, `test:`, `runtime:`, `human:`, `asserted:`) and its grammar, in `SCHEMAS.md`
- `CLAIM-EVIDENCE` — `REQ-BOXES` generalised to every note type with ticked boxes
- `CLAIM-STALE` — a claim whose evidence revision predates changes in its blast radius, reported as a finding, never a status ([[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]], [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]])
- Template and skill updates: task template, close-out, status-transition
- A `project-os-bench` dimension, since tokens are gradable without an LLM judge

**Out:**
- Retrofitting historical boxes. Untyped boxes read as `asserted:`; the rule applies going forward. Mass-rewriting 4,537 boxes would manufacture exactly the unearned confidence this feature exists to remove.
- Blocking on `asserted:` anywhere except terminal transitions.
- Anything requiring a hosted service.

## Open questions for planning

1. **Blast radius.** `CLAIM-STALE` needs to know which files a claim depends on. Cheapest useful version: the files the claim's own commit touched. Is that enough, or does it need declaring?
2. **Who writes `test:` and `mutation:`.** ADR-0010 gave `run-tests.py` custody of test *status*. The same script is the natural writer of these tokens, which keeps the conflict of interest removed rather than reintroduced one level up.
3. **`runtime:` quoting.** The token requires the observation be quoted (`runtime:"naturalWidth 1301"@85fa50c`). Is a free-form quote enough, or does that reopen the prose problem inside a typed token?
4. **Migration noise.** The first fleet run reports ~4,500 `asserted:` claims. Expected and correct per ADR-0014 — but it needs a presentation that reads as *"now measured"* rather than *"newly broken"*.
