---
type: "[[test]]"
id: TST-0007
aliases: ["TST-0007"]
title: "The hooks emit what their contracts now say they emit"
status: active
owner: user:edwin
created: 2026-09-03
updated: 2026-09-04
source: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]", "[[TASK-0102]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-hooks.sh"
command: "bash ../project-os/tools/scripts/test-hooks.sh"
requirements: []
features: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"]
issues: ["[[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]", "[[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule]]"]
tasks: ["[[TASK-0102]]", "[[TASK-0103]]", "[[TASK-0104]]"]
artifacts: []
adequacy: "Round 2, 2026-09-03, against the template at f264cb7 (34 assertions after review finding 9): (A) the sentence Send it to the independent-reviewer subagent appended to the terminal arm, 1 failure; (B) the blocked arm padded with PREFLIGHT three times, 2 failures (names a delegation; 909 chars); (C) both focus_value lines in the Stop hook replaced by the old echo-into-jq form, 4 failures (the hook never blocks: assertions 1, 2, 3 and 6); (D) both block reasons mid-flight sentence replaced by If work is ongoing, this is expected, acknowledge to continue, 3 failures; (E) the echo line tripled to HINT HINT HINT, 4 size-bound failures (empty 890, planning 953, doing 1,073, terminal 1,001 chars; review at 539 stays under). Every mutation confirmed landed by diff against the copy and reverted by copying back. Pristine tree 34 of 34. Round 1 recorded counts of 3, 2 and 4 for C, D and E without naming the mutated text; the review could not reproduce them, and the round-2 record names the text."
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
reviewed_by: model:claude-opus-5[1m]
review_date: 2026-09-03
review_verdict: approved

---

# The hooks emit what their contracts now say they emit

## Purpose

Three hooks change behaviour in [[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]] and [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]. All three are shell scripts that read a snapshot and print a message, so all three are directly testable against fixture repos — which is better than the walk an acceptance check would otherwise be.

## Procedure

`tools/scripts/test-hooks.sh` in `~/Dev/repos/project-os`, written by [[TASK-0102]]. Fixture snapshots under a tempdir, never this repo; each hook is run with `CLAUDE_PROJECT_DIR` pointing at the fixture and its JSON on stdin. Cross-repo command for the same reason [[TST-0004]]'s is. 34 assertions after the first review round:

1. **Stop hook, work complete** (assertions 1, 2, 6): focus set, the block reason names setting the status to done (or fixed, for an issue) and clearing focus now.
2. **Stop hook, mid-flight** (3 to 5): the reason names writing the handoff and stopping, "acknowledge" is gone, and with `stop_hook_active: true` the hook prints nothing, so the second stop goes through.
3. **Hint, empty focus** (7 to 9): says nothing is in flight, does not instruct delegation ("delegate preflight", "before coding" absent), and still says every change gets its note written before the code.
4. **Hint, planning state** (10 to 13): names the item, its status and its phase; recommends the planner for a multi-item scaffold or an ambiguous ask; says the delegation carries the prompt verbatim and what the result enables; says the lead keeps reading the code.
5. **Hint, review state** (14): names the `independent-reviewer`. **Blocked, deferred and terminal states** (15 to 17): say what their arm says (the blocker, re-adopt first, nothing in flight). **The six non-review states** (18 to 23): no review sentence.
6. **Hint size** (24 to 30): all seven states within 3 lines and 600 characters, the bound [[TASK-0103]] set, so the hint cannot grow into the SessionStart slice.
7. **Document-first gate, the four paths in [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]** (31 to 34): a scratchpad path with no repo above it is allowed, a path in a repo with no `SNAPSHOT.yaml` is allowed, a relative path inside the project is denied, an absolute path inside the project is denied.

## Expected results

- Exit 0: every assertion holds. First real run 2026-09-03 against template commit 3e5c1b3, 25 of 25; 34 of 34 at f264cb7 after the review round.
- Exit 1: at least one failed, each printed as `FAIL <name>: <detail>`.

## Adequacy (who verifies this test?)

**Round 2, after the first review (template at `f264cb7`, 34 assertions).** Review finding 9 showed three of the hint's seven arms were unguarded; fixtures for `blocked`, `deferred` and a terminal task now exist and the no-review-sentence and size assertions run over all seven states. Findings 6 to 8 showed the round-1 counts were not reproducible because the mutated text was not named. Each mutation below names its text, was confirmed landed by `diff` against the saved copy, and was reverted by copying the copy back:

- (A) `Send it to the 'independent-reviewer' subagent.` appended to the terminal arm: 1 failure (terminal state, no review sentence). Passed 25 of 25 before finding 9.
- (B) `$PREFLIGHT $PREFLIGHT $PREFLIGHT` appended to the blocked arm: 2 failures (names a delegation; 909 characters). Passed before finding 9.
- (C) both `focus_value` lines in the Stop hook replaced by the old `echo "" | jq -r --arg f ... '$f'` form: 4 failures, assertions 1, 2, 3 and 6, because the hook never blocks on a task or an issue. This is the mutation that found the latent defect: the hook as shipped since January had never blocked on a set focus.
- (D) the mid-flight sentence in both block reasons replaced by `If work is ongoing, this is expected — acknowledge to continue.`: 3 failures (mid-flight, no-acknowledge, issue in focus).
- (E) the echo line changed to `$HINT $HINT $HINT`: 4 size-bound failures at 890, 953, 1,073 and 1,001 characters (empty, planning, doing, terminal); the review-state hint tripled measures 539 and stays under the bound (round 1 wrote 561, three times the pristine length, a number no FAIL line printed).
- Round 1 also reverted the gate fallback to the previous commit: 2 failures, the scratchpad path and the no-snapshot repo path; the review reproduced it exactly.

The pristine tree passes 34 of 34.

## Independent review

Reviewed 2026-09-03 by `model:claude-opus-5[1m]` in a fresh session that started from the notes and the diffs and never saw the author's reasoning. Round 1 verdict: **changes-requested**; round 2 verdict: **approved**, recorded in the frontmatter. The round-1 findings are kept below as the record of what was wrong, followed by the round-2 re-check. The implementation was sound in both rounds; the findings were about what the test guards and what three notes say. Every mutation below was made on a file copied aside first, confirmed to have landed by `diff` against the copy, and reverted by copying the copy back; the template tree ends with no diff against `HEAD` under `tools/adapters/claude-code/hooks/`.

### Reproduced

1. **The Stop hook had never blocked on focus — reproduced.** `git show 80a4a85~1:…/close-out-check.sh` run against a fixture with `focus.task: "TASK-0001"`, `{"stop_hook_active": false}` on stdin and `CLAUDE_PROJECT_DIR` on the fixture prints nothing and exits 0. The current hook prints the `"decision": "block"` JSON on the same fixture. The mechanism is confirmed in isolation: the `grep`/`sed` chain returns `TASK-0001`, and `echo "" | jq -r --arg f TASK-0001 '$f'` returns the empty string, because jq runs the filter once per input value and an empty input has none. This is version-independent, not a quirk of the local jq 1.7.1.
2. **Pristine run — reproduced.** `bash ../project-os/tools/scripts/test-hooks.sh` from the project-os-dev root: 25 assertions, 0 failures, exit 0. Run three times across the session, including after every mutation was reverted.
3. **Inversion 1 (review sentence removed) — reproduced exactly.** 1 failure, `hint, review state: sends verification to the reviewer`.
4. **Inversion 4 (gate fallback reverted to `7b6890f~1`) — reproduced exactly.** 2 failures, the scratchpad path and the no-snapshot repo path.
5. **The four-path table of [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]] is assertions 22 to 25 — reproduced.** The Resolution section's numbering is the correct one.

