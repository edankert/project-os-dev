---
type: "[[adr]]"
id: ADR-0028
aliases: ["ADR-0028"]
title: "A review gate runs two rounds, and only a behavioural finding blocks"
status: "accepted"
owner: user:edwin
created: 2026-09-10
updated: "2026-09-10"
source: ["Edwin, 2026-09-10, asking whether the independent-review cycle should follow ADR-0026 and whether reviewers should exchange positions", "[[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them]] through [[ISS-0039-The-Restatement-Reached-Three-Surfaces-Of-Four]], seven rounds on one change", "arXiv 2603.16244, More Rounds More Noise", "arXiv 2608.18167, Adversarial Review", "arXiv 2509.16533, Challenging the Evaluator", "arXiv 2604.19049, Refute-or-Promote"]
decision: "Option 4. A review gate runs at most two rounds: round one reviews the work, round two verifies the fixes to round one's blocking findings and nothing else. A finding blocks a terminal status only when it refutes a claim about behaviour or an acceptance criterion; every other true finding becomes an ISS-* at triage and does not block. When round two still returns changes-requested the gate does not run round three — it runs one adjudicated exchange between a reviewer and a separate critic, where every disagreement cites specific code and both positions reach the adjudicator side by side, and its output is a decision for the owner rather than another round. The author never answers the reviewer in turns."
context: "The gate has no round cap and no severity bar, so any true finding loops it. One change here was reviewed eight times; rounds four to seven found no code defect and blocked on stale numbers in notes. ADR-0026 left the gate alone on a changes-requested rate of about 10%, but that rate counts final verdicts in frontmatter, which has nowhere to record a round — the eight-round change reads `approved` and the five-round change reads empty."
alternatives: ["Change nothing", "Mirror ADR-0026 and run three parallel reviewers at every gate", "Cap the rounds and stop there", "Record rounds first and decide later"]
consequences: ["QUALITY.md gains the round cap, the severity bar and the escalation rule; independent-review/SKILL.md links them rather than restating them", "A gate can now close with true findings outstanding, carried as ISS-* at triage", "The reviewer's instruction to report every finding is unchanged; what changes is which findings block", "Round counts are still recorded nowhere, so the cap is convention rather than check until ISS-0062 lands", "The adjudicated exchange is specified and unexercised; its first use is the evidence for keeping it"]
supersedes: ""
superseded: ""
related: ["[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[ADR-0019-A-Change-Note-Is-Not-Reviewed]]", "[[ISS-0061-A-Review-Gate-Has-No-Round-Cap-And-No-Severity-Bar]]", "[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]", "[[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them]]", "[[ISS-0039-The-Restatement-Reached-Three-Surfaces-Of-Four]]"]
decided_option: "4"
---

# A review gate runs two rounds, and only a behavioural finding blocks

## Context

> [!quote] As raised — 2026-09-10 (user:edwin)
> Can you do some investigation/research (online or whereever) and tell me if the independent-review cycle should follow the same logic and if the reviewers exchanging positions would be beneficial. At the moment, I notice that another review cycle seems to be going on forever.

