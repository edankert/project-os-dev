---
type: "[[test]]"
id: TST-0005
aliases: ["TST-0005"]
title: "One pause rule stated once, and twelve stop-points in nine files that link it"
status: passing
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]", "[[TASK-0091]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-pause-rule.sh"
command: "bash ../project-os/tools/scripts/test-pause-rule.sh"
last_run: "2026-09-03T16:00Z"
requirements: []
features: ["[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"]
issues: []
tasks: ["[[TASK-0090]]", "[[TASK-0091]]"]
artifacts: []
adequacy: "Round 2, 2026-09-03 after review findings 1 to 3, on the template at 79e0332: heading renamed to 'When to ask the user', 1 failure on the new heading assertion (plus the generator check); PHASES.md link dropped, 1 failure naming docs/PHASES.md; release-prep second link dropped, 1 failure (1 link, want 2); LIFECYCLE.md line-61 link dropped, 1 failure (1 link, want 2). 14 of 14 on the pristine tree. Round 1: inverted three ways on 2026-09-03 against the template at commit bb6eb70, each on the working tree and reverted with git checkout: (1) the link deleted from close-out/SKILL.md, 11 assertions, 1 failure, exit 1, naming tools/skills/close-out/SKILL.md; (2) the old phrasing restored in feature-scaffold/SKILL.md, 2 failures, exit 1, the missing link and the stale phrasing both named; (3) the anchor sentence appended to HOOKS.md, 2 failures, exit 1, found 2 files and the wrong-file check. The pristine tree passes 11 of 11."
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
reviewed_by: "model:claude-opus-5[1m]"
review_date: 2026-09-03
review_verdict: approved
exit_code: 0

---

# One pause rule stated once, and twelve stop-points in nine files that link it

## Purpose

[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]] claims two things a grep can settle: the pause rule is stated in exactly one file, under a heading that exists, and each of the twelve stop-points in nine files links it instead of restating it. The review of 2026-09-03 counted eleven sites in eight files; the independent review of this feature found the twelfth, in `docs/PHASES.md`. This note executes that check.

It is deliberately a text check and not a behaviour check. Whether an agent actually pauses better is a question for the review pass on the first few sessions after the change; what this pins is the property the feature is allowed to claim.

## Procedure

`tools/scripts/test-pause-rule.sh` in `~/Dev/repos/project-os`, written by [[TASK-0091]]. The command is cross-repo for the same reason [[TST-0004]]'s is: every file under test lives in the template, and this repo's copies are a sync behind.

The script asserts:

1. Exactly one file under `tools/` plus `tools/scripts/generate-adapters.py` and `docs/PHASES.md` contains the full pause rule (the anchor sentence [[TASK-0090]] writes into LIFECYCLE.md), it is LIFECYCLE.md, and the heading `### When to pause for the user` exists there exactly once.
2. Each of the twelve sites links that heading, at the count each file carries: LIFECYCLE.md (two), `HOOKS.md`, `status-transition/SKILL.md`, `issue-intake/SKILL.md` (two), `feature-scaffold/SKILL.md`, `release-prep/SKILL.md` (two), `close-out/SKILL.md`, the planner prompt string in the generator, and `docs/PHASES.md`.
3. None of the retired phrasings remains at any of those paths.
4. `.claude/agents/planner.md` matches what the generator would produce, so the regeneration was not forgotten.

## Expected results

- Exit 0: every assertion holds. First real run 2026-09-03 against template commit bb6eb70, 11 of 11; 14 of 14 after the review round.
- Exit 1: at least one failed, each printed as `FAIL <name>: <detail>`, naming the site.

## Adequacy (who verifies this test?)

**Round 2, after the first review.** Findings 1 and 3 below were each closed by an assertion and each inverted once on the template at `79e0332`: the heading renamed (1 failure on the heading assertion; the generator check also fails because the Cursor copy is stale), the PHASES.md link dropped (1 failure naming `docs/PHASES.md`), release-prep's second link dropped (1 failure, 1 link want 2), LIFECYCLE.md's line-61 link dropped (1 failure, 1 link want 2). The pristine tree passes 14 of 14.

**Round 1.** Inverted three ways on 2026-09-03, each on the template working tree at commit bb6eb70 and reverted afterwards with `git checkout`:

1. The link deleted from `close-out/SKILL.md`: 11 assertions, 1 failure, exit 1, naming `tools/skills/close-out/SKILL.md`.
2. The old phrasing "stop and present resolution options" restored in `feature-scaffold/SKILL.md`: 2 failures, the missing link and the stale phrasing both named.
3. The anchor sentence appended to `HOOKS.md`: 2 failures, "found 2" on the exactly-one assertion and the wrong-file assertion.

