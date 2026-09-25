---
type: "[[feature]]"
id: FEAT-0033
aliases: ["FEAT-0033"]
title: "A release walk keeps the actions needed to reach each owed observation"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-16
updated: 2026-09-24
source: ["Your Trainer FEAT-0122, 2026-09-16: implement and test the guided walk fully"]
goal: "A procedure can name required preparation, relevant setup and platform instructions, and the generator retains them without changing the owed check set."
requirements: ["[[REQ-0031-Preparation-Is-Declared-And-Validated]]"]
tasks: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
tests: ["[[TST-0023]]", "[[TST-0011]]"]
acceptance_exception: "The generator has no screen of its own. Its output is walked in Your Trainer, where a person walking it is FEAT-0122's D4; here it is checked by TST-0023 and TST-0011 and by the REL-0017 sheets read on 2026-09-24."
reviewed_by: ["model:claude-opus-5-5", "model:claude-opus-5-5", "model:claude-opus-5-5"]
review_date: 2026-09-24
review_round: 2
review_verdict: approved
related: ["[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]"]
---

# A release walk keeps the actions needed to reach each owed observation

## Goal

The shared walk generator must give a rider the actions needed to reach every owed observation. A prerequisite action remains in the sequence even when the check originally attached to it already passed. It carries no new verdict.

The validator must also reject malformed backticked check tags. A valid tag beside an invalid one must not make the procedure appear complete while an observation is ignored. A rejected procedure keeps the per-check fallback visible.

An authored state reminder must continue until another declaration changes it. This lets a later retained step name the tier, ride or equipment state to restore after an interruption, without guessing from omitted actions.

An unscripted check can also name a platform-specific preparation or scope decision in its own frontmatter. The generator prints the reason on that platform's fallback row without dropping the owed check or inferring a reason from prose.

## Scope

- Add authored links from a procedure step to the earlier steps needed to perform it.
- Attach setup entries to the steps that need them, with platform variants and state transitions declared at the source.
- Validate missing or cyclic prerequisites, contradictory state and invalid platform coverage.
- Keep the owed set unchanged while the sheet and cockpit receive the same prepared sequence.
- Fix child-screen placement when only a child is named by a change note.

The generator does not infer an order from prose. Existing procedures without new fields keep their current valid behavior until their authors annotate them.

## Acceptance

- [x] A later owed FREE-rides step retains its authored workout start and finish prerequisites when those earlier checks are settled — evidence: Your Trainer FEAT-0122, "Implementation evidence, 2026-09-16" (A1): the FREE sitting printed four actions for its two owed observations. Re-checked 2026-09-24 on the REL-0017 Android sheet: Sitting 5 keeps step 1 (start Sweet Spot Base) and step 3 (ride to the programmed end) as preparation around the owed summary step; TST-0023 `test_transitive_actions_and_only_their_setup_survive`
- [x] The final language sweep shows no AI key, translation fixture, email account or hosted redirect setup solely used by omitted steps — evidence: FEAT-0122 (A2), 2026-09-16. Re-checked 2026-09-24: Sitting 13's printed setup has none of them, while the procedure declares them for left-out steps; TST-0023 `test_setup_for_an_omitted_step_is_left_out`, which a mutation printing all setup now fails
- [x] The validator reports missing and cyclic prerequisites without silently dropping an owed observation — evidence: TST-0023 `test_broken_declarations_are_refused` (an absent step and a cycle are reported, and the sheet still prints the owed TST-1002 row); mutation M4 fails it
- [x] A preparation action has no owed verdict tags and the sheet and cockpit agree on the resulting owed set — evidence: TST-0023 (a settled expectation in a kept preparation step does not print and records no verdict); FEAT-0122 (A4, B2), 2026-09-16, including Android preparation steps producing no verdict on copied ledgers; the cockpit's `test_walk_agreement.py` among its 81 walk tests passing on 2026-09-24 against the synced generator
- [x] A changed child screen is displayed under its top-level screen even when that screen has no change note — evidence: TST-0023 `test_changed_child_stays_under_its_unchanged_parent`. Amended 2026-09-25 from "under its actual parent … even when the parent has no change note", on Edwin's decision: reviewer A showed that a screen three levels deep prints under its top screen, not its direct parent. That is rule 2's design (`top_screen`, which predates this feature): the survey lists places to open, and the top-level screen is where a walker opens a nested one. Rule 2's wording was clarified to match.
- [x] A fallback check's declared readiness appears only on its named platform, and malformed declarations fail validation.

## Current browser finding

The shared generator now corrects the action heading seen in a Chrome render of Your Trainer's walk. A known `SUR-*` id shows its screen title while retaining the id for linking. An unknown id stays visible.

The shared generator now accepts `walk_readiness_for` on unscripted acceptance checks. It validates platform entries and prints the matching reason before fallback instructions. A malformed declaration prints a decision warning instead of a ready row. Twelve focused preparation tests and the shared sheet test pass; the generator is synced to Your Trainer and both cockpit copies. [[CHG-20260917-Declare-readiness-for-unscripted-walk-checks]] records the change. The broader readiness and corpus audits remain open.

## Verification

