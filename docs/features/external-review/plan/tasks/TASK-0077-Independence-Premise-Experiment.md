---
type: "[[task]]"
id: TASK-0077
title: "Test the independence premise: clean-context Opus vs a different family, identical prompt"
status: done
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

- [~] Both arms run to completion on a byte-identical prompt — **reconciled, not met.** Arm A completed twice (HEAD and pre-fix). Arm B completed twice on `gpt-5-codex` but its `gpt-5.6-terra` run was cut off by a usage cap. The prompt was byte-identical throughout; the completion was not. The result rests on Arm A, and the ADR says so.
- [x] Findings triaged by whether their `repro` actually reproduces — the same bar every Fable finding met
- [x] The result is recorded whatever it is, including a null result from both arms
- [x] The implication for `QUALITY.md`'s rule is stated: confirmed, weakened, or unresolved

## Result

**The premise failed on its own strongest prediction.**

| Arm | Relation to author | Doubled file | Findings |
|---|---|---|---|
| Fable, round 3 (baseline) | same family, different pin | found | 3 |
| **clean-context Opus** | **same family, same pin** | **found — the run's only `high`** | **5** |
| gpt-5-codex, read-only sandbox | different family | missed | 3 |
| gpt-5.6-terra, write access | different family | incomplete — usage cap | — |
| **Antigravity (`agy`), full tools** | **different family** | **found — rated `high`** | **4** |

Clean-context Opus, on the pre-fix tree, with a prompt verified to leak nothing about duplication, line counts or structure, found the doubled file **and described it more accurately than the baseline had**: importers bind the second copy while script runs use the first, so `sync-snapshot.py` and the cockpit bundle execute different code from the CLI, and an edit to the first copy is invisible to every importer. The baseline had called the tail "inert". Confirmed independently by `inspect.getsourcelines`.

Adopted as [[ADR-0013]]. `QUALITY.md` now gates on clean context rather than model family, and both phase-routed agent pins move to Opus.

Four further defects came out of the HEAD arm of the same experiment and are fixed in [[ISS-0016]] — including the sharpest of the whole ISS-0011..0016 sequence: the completeness registry was keyed on `id()`, and CPython deduplicates equal tuple constants, so an unregistered status table whose literal matched a registered one was invisible to the guard built to catch exactly that.

## The fourth arm changes the conclusion

Antigravity's `agy` CLI (Google) finally gave the different-family arm a fair run: real tool access, `--effort high`, the same unleaked prompt, the same doubled tree. **It found the doubling and rated it `high`**, with a repro that matches the one confirmed independently — `inspect.getsourcelines(vd.validate)[1]` returns 2032, the second copy. It also found the dict evasion, the surviving inline literals, and nested-collection evasion: four findings, three of them matching what other arms found separately.

So the discriminator is **tool access, not family**:

| | Full tools | Found the doubling |
|---|---|---|
| Fable (same family, diff pin) | yes | yes |
| clean-context Opus (same family, same pin) | yes | yes |
| Antigravity/Gemini (different family) | yes | yes |
| gpt-5-codex (different family) | **no — read-only sandbox** | **no** |

Three of four arms with a working shell caught it. The one without did not. The sandbox confound flagged when that result came in was the whole explanation, and this removes the uncomfortable reading that a different family is *worse* at this.

[[ADR-0013]]'s conclusion is unchanged and better supported: family is not the gate. What the ADR could not say before is now sayable — a different family did fine, once it could actually run things. The requirement that matters is the one the runner was built around: **a reviewer needs a shell.**

**Caveat on this arm.** `agy` was invoked with `--model gemini-3.1-pro-high`, and the reviewer self-reported `model:gemini-3.6-flash`. Either the flag did not take, `agy` routes internally, or the self-report is unreliable. So this arm measures "a Google model with full tools", not specifically the selected Pro tier — and if anything that understates the result, since a Flash-class model found what a sandboxed frontier model missed. Do not cite this row as a Pro result.

## Two runner bugs, both silent hangs

Worth recording because `project-os-bench` reuses this adapter, where a hung candidate is indistinguishable from one that produced nothing:

- `codex exec --sandbox workspace-write` blocks on an approval prompt it cannot display without a TTY. No `--ask-for-approval` flag exists; `-c approval_policy="never"` is the fix.
- A third, found later: the runner's own timeout must exceed the CLI's internal one. A 360s outer limit against `agy`'s 5m default killed a run that was working. `agy` is also extremely slow — 849 seconds for a single file read — so reviews need hours, not minutes.
- The runner never closed stdin. `codex exec` appends piped stdin to the prompt, so an inherited pipe that never reaches EOF blocks it **before any network call**. `stdin=subprocess.DEVNULL`, applied to every runner.

Both presented as ~60ms of CPU over many minutes with no output and no exit — indistinguishable from a slow review unless you check CPU time. Found only because Edwin asked twice whether anything was actually happening.

## Honest limits, recorded before seeing results

- **n=1 per arm.** One run each cannot separate model capability from sampling. A finding is evidence; a null result from a single run is weak.
- **The task may be empty.** Five rounds have already hardened this target. "Nobody found a sixth defect" is consistent with "there is no sixth defect", and that is the most likely outcome. It would not vindicate either hypothesis.
- **Asymmetric information.** Both arms are told what the five rounds found and asked for something new. That is fair between arms, but it is *not* the same task Fable faced in rounds 1–3, when the earlier defects were still live and findable. So this measures "can it find #6", not "would it have found #1–5".
- **The decisive evidence needed a second experiment**, and it was run: the pre-fix-tree arms above. That is what makes this result more than suggestive.
- **A same-family arm's verdict is not admissible as a review.** Arm A measures the rule; it is not an exemption from it. The runner prints a warning to that effect and nothing is stamped.

## Notes

*Written before the run, kept for the record:* "the standing debt is unchanged unless Arm B returns something: `QUALITY.md` is satisfied by a different family or a human, and Arm A is neither."

That framing was right about the rule as it stood and wrong about where the experiment would lead. The debt was not discharged by satisfying the rule — it was discharged by [[ADR-0013]] establishing that the rule was measuring the wrong thing. Arm A could not satisfy the old rule and did not try to; it tested it.

The anticipated asymmetry held, in the first direction: Arm A found something real, so the premise is weakened and the review economics change. Clean-context subagents already exist and cost nothing extra; a second vendor is neither free nor, on this evidence, better.

## What the different-family arm deserves

*Written before the Antigravity run, and superseded by it — kept because the caution was right and the conclusion it guarded against would have been wrong.*

It never got a fair run, and this note should not be read as evidence against cross-family review.

The first pass was sandboxed read-only, so it attacked by injecting globals instead of mutating files — and still independently rediscovered two of [[ISS-0014]]'s three findings plus one of its own. The second hit a usage cap mid-review, with `reasoning effort: none`, after 67k tokens of genuine work (its own edits to the file are in the transcript).

What the experiment establishes is narrower than "family does not matter": **the fleet's rule rested on an untested premise, and its one direct test contradicted it.** That is enough to change a rule nothing could satisfy. It is not enough to conclude a different family adds nothing.
