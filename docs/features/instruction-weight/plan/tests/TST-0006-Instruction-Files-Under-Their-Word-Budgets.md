---
type: "[[test]]"
id: TST-0006
aliases: ["TST-0006"]
title: "The always-loaded instruction files are under their word budgets"
status: passing
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]", "[[TASK-0098]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-word-budgets.sh"
command: "bash ../project-os/tools/scripts/test-word-budgets.sh"
last_run: "2026-09-03T16:41Z"
requirements: ["[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]"]
features: ["[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"]
issues: []
tasks: ["[[TASK-0098]]"]
artifacts: []
adequacy: "Inverted 2026-09-03: the pre-trim Cursor copy (1,663 words at commit 90920e5; an earlier version of this field said 1,374) restored beside the trimmed source makes the command exit 1 on the size assertion and on the generator check added in the review round; pristine tree exit 0, 3 of 3. The first assertion cannot be inverted without editing LIFECYCLE.md itself; its evidence is the count, 996 after the review round."
reviewed_by: model:claude-opus-5[1m]
review_date: 2026-09-03
review_verdict: approved
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
exit_code: 0

---

# The always-loaded instruction files are under their word budgets

## Purpose

[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]] states one number that a command can settle: LIFECYCLE.md under 1,000 words (800 until the 2026-09-03 amendment recorded on the requirement). This note executes it, plus two more assertions: the generated Cursor copy is under 1,040 words, and `generate-adapters.py --check` reports every generated file current. The size check alone would pass a stale copy that happened to be short; the generator check is what shows the copy was regenerated, so a Cursor session does not keep loading the old 1,663 words after the source shrank.

The requirement's other two criteria are about shape, not size, and are discharged by the review of the diff. This test does not claim to cover them.

## Procedure

`tools/scripts/test-word-budgets.sh` in `~/Dev/repos/project-os`, two `wc -w` assertions. The command is cross-repo for the same reason [[TST-0004]]'s is: the files under test live in the template. It started as an inline `bash -c` command in this note; `run-tests.py` strips a trailing quote from a frontmatter value and broke it, so the check moved into a script (follow-up on the runner recorded in the FEAT-0026 close-out summary).

```bash
bash ../project-os/tools/scripts/test-word-budgets.sh
# tools/instructions/LIFECYCLE.md: < 1,000 (1,343 at the review, 1,632 after FEAT-0024, 966 after the trim)
# .cursor/rules/lifecycle.mdc:     < 1,030 (1,374 at the review, 1,005 after the trim)
```

## Expected results

- Exit 0: both files under budget. First real run 2026-09-03 after TASK-0098.
- Exit 1: either file over budget, or the Cursor copy not regenerated.

## Adequacy (who verifies this test?)

The second and third assertions are the ones worth checking: with the trimmed source in place, the pre-trim `.cursor/rules/lifecycle.mdc` (1,663 words at commit `90920e5`; the note first said 1,374, the count at the review before FEAT-0024, and the review corrected it) put back must make the command fail. Inverted on 2026-09-03: `git show 90920e5:.cursor/rules/lifecycle.mdc > .cursor/rules/lifecycle.mdc` in the template, the command exits 1 on the size assertion and, since the review round added it, on the generator check as well; restored with `git checkout -- .cursor/rules/lifecycle.mdc`, exit 0. Without the generator check the test passed on a short but stale copy, which the review pointed out.

**A note on this note's own status.** It carries `command:` together with `status: passing`, `last_run:` and `exit_code:`. The template's STATUSES.md says a test with a `command:` records no verdict (cockpit ADR-0038); this repo stamps the status by execution (ADR-0010) and its validator accepts that. The two models disagree, which is row 3 of [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]] and the decision ISS-0046 needs; the status here follows this repo's rule until that is settled.

## What this test deliberately does not check

Whether the shorter file still says everything it needs to. A word count cannot see a deleted rule, which is why the feature's acceptance carries a moved-text table and the close-out carries an independent review pass.

## Independent review

Reviewed 2026-09-03 by `model:claude-opus-5[1m]`, in a session that started from these notes and the diff and never saw the author's reasoning. Verdict: **changes-requested**. What follows covers TST-0006, both template change notes, REQ-0026 and the two features they close.

### The test itself works

Both assertions run and the second one can fail. Pristine tree: exit 0. Restoring the pre-trim Cursor copy (`git show 90920e5:.cursor/rules/lifecycle.mdc`) makes the command exit 1 on that assertion alone, and `git checkout -- .cursor/rules/lifecycle.mdc` returns it to exit 0. The inversion is real, so the test guards something.

Two corrections to what this note claims about it.

