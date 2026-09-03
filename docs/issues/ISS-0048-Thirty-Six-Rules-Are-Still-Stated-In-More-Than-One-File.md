---
type: "[[issue]]"
id: ISS-0048
aliases: ["ISS-0048"]
title: "Thirty-six rules are still stated in more than one file"
status: triage
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: docs
source: ["The docs-audit drift sweep (dimension 6) run over the template on 2026-09-03 at the close of PHASE-0003, pass 1, in a clean context"]
related: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[ISS-0006-Status-Transition-Test-Gates-Requirements]]", "[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]", "[[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]]", "[[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]", "[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
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

- [ ] Decide rows 1 and 3 with ISS-0046: does the acceptance verdict live on the note (`mark:`) or in the release ledger (ADR-0037)? The template says both.
- [ ] Decide row 17: does the Codex path require a change note before every edit, or at close-out when behaviour changes, as LIFECYCLE.md says?
- [ ] Decide row 11: which script owns `metrics.counts`.
- [ ] Fix the fifteen disagreeing rows first (1, 3, 4, 8, 9, 10, 11, 12, 14, 16, 17, 18, 30, 31, 32), one commit per home file, deleting the copy and linking.
- [ ] Then the twenty-one agreeing rows and the borderline six.
- [ ] Re-run the sweep until two consecutive passes find nothing (docs-audit quiescence rule), and record the passes in a change note.
- [ ] Reconsider the RULE-ONCE check when the count reaches zero (ADR-0024, Acceptance).

## Sibling search

Siblings found: [[ISS-0006-Status-Transition-Test-Gates-Requirements]], [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]], [[ISS-0042-Grandfathering-Is-Described-Two-Incompatible-Ways]], [[ISS-0043-Release-Skills-And-Two-Templates-Use-Retired-Vocabulary]]. Searched `docs/issues/` for: restate, drift, stated once, contradict. The family already has its rule, [[ADR-0024-A-Normative-Rule-Is-Stated-Once]]; this issue is the measured debt under it.

## Risk scan

No new risks: prose and two hook scripts, already covered by TST-0007's shape of test. The fixes touch merge-owned files (`docs/PHASES.md`, `SCHEMAS.md`) that downstream repos keep their own copies of; the sync reports them and does not overwrite, so each repo hand-merges those two.
