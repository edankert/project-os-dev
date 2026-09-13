---
type: "[[feature]]"
id: FEAT-0029
aliases: ["FEAT-0029"]
title: "The walk sheet: a generated procedure over the owed acceptance checks, in an order authored once"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "Edwin, 2026-09-13, asking for the thing on top of the tests that says what to do in what order"]
goal: "Hand the person walking a release one generated sheet: the surfaces the release changed first, then every owed check in the project's authored sitting order with its setup, steps and expected result inline, so nobody writes a run plan by hand and the sheet can never disagree with the gate."
requirements: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]"]
tasks: ["[[TASK-0110-ADR-0027s-Four-Headings-Land-In-The-Test-Template]]", "[[TASK-0111-TESTING-md-States-The-Walk-Once]]", "[[TASK-0112-The-WALK-md-Template]]", "[[TASK-0113-The-Generator-And-Its-Fixture-Test]]", "[[TASK-0114-The-Skills-And-Note-Templates-Hand-Over-The-Sheet]]", "[[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit]]"]
tests: ["[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
release: ""
acceptance_exception: ""
reviewed_by: "model:claude-opus-5"
review_date: 2026-09-13
review_verdict: approved
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[PHASE-0004-The-Walk]]", "[[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]", "[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
---

# The walk sheet

## Goal

A person preparing a release gets one generated document that says what to walk, in what order, with what on the bench, and what to look at first. Today they get a list of owed checks in id order and write the rest by hand.

To **walk** a check is to execute it by hand. The **walk sheet** is the generated document. A **sitting** is a group of checks that share one setup state and are walked in one go. The **survey** is the sheet's first section, the surfaces the release changed. The **walk order** is `docs/tests/acceptance/WALK.md`, one authored file per project. The rules behind all four are decided in [[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once|ADR-0029]] and will be stated once in TESTING.md by TASK-0111; this note does not restate them.

## Scope

**In scope, all in the template repo `~/Dev/repos/project-os`:**

- ADR-0027's four headings (Setup, Steps, Expect, Not this check) land in `docs/__templates__/test.md`, TESTING.md and the test-authoring skill, because a sheet row prints them ([[TASK-0110-ADR-0027s-Four-Headings-Land-In-The-Test-Template|TASK-0110]]).
- TESTING.md gains "The walk"; SCHEMAS.md and the test template gain the optional `after:` field; the glossary gains the four terms ([[TASK-0111-TESTING-md-States-The-Walk-Once|TASK-0111]]).
- `docs/__templates__/walk.md`, the template for a project's WALK.md, with a syntax the generator can parse ([[TASK-0112-The-WALK-md-Template|TASK-0112]]).
- `tools/scripts/walk-sheet.py` and its fixture test `tools/scripts/test-walk-sheet.sh` ([[TASK-0113-The-Generator-And-Its-Fixture-Test|TASK-0113]]).
- The release-prep, release-verification and close-out skills hand over the sheet instead of a list; the task and change templates offer `## Acceptance checks reopened` ([[TASK-0114-The-Skills-And-Note-Templates-Hand-Over-The-Sheet|TASK-0114]]).
- Sync to the consumers, the cockpit's feature filed, adapters regenerated ([[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit|TASK-0115]]).

**Out of scope, and where it lives instead:**

- The cockpit's walk page, its survey rendering and its bundling of the generator: project-os-cockpit FEAT-0149.
- your-trainer's WALK.md, its Setup lines on the owed checks and the retirement of its hand-written run plan: your-trainer FEAT-0119.
- ADR-0027's validator rule for a check without a Setup heading: ADR-0027's own acceptance thread.
- The validator reading the ledger instead of `mark:`: [[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger|ISS-0060]].

## Acceptance

- Running `python3 tools/scripts/walk-sheet.py --release REL-0017 --platform android` in a consumer repo with a ledger prints a sheet whose rows equal `ledger.owed()` for that platform, opens with the survey, follows WALK.md's sitting order, labels unplaced checks, prints "Setup: not stated" where the heading is missing, and contains no time estimate.
- Running it in a repo without `docs/releases/ledgers/` exits non-zero with a message naming ISS-0059.
- `bash tools/scripts/test-walk-sheet.sh` passes on a fixture ledger and a fixture WALK.md, and is the acceptance check for this feature (a `TST-*` note with that `command:`, allocated by TASK-0113).
- Every criterion of [[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk|REQ-0028]] is ticked with evidence at close-out.

## Risk scan

No `RISK-*` is owed. The feature adds one script with no dependency beyond the Python standard library the other `tools/scripts/*.py` already assume, no environment variable, no new directory (WALK.md sits in the existing `docs/tests/acceptance/`), no long-running step, and no credential. The one hazard is a second implementation of the owed predicate in the cockpit; rule 7 of ADR-0029 removes it by bundling, and the cockpit records the decision on its FEAT-0149.

## Independent review, 2026-09-13 (model:claude-opus-5, clean context)

Verdict `changes-requested`. The reviewer read the notes and the diff, never the authoring conversation, in a separate session on the same model family; `reviewed_by` records that. Judged against `walk-sheet.py` sha1 `8f6be72f`, which is not the version the review opened on — the generator and the harness were edited mid-review and the review was re-baselined and re-run against the current files.

**What held up.** The claim the feature rests on is the one that was checked hardest and survived. `resolve()` here and `ledger.verdicts()` in project-os-cockpit were run independently over your-trainer's live corpus on both platforms: 583 resolved keys each on android, 1 each on ios, empty symmetric difference, zero mark or date differences. The refusal path, the no-WALK.md fallback, the `after:` layering, first-sitting-wins placement, the Unplaced label, `section()` against fenced blocks and repeated headings, and the four skills' links to TESTING.md all behave as the notes say. The eight mutations recorded on TST-0009 all reproduce at the counts recorded.

**What does not.** The reproduced defects are written up on [[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk|REQ-0028]] (four ticked criteria refuted) and on [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]] (12 of 22 further mutations survive the 38-assertion harness, the sealed-ledger layer chief among them). Two more sit at this level:

- **A hand-written WALK.md loses block-style YAML silently.** `_YAML_LIST_RE` reads only the inline form. A sitting written with `surfaces:` on its own line and `- Home` beneath it parses as an empty list; if the same block also carries an inline `checks:`, the sitting still claims something, so no warning fires and the surfaces vanish. `bench:` in block form disappears with no warning in any case, because `claims_nothing` looks only at `surfaces` and `checks` — and the bench list is the thing PHASE-0004 says a sitting exists to carry. Neither `docs/__templates__/walk.md` nor SCHEMAS.md says the lists must be inline; both only show inline examples.
- **`lead_paragraph()` takes the first prose it meets, not the prose under the title.** An `# H1` counts as the title only when nothing non-blank has been collected yet, so a note with an HTML comment before its title yields that comment as the row's Steps and drops the real procedure. The rendered row then says "**Steps: no heading.** The note's own description is below" followed by something a markdown renderer hides — worse than the `_The note states no steps._` it replaced, because the row now claims to carry a procedure. A note whose lead is provenance ("Source: imported from the v2.1.1 plan") prints that as its steps.

**Bookkeeping that does not match what landed.** TASK-0113's fourth Definition-of-Done box is ticked and is false as written: it requires "a `TST-*` note in the template's `docs/tests/`" carrying `command: bash tools/scripts/test-walk-sheet.sh`, and TST-0009 lives in project-os-dev under `docs/features/walk-sheet/plan/tests/` with `command: bash ../project-os/tools/scripts/test-walk-sheet.sh`. The consequence is real rather than clerical: `python3 tools/scripts/run-tests.py` in the template prints "project-os — no TST-* notes declare a `command:`", so the template ships the harness with nothing pointing at it, and a consumer repo receives the same. The note's Evidence section records the actual command without amending the box. TASK-0113's Evidence also still reads "32 assertions, 0 failures. Eight fixture checks", where the harness is now 38 assertions over nine fixture checks. Separately, `tools/scripts/__pycache__/validate-docs.cpython-313.pyc` is a tracked, committed file in project-os-dev and is deleted in this working tree; TASK-0115's evidence describes that deletion as removing a gitignored stray, which is true of the template and not of this repo.

**Round two, 2026-09-13 — `approved`.** Verification only, against `walk-sheet.py` sha1 `80370fcb` and the 72-assertion harness, all four fixture repos. Every round-one finding was re-tested by running it, not by reading the fix.

All seven behavioural findings are fixed. Both feature-level ones verified: a block-style YAML list in WALK.md is now named individually per key — including `bench:`, which previously warned in no case at all, and including the mixed inline/block sitting that previously warned in no case either — while the inline syntax ADR-0029 fixed still parses its surfaces, checks, state and bench unchanged. `lead_paragraph()` now collects nothing before the `# ` heading, so a note with an HTML comment above its title prints the prose under the title rather than the hidden comment. A note whose lead genuinely is provenance still prints that as its steps, which is correct: it is the prose under the title, and the "Steps: no heading" label says so.

The consistency items all hold. TASK-0113's fourth box is `[~]` with a better answer than the box asked for — a note about the template's own harness placed in the template's `docs/tests/` would be seeded into every project derived from it — and the real consequence is filed as ISS-0065. Its Evidence reads 72 assertions. The tracked `.pyc` is restored; `git status --short tools/scripts/__pycache__/` is empty. ISS-0064 and ISS-0065 are both at `triage`, unfixed, which is the severity bar working rather than an omission.

Two things remain open, neither of them a gate. The guarding gap is written up on [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]]: thirteen of the fifteen round-one survivors are now caught, and the two that remain leave the shipped code correct — but one of them, reversing the sealed-before-open ledger order, passes 72 of 72 while costing 35 of your-trainer's 61 owed rows, and `adequacy:` currently reports it as caught. That field needs a correction and the fixture needs one open-ledger invalidation over a sealed pass. Smaller: TST-0009's Procedure line still says "eight acceptance checks" where the first fixture now builds ten.