**The Adequacy section quotes the wrong number.** It says the pre-trim copy at commit `90920e5` is 1,374 words. It is 1,663. The 1,374 was the count at the review, before FEAT-0024 added text; the change note's Counts table has both numbers right and this note conflates them. The Purpose section repeats the same error ("the old 1,374 words").

**The second assertion does not check that the Cursor copy was regenerated.** It checks that the copy is under 1,030 words. A stale copy that happens to be short still passes. `python3 tools/scripts/generate-adapters.py --check` is the check that actually detects staleness, and it passes today over 35 artifacts. The Purpose section overstates the assertion; either say it checks size, or add the generator check.

**The margin is now six words.** As of template commit `6730eb4`, LIFECYCLE.md is 986 words and the Cursor copy is 1,024 against the 1,030 budget. Commit `6730eb4` exists only to trim LIFECYCLE.md back under budget after `2b6ef10` added one sentence. The budget is already forcing defensive edits within hours of landing.

**This note breaks the rule it was written under.** It carries `command:`, `status: passing`, `last_run:` and `exit_code: 0` together. STATUSES.md is explicit: "A test that carries a `command:` records no verdict — not `ready`, not `passing`, not `failing`, and no `last_run:` or `exit_code:` (ADR-0038)." This is the same class of defect as ISS-0046.

### Criterion 2 of REQ-0026: does not hold as written

The criterion reads "every rule in the six trimmed files is a normative sentence, one line of reason, and a link". Two problems.

First, there are five trimmed files, not six. The change note's own title says five. FEAT-0026's Goal says "the other five" while its Scope table lists four, so the set the criterion quantifies over is not defined anywhere consistently.

Second, and substantively: most rules in these files carry no reason and no link. Counting bullet and numbered rule lines against lines carrying an explicit `Reason:` or an `ADR-00NN` citation gives LIFECYCLE 31 rules / 4 reasons / 3 links; STATUSES 85 / 4 / 18; TESTING 26 / 2 / 2; QUALITY 25 / 3 / 5; DECISIONS 12 / 4 / 5. Under a quarter of rules have either. LIFECYCLE.md close-out steps 2, 4, 5, 6 and 7, all four phase-alignment steps, and all five risk-scan triggers are bare imperatives.

This is probably the right outcome — giving thirty rules a reason and a link would not fit in 966 words — but it is not what the criterion says. The criterion and REQ-0026's own Statement ("must state its rules, the reason for each, and a link to the decision that took it") pull directly against the word budget, and the implementation resolved that tension silently in favour of the budget. Restate the criterion as what was actually achieved: no rule lost a reason it previously had, and the reasons that remain are one line plus a link. Do not tick it in its current wording.

### The central claim is refuted: rules were dropped, not only history

Each item below was checked by reading the full before and after text, not the unified diff, and then grepping `tools/instructions/` and `tools/skills/` for a surviving statement. None of them appears in the change note's moved-text table.

1. **STATUSES.md — an automated test may not sit at `ready`.** Before: "A test that carries a `command:` records no verdict — **not `ready`, not `passing`, not `failing`**, and no `last_run:` or `exit_code:`". After: "A test with a `command:` records no verdict, `last_run:` or `exit_code:`". `ready` is not a verdict, so the compressed wording no longer forbids it, and the line two above says `ready` is "the state a test note is created in". A reader of the trimmed file alone would create an automated test at `ready` and think it correct.
2. **LIFECYCLE.md — Bases views are not canonical for agents.** The sentence "Bases views are for human consumption: they render views over note frontmatter and are not canonical for agents" is gone, and no file under `tools/instructions/` states it. SNAPSHOT.md line 18 says something different.
3. **LIFECYCLE.md — where notes are filed.** Preflight step 4 listed six directory paths with their `ID-####-*.md` filename patterns. It now names only `docs/__templates__/` and the note types. A reader of the trimmed file does not know where an issue, requirement, phase or risk note goes.
4. **TESTING.md — the lower half of the adequacy cadence rule.** Before: "if mutation scores on guarding tests are consistently above ~80%, reduce the adequacy-check cadence; **below that, keep checking every guarded fix**." After keeps only the permission. The obligation below the threshold is gone.
5. **DECISIONS.md — ADR-0011's three clauses.** Before: "the cutover is encoded in code, no more than 90 days out, and promotion over unpaid debt is forbidden", plus grandfathered instances listed "by ID with reasons". After: "ADR-0011 applies unweakened". A numeric cap, an absolute prohibition and a required record format all became a citation. In this repo that citation resolves to nothing: `docs/decisions/` contains only `README.md`. The 90-day cap survives in the template only inside Python comments in `validate-docs.py`.
6. **STATUSES.md — the re-adoption enumeration.** "set the non-parked status (`backlog`/`open`/`draft`/`planned`)" became "the non-parked status".
7. **QUALITY.md — what the validator checks, and two enforcement paths.** The five-item enumeration (snapshot-filesystem agreement, frontmatter consistency, counter integrity, link-graph integrity, the verification invariant) survives nowhere. `install-git-hooks.sh` and `.github/workflows/validate-docs.yml` were both dropped from the sentence naming the three enforcement layers.

