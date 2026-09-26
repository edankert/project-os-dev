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
tasks: []
issues: [ISS-0087, ISS-0088, ISS-0089, ISS-0090, ISS-0091, ISS-0092, ISS-0093, ISS-0094, ISS-0095, ISS-0096, ISS-0097, ISS-0098, ISS-0099, ISS-0100, ISS-0101, ISS-0102]
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

- [ ] The pre-commit hook takes under 5 s per commit (54 s on 2026-09-26).
- [ ] The Stop hook takes under 3 s per stop after a write (40 s on 2026-09-26).
- [ ] Adding a task writes its membership in one place, the task itself (six places on 2026-09-26).
- [ ] The validator reports nothing about a finished note except a structural fault: a link that does not resolve, or frontmatter that does not parse (581 of 1,139 findings were about finished notes on 2026-09-26).
- [ ] A feature filed for later produces its feature note only (FEAT-0128 produced a full set of notes over two planner runs).
- [ ] The share of a session's opened and edited notes that are finished falls from ISS-0100's baseline, by an amount stated when the baseline is taken.
- [ ] ISS-0087 to ISS-0102 are each fixed or deliberately declined, and the template changes are synced to this repo.

## Notes

- **Order matters.** ISS-0093's index is read by ISS-0090, ISS-0095, ISS-0096 and ISS-0101, so it lands first after the baseline.
- **Decided already** (ADR-0048, Edwin, 2026-09-26): a ticket is frozen once its release is out; a tool writes the supersession back-pointer into the old note; editing a frozen ticket is a warning, not an error.
- **Still to decide, before step 4:** ISS-0091's archive design, in its `question:` field: which note types move, and whether the lasting facts move up into the feature at close-out.
- **Crosses into the cockpit:** ISS-0088 needs the cockpit's walk page to render a check's current text, and it changes ADR-0045's word-for-word rule, which exists so that a tick on a procedure step counts as a verdict on the check.