2026-09-24, template working tree: `test-walk-preparation.py` 16 of 16 (TST-0023), `test-walk-sheet.sh` 157 of 157 (TST-0011), every other template harness passing, `validate-docs.sh` OK. Synced to project-os-dev, project-os-cockpit (81 walk tests pass) and your-trainer (`--check` passes on both platforms). Your Trainer's own `test-walk-corpus.py` fails 12 of 57 with or without this change; see TASK-0125.

## Review

**Round 1, 2026-09-24. Verdict: `changes-requested`.** Two `independent-reviewer` subagents on one packet, each in a clean context (`model:claude-opus-5-5` both, by their own report). The packet covered template commit `c71dbb7` and the uncommitted 2026-09-24 change. No behaviour claim was refuted: each reviewer ran the generator directly and found it doing what the criteria say. What they refuted was test evidence: three guards could be removed with every test still passing.

| Claim | Combined verdict | Evidence, and what was done |
|---|---|---|
| Criteria 1 to 5 | holds as behaviour | Both regenerated the REL-0017 Android sheet and read Sittings 5 and 13; broke the preparation-print, setup-filter and survey-parent guards and saw tests fail; ran the cockpit's agreement tests (81 walk tests pass) |
| Criterion 6, malformed declarations fail validation | holds as behaviour, **refuted as tested** | Removing `problems.extend(check.readiness_problems)` in `check_repo` failed no test (both). A misspelt platform in a check's `walk_readiness_for` was accepted (both). **Fixed:** `load_checks` now rejects a platform with no ledger; three new `test-walk-sheet.sh` assertions run `--check` against a malformed and a misspelt declaration |
| REQ-0031 criterion 1 and TST-0023 step 1, prerequisites followed transitively | **refuted as tested** | Stopping the closure after one hop failed no test, because the fixture's `4: [2, 1]` names step 1 directly (both). **Fixed:** `test_prerequisites_are_followed_through_a_chain` declares `2: [1]` and `4: [2]` |
| Scope item 3, a later step refused as a prerequisite | **refuted as tested** | Disabling the check failed no test (B). **Fixed:** `test_a_later_step_cannot_be_a_prerequisite` |
| TST-0011 guards this feature | refuted for the new behaviour | It guards only wording and headings for this feature (both). TST-0023 is the feature's test; TST-0011 stays linked for the output shape it does check |
| Author claims: corpus clean, copies identical, your-trainer's 12 failures predate the sync | holds | Both ran `--check` on both platforms; `shasum` of all six generator copies matched; A reproduced the same 12 failures on the old generator |

**Other observations, and what was done:**

- The "numbers its steps" remark listed every step but counted only those on the platform (A): fixed.
- A check's readiness problem printed once per platform (A): now printed once, with an assertion.
- `duplicate_declarations` found the frontmatter by splitting on any `---` (A): it now stops at the closing delimiter line; `test_frontmatter_ends_at_its_own_delimiter`.
- The sheet numbers kept steps 1, 2, 3 and shows "(source step N)", while procedure prose still refers to source numbers: Sitting 13's setup says "For step 21", and that step prints as step 3 (A). Rule 9 does say "Display positions are consecutive; source positions remain visible". Whether prose references should read naturally is a design question, and it is put to Edwin, not fixed here.
- A screen three levels deep prints under its top screen, not under its direct parent (A). That follows rule 2 and `top_screen`, which predate this feature. Criterion 5's word "actual" is wider than the design, and that question also goes to Edwin.
- In Your Trainer's FREE-rides procedure, preparation step 1 still tells the walker to read the heart-rate metric (B). This is Your Trainer's authored text, part of its TASK-0960.
- A malformed readiness declaration shows a decision on every platform, and fails only through `--check` (B). Both are the documented fallback behaviour; unchanged.
- The two reviewers broke guards in the same template working tree, and one scratch copy was symlinked into your-trainer: [[ISS-0085-Parallel-Reviewers-Mutate-The-Same-Working-Tree|ISS-0085]]. Every copy of the generator was checked by hash afterwards and was intact.

Every fix has a mutation that fails its new test (recorded on TST-0023). After the fixes: TST-0023 19 of 19, `test-walk-sheet.sh` 160 of 160, your-trainer `--check` 0 problems on both platforms, cockpit walk tests 81 passed, generator re-synced (`d046cda`). Round two goes to one reviewer.

**Round 2, 2026-09-24. Verdict: `approved`.** One reviewer, clean context, working in a real copy of the template with no symlinks (per ISS-0085), never in the template's own tree. Each refuted claim is *fixed*: with each guard broken, a test failed (`check_repo` readiness, 3 failures; readiness platform names, 1; one-hop closure, `test_prerequisites_are_followed_through_a_chain`; later-step prerequisite, `test_a_later_step_cannot_be_a_prerequisite`; frontmatter split, `test_frontmatter_ends_at_its_own_delimiter`; duplicate prints, 1). One gap: the numbering remark was fixed in behaviour but no test held it, so "every fix has a mutation that fails its new test" was not yet true. Closed the same day: `test_the_numbering_remark_counts_only_this_platforms_steps`, which the old remark code fails in a full copy of the template (1 failure); TST-0023 20 of 20, synced to all three consumers.