Two claims I expected to find and did **not** reproduce, recorded so the author does not chase them: the rule that a cancelled or superseded feature cancels rather than advances its requirement **survives** at STATUSES.md line 86, so dropping it from QUALITY.md is correct de-duplication under ADR-0024; and the PHASE-CHILDREN and PHASE-BOXES paragraphs kept their gates, their scope, the `- [~]` reconciliation mark and the `superseded` exemption, losing only the "resolve or re-home the child" remediation.

### The moved-text table has four inaccurate rows

- **`docs/__templates__/adr.md` "carries the form"** — it carries only the numbered-list form. The row says the *second* worked example moved there; that example was the `### N. Title` form, which appears nowhere in the template, in the trimmed DECISIONS.md, or in the change note. Both examples were deleted, and the template's own comment says "Either form; both are read" while showing one.
- **"rewritten literally"** is true for `feature-scaffold/SKILL.md` only. In TAXONOMY.md the clause "the drift travelling under its own fix" was deleted, not restated. `docs/__templates__/feature.md` was not touched by commit `28c857a` at all; its phrase went in `74753d1` with the surrounding comment.
- **The PHASE row's destination is a label.** "the rest is this note" is false — the change note carries the row's summary, not the deleted paragraphs. Little is actually lost (see above), so fix the row, not the file.
- **TESTING.md now cites a note that is not where it says.** Line 40 reads "measured in project-os-dev CHG-20260903-Instruction-Weight". That change note is in project-os, not project-os-dev. The citation was introduced by this trim and dead-ends.

### The reachability problem under all of it

The trim's strategy is "the reason moves to the decision the rule cites". In the template that strategy has no destination: `project-os/docs/decisions/` holds only `README.md`. The trimmed files cite `ADR-0007`, `ADR-0008`, `ADR-0011`, `ADR-0013`, `ADR-0019`, `ADR-0020` and `ADR-0023` as bare numbers. Downstream those numbers resolve to unrelated decisions — cockpit's ADR-0008 is "Legacy Status Tolerance", your-health's ADR-0007 is "Health-Connect-Is-The-Store-Of-Record". Two citations are repo-qualified and do work: `(ISS-0006; project-os-dev ADR-0024)` and `(project-os-cockpit ADR-0031)`. Qualify the rest the same way. This problem predates the change; the change makes the fleet depend on it.

### Criterion 5 of FEAT-0025: partly met

The first notes written after WRITING.md rules 7 to 10 landed follow some of the rules and break others.

They follow rule 3 (concrete subject, real verb) and rule 5 (name what the reader sees before the code symbol) consistently: "the template's `focus.note` is 266 words", "1,343 at the review, 1,632 after FEAT-0024, 966 after the trim". Rule 4 is honoured — "mannered prose" is glossed on first use. Rule 6 holds; every heading states a fact.

They break these:

- **The twelve-word title limit**, in both change notes the feature produced. "Five instruction files are rules, reasons and links; the history moved to the decisions that hold it" is 17 words. "WRITING.md covers the message a person reads, and snapshot fields have a length" is 13. Commit `e4d0688` set that limit hours earlier.
- **Rule 1, in CHG-20260903-Instruction-Weight's Summary.** It opens with two sentences of background about what sessions load. The point — "Five files now state each rule once as a normative sentence, one reason, and a link" — is the fifth sentence. The same commit's new template asks for "two or three sentences, point first"; that Summary is five sentences. The sibling change note gets this right, opening with what changed.
- **Rule 2, throughout.** Counting sentences over 25 words outside tables and checkboxes: 7 in CHG-20260903-Instruction-Weight, 4 in CHG-20260903-Writing-Rules-And-Lengths, 2 in each of the six task notes. The worst is 83 words joined by a semicolon ("Two smaller changes in the same feature: ..."), and one of 68 words listing all four new rules.
- **Rule 7, the rule this feature added.** New prose written after it still reaches for metaphor: "the second assertion that keeps the first honest" (this note), "LIFECYCLE.md grows back" and "every future rule arrives with its story attached" (REQ-0026), "a check arriving over undismantled debt is a check that gets disabled" (FEAT-0025), "A length check over a fleet with undischarged debt is the shape ADR-0011 forbids arming" (REQ-0026, which also fails rule 3).

