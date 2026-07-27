---
type: "[[adr]]"
id: ADR-0013
aliases: ["ADR-0013"]
title: "Independence is a clean context, not a different model family"
status: accepted
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["experiment:TASK-0077", "user decision 2026-07-27"]
decision: "Replace QUALITY.md's different-model-family requirement with a clean-context requirement. An independent review is a session that (a) starts from a fresh context — the notes and the diff, never the author's reasoning trace — and (b) is not the same session that authored the work. Model family is no longer the gate. All phase-routed agents move to Opus; the separation that does the work is context, not pin."
context: "The family rule was asserted, never tested, and produced a standing unmet obligation: every review this fleet has recorded disclosed itself as same-family harm reduction. TASK-0077 tested it directly against the one case in the fleet with a known answer, and the premise failed on its own strongest prediction."
alternatives:
  - "Keep the family rule and satisfy it with a second vendor. Rejected on evidence, not cost: the different-family arm found less than the same-family clean-context arm, and missed the one defect the rule's premise predicts only a different family could catch. Cost was a secondary factor — the free tier exhausted mid-experiment — but a rule that bought coverage would have been worth paying for."
  - "Keep the family rule as an aspiration and continue disclosing it as unmet. Rejected: a rule nothing satisfies is not a standard, it is a ritual disclaimer. Four months of review notes each carrying 'a cross-vendor pass is still owed' is evidence the rule was unusable, not that the fleet was negligent."
  - "Require both — clean context AND a different family. Rejected: it keeps an unsatisfiable condition attached to a satisfiable one, so the gate stays permanently open and the clean-context requirement inherits the family rule's unenforceability."
  - "Require a different model *pin* within the family (the previous de-facto arrangement: Fable reviews Opus). Rejected as the gate: the experiment's best-performing reviewer was the same pin as the author with a clean context, and its advantage over the different pin was substantial. Pin difference is not forbidden — it is simply not what is being asserted."
consequences:
  - "`QUALITY.md`'s independent-review rule changes from 'a different model family or a human' to 'a clean context, and not the authoring session'. The rule becomes satisfiable by tooling that already exists."
  - "`PLANNER_MODEL` and `REVIEWER_MODEL` in `generate-adapters.py` both move to Opus. The pins no longer encode an independence claim, so the long caveat comment they carried is replaced by a pointer to this ADR."
  - "The independence disclosure in the reviewer agent changes from 'this is not independent' to a statement of what actually was independent: fresh context, separate session, model recorded in `reviewed_by`."
  - "`reviewed_by` keeps recording the model. It is provenance, not a compliance token — a later reader still needs to know who reviewed, and a future finding about a specific model's blind spots needs the data."
  - "Reviews recorded before this ADR remain accurate as written; they disclosed a real limitation under the rule in force at the time. They are not retroactively upgraded."
  - "The standing 'cross-vendor pass still owed' debt is discharged, not deferred. Nothing in the fleet is waiting on a second vendor any more."
supersedes: ""
superseded: ""
related: [ADR-0011, TASK-0077, ISS-0016, TST-0002]
---

# Independence is a clean context, not a different model family

## What the rule said, and what it cost

`QUALITY.md` required "a different model family or a human, never a second pass by the authoring model", and `independent-review/SKILL.md` justified it: *"A second session of the same model is NOT independent — it reproduces the same blind spots."*

Claude Code subagents can only pin Claude models. So the rule was, in practice, unsatisfiable by the fleet's own tooling, and every review note recorded the same disclosure: same-family, harm reduction, a cross-vendor pass still owed. That debt was carried for months and never paid.

A rule nothing satisfies is not a standard. It is a ritual disclaimer attached to work that was, in fact, being reviewed carefully.

## The experiment

[[TASK-0077]] tested the premise against the only case in the fleet with a known answer: the `validate_status_tables` sequence, hardened over four rounds by a different-pin same-family reviewer, each round finding a real defect with a reproduction.

