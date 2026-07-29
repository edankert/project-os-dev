---
type: "[[issue]]"
id: ISS-0023
aliases: ["ISS-0023"]
title: "Round two on ADR-0017: the frontmatter three-question test still asks who writes the field, which the amended clause 3 abandoned, so it fails the two mechanisms the body calls compliant; two notes still quote the superseded clause; and ISS-0021's new provenance paragraph mis-cites TASK-0070 and claims months of drift where the tree shows three days"
status: open
severity: medium
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: docs
source: ["review:2026-07-29-independent-re-review-ADR-0017"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [ADR-0017, ISS-0022, ISS-0019, ISS-0021, ADR-0014, REQ-0023]
tests: []
---

# Round-two review findings on ADR-0017: the amendment did not reach its own operational test

## Problem

Round-two clean-context independent review of [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]], reviewing the fixes the author session applied after round one ([[ISS-0022-ADR-0017-Ratifies-A-Proposed-ADR-And-Clause-3-Has-No-Scope|ISS-0022]], verdict `changes-requested`). **All five round-one findings are resolved in the text and re-verified against the tree** — the ticks on ISS-0022's Next Actions carry the evidence. `status: accepted` stands on the owner's re-affirmation of the amended clause 3 and is not a finding.

What does not survive is the new material. Clause 3 was reworded from *"never written by the party seeking the transition"* to *"never trusted on the unmarked word of the party seeking the transition"* — a real improvement, and the change that makes the waiver and manual-test paths compliant instead of contradictory. But the rewording reached the Decision section only. Three places still encode the abandoned wording, one of them the ADR's own frontmatter, and two of them notes that quote it verbatim.

### 1. Blocking — the three-question test contradicts the clause it operationalises

`ADR-0017:23`, unchanged by the fix:

> Every future state field gets a **three-question test** — can this be executed? if not, is it labelled and dated? **and can the party seeking the transition write it?** — rather than an ADR-length argument

The third question is the pre-amendment clause 3. The amended clause 3 (`ADR-0017:54`) says the writer's identity is *not* the test, and `ADR-0017:58` states the consequence explicitly: `last_verified:` and `waiver_expires` are *"both written by the closing agent, compliant because labelled and expiring, **not because independently authored**."*

So apply the test as written to `waiver_expires`. Q1: can it be executed? No — nothing derives the date. Q2: is it labelled and dated? Yes. Q3: can the party seeking the transition write it? **Yes** — 19 of 19 in this repo were written by the closing agent. Under Q3 the field fails; four lines further down the ADR says it is compliant. The same result for `last_verified:`. The two mechanisms the ADR holds up as clause 2 working correctly are exactly the two its own test rejects.

This matters more than a wording slip because the ADR stakes its entire value on that test: *"If six months pass and it has not been cited to settle a question about a new field, it did not earn its place"* (`ADR-0017:83`). The artifact an agent will actually reach for is the three-question list in frontmatter, not the paragraph in the body — and it gives the wrong answer for the clause-2 path.

A second gap in the same list: the amended clause 3 newly names the *gate reads nothing* case as its central violation (`ADR-0017:56`, citing [[ISS-0019-Verify-Is-Blind-To-Tests-That-Were-Never-Linked|ISS-0019]]), and none of the three questions can detect it — all three presuppose a recorded value to interrogate. The test cannot find the one defect the amendment added.

The fix is a Q3 that matches the rule: *does the gate read anything, and if what it reads is this party's own word, is it marked as such?*

### 2. Blocking — two notes still quote the superseded clause 3 as ADR-0017's text

The amendment changed a normative clause in an `accepted` ADR and left its verbatim quotations behind:

- `docs/issues/ISS-0019-Verify-Is-Blind-To-Tests-That-Were-Never-Linked.md:81` — *"This is a clause-3 instance under ADR-0017: **never written by the party seeking the transition.**"*
- `docs/reference/Intake-Quality-Without-Reading-2026-07-29.md:51` — *"ADR-0017 states it in three clauses instead, of which the third (**never written by the party seeking the transition it gates**) is the invariant that actually unifies…"*

