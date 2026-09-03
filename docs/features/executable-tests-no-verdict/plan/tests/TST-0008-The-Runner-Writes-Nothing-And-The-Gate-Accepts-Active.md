---
type: "[[test]]"
id: TST-0008
aliases: ["TST-0008"]
title: "The runner writes nothing, and the gate accepts an executable test at active"
status: active
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]", "[[TASK-0107]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-verdict-model.sh"
command: "bash ../project-os/tools/scripts/test-verdict-model.sh"
requirements: []
features: ["[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"]
issues: ["[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
tasks: ["[[TASK-0106]]", "[[TASK-0107]]", "[[TASK-0109]]"]
artifacts: []
adequacy: "Round 2, 2026-09-03, harness at template 293e5a2 (18 assertions): (A) the gate skip for a command: test removed, 3 failures; (B) the COMMAND-VERDICT cutover moved to the past, 2; (C) the runner made to append a line to every note, 2; (D) the review mutant, a runner that writes only on a passing outcome, 1 (the passing-fixture byte-identity assertion added for it); (E) the review mutant, a skip keyed on the command key existing, 1 (the empty-command fixture added for it); (F) the CI unrunnable rule removed, 1. Each mutation confirmed landed and reverted by copying the saved file back; pristine tree 18 of 18. Round 1 had 11 assertions and recorded A as 2 failures; the twelfth assertion (b5e8f9f) made it 3."
reviewed_by: model:claude-fable-5-1
review_date: 2026-09-03
review_verdict: changes-requested
related: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
---

# The runner writes nothing, and the gate accepts an executable test at active

## Purpose

[[ADR-0025-An-Executable-Test-Records-No-Verdict|ADR-0025]] makes two claims a harness can settle: `run-tests.py` leaves every note byte-identical, and the verification gate treats a `command:` test at `active` as settled while warning on one that still carries a verdict. This note executes both against fixture repos.

## Procedure

`tools/scripts/test-verdict-model.sh` in `~/Dev/repos/project-os`, fixture repos under a tempdir, 18 assertions after the review round:

1. A done task linked to a `command:` test at `active`: the validator passes and no VERIFY error names the test (1, 2); the same at `level: acceptance` owes no mark (3).
2. The same test at `passing` with `last_run:`: COMMAND-VERDICT as a warning, not an error, exit 0 (4 to 6).
3. A manual test (no `command:`) at `ready` under a done task still fails the gate (7, 8); so does one with the template's default `command: ""` (9); a manual test at `passing` with a fresh `last_verified:` passes and a stale one fails (10, 11).
4. `run-tests.py`: exit 1 when a command fails, the failing note byte-identical, `--write` rejected, exit 0 when every command passes, the passing note byte-identical too (12 to 16); with `CI` set an unrunnable command fails the run, locally it is an environment gap (17, 18).

## Expected results

- Exit 0: every assertion holds. First real run 2026-09-03 at template commit a8694f0, 11 of 11; 18 of 18 at 293e5a2 after the review round. CI runs it on every push through run-tests.py once this repo's workflow checks the template out beside it, which the review found it did not (a cross-repo command that cannot run exited 0 as an environment gap; in CI it now fails the run).

## Adequacy (who verifies this test?)

**Round 2, after the first review (template at `293e5a2`, 18 assertions).** The review found two mutants the first eleven let through and re-ran the inversions with different counts; each mutation below names its text, was confirmed to have landed, and was reverted by copying the saved file back:

- (A) the gate's skip for a `command:` test removed: 3 failures (round 1 recorded 2 against 11 assertions; the twelfth, added in `b5e8f9f` for the acceptance-level case, makes it 3).
- (B) the COMMAND-VERDICT cutover set to 2026-01-01: 2 failures.
- (C) the runner made to append a line to every note it ran: 2 failures (both byte-identity assertions).
- (D) the review's mutant, a runner that appends `status: passing` only on a passing outcome: 1 failure, the passing-fixture byte-identity assertion written for it; it passed 12 of 12 before.
- (E) the review's mutant, the gate skip keyed on the `command` key existing rather than holding a value: 1 failure, the empty-command fixture written for it; it passed 12 of 12 before.
- (F) the CI rule removed from the runner: 1 failure.

The pristine tree passes 18 of 18.

**Round 1** (template at `a8694f0`, 11 assertions): A 2 failures, B 2, C 1; pristine 11 of 11.

## Independent review

Reviewed 2026-09-03 by `model:claude-fable-5-1` in a fresh session from the notes and the template diffs (`a8694f0`, `3d67f11`, `87b64cf`, `edafa94`, and `b5e8f9f`, which landed while the review ran). Verdict: **changes-requested**. Every finding is labelled reproduced (a command run, with what it printed) or not reproduced.

**Reproduced.**

1. The record on this note is behind the harness. `bash ../project-os/tools/scripts/test-verdict-model.sh` prints `12 assertions, 0 failure(s)`; the adequacy field and Expected results say 11 of 11 at `a8694f0`. The 12th assertion came with template `b5e8f9f`, which fixed a defect in `a8694f0` that the original 11 did not pin: an acceptance-level `command:` test at `active` drew VERIFY-ACCEPTANCE because the gate reached the level check before the ADR-0025 skip (project-os-dev showed twelve on sync). This note is itself `level: acceptance` with a `command:`. FEAT-0028's acceptance cites "assertions 1 to 5" and "8 to 11", which are now 1 to 6 and 9 to 12; TASK-0107 says 11 assertions and names only `a8694f0`; the change note's `commit:` omits `b5e8f9f`.
2. Inversion 1 re-run (gate skip removed, mutation confirmed with a string check, restored by copying the saved file back): 3 failures, not the 2 recorded. Inversion 2 (cutover set to 2026-01-01): 2 failures, as recorded. Inversion 3 (runner appends a line to every note): 1 failure, as recorded.
3. Two mutants survive. A runner that appends `status: passing` only when the outcome is passing: 12 of 12 pass, because byte-identity is compared only on the fixture whose command is `false`; the Procedure says "one passing and one failing command: the notes are byte-identical" and the harness checks half of that. A gate skip keyed on the presence of the `command` key rather than a non-empty value (`"command" in fm` for `has_value(...)`): 12 of 12 pass, because no fixture carries the template's default `command: ""`; the manual fixture omits the key.
4. "CI runs it on every push through run-tests.py" (Expected results) does not hold for this repo. `bash /nonexistent/x.sh; echo $?` prints 127; the runner treats 127 as unrunnable, prints `note: an unrunnable test is an environment gap, not a failure` and exits 0 (fixture with `command: "bash ../nonexistent/x.sh"`: `runner exit=0`). In GitHub Actions `../project-os` is not checked out, and TST-0004 to TST-0008, five of this repo's eight `command:` tests, run `../project-os/tools/scripts/...`. A timeout is also unrunnable (`sleep 3` with `--timeout 1`: `runner exit=0`). So for this repo CI is green whatever these five tests would say.
5. Nothing pins that a manual test at `passing` with a fresh `last_verified:` still passes the gate, or that a stale one still fails. Both hold today (fixtures: `validate-docs: OK` at exit 0 for `last_verified: "2026-09-01"`; `ERROR [VERIFY] ... passing yet stale` at exit 1 for `2025-01-01`), but the harness only checks `ready`.
6. The fleet count in the PROMOTIONS comment and on TASK-0107 does not hold. At project-os-dev `c5cfbbc` (before the strip) the template validator reports 4 COMMAND-VERDICT lines (TST-0001 to TST-0004 at passing with last_run and exit_code), not 7; TST-0005 to TST-0007 were `draft` with `last_run: ""`, which the check ignores. project-os-cockpit reports 0 at HEAD and at every one of the last six commits, not 1. By status the fleet had 29 (4, 19, 4, 2, 0), not 33; `ready` is 2 (both your-health), not 5. By the check's own criterion, which also fires on a bare `exit_code:`, today's trees draw 98 warnings: your-health 21, your-sudoku 4, your-trainer 69 (67 of them `active` with `exit_code:` only), project-os-dev at `c5cfbbc` 4.
7. The template still describes the runner writing. `docs/__templates__/test.md:13`: `command: ""  # runnable check; when set, status is written by the runner, never by hand (ADR-0010)`, three lines above a callout saying the opposite. `tools/scripts/validate-docs.py:2262` (ACCEPTANCE-STATUS message): "A command: exempts passing/failing (the runner writes those)", and the exemption logic on line 2253 still exempts them. `docs/tests/README.md:30` lists `last_run` as what the LLM updates on the test note; `docs/__bases__/CONTEXT.base:29,99` keep a `last_run` column. The last two are not in the change note's impacts.
8. The change note's impacts list names `.claude/skills/release-verification/SKILL.md` and `.claude/skills/test-authoring/SKILL.md`; `git log a8694f0^..HEAD -- <those two>` is empty. They are generated pointers to the canonical skill and did not change.
9. A done task can sit over a genuinely failing executable test: fixture with `command: "false"` under a done task prints `validate-docs: OK` (exit 0) and the runner prints `TST-0001 failing`, exit 1. Neither repo's pre-commit runs the runner (`grep run-tests tools/scripts/*.sh` finds only the harness), so the failure surfaces only where CI runs `run-tests.py` and the command is runnable there; see finding 4. A hand-written `status: failing` on a `command:` test under a done task is a COMMAND-VERDICT warning, exit 0, where ADR-0010 made it a VERIFY error.

**Not reproduced (leads).** ISS-0046's Expected section still states the runner-stamps model it was filed under; the vendored cockpit's `cockpit.py:1574` says "the runner stamps it" (the change note defers only the bundled validator); ADR-0025's frontmatter carries `alternatives: []` and `consequences: []` while the body lists both.

**Independence.** Fresh session, no memory of authoring any of this, started from the notes and diffs; same model family as the author (`Claude-Session` on the template commits is the authoring session; this review is a different one). The tree moved during the review: `b5e8f9f`, and project-os-dev commits `a66dab7`, `5e8cd65`, `6d5e18a`, landed after the first reads, and the findings are against the state after them.