The pristine tree passes 11 of 11. A grep suite that passes with the links removed is checking nothing; this one does not.

## Independent review

Reviewed 2026-09-03 by a fresh session with no memory of authoring this work, from the notes and the diff only (`model:claude-fable-5-1`; same model family as the author, which ADR-0013 permits — the independence is the context). Verdict `changes-requested`. Every mutation below ran on the template working tree at `e5aa1cd` and was reverted with `git checkout`; the tree was left clean and passing 11 of 11.

**What holds.** All three inversions recorded in `adequacy:` reproduce exactly as written: deleting the `close-out/SKILL.md` link gives 11 assertions, 1 failure, exit 1, naming that file; restoring "stop and present resolution options" in `feature-scaffold/SKILL.md` gives 2 failures naming both the missing link and the stale line; appending the anchor sentence to `HOOKS.md` gives 2 failures, "found 2" and the wrong-file check. The pristine tree passes 11 of 11 from either repo root, so the cross-repo `command:` is correct as recorded.

**Finding 1 — reproduced (medium): renaming the anchor section leaves eleven dangling citations and the suite still passes.** The suite asserts that the literal text `"When to pause for the user"` appears in each site, never that the section it names exists. Renaming `### When to pause for the user` to `### When to ask the user` in LIFECYCLE.md and re-running the generator gives 11 assertions, 0 failures, exit 0 — with every one of the eleven citations now pointing at a heading that is gone. A heading rename is the most likely future drift, and it is the one thing this suite cannot see. One added assertion (`grep -c '^### When to pause for the user' tools/instructions/LIFECYCLE.md`) closes it.

**Finding 2 — reproduced (medium): a twelfth stop-point was never converted, and the suite cannot see it.** `docs/PHASES.md:65`, under a heading that reads "Operational Rules for LLMs", still says "**Flag scope concerns**: If a task requires future-phase dependencies, document it and discuss before proceeding" — the exact sentence `bb6eb70` rewrote in LIFECYCLE.md. The stale-phrasing grep scans only `tools/instructions`, `tools/skills` and `generate-adapters.py`, so `docs/` is outside it, and that phrasing is not one of the four patterns it matches either. The change note's sentence "Every other site names the decision the user owns and links that section" is therefore false as shipped. The site is outside the eleven the review enumerated, so under this feature's own scope rule it belongs in an `ISS-*` at `triage`, not in this diff — but the claim in the notes needs narrowing either way.

**Finding 3 — reproduced (medium): three of the eleven converted sites are unguarded.** The `SITES` list covers seven files and eight link occurrences. It omits LIFECYCLE.md's own two citations (lines 61 and 72, which TASK-0091's Notes count among the eleven), and it asks `release-prep/SKILL.md` for at least one link where that file carries two. Dropping the link at LIFECYCLE.md line 61 and regenerating the adapters: 11 assertions, 0 failures. Dropping the second link in `release-prep/SKILL.md` step 2: 11 assertions, 0 failures. Both are regressions of sites the feature claims to have converted, and neither fails the test that claims to guard them. Adding the two LIFECYCLE.md sites to `SITES` and raising release-prep to 2 makes the list match the eleven.

**Finding 4 — reproduced (low): the change note's word count is wrong.** `CHG-20260903-Pause-And-Scope-Rules.md` says LIFECYCLE.md "grew from 1,343 to 1,599 words". 1,599 is its length after `0154e9d` alone; after `bb6eb70` and through `e5aa1cd` it is 1,632 (`git show <rev>:tools/instructions/LIFECYCLE.md | wc -w`). FEAT-0026 reads that figure as its starting point for the trim.

**Finding 5 — reproduced (low), documentation: eight or eleven is unresolvable from the notes.** FEAT-0024's Goal and the change note say eleven stop-points; acceptance criterion 2, this note's title and TASK-0091's title say eight. Only TASK-0091's Notes section reconciles them, by enumerating eleven sites across eight files. A reader who has the feature note and this test note — the handoff surface — cannot tell how many sites changed, and cannot tell that three of them are outside the test.

**Finding 6 — reproduced statically (low), in `tools/scripts/review-external.py`: a `reproduced: true` label is no longer checked against its evidence.** The derivation runs only when the key is absent (`if "reproduced" not in f`), so a verdict carrying `{"reproduced": true, "repro": "", "observed": ""}` is counted and printed as reproduced and reaches the transcriber in the "becomes an `ISS-*`" bucket. The filter this replaced dropped any finding lacking both fields regardless of what it claimed. Reproduced by reading the code path rather than by a live model run, which is why it is labelled low.