Both now misquote the ADR they cite, and both were checked with `grep -rn "never written by the party" docs/ tools/`. The reference-note case is the worse of the two: the fix **edited that file** (the sequencing paragraph at line 53) without noticing the quotation two lines above it. ISS-0019's case additionally inverts the argument — it invokes the old wording to explain why closing with no test violates clause 3, whereas the amended clause reaches that case through *unmarked word*, which is a stronger and different route.

The same reference note also still carries round-one finding 1's shape in its own prose: line 51 lists ADR-0014 among the decisions the third clause *"actually unifies"*, and the disposition table says ADR-0014 *"deliberately made legal"* the `human:`/`asserted:` tokens — present indicative about a `proposed` ADR. The fix applied the proposal-register correction to ADR-0017 only.

### 3. Minor — the replacement `monitoring` clause is still refutable, one scope narrower

`ADR-0017:75` now reads: *"In the status taxonomy, `monitoring` appears only as a rejected risk status (`STATUSES.md:106`); its other occurrences repo-wide are the validator's legacy-vocabulary constant and historical notes."* The first half is correct and `STATUSES.md:106` re-checked clean. The second half is not, by `grep -rn "monitoring" --include=*.md --include=*.py --include=*.yaml`:

- `tools/cockpit/src/project_os_cockpit/cockpit.py:126` — a **live literal** in `TASK_STATUS_ORDER`, which `tests/test_status_vocabulary.py` keeps in step with the vocabulary. Not the validator's, not a note.
- `tools/scripts/migrate-status-vocabulary.py:88` — a live mapping entry, `("risk", "monitoring"): "open"`.
- `tools/instructions/SNAPSHOT.md:99` and `tools/skills/risk-mitigation-planning/SKILL.md:30` — current instruction and skill files, not historical notes.
- `tools/scripts/validate-docs.py:220` and its bundled copy — these two *are* fairly described as the legacy-vocabulary constant's commentary. Round one's own description of line 220 as a "live literal" was itself imprecise; it is a `#:` comment.

The row's conclusion is unaffected either way. This is the third revision of one sentence, which is the signal worth acting on: the sentence is trying to characterise 25 occurrences it does not need to mention. Dropping the second clause entirely leaves the row true.

### 4. Blocking — ISS-0021's new provenance paragraph attributes the waiver backfill to the wrong work

[[ISS-0021-Verification-Waivers-Have-No-Budget|ISS-0021]]`:46`: *"`2026-10-23` is the migration default — the **FEAT-0017/TASK-0070** backfill dated 49 waivers fleet-wide with that single date when `WAIVER` was promoted to error."*

`TASK-0070` is *"Clear ~325 REQ-BOXES/FEATURE-REQ findings across the fleet, and resolve the live ADR-0007 cutover."* It is a different backfill and its note contains no mention of waivers. The waiver dating belongs to **FEAT-0016 / [[TASK-0068-Staleness-And-Waiver-Expiry|TASK-0068]]**, whose Definition of Done reads *"The 48 existing waivers and the fleet's manual tests are dated"*, and the decision is recorded in [[REQ-0023-Manual-Verification-Expires|REQ-0023]]'s amendment: *"The 49 waivers were dated uniformly to 2026-10-23 (90 days)."* FEAT-0017 / `TASK-0069` records the number only as the precondition for promoting `WAIVER` to error (`TASK-0069:67`).

The intake reference note repeats the same mis-attribution — *"the shared expiry date is the FEAT-0017 migration default"* (line 53) — while its own disposition table, five lines earlier, correctly cites `TASK-0068`. One file, two attributions, contradicting each other.

