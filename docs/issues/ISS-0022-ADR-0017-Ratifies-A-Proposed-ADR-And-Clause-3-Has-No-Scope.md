---
type: "[[issue]]"
id: ISS-0022
aliases: ["ISS-0022"]
title: "ADR-0017 is accepted while ratifying ADR-0014, which is only proposed; clause 3 has no stated subject, so read literally it forbids the waiver and manual-test paths the same ADR says it preserves; and a consequence names ISS-0020 for ISS-0019's defect"
status: open
severity: medium
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: docs
source: ["review:2026-07-29-independent-review-ADR-0017"]
phase: "[[PHASE-999-Parking-Lot]]"
parent: ""
related: [ADR-0017, ADR-0014, ADR-0010, ISS-0019, ISS-0020, ISS-0023, REQ-0018]
tests: []
---

# Independent-review findings on ADR-0017

## Problem

Five findings from the clean-context review of [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]] (accepted 2026-07-29). Three block; two are corrections. The ADR's central claim — that ADR-0009, ADR-0010 and ADR-0014 share one rule — survives all of them; what does not survive is the ADR's description of how much of that rule is currently in force, and the definition of the clause it calls load-bearing.

### 1. Blocking — the ADR is `accepted` and ratifies a `proposed` ADR

`ADR-0014` is `status: proposed`, and its implementing feature `FEAT-0020` is `status: backlog` (snapshot note: *"Not yet planned: four open questions"*). ADR-0017 describes it in the present indicative throughout:

- body §Context: *"Three decisions in this repo **implement** the same rule for one field each"*, listing ADR-0014 third
- body line 36: *"a ticked box **carries** a typed evidence token and a revision"* — no ticked box in the fleet carries one
- body line 52: *"`--fix-metrics`, `run-tests.py`, `waiver_expires`, **ADR-0014's revision** and **ISS-0017's fingerprint** are all clause 3 with different plumbing"* — the last two are unbuilt. `grep -rln "fingerprint\|sha256\|content_hash" tools/` returns nothing, which ISS-0017 itself records as its evidence
- frontmatter consequence: *"This ADR **ratifies** ADR-0009, ADR-0010 and ADR-0014 rather than changing them; **no existing behaviour moves**"*

Ratifying a proposal is not a no-op: an accepted ADR that states ADR-0014's substance as settled rule pre-empts ADR-0014's own open decision, and `STATUSES.md` gives an ADR's status to *"human decision"*, not to citation by a later ADR. The slippage is not a uniformly loose register either — line 60 is careful and correct about what is *"already in force in two places (`last_verified:`, `waiver_expires`)"*, which is exactly the distinction the ADR-0014 sentences drop.

The failure mode is the one ADR-0017 exists to name: a claim written wider than the system, read as current by the next agent.

### 2. Blocking — clause 3 has no stated subject, and read literally it contradicts the mechanisms the ADR preserves

Clause 3: *"never written by the party seeking the transition it gates, **in either case**."* "In either case" extends it over clause 2, the unexecutable path. Two live mechanisms then fail it:

- **`verification_waiver` / `waiver_expires`.** Both fields are written by the closing agent — `QUALITY.md` says *"record an explicit `verification_waiver: <reason>` in the note frontmatter"*, and nothing derives the date. All 19 waivers in this repo carry the same author-chosen `waiver_expires: 2026-10-23`, which is what author-written looks like. So listing `waiver_expires` as *"clause 3 with different plumbing"* (line 52) mis-files it: perishability is **clause 2's** mechanism, and clause 2 exists precisely because independent authorship is unavailable there.
- **Manual test status.** `STATUSES.md` "The contract at a glance": *"Author-written only for manual tests, which must carry `last_verified:` and go stale."* If the author is the agent closing the gated item — the normal case — clause 3 is violated by the path ADR-0010 deliberately kept. `QUALITY.md` line 35 (*"a human runs it and reports results; the LLM then updates the test"*) rescues clause 3 for manual tests by reading, but nothing derives or checks that a human ran it, and the normative file says "author-written".

Taken wider still, `STATUSES.md` assigns *"agent, at close-out"* as the writer for 8 of 10 note types. Whether a task's `done` is "a claim about whether the software works" decides whether clause 3 contradicts that whole column, and the ADR does not say. A rule sold as *"the three-question test applied to every future state field"* cannot be applied while its third question has no defined subject: the reader cannot tell whether clause 3 governs the gating evidence only, or the gated status too.