### Not reproduced

6. **Inversion 3's failure count — not reproduced.** The record says "3 failures, because the Stop hook then never blocks at all". Reverting *both* `FOCUS_TASK` and `FOCUS_ISSUE` to the `echo "" | jq` form gives **4** failures: assertions 1, 2, 3 and also 6, `stop hook, issue in focus`. Reverting only the task line gives 3 failures, but then the hook still blocks on a focused issue, so "never blocks at all" is false. The count and the stated reason cannot both hold. `tools/scripts/test-hooks.sh` has not changed since `80a4a85`, so the harness is not the variable.
7. **Inversion 5's failure count — not reproduced.** The record says "4 size-bound failures at 890 to 1,073 characters". Tripling the emitted hint gives **3** failures, at exactly 890, 953 and 1,073 characters — the same range, so this was very likely the same mutation with the count mis-stated. The fourth size assertion (review state) passes, because the review-state hint is 187 characters and three of it is still under the 600-character bound. That matters beyond arithmetic: this inversion does not exercise the review-state size bound at all.
8. **Inversion 2's failure count — not reproducible from the note.** The record says 2 failures; restoring the pre-`80a4a85` reason string wholesale gives 3 (assertions 2, 3 and 4). The note does not say which text was restored, so the number cannot be checked. Adequacy records should name the mutated text, not only its gist.

