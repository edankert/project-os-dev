---
type: "[[task]]"
id: TASK-0077
title: "Test the independence premise: clean-context Opus vs a different family, identical prompt"
status: doing
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["session:2026-07-27", "user hypothesis"]
parent: "[[FEAT-0018]]"
effort: "S"
due: ""
depends: ["[[TASK-0075]]"]
blocks: ["[[TASK-0076]]"]
related: ["[[TASK-0076]]"]
tests: []
---

# Test the independence premise

## The hypothesis under test

`QUALITY.md` requires "a different model family or a human", and `independent-review/SKILL.md` justifies it: *"A second session of the same model is NOT independent — it reproduces the same blind spots."*

**That premise has never been tested in this fleet.** It has been asserted, disclosed as unmet in every review note, and used to justify a standing debt. Edwin's hypothesis (2026-07-27): a clean-context Opus might match or beat Fable, because the mechanism doing the work may be *fresh context* rather than *different weights* — the skill already withholds the author's reasoning trace (rule 3), so a fresh reviewer of any family starts from notes and diff alone.

Both readings are plausible and they predict different things:

| If the active ingredient is… | Then clean-context Opus should… |
|---|---|
| fresh context (no anchoring on the author's reasoning) | perform like any other fresh reviewer — family is close to irrelevant |
| shared weights and training | miss the same class of thing the author missed |

## Why this case can distinguish them

`ISS-0011`..`ISS-0015` is the only case in the fleet with a known answer. Four Fable rounds, each finding a real defect, each with a reproduction:

| Round | Fable found | Subagent tokens |
|---|---|---|
| 1 | ISS-0012 — the guard's own new constant left unregistered | 94,725 |
| 2 | ISS-0013 — the walker saw only `tuple` | 102,043 |
| 3 | ISS-0014 — **the silently doubled file** | 111,557 |
| 4 | ISS-0015 — depth cap; hash-ordered type pick | 131,903 |

Round 3 is the sharp one for this experiment. The doubled file was *authored by Opus*, and the author's specific failure was treating `ast.parse` success as evidence of structural integrity — a doubled file parses. If that error mode is architectural rather than contextual, a fresh Opus shares it and would not have caught it. Fable did.

## Method

Identical prompt to every runner, guaranteed by `review-external.py` building it once from the same inputs. The prompt deliberately says nothing about which model the reviewer is or how it relates to the author — an earlier draft opened with "you were selected because you are a different model family", which would have been false for the Claude runners and would have measured the prompt rather than the models.

- **Arm A** — `claude-opus`, clean context (separate process, no conversation history)
- **Arm B** — `codex` (OpenAI, genuinely different family)
- **Baseline** — Fable's four rounds, already recorded above

Task: find something all five rounds missed, on a corpus where all five findings are already fixed.

## Definition of Done

- [ ] Both arms run to completion on a byte-identical prompt
- [ ] Findings triaged by whether their `repro` actually reproduces — the same bar every Fable finding met
- [ ] The result is recorded whatever it is, including a null result from both arms
- [ ] The implication for `QUALITY.md`'s rule is stated: confirmed, weakened, or unresolved

## Honest limits, recorded before seeing results

- **n=1 per arm.** One run each cannot separate model capability from sampling. A finding is evidence; a null result from a single run is weak.
- **The task may be empty.** Five rounds have already hardened this target. "Nobody found a sixth defect" is consistent with "there is no sixth defect", and that is the most likely outcome. It would not vindicate either hypothesis.
- **Asymmetric information.** Both arms are told what the five rounds found and asked for something new. That is fair between arms, but it is *not* the same task Fable faced in rounds 1–3, when the earlier defects were still live and findable. So this measures "can it find #6", not "would it have found #1–5".
- **The decisive evidence is unavailable.** The question the doubled file poses — would a fresh Opus have caught it? — needs a run against the *pre-fix* tree, which is a different experiment (and worth doing if this one is inconclusive).
- **A same-family arm's verdict is not admissible as a review.** Arm A measures the rule; it is not an exemption from it. The runner prints a warning to that effect and nothing is stamped.

## Notes

Whatever the outcome, the standing debt is unchanged unless Arm B returns something: `QUALITY.md` is satisfied by a different family or a human, and Arm A is neither.

The valuable asymmetry: if Arm A finds something real, the premise is weakened and the fleet's review economics change (Claude subagents are already available; a second vendor is not). If Arm B finds something Arm A missed, the premise is supported and the cross-family runner is worth promoting upstream.