### 3. Blocking — a consequence names the wrong issue

Frontmatter consequence: *"ISS-0017 (review verdicts) and **ISS-0020** (VERIFY blind to absent tests) are both instances"*. ISS-0020 is *"Nothing requires a `TST-*` to carry a `command:`"*; the VERIFY-blind-to-absent-tests defect is [[ISS-0019-Verify-Is-Blind-To-Tests-That-Were-Never-Linked|ISS-0019]], which self-identifies as *"a clause-3 instance under ADR-0017"*. `SNAPSHOT.yaml` `focus.note` from the same commit confirms the intent: *"ADR-0017 classifies ISS-0017 and ISS-0019"*. ADR-0017's `related:` also omits both ISS-0019 and ISS-0020 although both name it, so the only two "instances" the ADR claims to classify are one wrong ID and no link.

The same sentence's tail — *"neither was recognised as one before the rule had a name"* — is contradicted by the notes' own `source:` fields: ISS-0017 came from *"landscape review 2026-07-29: Doorstop item fingerprints"*, ISS-0019 from the intake's finding 7. Both were recognised by external comparison, in the same commit that named the rule.

### 4. Minor — "`monitoring` appears once" is refuted by grep

Non-goals table, observability row: *"`monitoring` appears once, at `STATUSES.md:106`, as a rejected risk status"*, in a sentence whose preceding clause scopes itself *"anywhere"*. Repo-wide it appears in ~20 places, including a **live** literal at `tools/scripts/validate-docs.py:220` and its bundled copy, `SNAPSHOT.md:99`, `risk-mitigation-planning/SKILL.md:30`, ADR-0007, ADR-0008, ISS-0012 and TST-0002. Only the narrow reading ("once *within* `STATUSES.md`") holds. The row's conclusion is unaffected — there is no observability vocabulary, and `monitoring` is a retired risk status — and the quoted rejection reason is faithful. The source reference note states the same row without "appears once", so the overreach entered at the ADR.

### 5. Minor — the rejection of "state it in QUALITY.md" rests on a link that does not exist

Alternative 3: *"rejected on placement only... The ADR states the rule; QUALITY.md and STATUSES.md **link to it**, per REQ-0018."* Neither file references ADR-0017 (`grep -n "ADR-0017" tools/instructions/QUALITY.md tools/instructions/STATUSES.md` → no match), the commit adds no such link, and no task or issue tracks adding one. REQ-0018 is `implemented` on the rule that a norm lives in one file that others reference; an accepted ADR that no normative file points at is invisible from the surface agents actually read — the ISS-0006 shape. The rejection of alternative 3 is sound only once the link exists.

## Expected

An accepted ADR describes the tree as it is: mechanisms in force stated as in force, proposals stated as proposals, cited IDs correct, and a normative clause whose subject is defined well enough to apply.

## Actual

Three of five clause-3 exemplars are unbuilt or mis-filed, one cited issue ID is wrong, one grep-checkable "verified state" cell is false as scoped, and the placement argument's premise is unimplemented.

## Evidence

- `grep -m1 "^status:" docs/decisions/ADR-0014-*.md` → `proposed`; `FEAT-0020` → `backlog`
- `grep -rln "fingerprint\|sha256\|content_hash" tools/` → no matches (exit 1)
- `bash tools/scripts/validate-docs.sh | grep -c VERIFY-WAIVED` → **19**, every one `expires 2026-10-23`
- `grep -n "ADR-0017" tools/instructions/QUALITY.md tools/instructions/STATUSES.md` → no match
- `grep -rni "monitoring"` over `*.md`/`*.py`/`*.yaml` excluding ADR-0017 → ~20 hits across 15 files
- `tools/instructions/STATUSES.md` "The contract at a glance", writer column; `tools/instructions/QUALITY.md:35,45`
- ISS-0019's 52-item measurement independently reproduced: 40 tasks + 7 issues + 5 features = 52

## Next Actions

Ticks below were applied by the **round-two reviewer** (2026-07-29, `model:claude-opus-5[1m]`, fresh session — the verifier, not the author). Each carries what was actually checked. Unticked bullets are either declared follow-up work or not discharged.