### New findings

9. **Three of the hint's seven status branches are guarded by nothing** (severity: the highest here). The fixtures reach the planning arm (`backlog`), the execution arm (`doing`), the review arm and the `*)` wildcard — the "empty focus" fixture resolves no item, so it lands on the wildcard, not on the terminal arm. The `blocked` arm, the `deferred` arm and the whole `done|fixed|declined|cancelled|superseded|implemented|retired` terminal arm are never run. Two mutations demonstrate the hole, each passing **25 of 25**: (a) inserting `Send it to the 'independent-reviewer' subagent.` into the terminal arm, which is exactly the behaviour [[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]'s second acceptance criterion says was removed; (b) padding the `blocked` arm to 1,077 characters over 5 lines, four times the stated bound. Two claims are therefore wider than the test: this note's "**Hint size** (18 to 21): every state within 3 lines and 600 characters" covers four states of seven, and FEAT-0027's "The review sentence appears only in review states — evidence: assertions 14 to 17" is asserted for three non-review states of six. The fix is small: fixtures for `blocked`, `deferred` and a terminal status, each carrying a no-reviewer assertion and a size assertion.
10. **The change note's impacts list names two files that no commit touched.** `docs/changes/CHG-20260903-Hooks-Serve-State.md` lists `.claude/skills/ad-hoc-intake/SKILL.md` and `.claude/skills/issue-intake/SKILL.md`. Neither appears in `80a4a85`, `7b6890f`, `3e5c1b3`, `f6ac538` or `8d35297`; their last change was `2025f32`, an earlier feature. They are not stale either — `python3 tools/scripts/generate-adapters.py --check` reports all 35 artifacts current, because the generated skill bodies stopped carrying the Steps section. The impacts list is what a downstream sync reads, so two of its thirteen entries point at files that need nothing. The other eleven are correct.
11. **`ADAPTER.md` still describes HC-008 the way it behaved before this feature.** The routing table at line 152 and the prose at line 160 were both updated in `3e5c1b3`, but the hook-registration table at line 138 still reads "Advisory: maps the focus item's status to the agent that should do the work (planner / main loop / independent-reviewer)". That mapping is the thing the feature removed, and it now contradicts two other passages in its own file. This is the failure the delivery plan named in advance under "What ADAPTER.md must not be allowed to become".
12. **[[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]] contradicts itself.** Its status is `fixed` and its Resolution section says so, but the "Remaining work" section below still lists the four-line gate change and the HC-001 sentence as work to do, and states "It is assertion 7 of [[TST-0007]]" where the Resolution says assertions 22 to 25. Assertion 7 is a hint assertion. A reader arriving at the bottom of the note is told the fix has not landed.
13. **Minor, close-out state.** `SNAPSHOT.yaml` still has `focus.task: "TASK-0102"` while TASK-0102 is `done` — the condition the Stop hook fixed in this very feature now blocks on. And ISS-0003, reopened and moved to `fixed` today, has no `items.issues` entry, so the snapshot's PHASE-0003 record does not show it; `sync-snapshot.py --report-unregistered` lists it.