The decisive run used the **pre-fix tree** — the commit where a genuinely doubled file existed, 2560 lines against a parent's 1514. That defect is the rule's best case: it was authored by Opus, and the author's specific error was treating `ast.parse` success as evidence of structural integrity. A doubled file parses. If that blind spot is architectural, a fresh Opus shares it and cannot catch it. That is precisely what the family rule predicts.

Both arms got a byte-identical prompt with no hint — no mention of duplication, line counts, or structure. Only the notes that existed at that commit.

| Arm | Relation to author | Doubled file | Findings |
|---|---|---|---|
| Fable, round 3 (baseline) | same family, different pin | found | 3 |
| **clean-context Opus** | **same family, same pin** | **found — rated `high`** | **5** |
| gpt-5-codex, read-only sandbox | different family | missed | 3 |
| gpt-5.6-terra, write access | different family | incomplete (usage cap) | — |
| Antigravity `agy` (Google), full tools | different family | found — rated `high` | 4 |

Clean-context Opus found the defect the premise says it could not, rated it the only `high` in the whole experiment, and characterised it *better than the baseline had*: it identified that importers bind the second copy while script runs use the first, so `sync-snapshot.py` and the cockpit's bundled copy execute different code from the CLI, and an edit to the first copy is invisible to every importer. The baseline had called the tail "inert". Verified independently.

## The decision

The active ingredient is **fresh context**, not different weights.

This should have been the obvious reading all along, and `independent-review/SKILL.md` rule 3 already half-stated it: *"The reviewer gets the notes and the diff, not the author's reasoning transcript."* The mechanism that makes a reviewer independent is not having been in the room while the work was rationalised. A model that never saw the author's reasoning approaches the artifact as a stranger regardless of its weights.

So: an independent review is a session that starts from a **clean context** and is **not the session that authored the work**. Family is dropped as a gate.

Per the same decision, all phase-routed agents move to Opus. Routing by pin was a proxy for independence; with independence redefined, the proxy has no job, and the strongest available model should do every phase. The separation now comes from context boundaries — planning, implementation and verification each start fresh — not from model selection.

## What this does not claim

- **n=1 per arm.** One run each cannot separate model capability from sampling. The result is strong because of *which* defect was caught, not how many.
- **A different family does fine — once it can run things.** This section originally recorded that the different-family arm had been handicapped (read-only sandbox, then a usage cap at `reasoning effort: none`) and cautioned against reading the result as evidence against cross-family review. That caution was justified and is now resolved: a fourth arm, Google's Antigravity CLI with full tool access, **found the doubling and rated it `high`**, plus three further real findings. Amended 2026-07-27, same day.

  The discriminator turns out to be **tool access, not family**. All three arms with a working shell found the defect; the one confined to a read-only sandbox did not. That strengthens this ADR's conclusion — family is not the gate — and removes the reading it never intended, that a different family is worse.

  It also promotes an assumption to a finding: **a reviewer needs a shell.** The runner was built on that premise from the start (five same-family rounds found real defects only because the reviewer executed), and the sandboxed arm is the controlled case that demonstrates it.
- **This is not a licence for self-review.** A session reviewing its own work remains forbidden and is the thing the rule was always most right about. What changed is the boundary: session and context, not vendor.
- **A human pass remains the strongest option** and is still explicitly allowed.

## Why the rule was wrong in a specific way

The family rule conflated two different sources of correlation. Shared *weights* produce correlated capability — a model bad at spotting a class of bug is bad at it twice. Shared *context* produces correlated commitment — a reviewer who watched the author reason toward a conclusion inherits the conclusion.

The fleet's failures have consistently been the second kind. Five rounds of ISS-0011..0016 were not misses of capability; they were claims written wider than the code, which survived because every check agreed with the claim and nobody arrived without the claim already in mind. A stranger with the same weights breaks that, which is exactly what was observed.
