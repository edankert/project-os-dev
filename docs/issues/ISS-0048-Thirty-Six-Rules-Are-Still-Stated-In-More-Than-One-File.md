---
type: "[[issue]]"
id: ISS-0048
aliases: ["ISS-0048"]
title: "Thirty-six rules are still stated in more than one file"
status: fixed
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-03
updated: "2026-09-04"
component: docs
source: ["The docs-audit drift sweep (dimension 6) run over the template on 2026-09-03 at the close of PHASE-0003, pass 1, in a clean context"]
elated: ["[[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make]]", "[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]], "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[ISS-0006-Status-Transition-Test-Gates-Requirements]]", "[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]", "[[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]]", "[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]", "[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
tasks: []
tests: []
---

# Thirty-six rules are still stated in more than one file

## Problem

The first drift sweep under [[ADR-0024-A-Normative-Rule-Is-Stated-Once|ADR-0024]] found 36 confirmed restatements and 6 borderline pointer-plus-summary cases across the template's instruction files, skills, templates and root files. Fifteen of the 36 disagree with each other, which is the failure the rule exists to stop: an agent reading two of those files is told two different rules. The four fixed today (ISS-0041 to ISS-0043 and the pause rule) were the ones a person had noticed; a full read of the corpus found the rest.

> [!quote] As reported — 2026-09-03 (the drift-sweep agent, clean context)
> Every file in the domain was read (17 instruction files, 25 skills, 19 templates plus SCHEMAS.md, AGENTS.md, CONTEXT.md, PHASES.md, the four adapter docs, the eight hook scripts and three Codex helper scripts, and the generated outputs). Nothing was edited.

Filed at `triage` because several rows need a decision before they can be fixed, not because the defect is unclear: which model the acceptance verdict follows (row 1, the same question as ISS-0046), whether the Codex path requires a change note before every edit (row 17), and which script owns `metrics.counts` (row 11).

## The findings

Paths are relative to the template root. "Home" is the file that should own the rule, as the files themselves declare where they declare it. "Agree" is whether the copies say the same thing.

| # | Rule | Home | Restated at | Agree | Fix |
|---|---|---|---|---|---|
| 1 | Where an acceptance test's verdict lives | `TAXONOMY.md` "Acceptance outcomes" and `SCHEMAS.md` (ledger, ADR-0037) | `STATUSES.md` `[[test]]` twice ("walking one writes `mark:`, `verdict_date:`, `verdict_reason:`"); `TESTING.md` twice; `QUALITY.md` "Independent review" | **No**: three files describe on-note verdict fields the schema says the validator refuses | Decide the model (with ISS-0046); the losing files say only "the verdict is not a status; see TAXONOMY" |
| 2 | An acceptance test rests at `active`; verdict rules, review gate and Run obligation never engage | `STATUSES.md` `[[test]]` | `TESTING.md` twice; `TAXONOMY.md` twice; `QUALITY.md`; `SCHEMAS.md` twice | Yes | Keep STATUSES; the six others become pointers |
| 3 | A test with `command:` records no verdict | `STATUSES.md`, `TESTING.md` (ADR-0038) | `SCHEMAS.md` and `test.md` ("status written by `run-tests.py` from the exit code", ADR-0010); `release-verification/SKILL.md`; `test-authoring/SKILL.md` ("once run, set `status: passing\|failing`") | **No**: the templates and two skills carry the superseded ADR-0010 rule | Same decision as row 1; then the losers link STATUSES |
| 4 | Feature `done`: every task scope-resolved | `STATUSES.md` (`done`/`cancelled`/`superseded`) | `QUALITY.md` and `close-out/SKILL.md` and `SCHEMAS.md` (`done` or `cancelled`); `status-transition`, `snapshot-sync` (with `superseded`); `TRACEABILITY.md` | **No**: three of six omit `superseded` | Others say "scope-resolved (`STATUSES.md`)" |
| 5 | Feature `done`: no requirement with an unresolved criterion | `STATUSES.md` | `QUALITY.md`; `status-transition`; `close-out`; `requirement.md` | Yes | Delete and link |
| 6 | Requirement `implemented` gate (criteria only, REQ-BOXES, REQ-STALE, no `verified`) | `STATUSES.md` | `QUALITY.md`; `close-out` (walk); `status-transition` twice; `test-authoring`; `SCHEMAS.md`; `requirement.md` | Yes | STATUSES owns the gate, close-out owns only the walk procedure, others link |
| 7 | `implements:` names at most one feature | `STATUSES.md` | `close-out` twice; `SCHEMAS.md`; `requirement.md` twice | Yes | Keep STATUSES and the template comment; drop the rest |
| 8 | Issue `fixed` is the single terminal status; gate is tests passing and not stale | `STATUSES.md` | `QUALITY.md`; `LIFECYCLE.md`; `test-authoring`; `snapshot-sync`; `close-out` ("`fixed/closed`") | **No**: close-out still offers `closed`; QUALITY omits "not stale" | Fix close-out; others link |
| 9 | What owes an independent review | `QUALITY.md` (keyed on status; a CHG owes none, ADR-0019) | `LIFECYCLE.md` step 10 and `close-out` ("touched a `TST-*` or `CHG-*`"); `independent-review/SKILL.md` "When to use" (CHG and waiver as triggers); the generated reviewer description ("transitions a requirement to **verified**") | **No**: four sites trigger on CHG; the agent description names a retired status | QUALITY owns; the others say "at the review gates in QUALITY.md" |
| 10 | Snapshot statuses, counters and metrics are derived; never hand-written | `LIFECYCLE.md` / `STATUSES.md` | `status-transition` ("set the item status"); `release-verification`; `phase-planning` ("increment `counters.PHASE`"); `release-prep`; `SNAPSHOT.md` ("keep `counters` up to date"); the planner prompt ("allocate IDs by incrementing `counters`") | **No**: six sites instruct the hand-write the rule forbids | One home; delete the pre-ADR-0009 instructions |
| 11 | Which script recomputes `metrics.counts` | `SNAPSHOT.md` (`validate-docs.py --fix-metrics`) | `LIFECYCLE.md`, `STATUSES.md`, `QUALITY.md`, `HOOKS.md` (`sync-snapshot.py`) | **No**: two scripts named for one job | Decide the owner; state it once |
| 12 | Trust direction when notes and snapshot disagree | `LIFECYCLE.md` (notes are authored) | `AGENTS.md` ("trust `SNAPSHOT.yaml`"); `CONTEXT.md`; `LLM_BRIEF.md` | **No**: AGENTS says the opposite | Rewrite AGENTS; the others link |
| 13 | The deferral procedure and re-adoption | `STATUSES.md` (rule) and `status-transition` (steps), each stating both | `TRACEABILITY.md`; `SNAPSHOT.md`; `QUALITY.md`; `close-out`; `SCHEMAS.md`; `backlog-grooming` (offers `wont-fix`, which exists nowhere) | Mostly; `wont-fix` is a ghost | Each home keeps its half; fix `wont-fix` |
| 14 | Which terminal statuses the verification gate hook gates | `HOOKS.md` HC-003 (`done`, `fixed`, `implemented`, `done`) | `ADAPTER.md` ("done/closed/verified"); `verification-gate.sh` and `.py` regex `(done\|closed\|implemented)` | **No**: the hook never gates `fixed`; `closed` and `verified` are retired | Regex and comments follow HOOKS |
| 15 | Verification waiver semantics | `QUALITY.md` | `HOOKS.md` twice; `ADAPTER.md`; `independent-review` | Yes, except row 9 | Borderline; HC-003 links QUALITY |
| 16 | The document-first exemption list | `HOOKS.md` HC-001 | `document-first-gate.sh` (full list); `tools/agents/check-docs-first.sh` (a different list) | **No**: the Codex script gates `tools/scripts/*` and `CONTEXT.md`; the Claude hook does not | State the list once in HC-001; both scripts cite it |
| 17 | When a `CHG-*` note is created | `LIFECYCLE.md` (at close-out, when behaviour, paths or contracts change) | `AGENTS.md` (before any code edit, every change); `check-docs-first.sh`; `CONTEXT.md` ("every meaningful change"); `change-note/SKILL.md` | **No**: the Codex path requires it before and always | Decide the Codex path's rule; write it once |
| 18 | The change-note template | `docs/__templates__/change.md` | `tools/agents/start-change.sh` (an embedded copy with `status: draft`, no review fields) | **No**: `draft` is not an allowed change status | The script reads the template file |
| 19 | Preflight, document-first and close-out sequence | `LIFECYCLE.md` | `CONTEXT.md`; `AGENTS.md`; `SNAPSHOT.md` "Update rules" | Yes in outline | Borderline; pointers |
| 20 | Phase alignment rules | `LIFECYCLE.md` | `docs/PHASES.md` "Operational Rules for LLMs" (near-verbatim); `SNAPSHOT.md`; `status-transition` | Yes | PHASES.md becomes a link (merge-owned, so downstream copies carry it too) |
| 21 | The risk-scan trigger list | `LIFECYCLE.md` | `risk-scan/SKILL.md` (full list); `HOOKS.md` | Yes | risk-scan step 1 links LIFECYCLE |
| 22 | The ambiguity threshold | `issue-intake` step 1 | `LIFECYCLE.md` "Scope of a change"; the planner prompt | Yes | LIFECYCLE keeps the scope rule and links intake |
| 23 | `--as-committed` before push, `gh run list` after | `LIFECYCLE.md` steps 8 and 9 | `close-out`; the generated close-out skill | Yes | Link |
| 24 | The three enforcement layers | `QUALITY.md` or `HOOKS.md` | `HOOKS.md`; `ADAPTER.md`; `AGENTS.md`; `LIFECYCLE.md` | Yes | Borderline; pick one |
| 25 | The team model holds no session state | `SNAPSHOT.md` | `SNAPSHOT.md` twice more; `HANDOFF.md` | Yes | Collapse |
| 26 | `check` retired, `CHK-*` kept as alias | `TAXONOMY.md` or `SCHEMAS.md` | `STATUSES.md`; `TESTING.md`; `SCHEMAS.md`; `TAXONOMY.md` again | Yes | One home |
| 27 | Section derivation; adding `command:` automates a check | `TESTING.md` | `STATUSES.md`; `TAXONOMY.md` twice; `SCHEMAS.md` three times; `acceptance-tests.md` template; `release-verification`; `release-prep` | Yes | Keep TESTING; the template's Sections and Rules blocks become a pointer |
| 28 | Nothing removes a check | `TESTING.md` | `STATUSES.md`; `SCHEMAS.md`; `acceptance-tests.md` twice | Yes | Delete and link |
| 29 | Release gating | `TESTING.md` | `release-verification` and `release-prep` (pointer, then the bullets again); `acceptance-tests.md` | Yes | Keep the pointer, drop the bullets |
| 30 | The staleness field on manual tests | `STATUSES.md`, `SCHEMAS.md` (`last_verified:`) | `release-verification` three times and `SNAPSHOT.md` (`last_run`); `SCHEMAS.md` and `test.md` keep both | **No**: two field names for one fact | One field (ISS-0046 territory) |
| 31 | The test `kind` field | `TAXONOMY.md`, `SCHEMAS.md` (removed, ADR-0034) | `SNAPSHOT.md` (lists `kind`); `test-authoring` ("add `kind`") | **No** | Remove both |
| 32 | Where test notes live | `LIFECYCLE.md` | `TESTING.md` twice; `test-authoring` twice; `docs/tests/acceptance/` in TESTING and release-prep versus `plan/tests/` in feature-scaffold | Partly: the acceptance location is stated two ways | One storage rule covering acceptance |
| 33 | `ready` is the state a new executable test is created in | `STATUSES.md` | `SCHEMAS.md`; `test.md`; `test-authoring` | Yes | Template callout links STATUSES |
| 34 | A task has exactly one `parent` | `TRACEABILITY.md` | `CONTEXT.md` (no deferred exception); `LIFECYCLE.md`; `SCHEMAS.md` | CONTEXT is stricter | Borderline; CONTEXT links |
| 35 | Verbatim reporter words in the callout | `issue.md` | `issue-intake`; `ad-hoc-intake`; the planner prompt; `HANDOFF.md` | Yes | Borderline; skills keep one clause |
| 36 | The hard-wrap rule | `MARKDOWN.md` | `README.md`; `AGENTS.md`; `CONTEXT.md` | Yes | Borderline; pointers |
| 37 | The HC-008 size bound | `HOOKS.md` | the hook's comment; the harness assertion | Yes | Borderline; the test is the discharge |
| 38 | Phase `done` gates | `STATUSES.md` | `close-out` (loose paraphrase) | Yes | Borderline; link |
| 39 | A plan's status follows its feature | `STATUSES.md` | `close-out` (near-verbatim) | Yes | Delete and link |
| 40 | Landing a rule over an existing corpus | `STATUSES.md` "Grandfathering" | `DECISIONS.md` "Landing a rule" | Yes | DECISIONS links |
| 41 | The retention policy | `SNAPSHOT.md` | `close-out`; `project-init`; pointers elsewhere | Yes | Borderline; link |
| 42 | The requirement approval gate (no `doing` while a requirement is `draft`) | `feature-scaffold` | none; but `STATUSES.md` claims to be the single source for every gate and does not carry this one | n/a | Add a one-line entry to STATUSES that links the skill |

Clean on the same sweep: the allowed status lists (only in STATUSES.md), the DECISION-RULE and DECISION-OPTIONS conventions, the mark vocabulary, the word and length limits, the hook contracts HC-002 and HC-004 to HC-008 against their scripts, the owner formats, test adequacy, `acceptance_exception`, the design conventions, the inbox rules, the sibling search, and every generated output (byte-current with the generator).

## Repro

```bash
cd ~/Dev/repos/project-os
grep -rn "done\` or \`cancelled\`\|done or cancelled" tools/instructions/QUALITY.md tools/skills/close-out/SKILL.md docs/__templates__/SCHEMAS.md   # row 4: three copies without superseded
grep -rn "closed" tools/adapters/claude-code/hooks/verification-gate.py                                                                 # row 14: a retired status in the gate's regex
grep -n "trust" AGENTS.md                                                                                                               # row 12
```

## Expected

Each rule has one home file; every other document links to it. The docs-audit drift dimension finds zero restatements on two consecutive passes.

## Actual

36 confirmed restatements, 15 of them disagreeing, and 6 borderline cases, on the first pass at the close of PHASE-0003.

## Evidence

- The sweep agent's report, 2026-09-03, reproduced in the table above.
- The four instances fixed the same day: ISS-0041, ISS-0042, ISS-0043 (template commits `1b5956e`, `685eef7`, `0049206`) and the pause rule (`bb6eb70`, `79e0332`).

## Next Actions

- [x] Decide rows 1 and 3 with ISS-0046: Edwin, 2026-09-03, no verdict on the note for a `command:` test (ADR-0025); the acceptance verdict follows the newest decision, the ledger (ADR-0037). Fixed in template commits `87b64cf` and `09ae4dc`.
- [x] Decide row 17: Edwin, 2026-09-03, at close-out when behaviour changes; the Codex helper warns instead of failing (`01ac917`).
- [x] Decide row 11: Edwin, 2026-09-03, the sync script owns it and the repair flag stays; SNAPSHOT.md says both (`80a5b5c`).
- [x] Fix the fifteen disagreeing rows first (1, 3, 4, 8, 9, 10, 11, 12, 14, 16, 17, 18, 30, 31, 32), one commit per home file, deleting the copy and linking. Template commits `ab94b0c`, `edec25d`, `80a5b5c`, `01ac917`, `09ae4dc`.
- [x] Then the twenty-one agreeing rows and the borderline six. Same commits; pass 2 (at `5cf6ded`) found 26 rows gone, 10 still restated and 8 new sites, all taken up in `09ae4dc`.
- [ ] Re-run the sweep until two consecutive passes find nothing (docs-audit quiescence rule), and record the passes in a change note. No clean pass currently stands: pass 7 was clean, pass 8 re-read the corpus without the earlier tables and found 21, and passes 9 to 11 found 2, 5 and 25. Pass 11's count is the widest domain any pass has read, not a regression -- it was the first to open the `.base` views, `docs/STYLEGUIDE.md`, `docs/releases/README.md`, `MANIFEST.yaml` and the rule-bearing regions of `validate-docs.py`.
- [ ] Reconsider the RULE-ONCE check when the count reaches zero (ADR-0024, Acceptance).

## Sweep passes

Each pass is a full read of the domain in a clean context, as the docs-audit skill asks; the quiescence rule is two consecutive passes with nothing new.

| Pass | Template at | Found | Result |
|---|---|---|---|
| 1 | `5494c9f` | 36 confirmed restatements, 15 disagreeing, 6 borderline | the table above |
| 2 | `5cf6ded` | 26 rows gone, 10 still restated (2, 10, 11, 13, 20, 27, 28, 32, 33, 40), 3 waiting on a decision (1, 3, 30), 8 new sites (backlog-grooming, HANDOFF.md, LIFECYCLE.md close-out step 2 and its first section, snapshot-sync, close-out, impact-analysis, release-verification's citation, SCHEMAS.md's ledger README), 4 citations to bold labels | taken up in `09ae4dc`, and ADR-0025 settled rows 1, 3 and 30 |
| 3 | `09ae4dc` | 2 confirmed (`test.md` line 13's command: comment; SNAPSHOT.md's Metrics section), 0 dangling citations, 5 borderline judged acceptable | fixed in `c7d7bfd` |
| 4 | `c7d7bfd` | 3 confirmed (the test template's body callout restating the verdict rule; the design rules in both STATUSES.md and TRACEABILITY.md; TESTING.md's `invalidated_by:` note field, which ADR-0037 moved into the ledger), 1 borderline fragment in two skills | fixed in `ae33478` |
| 5 | `ae33478` | 2 confirmed (the surface template's comment restating TAXONOMY.md "kind (surfaces)"; STATUSES.md citing cockpit ADR-0038 where six files cite ADR-0025), 0 dangling citations | fixed in `de6e89b` |
| 6 | `de6e89b` | 2 confirmed (AGENTS.md restating the change template's coverage checklist; design-authoring restating TRACEABILITY.md's revisions rule), 0 dangling citations | fixed in `1afc71e` |
| 7 | `1afc71e` | 0 confirmed, 0 dangling citations; the first clean pass | |
| 8 | `1afc71e` | read fresh without the earlier tables: 21 confirmed (enum values in the test template and SCHEMAS.md, the no-verdict and clean-context rules restated in skills, the close-out steps in QUALITY.md, the edit boundaries in AGENTS.md, the pause clause quoted at two sites, the negative-result convention with no home, and one contradiction in enforcement: HC-003 test-gated requirements), 2 mis-citations | fixed in `277c46d` |
| 9 | `653f9c6` | 2 at the pointer-gloss boundary, both in the Claude Code adapter (the enforcement mechanics beside the QUALITY.md pointer; the definition of independence beside its pointer) | fixed in `bb6f8f7` |
| 10 | `bb6f8f7` | 5 (TESTING.md restating the review-is-the-walk rule; CONTEXT.md the feature links; README.md the project-owned path list; the plan template comment; inbox-triage) | fixed in `19ba330` |
| 11 | `19ba330` | 25 restatements and 10 bad citations, read wider than any pass since 8: the shipped Bases views and five more files still filtering on statuses PHASE-0002 retired; `SYNCING.md` contradicting `MANIFEST.yaml` on sync ownership; `SCHEMAS.md` contradicting itself on `tier` and claiming a refusal no shipped validator makes; `docs/OWNERSHIP.md` restating the rules its instruction file owns; the staleness window and HC-005's trigger list with no home; four index files behind their directories | fixed in `acdcccb`, `7c13209`, `e2bee28`; two decisions split out as [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make|ISS-0049]] and [[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them|ISS-0050]] |
| 12 | `e2bee28` | 25 confirmed and 12 bad citations, almost none of them pass 11's: the sync script derives `goal:` where four documents say it does not; six directory READMEs carry their own trigger lists for change notes, risks and ADRs; `waiver_expires:` and the `fixes:` back-link are enforced and documented nowhere; `docs/designs/` is checked and named in no document; and the HC-003 hook blocks every feature carrying the acceptance check the scaffold skill requires | not yet fixed. The hook bug is [[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule|ISS-0051]]; findings 17 and 21 restate [[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them|ISS-0050]] and [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make|ISS-0049]], filed from pass 11 |

## In flight (handoff, 2026-09-04)

**Why focus is still set.** This issue is not resting; it is blocked on one decision, [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]]. Deciding it says how many more passes run, which is the only thing standing between here and a close. Do not resume sweeping before it is decided -- another pass would answer the question by fait accompli.

**Where this stands.** Pass 12 has returned and is recorded below: 25 findings, four of four spot-checked confirmed real, and almost none of them the same findings as pass 11's. Its fixes are **not** applied -- the pass is recorded, the high-severity hook bug is filed as [[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule|ISS-0051]], and the rest await the decision below.

**The quiescence rule looks unreachable and the evidence is now strong enough to say so.** Twelve passes have run. The per-pass counts are 36, 26, 2, 3, 2, 2, 0, 21, 2, 5, 25, 25. Pass 7 was clean and pass 8 found 21. Pass 11 found 25, every one was fixed, and pass 12 then found 25 more that pass 11 had not raised. A clean-context pass over ~130 files samples a different subset of the defect space each time; it does not converge on it. "Two consecutive passes find nothing" assumes convergence, and this corpus does not converge. Edwin raised exactly this concern on 2026-09-04; the options are in the reply and no decision is recorded yet.

**What pass 11 changed**, all committed: template `acdcccb` (retired statuses out of the shipped Obsidian views and six documents and two hooks), `7c13209` (SYNCING.md, docs/OWNERSHIP.md and SCHEMAS.md stop restating what other files own), `e2bee28` (four bad citations, four stale indexes, and homes for the staleness window and HC-005's trigger list). Synced into project-os-dev as `00b4fd8` with [[CHG-20260904-Views-Stop-Filtering-On-Retired-Statuses]].

**Neither repo is pushed.** project-os is 26 commits ahead of origin, project-os-dev 22. That has been the pattern across this whole issue; a successor should ask before pushing rather than assume.

**Quiescence is further away than the pass numbers suggest.** Pass 7 was clean, but pass 8 re-read the corpus *without* the earlier findings tables and found 21. That is the lesson worth keeping: a pass primed with the previous table confirms the previous table. Passes 9, 10 and 11 found 2, 5 and 25, and pass 11's jump is domain, not regression — it was the first to open the `.base` views, `docs/STYLEGUIDE.md`, `docs/releases/README.md`, `tools/sync/MANIFEST.yaml` and the rule-bearing regions of `validate-docs.py`. Brief each new pass to enumerate with `find` rather than work from a list, and do not hand it this table.

**Paused on a decision, 2026-09-04.** Edwin asked whether the clean-context review is worth what it costs, saying he cannot tell whether the reviewer checks the right things or steers the work wrong, and proposed capping the review cycles and putting a human acceptance test in the loop. The five options are now written up as [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]], `proposed`, with the measurement as its Context and three acceptance criteria for the threads it leaves open. Nothing resumes here until it is decided:

1. Replace the quiescence rule with a bounded budget (run, fix, record, stop) instead of "two consecutive clean passes".
2. Run passes in parallel at one commit and keep what two of three agree on, rather than sequentially after each fix.
3. Require a reproduction command with every finding, and verify before fixing.
4. Put the human checkpoint on decisions owed, not on findings.
5. Convert recurring finding classes into mechanical checks, which reopens the RULE-ONCE question ADR-0024 declined at a count of 36.

Pass 12's remaining findings are unfixed and stay that way until the ADR is decided, because how many rounds to spend on them is exactly what is being decided. The one exception was [[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule|ISS-0051]], too severe to hold: fixed in template `ad61433`.

The measurement behind that reply, kept because it is the argument: the per-pass counts are 36, 26, 2, 3, 2, 2, 0, 21, 2, 5, 25, 25; 17 of 17 spot-checked findings across passes 11 and 12 were real; the recorded independent-review gate stands at 16 approved against 2 changes-requested. The reviewer is accurate and the termination rule is what does not work.

**A retracted finding, 2026-09-04.** An earlier version of this handoff said `close-out-check.sh` keeps no record of whether a handoff was written and therefore blocks every stop, making its own message false. That was wrong, and it is corrected here rather than deleted because a retraction that leaves no trace is how a wrong finding gets re-filed. The hook reads `stop_hook_active` from the payload and exits 0 when it is true (`close-out-check.sh:16-19`), and `test-hooks.sh` asserts exactly that ("the loop guard lets the second stop through"). It blocked twice in that session because each stop followed new work and was a fresh stop, which is the intended behaviour. No defect; nothing to file.

**Done since the pause, 2026-09-04.** Edwin asked for two things and both landed. [[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule|ISS-0051]] is `fixed` (template `ad61433`, synced here): the HC-003 hook gained the validator's two exemptions, HC-003 states them once for both gates to read, a waiver needs an expiry in both, and TST-0007 gained six assertions that fail against the old logic. [[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] is written and `proposed` at option 5, carrying Edwin's concern verbatim and three open acceptance criteria. Recorded as [[CHG-20260904-The-Verification-Gate-Stops-Blocking-Acceptance-Checks]].

**Approaches set aside.**

- *Fixing the two decision rows in pass 11 rather than filing them.* Both change enforcement — [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make|ISS-0049]] would start erroring on unmigrated downstream notes, [[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them|ISS-0050]] on surface notes. Closed as the user's call, not the sweep's.
- *Tightening `Phases (Open)` in `NAVIGATION.base` from `status != "done"` to an explicit list.* It shows `deferred` and `superseded` phases under "Open", which is the same class of defect as the retired filters. Closed as scope: no retired value is involved, so it is not an ADR-0024 instance. Worth a separate issue if it bothers a reader.
- *Hand-merging `docs/__templates__/SCHEMAS.md` in project-os-dev.* Merge-owned and two months behind (`updated: 2026-05-08` against the template's `2026-07-21`), missing `origin`, `acceptance_exception` and the ADR-0032 removal of a feature's `tests` list. Closed as too large to fold into a drift pass; it is a follow-up on the change note.

**Also owed, neither touched:** three `.DS_Store` files are tracked in project-os-dev with no `.gitignore` entry, and `compass_artifact_wf-84fa61ff-...md` has sat at the template repo root since `d3f9a8f` with no frontmatter and no ID, where `LIFECYCLE.md` close-out step 3 puts a research report under `docs/reference/`.

## Residue at close (pass 12, template `e2bee28`)

[[ADR-0026-When-A-Drift-Sweep-Stops|ADR-0026]] closes a sweep on a recorded residue rather than a clean pass, so this is the residue. These are pass 12's confirmed findings that were **not** fixed. They are real; they were verified where marked; nothing here is lost by closing this issue, because this list is the record.

| # | Finding | Where | Status |
|---|---|---|---|
| 1 | `sync-snapshot.py` derives `goal:` (`DERIVED_FIELDS = ("title", "goal")`) while `LIFECYCLE.md:49`, `SNAPSHOT.md:79`, `snapshot-sync` and `close-out` all say the script leaves it alone; `SNAPSHOT.md` contradicts itself between lines 61 and 79 | four documents vs `sync-snapshot.py:97` | **Verified.** Open — needs a decision on which behaviour is correct before the prose is fixed |
| 2 | `SNAPSHOT.md:67,73` still tells authors to write a feature's `tests:` and a test's `features:`, both removed by ADR-0032 in favour of `covers:` | `SNAPSHOT.md` vs `SCHEMAS.md:90` | Open |
| 3 | `docs/requirements/README.md:23` says `implements:` may point at features, scripts, tests or workflows; `STATUSES.md:93` says at most one feature, and REQ-OWNER errors on two | `requirements/README.md` | Open |
| 4 | Six directory READMEs (`changes/`, `risks/`, `decisions/`, `tests/`, `features/`, `phases/`) carry their own trigger lists for change notes, risk scans and ADRs, two of them turning a mandatory rule discretionary | `docs/*/README.md` | Open. ADR-0026 decided this class stays the sweep's job; a check cannot read for meaning |
| 5 | `waiver_expires:`, `fixes:` and `docs/designs/` are enforced and defined in no document | `validate-docs.py` | `waiver_expires:` **fixed** 2026-09-04 with ISS-0051; the other two are [[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks\|ISS-0052]] check 1 |
| 6 | `metrics.counts` computes 18 keys and `SNAPSHOT.md` defines 16 | `SNAPSHOT.md:91` | Open |
| 7 | `SNAPSHOT.md:20` lists required top-level keys and omits `template:`, which two hooks branch on, plus `docs_system:` and two `retention.*` keys | `SNAPSHOT.md` | Open |
| 8 | `CONTEXT.md:33` files `docs/requirements/` and `docs/risks/` under "LLM should not change casually" while LIFECYCLE requires the agent to create and update exactly those; it omits five more directories | `CONTEXT.md` | Open |
| 9 | `validate-docs.py` error text tells authors to write `mark:`, `verdict_date:` and `invalidated_by:`, the fields ADR-0037 removed | `validate-docs.py:2262,2304` | Open, and adjacent to [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make\|ISS-0049]] |
| 10 | ~22 unresolvable or wrong citations, including a quoted STATUSES.md sentence that appears in no file, and ~50 bare `ADR-####` references that mean a different decision in each repo | corpus-wide | [[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks\|ISS-0052]] check 2 |
| 11 | Index files behind their directories: `docs/INDEX.md` omits `OBSIDIAN.md` and `TESTING.md`; `SNAPSHOT.yaml`'s `docs_system.instructions` lists 3 of 16 | `docs/INDEX.md`, `SNAPSHOT.yaml` | [[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks\|ISS-0052]] check 3 |
| 12 | `SCHEMAS.md` defines no fields for `design.md`, `design-system.md` or `surface.md`, three shipped templates; no `SUR` counter exists though `SUR` is a live prefix | `SCHEMAS.md`, `SNAPSHOT.yaml` | Open |
| 13 | The Bases "Open" views use three different exclusion strategies, `implemented` appears in an "All (Open)" view, and `deferred` (which `SNAPSHOT.md` calls active) appears in none | `docs/__bases__/` | Open. Considered and set aside in pass 11 as out of scope; `BASE-STATUS` now covers only the non-existent-value half |
| 14 | `compass_artifact_wf-84fa61ff-...md` sits at the template root with no frontmatter, no type and no ID, and is the source of claims quoted inside the instruction files — including the quiescence rule ADR-0026 has now removed | template repo root | Open |

Rows 1, 3, 6, 7, 8 and 12 are the ones a person should look at next: each is a document telling a reader something the code does not do.

## Sibling search

Siblings found: [[ISS-0006-Status-Transition-Test-Gates-Requirements]], [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]], [[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]], [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]. Searched `docs/issues/` for: restate, drift, stated once, contradict. The family already has its rule, [[ADR-0024-A-Normative-Rule-Is-Stated-Once]]; this issue is the measured debt under it.

## Risk scan

No new risks: prose and two hook scripts, already covered by TST-0007's shape of test. The fixes touch merge-owned files (`docs/PHASES.md`, `SCHEMAS.md`) that downstream repos keep their own copies of; the sync reports them and does not overwrite, so each repo hand-merges those two.

## Decision record

> [!note] Accept — 2026-09-03 (user:edwin)
> Ask me for each of these decisions in plain language.

> [!note] Decide — 2026-09-03 (user:edwin)
> Rows 1, 3 and 30, asked in plain language: "No verdict on the note" (ADR-0025). Row 17: "At close-out, when behaviour changes". Row 11: "sync script owns it, keep the repair flag".