So the criterion cannot be ticked as stated. The rules were followed at the level of individual word choice and broken at the level of sentence length and message structure, and the two numeric limits the same feature introduced were broken by the notes announcing them.

### The amended budgets on REQ-0026 are honest, with one exception

The amendment is not retrofitted. The sentence it leans on — "Re-set them from the measured ratio once TASK-0098 has landed. If the honest trim of that file comes out at 700 or at 900 words, the other four budgets move with it" — was committed at planning time in `c5cfbbc` and is untouched by this diff. The method was written down before the outcome was known, which is what separates an amendment from a retrofit. The LIFECYCLE.md amendment then follows that method: 966 of 1,632 is 59%, against the 60% the budget was built from, and the 289 words FEAT-0024 added to the same file after the budget was set are a real, separately-authored change of baseline.

The exception is DECISIONS.md. The second amendment does not use the pre-committed method; it sets each budget to "the next round number above the measured count", which passes every file by construction. For STATUSES.md (60.0%), TESTING.md (59.8%) and QUALITY.md (62.3%) this makes no difference, because they met the ratio and missed only the rounding. DECISIONS.md landed at 69.1%. Applying the pre-committed ratio would have given about 828 words and left it failing; the round-up rule gives 1,000 and passes it, an 18% raise. The stated reason — two fenced examples and the three-section rule-ADR block are the convention itself — is checkable and I believe it, but the switch of method is not disclosed. Say that the shape rule, not the ratio, is what settled DECISIONS.md.

One knock-on: FEAT-0026's Out of scope still says "The word budgets for the other five files ... The others are shaped, not counted", and the plan's open question still asks whether the owner wants numbers. REQ-0026 now carries four counted budgets as ticked criteria. Reconcile the three documents.

### Close-out and consistency defects

- **`bash tools/scripts/validate-docs.sh` fails in project-os-dev with 2 errors.** REQ-STALE: REQ-0026 is `approved` while FEAT-0026 is `done`. FEATURE-REQ: FEAT-0026 is `done` with one unticked criterion on REQ-0026. Leaving the criterion unticked pending this review was right — that is independence rule 2. Setting the feature to `done` anyway was not; it should have stayed at `review`. LIFECYCLE close-out step 7 requires the validator to pass.
- **TASK-0098 ticks a box whose text is false.** Its filename, title and first Definition-of-Done line all say "under 800"; the result is 966; the box is `[x]`. Only the Notes paragraph corrects it. Retitle the task and restate the box, or the ticked list reads as evidence for a claim that was not met.
- **TASK-0096's title says "five rules"; four were added** (rules 7 to 10). FEAT-0025, the change note and the commit message all say four. The snapshot carries the "five" title.
- **SNAPSHOT.yaml's REQ-0026 note is stale**: "LIFECYCLE.md under 800 words is the firm criterion. Budgets for the other four files were added ... as provisional stopping rules ... not gates." All three clauses are now wrong. `note:` prose is curation the sync script leaves alone, so nothing will fix this automatically.
- Commit `38db9ad`'s message says the pre-trim count was 1,599; it was 1,632. Commit `6acf773` says DECISIONS.md landed at 860; it is 954. The change note discloses both, which is the right handling.

### What was independent, and what was not

Independent: a fresh session that had never seen the author's reasoning, working from the notes, the diffs and the two repositories. I read the full before and after text of all five instruction files rather than the diffs, ran the test and its inversion, ran `validate-docs.sh` and `generate-adapters.py --check` in both repos, and checked each moved-text row against the file it names.

Not independent: the model. The author's commits are co-authored by Claude Fable 5.1 and this review ran on `claude-opus-5[1m]`. Under ADR-0013 that is acceptable and it is recorded in `reviewed_by` as provenance; a reader who wants a different-weights pass should commission one.

Method note, so the findings can be weighed: three parallel subagents did the mechanical before-and-after enumeration, and I verified every finding above against the files myself. Two of their strongest claims did not survive that check and are recorded as not reproduced in the section above.

### What would clear this

Restate criterion 2 to what was achieved and criterion 5 of FEAT-0025 likewise, or fix the notes so they hold. Restore the seven dropped rules or record them in the moved-text table with real destinations. Fix the four inaccurate table rows and the TESTING.md citation. Qualify the bare ADR numbers with their repo. Correct this note's 1,374 and its claim about regeneration, and remove `last_run:`/`exit_code:` and the `passing` verdict from a note carrying a `command:`. Move FEAT-0026 back to `review` until REQ-0026's criteria are settled, so the validator passes.