This is the identical defect class as round-one finding 3 (a consequence naming ISS-0020 for ISS-0019's work), reintroduced by the fix for it.

### 5. Blocking — "no waiver has diverged from the migration default since" is refuted by the dates

ISS-0021's reframing (title, and line 48) turns the finding into an ongoing-neglect claim: *"the migration default **no waiver has diverged from since**"*, and *"nineteen items carrying the migration's one-size date **months later** means that judgement has not happened once."*

Measured: all 19 `waiver_expires` values were introduced in a single commit, `18e8f81`, dated **2026-07-26** — three days before the note (`git log -S"waiver_expires"` per file, oldest entry, for each of the 19; all 19 return that one commit). No waiver has been created since the migration, so none has had the opportunity to diverge, and "months later" is off by roughly two orders of magnitude in the direction that flatters the finding.

The **original** finding was sound and is now weaker than what replaced it: one date applied to 49 items is one judgement applied 49 times, and that is true of the migration whatever the elapsed time. The reframing traded a checkable claim for an unsupported one about duration. Restate as: the migration deliberately chose a uniform date (`REQ-0023`: *"letting renewal be the forcing function"*), and the open question is whether anything will force per-item judgement at renewal — not that judgement has been neglected for months.

## Expected

An amendment to a normative clause reaches every place that states or applies it: the operational test in the same frontmatter, and the notes that quote it. Corrections cite the work that actually did the thing.

## Actual

The reworded clause 3 reached the Decision section. Its own three-question test, two verbatim quotations, and one still-present-tense reference note were left on the superseded wording; and the adjacent numeric correction shipped with a wrong task ID and a duration claim the commit dates refute.

## Evidence

- `ADR-0017:23` vs `ADR-0017:54,56,58` — the Q3/clause-3 contradiction, read directly
- `grep -rn "never written by the party" docs/ tools/` → `ISS-0019:81`, `Intake-Quality-Without-Reading-2026-07-29.md:51`
- `grep -rn "monitoring" --include=*.md --include=*.py --include=*.yaml .` → 25 hits across 17 files outside ADR-0017 and this note's siblings; `cockpit.py:126` and `migrate-status-vocabulary.py:88` are live literals
- `TASK-0070` title and body (no waiver content); `TASK-0068` DoD line *"The 48 existing waivers … are dated"*; `REQ-0023:68`; `TASK-0069:67`
- `for f in $(grep -rl "^waiver_expires:" docs/); do git log --format="%h %ad" --date=short -S"waiver_expires" -- "$f" | tail -1; done | sort | uniq -c` → `19  18e8f81 2026-07-26`
- Recounts reproduced independently: 19 `waiver_expires: 2026-10-23`, 19 `VERIFY-WAIVED`, and 40 tasks + 7 issues + 5 features = 52 terminal items with neither test nor waiver, so 52 + 19 = 71
- `git log --diff-filter=A` → ADR-0017, ISS-0017 and ISS-0019 all added in `44dbd48`, so *"filed in the same batch that named the rule"* holds

Noted, not a defect of this change: `SCHEMAS.md` declares `reviewed_by`/`review_date`/`review_verdict` only under `change.md` and `test.md`, and `review_note` under no type, while `ADR-0006` and `ADR-0017` both carry them. Pre-existing, and adjacent to ISS-0022's last bullet about `REVIEW_SETTLED_STATUSES` not covering `decisions`.

## Next Actions

- [ ] Rewrite the third question in `ADR-0017`'s first consequence so it matches the amended clause 3, and add or fold in the gate-reads-nothing case.
- [ ] Update the two verbatim quotations of the old clause 3 (`ISS-0019:81`, `Intake-Quality-Without-Reading-2026-07-29.md:51`), and apply the proposal-register correction to the reference note's ADR-0014 sentences.
- [ ] Drop the second clause of the observability row's `monitoring` sentence, or correct it to name the cockpit literal and the two instruction files.
- [ ] Correct ISS-0021 and the reference note to attribute the waiver dating to FEAT-0016 / TASK-0068 / REQ-0023's amendment, with FEAT-0017 / TASK-0069 as the promotion record.
- [ ] Restate ISS-0021's title and line 48 so the finding is the uniform migration date and the absent renewal forcing-function, not months of drift — the commit is three days old.
- [ ] Re-review once applied. Two rounds have now each found the fix for the previous round's finding introducing a fresh one of the same class, which is itself worth a note on the review loop rather than a third round of the same shape.