[[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] bounded the docs-audit sweep and deliberately left the independent-review gate alone. This decision covers the gate.

### The gate loops, and the record shows how far

`independent-review/SKILL.md` step 5 says that on `changes-requested` the gate keeps the item out of terminal status "and loop". There is no round cap and no severity bar anywhere in the gate, so any finding a reviewer can defend blocks a terminal status, however small it is.

One change was reviewed **eight times**. `CHG-20260804-Retention-And-Field-Derivation.md` records it: rounds one to three found real engineering defects, including a prune that deleted three snapshot entries whose notes were zero-byte files. **Rounds four to seven found no code defect at all.** Each blocked on the record instead — a figure repeated inconsistently, a correction that reached three surfaces of four, a stale number in a test comment. Round eight approved.

The issue family that loop produced is the clearest evidence in the repo, because the severity field decays monotonically:

| Issue | Round | Severity |
|---|---|---|
| [[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them\|ISS-0033]] | 1 | high |
| [[ISS-0034-Cockpit-Features-Done-Still-Short-And-The-Suite-Does-Not-Guard-Either-Fix\|ISS-0034]] | 2 | medium |
| [[ISS-0035-Metric-Fix-Missed-The-Bundled-Validators-And-The-Notes-Still-Describe-Round-Two\|ISS-0035]] | 3 | medium |
| [[ISS-0036-Round-Four-Engineering-Resolved-Record-Still-Misstates-It\|ISS-0036]] | 4 | low |
| [[ISS-0037-Round-Five-Corrections-Landed-On-One-Note-Of-Two\|ISS-0037]] | 5 | low |
| [[ISS-0038-The-Seventeen-Names-Fourteen-Files-That-Do-Supply-Titles\|ISS-0038]] | 6 | low |
| [[ISS-0039-The-Restatement-Reached-Three-Surfaces-Of-Four\|ISS-0039]] | 7 | low |

Four consecutive rounds ended in a `low` issue, and each of those four blocked a terminal status exactly as hard as round one's `high` did. All eight remain `open` five weeks later, so the loop also generated a backlog it did not clear. Their own titles say it plainly: ISS-0036 through ISS-0039 each open with the engineering being clean for another consecutive round.

This is not a reviewer behaving badly. The reviewer was accurate every time, and `independent-review/SKILL.md` step 3 is right to tell it to report everything it finds. The defect is that a binary verdict with no severity bar converts every true observation into a blocker.

### Why ADR-0026 concluded the gate was cheap

ADR-0026 cleared the gate on a measurement: 18 recorded verdicts, 2 of them `changes-requested`, about 10%. That statistic counts the `review_verdict` field in frontmatter, and **the frontmatter has nowhere to record a round**. The eight-round change carries one row reading `approved`. The five-round change on `CHG-20260726` carries an empty verdict and contributes no row at all. Across this repo the field holds 16 `approved`, 3 `changes-requested` and 16 empty.

So the number that justified leaving the gate alone is structurally blind to the cost this decision is about. That is a reason to revisit ADR-0026's scope, not a fault in it — the sweep conclusions stand.

### What the research says about copying ADR-0026's shape

The awkward detail first. [More Rounds, More Noise](https://arxiv.org/html/2603.16244v1) reviewed 30 fixed artifacts carrying exactly 5 injected errors each — a bounded artifact judged as a unit, which is the shape of **this gate**, not of the 130-file corpus sweep it was cited for in ADR-0026. Its numbers therefore transfer here more directly than they did there. Single-pass scored F1 0.376, every multi-turn variant scored worse, and a three-run majority-vote ensemble scored 0.393, the best result in the paper. The mechanism it names is false-positive pressure: once the discoverable defects are gone, a reviewer asked to look again produces roughly four to five new false positives for every additional true one.

That argues for bounding rounds, and it argues weakly for three parallel reviewers. Three reviewers is rejected on cost rather than on evidence — see Option 2.

The stopping-rule literature agrees on where to bound. [Semantic early-stopping](https://arxiv.org/abs/2606.27009) exists because fixed caps are blind to whether an answer is still improving, and the surveyed convergence work puts roughly 75% to 95% of reachable improvement in the first two rounds. Two is where this repo's own curve turns as well: three productive rounds, then four unproductive ones.

### What the research says about reviewers exchanging positions

Exchanging positions helps in one shape and hurts in another, and the difference is not subtle.

**The harmful shape is the author answering the reviewer.** [Challenging the Evaluator](https://arxiv.org/abs/2509.16533) found that models endorse a counterargument far more readily when it arrives as a follow-up turn than when both positions are presented simultaneously for judgment, that a rebuttal carrying detailed reasoning is more persuasive **even when its conclusion is wrong**, and that casually phrased pushback beats formal critique. The author is precisely the party holding detailed reasoning and a motive to be finished. [Adversarial Review](https://arxiv.org/html/2608.18167) hit this directly: its critic raised a legitimate concern, the reviewer answered with a confident-sounding rebuttal citing no code, the critic yielded, and real bugs left the final review. Its unconstrained protocol scored **worst of everything tested** on review quality, F1 0.457 against 0.495 for a single reviewer.

**The useful shape is a reviewer against a separate critic, with citations mandatory.** One constraint moved that same protocol from worst to best: a disagreement must cite specific code, and the reviewer must then either firm the claim up with code or abandon it. F1 0.533, against 0.503 for two independent reviewers. On repair tasks three agents beat a five-agent panel — 87% against 82% on LiveCodeBench, 75.2% against 72.6% on SWE-bench Verified. More voices was not the active ingredient. Auditable disagreement was.

This gate already holds the precondition. `independent-review/SKILL.md` step 3 requires every finding to be labelled reproduced or not reproduced, which is the same evidence discipline [Refute-or-Promote](https://arxiv.org/abs/2604.19049) used to kill 79% of 171 candidates before disclosure while still landing four CVEs. That result also supports ADR-0026's union-over-agreement amendment after the fact: a refutation gate does the work majority voting was supposed to do.

Caveats, because the decision rests on them: the rounds paper is single-model with synthetic injected errors over 30 artifacts and says explicitly that it should not be read as evidence against multi-round *human* review; Adversarial Review rests on three benchmarks and costs 4.5 times the tokens; the sycophancy paper publishes no effect sizes in its abstract.

### Why this is not a rule-ADR

The sibling search at intake found seven issues of one kind, well past the second-instance harvest trigger in `issue-intake/SKILL.md` step 2, and the domain is nameable — the three gate transitions `QUALITY.md` lists. What is missing is the third section. `DECISIONS.md` requires a rule-ADR to name a discharge and `adr-authoring/SKILL.md` step 3 says to land the conformance rather than promise it, and no check can count a review's rounds while nothing records them. [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] is that missing registry. Promoting this decision to a rule-ADR is acceptance criterion 3 below.

## Options

1. **Change nothing.** The gate is accurate and finds real defects, which is true and is not the complaint. Costs: the eight-round case recurs, and nothing bounds it.
2. **Mirror ADR-0026 — three parallel reviewers at every gate.** Buys the configuration the rounds paper scored highest (F1 0.393 against 0.376). Costs three times the tokens on the most frequent transition in the system, and 16 of this repo's 19 final verdicts were approvals, so most of that spend would buy a second and third confirmation of a pass. The sweep needs three passes because it samples a 130-file corpus; a gate reads one bounded change and does not.
3. **Cap the rounds and stop there.** Bounds the loop, and leaves round two able to block on a stale comment. Half the eight-round case survives.
4. **Cap the rounds, add a severity bar, and escalate instead of looping.** The package. Round one reviews, round two verifies round one's fixes, and a third disagreement goes to one adjudicated reviewer-versus-critic exchange whose output is a decision rather than a round.
5. **Record rounds first and decide later.** Honest and slow: it fixes nothing this quarter, and the two changes in Option 4 do not need the measurement to be obviously right.

## Decision

**Option 4**, accepted 2026-09-10.

Four rules, and `QUALITY.md` is their single home:

1. **A gate runs at most two rounds.** Round one reviews the work. Round two verifies the fixes to round one's blocking findings and nothing else — it is not a fresh sweep for new defects.
2. **A finding blocks a terminal status only when it refutes a claim about behaviour or an acceptance criterion.** Every other true finding is filed as an `ISS-*` at `triage` and the item closes. What the reviewer is asked for does not change; only which findings hold the gate shut.
3. **A third disagreement is adjudicated, not looped.** If round two still returns `changes-requested`, run one exchange between the reviewer and a separate critic in which every disagreement cites specific code, present both positions to the adjudicator side by side rather than as a conversation, and hand the owner a decision.
4. **The author never answers the reviewer in turns.** Where the author's counter-position enters, it reaches the adjudicator beside the finding, never as a follow-up message to the reviewer.

Rule 2 is the one that fixes the case that prompted this. Applied to the eight-round review, rounds four to seven produce three `ISS-*` notes at `triage` and no delay at all.

## Alternatives

- **Keep looping but ask the reviewer to be conservative.** Rejected, and `independent-review/SKILL.md` step 3 already owns the reason: a reviewer told that small findings are not findings drops the plausible ones itself and nobody downstream sees them. The filter belongs at transcription, which is where rule 2 puts it.
- **Let the author rebut the reviewer directly.** Rejected on the sycophancy evidence above. It is the cheapest-looking option and the one that measurably drops true findings.
- **Cap by tokens or wall-clock instead of rounds.** Rejected: a budget bounds cost without saying what the second round is for, and rule 1's value is mostly in narrowing round two's job.

## Consequences

- `QUALITY.md`, "Independent review (clean-context)", gains the cap, the bar and the escalation rule. `independent-review/SKILL.md` step 5 links them and restates none of them (REQ-0027).
- **A gate can now close with true findings outstanding.** That is the intended trade and it is a real loss: those findings live on `ISS-*` notes at `triage` and depend on grooming rather than on the gate. The eight `open` issues from the eight-round review are the evidence that this backlog is already how the loop behaves, minus the delay.
- The severity bar is a judgment, so it can be misused the same way any threshold can. What keeps it honest is that a non-blocking finding still has to be filed, which makes a wrong call visible to the next reader instead of invisible.
- Nothing records rounds, so rule 1 is convention until [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] lands.
- The adjudicated exchange has never run here. It is specified so that the first stall has somewhere to go, and its first use is what decides whether it stays.

## Acceptance

- [x] **The cap, the bar and the escalation rule are stated once** — evidence: `QUALITY.md` "Independent review (clean-context)" carries all three; `independent-review/SKILL.md` step 5 links them. Landed in the template, recorded on [[CHG-20260910-A-Review-Gate-Runs-Two-Rounds]].
- [ ] **Rounds are recorded**, so the cap can be checked rather than remembered — [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]]. Until then a ninth round would pass every check in the system.
- [ ] **Promoted to a rule-ADR** once criterion 2 gives it a conformance: `## Rule` (a gate runs at most two rounds), `## Domain` (the three gate transitions), `## Conformance` (the check ISS-0062 makes possible).
- [ ] **The adjudicated exchange runs once and is recorded** — whether the citation constraint held, whether the critic capitulated, and whether the owner got a decision or another list.

## Decision record

> [!note] Accept — 2026-09-10 (user:edwin)
> write it up
>
> and down stream the change.
>
> Given after the research summary that became the Context section above. The second line instructed the template implementation, which is what makes this `accepted` rather than `proposed`.
