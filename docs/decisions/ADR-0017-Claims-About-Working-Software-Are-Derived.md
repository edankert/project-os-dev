---
type: "[[adr]]"
id: ADR-0017
aliases: ["ADR-0017"]
title: "A claim about whether the software works is derived from execution where execution is possible, labelled and dated where it is not, and in neither case written by the party seeking the transition it gates"
status: accepted
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
source: ["intake 2026-07-29: articles repo, quality-without-reading thesis, finding 1"]
decision: "State as one normative rule what ADR-0009, ADR-0010 and ADR-0014 each implement for one field: a claim about whether the software works must be derived from execution wherever execution is possible; where it is not possible the claim must be labelled as unexecuted, dated, and expire; and in neither case may it be written by the party seeking the transition it gates. The rule is the test applied to every future state field, and it is deliberately bounded to the running-system layer"
context: "ADR-0009 derived snapshot state from notes. ADR-0010 gave test status to the runner. ADR-0014 types evidence and gives it a revision. Three decisions, one rule, stated nowhere — so each new state field is argued from scratch and the generalisation is rediscovered each time. ADR-0009 line 50 already notices the habit: `--fix-metrics` 'is this ADR in miniature, applied to one field: nobody defends hand-authored metrics, they just had not yet generalised the argument'"
alternatives:
  - "Adopt the intake's stronger phrasing — 'any claim about whether the software works must be derived from execution, never asserted by an agent' — rejected: it outlaws manual tests, which ADR-0010 deliberately preserved with `last_verified:`, and outlaws the `human:` and `asserted:` evidence tokens, which ADR-0014 deliberately made legal and visible. A rule the system's two strongest decisions both violate is not the rule those decisions were following"
  - "Leave it implicit and argue each field on its merits — rejected: this is the current state, and it costs a full ADR per field while producing no test for the next one. It is also how ISS-0017 stayed invisible: a review verdict is the same claim shape, and nobody noticed because the shape had no name"
  - "State it in QUALITY.md as a normative section rather than an ADR — rejected on placement only, not substance: QUALITY.md states gates, and this is the reasoning that generates gates. The ADR states the rule; QUALITY.md and STATUSES.md link to it, per REQ-0018"
  - "Extend the rule to the whole seven-layer thesis (gates, observability, contracts, reversibility) — rejected: see the recorded non-goals. Those layers may deserve modelling, but they are not instances of this rule and bundling them would make an unfalsifiable principle out of a checkable one"
consequences:
  - "Every future state field gets a three-question test — can this be executed? if not, is it labelled and dated? and can the party seeking the transition write it? — rather than an ADR-length argument"
  - "The rule immediately classifies open work: ISS-0017 (review verdicts) and ISS-0020 (VERIFY blind to absent tests) are both instances, and neither was recognised as one before the rule had a name"
  - "It also classifies what is already correct, which is most of the system. This ADR ratifies ADR-0009, ADR-0010 and ADR-0014 rather than changing them; no existing behaviour moves"
  - "Bounding the rule to the running-system layer means recording four real gaps as deliberate non-goals. They are named below so they are not silently dropped and not silently adopted"
related: [ADR-0009, ADR-0010, ADR-0014, ADR-0016, ISS-0017]
supersedes: ""
superseded: ""
---

# Claims about working software are derived

## Context

Three decisions in this repo implement the same rule for one field each:

- [[ADR-0009-Snapshot-Is-Generated|ADR-0009]] — item state, counters and metrics are generated from note frontmatter, because writing them twice is how they disagree.
- [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] — a `TST-*` with a `command:` has its status written by the runner from the exit code, because *"the agent seeking the transition"* must not also grade the proof.
- [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]] — a ticked box carries a typed evidence token and a revision, because *"verified over real HTTP"* and *"I believe this works"* are the same string to every tool in the system.

The rule they share is stated nowhere. `ADR-0009` gets closest, and notices the pattern without naming it:

> `METRICS` already has `--fix-metrics`, which recomputes the block from the notes and rewrites it. That flag is this ADR in miniature, applied to one field: nobody defends hand-authored metrics, they just had not yet generalised the argument.

The cost of leaving it implicit is not aesthetic. It is that each new state field is argued from first principles, and that claims of the same *shape* go unrecognised. [[ISS-0017-Review-Verdicts-Never-Expire|ISS-0017]] is exactly that: a review verdict is a claim about whether the work is sound, asserted at one moment, read as current forever — the identical failure ADR-0010 removed for tests. It sat in `QUALITY.md` unremarked because the shape had no name to match against.