### Round 2, 2026-09-03: approved

Every round-1 finding is fixed. Verdict on TST-0006 and both template change notes moves to **approved**. What I checked, and what is left.

**The seven restored rules are in place.** I read each one in its file rather than trusting the commit message. STATUSES.md line 133 carries "not `ready`, not `passing`, not `failing`" again, and line 155 the `backlog`/`open`/`draft`/`planned` enumeration. LIFECYCLE.md line 16 carries the Bases sentence and line 32 all six note paths with their filename patterns. TESTING.md line 65 carries "below that, check every guarded fix". DECISIONS.md line 83 carries the cutover clause, the 90-day cap and the unpaid-debt prohibition. QUALITY.md line 25 carries the five checks, `install-git-hooks.sh` and `.github/workflows/validate-docs.yml`. The change note's "no rule was dropped" claim is now true for everything I found.

**The third assertion closes the gap I named, and it discriminates.** I made the Cursor copy stale without making it long — deleted one sentence, leaving it at 1,023 words against the 1,040 budget. Both size assertions still passed; `generate-adapters --check` failed and the command exited 1. That is precisely the case the old two-assertion version could not catch. Restored by copying the file back; pristine run is 3 of 3, exit 0. The 1,040 budget is derived rather than fitted: the source budget plus the generated header's 40 words.

**The moved-text table is now accurate.** The four rows I disputed say what actually happened: the `## Options` row reads "Deleted, not moved" and states that the template carries only the numbered-list form; the `feature.md` row names commit `74753d1` rather than `28c857a`; the TAXONOMY.md row says the clause was deleted rather than rewritten; the PHASE row quotes the removed sentences instead of labelling them. TESTING.md line 40 now cites the change note in project-os, where it is.

**The amendments disclose the method switch.** The third Amendments entry states plainly that the other four budgets were re-set by a different rule than the one the LIFECYCLE amendment used, gives DECISIONS.md at 70% and an 18% raise over the ratio, and says the review asked for the disclosure. That is the finding answered rather than absorbed. The narrowed criterion 3 is a fair statement of what was built.

**`validate-docs.sh` in this repo is clean apart from my own stale round-1 verdict**, which this approval clears. REQ-STALE and FEATURE-REQ are gone.

Residual findings, none blocking:

1. **Rule 2 is still broken in the two change notes.** Sentences over 25 words, outside tables and checkbox lists: nine in CHG-20260903-Instruction-Weight, three in CHG-20260903-Writing-Rules-And-Lengths. The 83-word sentence beginning "Two smaller changes in the same feature" survives, and the restoration paragraph added a new 79-word one. FEAT-0025's criterion 5 is ticked as "met after the fixes it prompted"; the titles and the point-first summary were fixed, but sentence length in the primary evidence was not. Either split those sentences or reconcile the criterion to say so.
2. **REQ-0026's Statement still contradicts its own criterion 3.** The Statement says an always-loaded file "must state its rules, the reason for each, and a link to the decision that took it". Criterion 3 was amended away from reason-on-every-rule precisely because that is unaffordable. Amend the Statement to match, or the requirement asserts the thing the amendment retired.
3. **"with reasons" was not restored.** DECISIONS.md said grandfathered instances are "listed by ID with reasons in `../GRANDFATHERED.yaml`"; the restoration brought back the ADR-0011 clauses but not this. "by ID" survives once in STATUSES.md line 40, which is correct de-duplication; the requirement that an entry carry a reason is now stated nowhere.
4. **Two budgets have four to six words of headroom.** LIFECYCLE.md is 996 against 1,000 and the Cursor copy 1,034 against 1,040. QUALITY.md's budget has now moved twice, 850 to 900 to 950. The amendments disclose all of it, so this is a note about fragility rather than a defect: the next one-sentence rule will fail the test, as commit `6730eb4` already showed.
5. **This note's account of its own status leans on the weaker of two claims.** It says "this repo stamps the status by execution (ADR-0010) and its validator accepts that". This repo's own STATUSES.md line 143 says the opposite, in the template's words, because it is synced. What is true is that the validator accepts it while the instruction file forbids it. Say that; the contradiction is the point of ISS-0048 row 3.
6. **The bare `ADR-00NN` citations remain**, correctly recorded as a follow-up on the change note with the downstream hazard named. Worth doing before the next fleet sync, not before this close-out.

Independence for this round is the same as round 1 and stated there: fresh context, separate session, same model family, recorded in `reviewed_by`. I re-derived every claim from the files rather than from the round-2 summary I was given.
