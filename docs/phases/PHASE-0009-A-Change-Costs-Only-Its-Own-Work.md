---
type: "[[phase]]"
id: PHASE-0009
aliases: ["PHASE-0009"]
title: "A change costs only its own work"
status: active
order: 9
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
goal: "A change costs only its own work: each fact is written once, the checks answer in seconds, and finished notes stay out of the way unless someone asks for them."
features: []
requirements: []
tasks: [TASK-0168, TASK-0169, TASK-0170, TASK-0171, TASK-0172, TASK-0173, TASK-0174, TASK-0175, TASK-0176, TASK-0177, TASK-0178, TASK-0179, TASK-0180, TASK-0181, TASK-0182, TASK-0183, TASK-0184, TASK-0185]
issues: [ISS-0087, ISS-0088, ISS-0089, ISS-0090, ISS-0091, ISS-0092, ISS-0093, ISS-0094, ISS-0095, ISS-0096, ISS-0097, ISS-0098, ISS-0099, ISS-0100, ISS-0101, ISS-0102, ISS-0103]
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[PHASE-0008-Measured-Note-Ranking]]"]
tags: [phase, agent-time, derived-state]
---

# A change costs only its own work

## Goal

A change costs only its own work: each fact is written once, the checks answer in seconds, and finished notes stay out of the way unless someone asks for them.

A your-trainer session on 2026-09-26 answered a user's question with a two-call-site code change and one test, and spent almost all of its time on documentation upkeep: re-parsing thousands of notes on every commit and stop, writing one fact in several places, and reading finished notes to rule them out. ADR-0048 (accepted 2026-09-26) set the rules; this phase carries them out. Opened by Edwin on 2026-09-26 after he accepted ISS-0087 to ISS-0102.

## Scope

In the order it runs:

1. **Baseline first.** [[ISS-0100-Nobody-Has-Measured-Time-Spent-On-Finished-Notes|ISS-0100]]: the share of notes a session opens and edits that are finished, and the hook times, measured before anything changes.
2. **Fast checks**, which everything later reads from. [[ISS-0093-The-Checks-Parse-Every-Note-Several-Times|ISS-0093]] (the note index and parse cache), [[ISS-0089-The-Validator-Said-OK-And-The-Commit-Was-Refused|ISS-0089]] (one final verdict line, `ERROR [WALK]`), [[ISS-0090-The-Stop-Hook-Validates-Without-Syncing-The-Snapshot|ISS-0090]] (the Stop hook syncs before it validates).
3. **Each fact written once.** [[ISS-0095-One-Relationship-Is-Written-In-Six-Places|ISS-0095]] (reverse lists generated), [[ISS-0096-Superseding-Means-Editing-The-Old-Note|ISS-0096]] (supersession written once, back-pointer stamped by a tool), [[ISS-0087-A-Parked-Feature-Gets-A-Full-Scaffold|ISS-0087]] (a parked feature gets only its feature note), [[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It|ISS-0088]] (walks cite the step and show its current text), [[ISS-0098-Notes-Grow-Into-Diaries|ISS-0098]] (notes hold current state), [[ISS-0092-A-Note-Restates-A-Rule-It-Should-Link|ISS-0092]] (link a rule, do not restate it).
4. **Finished notes out of the way.** [[ISS-0097-Nothing-Stops-A-Released-Ticket-Being-Edited|ISS-0097]] (released tickets frozen, editing one warns), [[ISS-0094-A-Rule-Judges-Notes-That-Closed-Before-It-Existed|ISS-0094]] (a rule judges only notes open when it arrived), [[ISS-0091-Finished-Notes-Have-No-Archive|ISS-0091]] (archive after release), [[ISS-0101-A-Search-Returns-Finished-Notes-Mixed-In|ISS-0101]] (search puts live notes first), [[ISS-0102-Shell-Searches-Read-Files-The-Repo-Ignores|ISS-0102]] (rg), [[ISS-0099-Ledger-Field-Warnings-Wait-Ninety-Days|ISS-0099]] (one migration for the ledger-field warnings).
5. **Measure again**, with ISS-0100's harness, and record the before and after here.

## Out of Scope

- [[ISS-0085-Parallel-Reviewers-Mutate-The-Same-Working-Tree|ISS-0085]] (reviewers editing one working tree) and [[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose|ISS-0086]] (step numbering, waiting on the cockpit). Related, but not about time spent on old notes.
- Each downstream repo's own migration. The fleet takes the tools by sync; the cockpit and your-trainer take them when their owners choose.

## Exit Criteria

Measured on your-trainer (3,150 notes), the largest repo, against the baseline taken in step 1:

- [x] The pre-commit hook takes under 5 s per commit (54 s on 2026-09-26). 2.2 s on a your-trainer clone with the final template and `derive_lists` on, 2026-09-26.
- [x] The Stop hook takes under 3 s per stop after a write (40 s on 2026-09-26). 2.1 s on the same clone. The first stop after a template update, which re-reads every note, takes 3.1 to 3.4 s.
- [x] Adding a task writes its membership in one place, the task itself (six places on 2026-09-26). With `retention.derive_lists`, which this repo turned on with this phase (TASK-0172, TST-0030).
- [x] The validator reports nothing about a finished note except a structural fault: a link that does not resolve, or frontmatter that does not parse (581 of 1,139 findings were about finished notes on 2026-09-26). Edwin, 2026-09-26: work finished since the last release is not a finished note, and a note released earlier should only draw a finding through a newer note that changes it. TASK-0184 built that. On a your-trainer clone, no finding names a note finished at v2.1.8 except PHASE-014's PHASE-CHILDREN, which is about two items open now; 189 are hidden and counted.
- [x] A feature filed for later produces its feature note only (FEAT-0128 produced a full set of notes over two planner runs). A planner run on a scratch template filed one note in 10 tool calls (TASK-0174).
- [ ] The share of a session's opened and edited notes that are finished falls from ISS-0100's baseline, by an amount stated when the baseline is taken. **Not yet measurable, and left open (Edwin, 2026-09-26: "okay").** The share of opened notes depends on sessions run with the new tools, and none has run in your-trainer yet: its owner syncs the template. What can be measured now: `snapshot-query.py --search` shows no finished note by default (a count stands in for them), against 42% of search results in the baseline. A plain `rg` on an archived your-trainer clone surfaces 36 to 51% finished notes for eight everyday terms, down from 51 to 64%.
- [x] ISS-0087 to ISS-0102 are each fixed or deliberately declined, and the template changes are synced to this repo. All sixteen are fixed; the template is synced as of `8f524e6`.

## Baseline, 2026-09-26

Taken with `tools/scripts/session-cost.py` (TST-0026) before any other PHASE-0009 change, over every Claude Code transcript that touched a note:

| Repo | Sessions | Opened, already finished | Edited, already finished | Surfaced by a search, already finished |
|---|---|---|---|---|
| your-trainer | 36 | 107 of 300 (36%) | 40 of 198 (20%) | 782 of 1,864 (42%) |
| project-os-dev | 13 | 10 of 33 (30%) | 8 of 51 (16%) | 153 of 336 (46%) |

Hook times on your-trainer with the template's scripts at `ca29288`: pre-commit 54.9 s (`sync-snapshot.py --check` 14.9 s, `validate-docs.sh` 39.9 s, `generate-adapters.py --check` 0.1 s); Stop hook 39.9 s.

The target for the finished-note share, stated now as the exit criterion asks: the share of surfaced notes that are finished falls to under 10% in the default search, and the share of opened notes that are finished halves.

## After, 2026-09-26

Every task is done (TASK-0168 to TASK-0183) and every issue fixed. Measured on a clone of your-trainer with the template at `8f524e6`:

| | Before (`ca29288`) | After |
|---|---|---|
| Pre-commit hook | 54.9 s | 2.2 s |
| Stop hook | 39.9 s | 2.1 s warm, 3.1 to 3.4 s the first time after a template update |
| Validator findings | 1,139 | 950, with the archive applied |
| Findings naming a finished note | 327 (29%) | 139 (15%) |
| Notes a default search puts in front of the agent that are finished | 42% (a plain grep) | 0% (`--search` folds them into a count) |
| Notes that may be archived | none | 1,063 (687 tasks, 308 issues, 54 change notes, 14 retired checks) |

The first column counts findings whose first word is a note id, so it reads 327 where the baseline's own count said 581. One exit criterion stays open: the share of opened notes, measurable once sessions use the new tools. The phase stays `active` until then.

## Notes

- **Tasks, 2026-09-26.** One per issue, TASK-0168 to TASK-0183, filed when Edwin set the goal "implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested". ISS-0091 is built to the your-trainer session's recommendation in its `question:`; ISS-0088 as proposed there: a walk step cites the check's step and the sheet shows the check's current text.

- **Order matters.** ISS-0093's index is read by ISS-0090, ISS-0095, ISS-0096 and ISS-0101, so it lands first after the baseline.
- **Decided already** (ADR-0048, Edwin, 2026-09-26): a ticket is frozen once its release is out; a tool writes the supersession back-pointer into the old note; editing a frozen ticket is a warning, not an error.
- **Decided 2026-09-26 (/goal):** ISS-0091 is built as the your-trainer session recommended.
- **Crosses into the cockpit:** ISS-0088's expansion lives in `walk-sheet.py`, so the cockpit's walk page shows a check's current text once its bundled copy is refreshed. ADR-0049 amends ADR-0045's word-for-word rule and keeps a tick a verdict on the check's own words.
