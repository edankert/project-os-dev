---
type: "[[adr]]"
id: ADR-0026
aliases: ["ADR-0026"]
title: "When a drift sweep stops"
status: "accepted"
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
source: ["Edwin, 2026-09-04, asking whether the clean-context review is worth its cost", "[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]] passes 1 to 12", "arXiv 2603.16244, More Rounds More Noise", "arXiv 2608.18167, Adversarial Review"]
decision: "Option 5. A sweep runs one round of three parallel clean-context passes at one commit, unions their findings, requires a reproduction with each, verifies those reproductions, fixes what survives, records the residue and stops. The human sees decisions owed, not findings. Amended at acceptance: findings are unioned and verified, not kept on two-of-three agreement -- measured on this corpus, agreement discards the real defects."
context: "The docs-audit skill says an audit is complete only after two consecutive passes find zero defects. Twelve passes over the project-os template have never produced two clean passes in a row, and the evidence says they cannot: each clean-context pass samples a different part of the corpus rather than converging on it."
alternatives: ["Keep the quiescence rule and run it less often", "Drop the sweep and rely on the validator", "Require a different model family (settled by ADR-0013)"]
consequences: ["docs-audit SKILL.md replaces the quiescence rule with one bounded round", "release-prep stops asking for a sweep to quiescence", "REQ-0027 criteria 1 and 3 are reworded off the clean-pair test", "ISS-0048 closes on a recorded residue"]
supersedes: ""
superseded: ""
related: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make]]", "[[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule]]"]
decided_option: "5"
---

# When a drift sweep stops

## Context

> [!quote] As raised — 2026-09-04 (user:edwin)
> I am a bit concerned about the running of the independent reviewer, it seems to delay the task completion significantly and I cannot say if this is actually beneficial, since I don't know if the reviewer is actually reviewing the right things and pushes the implementer in the right direction or steers it in the wrong direction. Instead it might be better to limit the number of review cycles significantly and/or have a human acceptance test in the loop somehow/womewhere. Review this and push back if required and suggest solutions.

Two mechanisms were in scope for that question and only one of them is expensive, so this ADR separates them. The **independent review gate** (`QUALITY.md`) fires on three status transitions and has produced 18 recorded verdicts across this project's history: 16 approved, 2 changes-requested. That is not where the time goes, and an 11% changes-requested rate is real signal rather than a rubber stamp, so this ADR proposes no change to it. The **docs-audit quiescence rule** is the expensive one, and it is what follows.

The docs-audit skill ends with a quiescence rule: the audit is complete only after **two consecutive full passes find zero new defects**. That rule has now been tested harder than any other rule in this project, and it does not hold.

Twelve clean-context passes have run over the template under [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]]. The findings per pass:

| Pass | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Found | 36 | 26 | 2 | 3 | 2 | 2 | **0** | **21** | 2 | 5 | 25 | 25 |

Pass 7 was clean. Pass 8 read the same corpus without being shown the earlier findings table and found 21. Pass 11 found 25, every one was fixed, and pass 12 then found 25 more that pass 11 had never raised.

**This is sampling, not convergence.** A pass reads ~130 files and reports what it happens to look at closely; a different pass looks closely at different files. The quiescence rule assumes the defect set is small enough to exhaust and that a clean pass is evidence it has been. Neither is true here. As written, the rule can run forever, and its counter measures the reviewer's sampling rather than the corpus improving.

Two things are **not** wrong and should not be changed by mistake:

- **The reviewer is accurate.** Seventeen of seventeen findings spot-checked across passes 11 and 12 were real. Pass 12 independently flagged two items pass 11 had deliberately deferred, without being told they existed.
- **The findings matter.** Pass 11 found the shipped Obsidian views filtering on statuses renamed seven weeks earlier, so every downstream repo had a dead "Features (Open)" table. Pass 12 found [[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule|ISS-0051]], where the blocking HC-003 hook denied `done` to any feature carrying the acceptance check the scaffold skill requires. Eleven prior passes and the whole test suite missed it.