## Links

- Requirements: [[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]
- Tasks: [[TASK-0110-ADR-0027s-Four-Headings-Land-In-The-Test-Template]], [[TASK-0111-TESTING-md-States-The-Walk-Once]], [[TASK-0112-The-WALK-md-Template]], [[TASK-0113-The-Generator-And-Its-Fixture-Test]], [[TASK-0114-The-Skills-And-Note-Templates-Hand-Over-The-Sheet]], [[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit]]
- Plan: `plan/PLAN.md`
- Repo paths (template): `tools/instructions/TESTING.md`, `docs/__templates__/test.md`, `docs/__templates__/walk.md`, `docs/__templates__/SCHEMAS.md`, `tools/scripts/walk-sheet.py`, `tools/scripts/test-walk-sheet.sh`, `tools/skills/release-prep/SKILL.md`, `tools/skills/release-verification/SKILL.md`, `tools/skills/close-out/SKILL.md`, `tools/skills/test-authoring/SKILL.md`

**After round two, same day.** The approval came with one measured gap in the harness rather than the code, and it was closed rather than filed: the fixture pinned the order of two *sealed* ledgers but not the boundary between sealed and open, so resolving the open ledger first dropped 35 of your-trainer's 61 owed rows in silence. A check passed in a sealed ledger and invalidated in the open one now holds that edge, and the two sealed ledgers were renamed so filename order contradicts seal order. Three sort mutations that survived now fail. The harness is 73 assertions; no generator code changed, so no third round is owed (`QUALITY.md`, "Independent review (clean-context)").