- [x] Decide the ADR-0014 question: either accept ADR-0014 first, or reword ADR-0017 to state ADR-0014 as a proposal whose principle this ADR anticipates — and drop the unbuilt items from the clause-3 exemplar list or mark them as intended. — **reword branch taken.** Verified: `ADR-0014` is still `proposed` and `FEAT-0020` still `backlog`; ADR-0017 now says "(still proposed)" in `decision:`, "(proposed) would type evidence" in `context:`, "(**proposed**; FEAT-0020 is unplanned backlog) — would have every ticked box carry…" in the body bullet, and "anticipates ADR-0014, which remains proposed" in the consequence. The exemplar paragraph now splits "In force today" from "Proposed extensions … neither is built"; `grep -rln "fingerprint\|sha256\|content_hash" tools/` still exits 1, so "neither is built" holds. Whether ADR-0014 is *accepted* remains its own open decision, outside ADR-0017.
- [x] Define clause 3's subject: does it govern the gating evidence only, or the gated status? State explicitly that the clause-2 path substitutes labelling-and-expiry *for* independent authorship, or say how the waiver and manual-test paths satisfy clause 3. — **both asks discharged in the body.** New paragraph names the subject ("any recorded value a gate reads") and excludes the gated status, citing `STATUSES.md`'s writer column (verified: "Who writes the status" = "agent, at close-out" for task/issue/feature); the exemplar paragraph states `last_verified:`/`waiver_expires` are "written by the closing agent, compliant because labelled and expiring, not because independently authored". **Caveat:** the definition did not propagate to the frontmatter's three-question test, whose third question still asks who *writes* the field — filed as [[ISS-0023-Three-Question-Test-Contradicts-The-Amended-Clause-3|ISS-0023]] finding 1.
- [x] Correct the consequence to ISS-0019, add ISS-0019/ISS-0020 to `related:`, and drop or support *"neither was recognised as one before the rule had a name"*. — all three done. Verified: the consequence now reads ISS-0019 with the matching defect; `related:` is `[ADR-0009, ADR-0010, ADR-0014, ADR-0016, ISS-0017, ISS-0019, ISS-0020, ISS-0021, ISS-0022]` and every ID resolves to a file; and the replacement clause *"filed in the same batch that named the rule"* is **true** — `git log --diff-filter=A` puts ADR-0017, ISS-0017 and ISS-0019 all in commit `44dbd48`.
- [x] Narrow the observability row's `monitoring` claim to `STATUSES.md`, or drop the count. — count dropped and the claim scoped to the status taxonomy; `STATUSES.md:106` re-checked and is the rejected-risk-status line. **Caveat:** the replacement clause characterising the other occurrences is itself refutable — ISS-0023 finding 3.
- [ ] Add the QUALITY.md / STATUSES.md pointer that alternative 3 claims exists, or restate the alternative in the future tense with a task behind it. — **half done, left open.** The future-tense restatement landed ("are to link to it … that wiring does not exist yet and is tracked on ISS-0022"), and `grep -rn "ADR-0017" tools/` still returns nothing, so the wiring is genuinely absent. No task stands behind it; the restatement points back at this bullet, so the bullet is still the only thing holding it.
- [x] Reconcile `SNAPSHOT.yaml` `focus.note` (*"Two ADRs await a decision — ADR-0016 … and ADR-0017"*) with ADR-0017's `accepted` status. — done. `focus.note` now states ADR-0017 accepted-then-reviewed and scopes the pending decision to ADR-0016 alone; `ADR-0016` verified still `proposed`.
- [x] Separately: correct ISS-0021 and the intake reference note from 15 waivers to 19 (the one-date finding is unaffected; the 52→"nearer 67" arithmetic becomes 71). — numbers corrected and **independently recounted**: 19 `waiver_expires: 2026-10-23` lines in `docs/`, 19 `VERIFY-WAIVED` from `validate-docs.sh`, and the 52-item population reproduced from `SNAPSHOT.yaml` + note frontmatter (40 tasks + 7 issues + 5 features), so 52 + 19 = 71 holds. **Caveat:** the provenance paragraph added alongside the numbers introduced two new defects — ISS-0023 findings 4 and 5.
- [ ] Consider whether `REVIEW_SETTLED_STATUSES` should cover `decisions` — an ADR carrying `review_verdict: changes-requested` is currently invisible to the validator, so this note is the only thing holding the finding. — **still open (expected).** Verified unchanged: `validate-docs.py:192` is `{"tests": ("passing",), "changes": ("merged",)}`. Round two adds a related datum: `SCHEMAS.md` declares `reviewed_by`/`review_date`/`review_verdict` only under `change.md` and `test.md`, and `review_note` under no type at all, while ADR-0006 and ADR-0017 both carry them — so the ADR review surface is undeclared as well as unchecked.