**Also checked and clean.** The change note's `impacts:` list matches exactly the nineteen non-CHG files changed in `163259b..e5aa1cd`, with nothing missing or spurious. FEAT-0024's acceptance criteria 3 and 4 quote text that exists verbatim in `issue-intake/SKILL.md` and in `9b53acb`. TASK-0095's three Definition-of-Done items are all present in the diff; `review-external.py --help` exits 0 and `--dry-run` assembles a prompt that carries the new instruction and the `reproduced` schema field, with the old "a finding without a reproduction is not a finding" string gone. Neither this note nor the change note carried `reviewed_by`/`review_verdict` before this pass, so rule 2 of the review skill was respected. The template validator is clean; the six `ITEM-STATUS` errors in project-os-dev all belong to the concurrent FEAT-0025 and FEAT-0026 work, not to this feature.

**Re-verified on a moved HEAD.** A concurrent session committed four more template commits during this review (`e490420`, `e4d0688`, `90920e5`, `38db9ad`), the last of which is FEAT-0026's LIFECYCLE.md trim. The suite still passes 11 of 11 on `38db9ad`: the trim kept the anchor sentence, the `### When to pause for the user` heading and both of LIFECYCLE.md's citations. Findings 1 and 3 still describe the harness as written. Finding 4 got worse in the meantime — `38db9ad`'s own subject line reads "1,599 words down to 966", and the true pre-trim size at `90920e5` is 1,632, so the wrong figure has now propagated from the change note into a commit message.

### Round 2 — approved

Re-reviewed 2026-09-03 against template `79e0332` and `5494c9f`, same fresh-context session, same model. Verdict `approved`. All six findings are fixed, and each fix was re-refuted by undoing it on the working tree: files were copied aside and copied back by name, never `git checkout .`, because the author had uncommitted work in the same tree.

Every new assertion fails when the thing it guards is undone. Renaming the heading to "When to ask the user": 1 failure, "found 0 heading(s)". Adding a second copy of the heading: 1 failure, "found 2 heading(s)", so the assertion is `exactly one`, not `at least one`. Dropping the `docs/PHASES.md` link and restoring its old sentence: 2 failures, the missing link and the stale phrasing, both naming line 65. Dropping release-prep's second link: 1 failure, "1 link(s), want at least 2". Dropping LIFECYCLE.md's first citation: 1 failure, same shape. Restoring the planner's retired "stop and return the ambiguities" beside its new link: 1 failure from the stale-phrasing grep, which is the case a link count alone cannot see. The pristine tree passes 14 of 14.

One methodological correction from this round, worth keeping: my first attempt at the LIFECYCLE.md mutation silently did nothing, because FEAT-0026's trim had reworded the line my pattern matched, and a no-op mutation looks exactly like an unguarded site. I only caught it by counting the links before and after. Any future inversion on these files should assert that the mutation landed before reading the result.

The other fixes check out. `docs/PHASES.md:65` now names the decision and links the rule like the other eleven. The change note's `impacts:` list matches exactly the twenty files touched by the seven commits in its `commit:` field, with `docs/PHASES.md` added and nothing spurious; comparing against the raw `163259b..79e0332` range instead gives ten extra files, all of them the interleaved FEAT-0025 and FEAT-0026 commits. The word count is corrected to 1,632 in the change note, TASK-0090, REQ-0026 and TST-0006, each with a sentence saying where 1,599 came from. In `review-external.py`, `f["reproduced"] = has_evidence and f.get("reproduced", True) is not False` was exercised over seven shapes: a claimed `true` with no command or no output now derives to `false`, an explicit `false` is still honoured when evidence is present, and an absent key still derives from the evidence.

Two stale numbers remain, both in FEAT-0024 and both cosmetic — recorded rather than blocking. The Scope table row for TASK-0091 still reads "2.1 (the eight stop-points)" and its Files column omits LIFECYCLE.md and `docs/PHASES.md`; the Out of scope list still opens "All eleven are legitimate". The Goal, the Goal paragraph, acceptance criterion 2 and the change note all say twelve in nine, so a reader can answer the question, but three different counts still appear in one note. Separately, this note's filename still says `Eight-Stop-Points` while its title says twelve; the `[[TST-0005]]` alias means nothing links through the filename, so renaming it is optional.

Rule 2 was respected again: the round-1 `changes-requested` was left standing in both notes rather than being optimistically flipped ahead of this pass.