So the problem is not review quality and not review value. It is that the process has no honest stopping rule, and the cost is real: roughly ten minutes and 290k tokens per pass, about 3.5M tokens across the twelve.

The outside evidence points the same way. [More Rounds, More Noise](https://arxiv.org/html/2603.16244v1) tested this exact shape — production and review split into independent sessions, then iterated. Single-pass scored F1 0.376 and every multi-turn variant did worse, the best at 0.303. Round two produced 63% more findings but only 15% more true positives, and precision fell from 0.30 to 0.20 under what the authors call false-positive pressure: once the discoverable defects are gone, a reviewer asked to look again invents things. Their best configuration was three independent parallel reviews with majority vote, F1 0.393. [Adversarial Review](https://arxiv.org/abs/2608.18167) separately found three agents beat five, and that what makes review work is disagreement that is minimal, structured and evidence-grounded rather than more reviewers.

The caveat belongs here too: that first study used synthetic injected errors on one model, and says explicitly that its finding is about LLM reviewers and should not be read as evidence against multi-round human review.

## Options

1. **Keep the quiescence rule.** No change. Honest about the ideal, and the record shows it costs unbounded passes and never terminates. Twelve passes is the evidence against it.
2. **Stop on a budget.** Run a fixed number of passes — one, or two for a corpus that has just changed a lot — fix what is confirmed, record the rest on the issue, and stop. The audit ends in bounded time and the residue is written down instead of chased.
3. **Run passes in parallel, not in sequence.** Three independent sweeps at one commit; keep findings at least two of the three report. One wall-clock interval instead of three, and it is the configuration the research scored highest. Costs three times the tokens of a single pass.
4. **Make each finding carry a reproduction, and verify before fixing.** No finding is actionable without a command that demonstrates it, and a separate step runs those commands. Attacks false-positive pressure directly. This was done by hand for passes 11 and 12 and 17 of 17 findings held.
5. **Adopt 2, 3 and 4 together, and move the human checkpoint onto decisions.** The sweep becomes: three parallel passes at one commit, findings kept on two-of-three agreement, each carrying a reproduction that is verified, fixed in one bounded round, residue recorded. Edwin sees the decisions owed — not the findings — and nothing waits on him that he would approve every time.

## Decision

**Option 5**, accepted 2026-09-04.

**One amendment, made at acceptance.** Option 5 as written kept "findings at least two of the three report". Implementing it against this corpus showed that rule would destroy the result, so it is replaced by *union the findings, then verify each against its reproduction*. The evidence is in this project: passes 11 and 12 ran at adjacent commits, found 25 findings each, and overlapped on almost nothing. Had they been two arms of one ensemble, a two-of-three rule would have kept close to zero — discarding the shipped Obsidian views that filtered on retired statuses (pass 11 only) and [[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule|ISS-0051]] (pass 12 only), both real and both severe.

Majority voting works in the study that recommended it because every reviewer there read one artifact with known injected errors. Here each pass samples a different part of ~130 files, so agreement measures overlap in sampling rather than truth. **Verification, not agreement, is what controls false positives** — which is exactly what option 4 is for, and it held 17 of 17 times when done by hand across passes 11 and 12.

Options 2, 3 and 4 are independent of each other and each is an improvement alone; 5 is the package, and the human checkpoint is the part that answers what Edwin actually asked. Adopting 5 also implies a sixth thing this ADR does not decide: every finding class that keeps recurring should become a mechanical check, at which point the sweep only has to hunt new classes. `test-pause-rule.sh` is the existing proof that the pattern works — it asserts one rule is stated once and linked from ten named sites, runs in milliseconds, and caught a real regression during this work. That is the subject of the first acceptance criterion below and reopens the RULE-ONCE question [[ADR-0024-A-Normative-Rule-Is-Stated-Once|ADR-0024]] declined at a count of 36.

## Alternatives

- Keep the quiescence rule and run it less often. Rejected as the primary answer: a rule that cannot terminate is not improved by invoking it less; it just fails less visibly.
- Drop the drift sweep entirely and rely on the validator. Rejected on evidence: the validator, `generate-adapters --check` and all four test scripts were green at every commit where a pass found real defects, including the two most serious. Nothing mechanical currently detects this defect class.
- Require a different model family for the sweep. Already settled by [[ADR-0013-Independence-Is-Clean-Context|ADR-0013]]: the discriminator is clean context and tool access, not vendor.

## Consequences

- `tools/skills/docs-audit/SKILL.md` step 4 changes from the quiescence rule to a bounded budget, and gains the parallel-ensemble and reproduction requirements. The skill is the single home for how a sweep runs.
- A sweep's output becomes two lists: what was fixed, and what decisions are owed. The second is what reaches the user.
- Sweeps get more expensive per round (three parallel passes) and far cheaper in total (bounded rounds instead of unbounded).
- [[REQ-0027-Every-Normative-Rule-Is-Stated-Once|REQ-0027]]'s first and third acceptance criteria are currently written to tick on "two consecutive clean passes". They need rewording against whatever this ADR settles, or they inherit a rule that cannot be satisfied.
- ISS-0048 can then close on a recorded residue rather than on a clean pair.

## Acceptance

- [x] **The budget number: one round of three parallel passes** — evidence: the research this ADR cites scored single-pass above every multi-turn variant and a three-way ensemble above single-pass, and twelve sequential rounds here never terminated. Landed in `docs-audit/SKILL.md` (template `17edc84`). What one round misses is caught by the cadence, not by re-running.
- [x] **REQ-0027 criteria 1 and 3 reworded** off the clean-pair test, which no longer exists — see that note. They now tick on a bounded round with its residue recorded.
- [x] **The recurring finding classes: listed and decided below.** Four of five become mechanical checks; the first is built, the rest are [[ISS-0052-Four-Drift-Classes-Should-Be-Checks-Not-Sweep-Findings|ISS-0052]]. This is the RULE-ONCE reconsideration ADR-0024 asked for, and the count that decided it is not 36 but "~25 per pass, indefinitely".

### The recurring classes

Taken from passes 11 and 12, the two that read the widest domain. A class is worth mechanising when a check can state it precisely and the sweep keeps rediscovering it.

| Class | Seen | Becomes a check? |
|---|---|---|
| A status value that `STATUSES.md` does not allow, used in a view filter or a document's status list | Both passes; produced the empty "Features (Open)" table every downstream repo had | **Yes — built.** `BASE-STATUS` for `.base` filters, where the literals are unambiguous and the defect was user-visible |
| A frontmatter field the validator enforces but no document defines (`waiver_expires:`, `fixes:`, `docs/designs/`) | Pass 12, three instances | **Yes** — every field a check reads should appear in `SCHEMAS.md`. ISS-0052 |
| A citation to a file, heading or ADR that does not exist or does not say what the citing file claims | Both passes, 22 instances | **Yes** — resolve every backticked path and cited heading. Pass 12's agent already ran this by hand. ISS-0052 |
| An index or README listing fewer entries than its directory holds | Both passes, 8 instances | **Yes** — trivially checkable. ISS-0052 |
| A directory README carrying its own copy of an instruction file's trigger list | Pass 12, six READMEs | **No.** A check cannot tell a legitimate orientation sentence from a restatement without reading for meaning; this stays the sweep's job |

## Decision record

> [!note] Accept — 2026-09-04 (user:edwin)
> accept option 5 and implement it

> [!note] Amend — 2026-09-04 (model:claude-opus-5[1m], at implementation)
> Option 5's "two of three agreement" is replaced by "union, then verify each reproduction". Passes 11 and 12 overlapped on almost nothing, so agreement would have discarded both of the severe defects those passes found. Recorded here rather than silently implemented, because it changes what was accepted. Reversible: if a later corpus shows high inter-pass overlap, agreement becomes affordable again.

> [!note] Accept — option 5: Adopt 2, 3 and 4 together, and move the human checkpoint onto decisions — 2026-09-04 (user:edwin)
> option