## Decision

**A claim about whether the software works is:**

1. **derived from execution wherever execution is possible** — the runner writes it, the generator computes it, the tool observes it;
2. **labelled as unexecuted, dated, and expiring where execution is not possible** — a manual check, a human judgement, an assertion;
3. **never written by the party seeking the transition it gates**, in either case.

Clause 3 is the load-bearing one. Clauses 1 and 2 describe two mechanisms; clause 3 is the invariant both exist to protect, and it is the one that catches new cases. `--fix-metrics`, `run-tests.py`, `waiver_expires`, ADR-0014's revision and ISS-0017's fingerprint are all clause 3 with different plumbing.

### Why not the stronger version

The intake that prompted this proposed: *"Any claim about whether the software works must be derived from execution, never asserted by an agent."*

That is too strong, and rejecting it matters. ADR-0010 deliberately kept manual tests with an author-written status plus `last_verified:`, on the grounds that forcing a `command:` round a judgement produces *fake* automation. ADR-0014 deliberately made `asserted:` **legal**, on the grounds that *"making unverified claims illegal produces the fake automation ADR-0010 rejected."* A principle that both of those decisions violate cannot be the principle they were following.

Clause 2 is what the stronger version omits: the answer to an unexecutable claim is to make it **visible and perishable**, not illegal. That is the harder and better idea, and it is already in force in two places (`last_verified:`, `waiver_expires`).

## Recorded non-goals

The intake assessed project-os against a seven-layer model of quality-without-reading and found four layers unmodelled. All four were verified real against this tree on 2026-07-29. They are **deliberate non-goals** as of this decision (accepted 2026-07-29), recorded here so they are neither silently dropped nor silently adopted. Each may be revisited on its own evidence; none is an instance of the rule above.

| Layer | Verified state | Why a non-goal |
|---|---|---|
| **Gate manifest** — what linters, scanners, audits, coverage thresholds and performance budgets the project's *code* runs | `docs/workflows/` holds three `WF-*` notes: derive, template sync, recovery. All are project-os operations. Nothing describes a consuming project's code gates | The gate configuration is real quality policy, but it is *executable already* — CI enforces it whether or not a note describes it. A note would be a second copy of a truth that cannot drift silently, which is the duplication ADR-0009 exists to remove. Revisit if a consuming repo's gates are found to have silently weakened |
| **Observability** — SLOs, operational requirements, post-release verification | No SLO/SLI/telemetry/alerting/canary/feature-flag/error-budget vocabulary anywhere. `monitoring` appears once, at `STATUSES.md:106`, as a *rejected* risk status | The rejection reason is the argument: `monitoring` was written **"never … across 5,890 fleet status writes."** ADR-0008 settled that declared values must be values the fleet writes. Adding a vocabulary with zero observed demand inverts that rule. Revisit when a fleet repo actually runs a service with an SLO |
| **Reversibility as a designed property** — flag, canary, migration reversibility, time-to-revert | `CHG-*` has `merged → reverted`; `REL-*` has `released → reverted` plus `previous_release` and a rollback procedure in `release-verification` | After-the-fact revert is modelled for both types. What is missing is *pre-commitment* — a claim about how reversible a change will be, made before it lands. That is a prediction, not a derived fact, so under clause 3 it would be written by exactly the party that benefits from it reading well. Would need a derivation before it would be worth adding |
| **Code contracts** — interface/API/schema contracts and the mechanism enforcing them | `SCHEMAS.md` plus frontmatter validation is a hard-enforced contract system for *documentation*. Nothing models a contract for code. `DES-*` is design, a different artifact | The strongest of the four, and the closest to in-scope: a crossed interface boundary is precisely what review cannot see. It is a non-goal because a contract note that no tool checks is a documentation artifact, not a contract — and the thing that checks it (schema validation, type checking, consumer tests) lives in the code. Revisit together with [[ISS-0018-Traceability-Stops-At-The-Docs-Boundary|ISS-0018]], whose mechanism it would share |

The common thread in all four rejections: project-os can *record* a claim about the running system, but it cannot *derive* one, because it does not execute the project's code. Recording without deriving is what clause 3 forbids. That boundary — not a lack of ambition — is why these four stay out, and it is also the condition under which any of them could come in.

## Consequences

See frontmatter. The one to watch: this ADR ratifies existing behaviour and changes none, so its value is entirely in what it classifies next. If six months pass and it has not been cited to settle a question about a new field, it did not earn its place.