### Round 2 — 2026-09-03, against the template at `f264cb7`

**Verdict: approved.** All five round-1 findings are fixed, and each fix was re-checked by running it rather than by reading the claim. The harness is 34 assertions and passes 34 of 34 on a pristine tree; every mutation below was made on a file copied aside first, confirmed landed by `diff`, and reverted by copying the copy back, and the template tree ends with no diff against `HEAD` under `tools/`.

**Finding 9 (the three unguarded arms) — fixed, verified by re-running both round-1 mutations.** Appending `Send it to the 'independent-reviewer' subagent.` to the terminal arm now fails assertion 23, `hint, terminal state: no review sentence` (1 failure; it passed 25 of 25 before). Padding the blocked arm with `$PREFLIGHT` three times now fails two assertions, `hint, blocked state: names the blocker, not a delegation` and the blocked size bound at 909 characters. The no-review-sentence loop runs over six non-review states and the size loop over all seven, so no arm of the case statement is unguarded any more. **Findings 10 and 11 — fixed:** the impacts list is down to eleven entries, and I confirmed each of the eleven is touched by one of the five commits; `ADAPTER.md` line 138 now describes the hint as it behaves, agreeing with lines 152 and 160. Nothing in `tools/`, `AGENTS.md`, `CONTEXT.md`, `.claude/` or `.cursor/` still asserts unconditional delegation — the only remaining `delegate preflight` string is the harness's own negative assertion. **Findings 12 and 13 — fixed:** ISS-0003's "Remaining work" is retitled as the pre-fix plan and its assertion numbers corrected to 31 to 34 in both places; `focus.task` is cleared and ISS-0003 has an `items.issues` entry.

**Findings 6 to 8 (the unreproducible counts) — fixed.** Every mutation in the round-2 adequacy record now names its text, and all five reproduce exactly on re-run: (A) 1 failure; (B) 2 failures at 909 characters; (C) 4 failures on assertions 1, 2, 3 and 6; (D) 3 failures, mid-flight, no-acknowledge and issue-in-focus; (E) 4 size-bound failures at 890, 953, 1,073 and 1,001 characters. That is the whole point of naming the text, and it worked.

**One figure still does not reproduce, and three small things to fix at close-out.** The record's "review at 539 stays under" is wrong: the tripled review-state hint measures **539** characters, on the harness's own review fixture and on an equivalent one. 561 is 187 × 3 — the pristine length multiplied, rather than the output measured. The emitted string carries the `project-os: ` prefix once, not three times, plus two joining spaces, which is the missing 22. The conclusion is unaffected — 539 is under 600, so the review-state size assertion still does not fail under mutation E — and it is telling that this is the one number in the record that no `FAIL` line printed. Also: the change note's `commit:` field still lists five hashes and omits `f264cb7`, which changed `test-hooks.sh` and `ADAPTER.md`, both named in the same note's impacts list; `f264cb7`'s own commit message says "32 assertions" where there are 34; and this note's procedure groups "Blocked, deferred and terminal states (15 to 17)" in an order the harness runs as terminal, blocked, deferred. None of the three changes what the test guards, so none holds the verdict.

### What was independent, and what was not

Independent: a separate session, across both rounds, with no memory of authoring any of this, starting from the notes and the diffs. Every claim above was re-derived by running the hooks and the harness, not by reading the author's account of them. Not independent: the model. This review ran on `claude-opus-5[1m]`, the same family as the authoring model recorded in the template commits (Claude Fable 5.1), which is expected under [[ADR-0013-Independence-Is-Clean-Context]] and is recorded in `reviewed_by` as provenance.
