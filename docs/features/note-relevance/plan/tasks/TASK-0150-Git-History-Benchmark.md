---
type: "[[task]]"
id: TASK-0150
aliases: ["TASK-0150"]
title: "The harness scores a ranker against 86 commits, and prints the caveat with every number"
status: done
phase: "[[PHASE-0008-Measured-Note-Ranking]]"
owner: user:edwin
created: 2026-09-21
updated: 2026-09-21
source: ["[[FEAT-0038-Note-Relevance-Harness]]", "prototype: scratchpad/bench.py, 2026-09-21"]
parent: "[[FEAT-0038-Note-Relevance-Harness]]"
effort: L
due: ""
depends: []
blocks: ["[[TASK-0151-Cold-Start-Baseline]]", "[[TASK-0152-Transcript-Benchmark]]", "[[TASK-0153-Supported-Ranker-Script]]"]
related: ["[[REQ-0032-Ranking-Claims-Measured]]"]
tests: ["[[TST-0021-Caveat-With-Every-Row]]"]
---

# The harness scores a ranker against 86 commits

## What this delivers

`rank-bench.py`: one command that takes a ranker and reports how much of what each commit touched it would have surfaced. The labelled set is built from the repo's own git history — commits touching between 2 and 12 notes, the commit message as the query, the notes touched as the labels. 86 commits qualify in this repo today.

Built 2026-09-21 as `tools/scripts/rank-bench.py` in the template repo, with `tools/scripts/rank-notes.py` as the first ranker scored. Both are stdlib-only; the default run takes no arguments and finishes in 8.6s over 86 commits.

At a 24-note budget the ranker's honest row (IDs stripped) scores **0.340**. The floor — the 24 most recently updated notes, which is what "look at what changed lately" gets you with no ranking at all — scores **0.450**. A whole-snapshot read scores **0.535**. The ranker loses to both, and that is the finding this task existed to produce.

Every commit is scored against the note corpus at its own parent. `--worktree` scores the same commits against the working tree instead, and exists only to measure what that costs: it lifts the honest row from 0.340 to 0.629 while leaving the two snapshot baselines bit-identical, because those never read the note corpus. That is a controlled measurement of a train/test leak, not an estimate of one. The figures this note carried before today — 0.768 / 0.620 / 0.152 — were all measured under it and are superseded.

## The caveat is part of the output, not part of a note

These labels are the notes the work **wrote**. Close-out mechanically touches the task note and the snapshot, so some of every label set is output rather than input. The bias sits in every row equally, so comparing rows is sound and reading a row as "N% of what you needed" is not. That sentence, or one like it, prints with the table. A reader who sees 0.768 without it has been misled by this harness.

## The corpus moves under the measurement

The prototype builds its index from the working tree, while the labels come from commits in the past. Those two drift apart, and writing this feature's own notes is what proved it: hours after the first run, the same harness on the same 86 commits reported the floor row at 0.161 instead of 0.219, and the ranker at 0.743 instead of 0.747. (Those four are pre-fix figures, quoted here only to show the size of the drift; the current numbers are in "What this delivers".)

Nothing about the ranker changed. Eleven PHASE-0008 planning notes had been created, all dated today, and they took eleven of the twenty-four slots in the most-recently-updated floor — where they can never match a commit made before they existed. The recency floor is the most exposed row because recency is all it uses, but every row shifts, because every row scores against an index that has grown.

So the figures quoted throughout these notes are as-of the corpus at their measurement, not properties of the ranker. The harness must read each commit's corpus at that commit, the way the cold-start baseline in [[TASK-0151-Cold-Start-Baseline|TASK-0151]] already reads `SNAPSHOT.yaml` at the parent commit. Until it does, this feature's own documentation degrades its own benchmark — and does so silently, which is the part worth catching.

## The prototype shipped with a known defect

Recorded because it nearly reached the port. The prototype scored every note with BM25 and then divided by `1 + log(1 + len/avg)` a second time. BM25's `b` term already handles document length, so this was a second penalty, and it fell hardest on the longest notes — the ones a feature's own documentation produces.

It was diagnosed early: removing it lifted recall at every depth on the link-graph proxy, and moved `ISS-0048` from rank 44 of 360 to rank 3 on a query matching its title almost verbatim. The fix was measured, reported as done, and **never written to the file**. It was tested in a throwaway function and the file kept the defect.

Running the ranker live on this feature's own notes is what exposed it. Asked "which notes cover the harness that measures which notes a session should read", the prototype returned neither [[FEAT-0038-Note-Relevance-Harness|FEAT-0038]] nor this task in its top six: at 1.9x and 2.7x the corpus mean they ranked 8th and 15th, pushed down by exactly the penalty already identified. With the fix applied they rank 1st and 2nd, and five of the top six are this feature's notes.

Two things to carry. The fix is applied in `~/Dev/reference/note-ranker-prototype-2026-09-21/rank.py` with `rank.py.bak` holding the defective version, and the corrected figures are the ones quoted above. And a benchmark that improves on average can hide a defect that is severe on one class of input — the link-graph proxy moved only 0.53 to 0.55 while a single note moved 41 places. Run the thing on a real query before trusting the aggregate.

## Definition of Done

- [x] `rank-bench.py` runs from the repo root on the standard library alone and needs no arguments for the default run.
- [x] A ranker is supplied through one documented interface — a callable taking a query and a budget and returning note IDs — so a second candidate can be scored without editing the harness.
- [x] Recall is reported at 5, 10, 24 and 50 for: the message as written, the message with IDs stripped, and the most-recently-updated floor.
- [x] The number of commits in the labelled set and the rule that selected them print with the table.
- [x] Every row built on these labels prints the notes-written-not-read caveat.
- [x] The note corpus for each labelled commit is read at that commit, not from the working tree (see "The corpus moves under the measurement" below).
- [x] Re-running at the same commit reproduces the same figures, and the output states which commit the corpus was read at.
- [x] The prototype at `scratchpad/rank.py` is the first ranker scored, so the harness is exercised end to end before TASK-0153 rewrites it.

## Steps

- [x] Port `scratchpad/bench.py`'s `commit_cases` and `bench_git` into the template's `tools/scripts/rank-bench.py`.
- [x] Pull the ranker out from behind the module import into an explicit interface.
- [x] Add the caveat text and the selection rule to the printed header.
- [x] Read each commit's note corpus at that commit rather than from the working tree, and print the commit the corpus came from.
- [x] Re-measure the 86-commit figures once the corpus is pinned, and record them. The working-tree figures (0.768 / 0.620 / 0.152 at a 24-note budget, measured 2026-09-21 against a corpus that already contained these notes) are the number to compare against, not the number to reproduce.

## Notes

The prototypes are `rank.py` and `bench.py` in `~/Dev/reference/note-ranker-prototype-2026-09-21/`. `bench.py` carries its known limits as module and function docstrings, including a `TODO(widen)` on the transcript extraction. `rank.py` is the corrected version; `rank.py.bak` beside it is the one with the length-normalisation defect and exists only as the record — do not port it.

They were written in a session scratchpad under `/private/tmp/claude-502/...`, which is session-scoped and by now almost certainly gone. That path appears in older revisions of these notes; the `~/Dev/reference/` copy is the one that exists.

## Handoff, 2026-09-21

Planning is done and no implementation has started. This task is still `backlog`; nothing has been committed.

**What was done.** The measurements came first and the notes were written from them, then one measurement was found wrong and everything written from it was corrected. A BM25 ranker prototype (`rank.py`) and a three-benchmark harness (`bench.py`) exist and reproduce their figures. Planning is complete: REQ-0032, FEAT-0038, TASK-0150 through TASK-0155, TST-0021 and RISK-0004 are open, PHASE-0008 is `active`, and all ten notes carry it. `validate-docs.sh` reports OK with zero errors and `sync-snapshot.py --check` is up to date.

**Nothing blocks the start.** Edwin approved REQ-0032 on 2026-09-21, releasing FEAT-0038 from the requirement-approval gate. The implementation repo, the phase and the scope were already settled. Statuses were left where they are because no implementation has begun: this task is `backlog` and FEAT-0038 is `planned`.

**The prototypes are safe, and corrected.** `rank.py` and `bench.py` live at `~/Dev/reference/note-ranker-prototype-2026-09-21/` and run there, so they no longer depend on a session scratchpad. `rank.py` had its length-normalisation defect applied on 2026-09-21 — see "The prototype shipped with a known defect" above — and `rank.py.bak` beside it holds the version that carried it. Port the corrected file. Every figure in these notes was re-measured after that fix; anything quoting 0.747, 0.582 or 0.219 is superseded and should be treated as a mistake if it reappears.

**What is next.** Port `commit_cases` and `bench_git` into the template's `tools/scripts/rank-bench.py`, per the Steps above — and pin the corpus first, because the working-tree figures decay (see "The corpus moves under the measurement").

**Three findings, two of them acted on.** `tools/skills/feature-scaffold/SKILL.md` step 7 and `tools/instructions/OWNERSHIP.md` give different answers to "who approves a requirement" — the skill addresses the scaffolding agent and names no human, the ownership rule names the stakeholder. Edwin asked for it to be filed and it is [[ISS-0077-Who-Approves-Requirements|ISS-0077]], at `triage`, carrying the decision as its `question:`.

The corpus-drift defect is fixed inside this task rather than filed, per the filing bar in `tools/instructions/QUALITY.md` — it is a defect in work this feature is doing. It has its own section above.

The link-form defect is also fixed here, and the convention it exposed is now settled. Edwin ruled on 2026-09-21: **"Links should include the full filename."** So `[[PHASE-0008-Measured-Note-Ranking]]` is correct and `[[PHASE-0008]]` is not, with a pipe for a readable label where the slug would be noise in prose.

What went wrong is worth recording, because the first fix was backwards. The notes used the full filename, `SNAPSHOT.yaml` used the bare ID, the two disagreed, and PHASE-0008 rendered in Obsidian as a dashed label rather than a note reference. Inferring the convention from what the repo did most often gave the wrong answer: the bare form is the more common one (137 notes across PHASE-0003 to 0007 and 999, against 123 using the full filename for PHASE-0001 and 0002), so the notes were rewritten to it — and Edwin then ruled for the form they already had. All eleven were put back and the ten snapshot entries corrected to match. Counting existing usage is not the same as reading the rule, and where no rule is written down, ask rather than count.

Nothing caught the inconsistency because the templates ship a bare `phase:` with no example value, `OBSIDIAN.md` says only "use links in properties instead of bare IDs" — which both forms satisfy — and the validator checks that a link resolves, never that it is written one way.

A second rule fell out of the first, because a full-filename link only reads well when the filename is short. PHASE-0008's file had swallowed its whole title — a 55-character descriptor where the next longest phase was 43 — which is what actually rendered as the dashed label. Its `title:`, H1 and filename all agreed; the filename was simply too long to display. On Edwin's instruction all thirteen notes of this feature were renamed to 15-25 character descriptors on 2026-09-21, titles untouched: `PHASE-0008-Measured-Note-Ranking`, `FEAT-0038-Note-Relevance-Harness`, `TASK-0154-Parameter-Sweep` and so on. They are the reference shape for the repo-wide rule, not an exception to it.

One correction worth carrying, since it nearly cost a second wrong sweep: these twelve were first reported as defective, and measured against their own types they were not. `TST-0021` and `ISS-0077` sat at their type's exact median, the tasks between the 66th and 96th percentile. PHASE-0008 was the only real outlier. Edwin chose to rename them anyway and scope the rest, which makes them the first notes under a new rule rather than twelve short names among 450 long ones — but the distinction mattered enough to put to him rather than assume.

Left open, outside this feature's scope and carried by [[ISS-0078-Link-And-Name-Forms|ISS-0078]]: 399 bare-ID wikilinks and 1057 non-link bare IDs across 347 of 459 notes, 108 snapshot entries, and 187 of 373 filename descriptors over 30 characters (ISS 71 of 78, TASK 56 of 155). PHASE-0006 and PHASE-0007 also carry no `aliases:`, so the bare links naming them resolve to nothing. The issue argues the checks matter more than the sweeps: both conventions drifted for months behind a green validator, because it verifies that a link resolves and never that it is written one way.

The one left open: PHASE-0008 is the third `active` phase alongside PHASE-0003 and PHASE-0006. Nothing in `STATUSES.md` or `docs/PHASES.md` limits that and the validator is green.

Checked on 2026-09-21 rather than assumed: PHASE-0003 ("Prompting-guide conformance") has exactly two unresolved children, [[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks|ISS-0052]] and [[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently|ISS-0053]], both `open`. Everything else under it is scope-resolved. So it is nearer to closing than to parking, and closing it would also need its exit criteria ticked (PHASE-BOXES). PHASE-0006 is parked until Codex is back.

Two traps for whoever checks this next. Grepping for the string `PHASE-0003` matches prose mentions — including this paragraph — so filter on the `phase:` frontmatter field. And statuses in frontmatter may be quoted, so an unquoted comparison silently misses terminal items. Both mistakes were made here first and produced a child list that was wrong in both directions.

Worth knowing separately: `docs/PHASES.md` no longer lists phase statuses at all. Its table was removed on 2026-09-19 under [[ISS-0072-PHASES-Md-Repeats-Every-Phase-Status-And-Drifts-From-The-Phase-Notes|ISS-0072]] because it drifted, and it now points at `docs/phases/` or the cockpit. A reader who opens the overview expecting to see which phases are active will see nothing — which is by design, and is how this question came up.

**Approaches set aside.** Using a model to verify the note rules was considered and declined on 2026-09-21; the reasoning is recorded in [[ISS-0078-Link-And-Name-Forms|ISS-0078]] rather than here, because that is where someone will act on it. Short version: link form and filename length are decidable in code, and every defect found across this whole session — bare-ID links, oversized filenames, the corpus drifting under the benchmark, a snapshot note still claiming a requirement was at `draft` — was found by grep, arithmetic or reading. None needed semantic judgment. That is a data point about where this repo's defects live, and it argues for more deterministic checks rather than for a model.

A Jev (TypeSafe System One) reranker was measured on paper and deferred, not rejected. Its trigger is TASK-0154's last definition-of-done line: read the twenty highest-ranked misses and say whether the wording overlapped. If the misses are lexical-gap cases, a semantic rerank over the script ranker's top 50 is worth pricing; if they are not, Jev would not fix them either. The `typesafe@typesafe-ai` plugin is installed and `TYPESAFE_API_KEY` is set, but no Jev call has ever been made and none is in scope here.

Two measurement approaches were tried and found wanting, and both are recorded so they are not retried blind. Using the link graph as ground truth (a note's outbound links as labels) scored 0.552 at 24 notes but the labels are noisy — they include parent backlinks and boilerplate citations. Comparing the ranker against a *finished* session's reading (0.75) was the wrong comparator twice over: a session-start aid competes with what a session holds before it starts, not with what it knows after it has worked. That mistake is why the cold-start baseline in TASK-0151 exists.

**Edwin's decisions, in his words.** On building it as a script rather than a model call: *"Could we build a ranker using scripts instead?"* On opening the work: *"make it so"*. On where the code lands: *"The template, dogfooded here"*. On phasing: *"Open PHASE-0008"*.

One question he raised is answered in the notes but worth carrying: he pushed back on the token-savings case, asking whether a model that reads notes retains and caches context that a ranker discards. He was right. Under prompt-caching semantics a note read late costs less than one read early, so filtering saves far less than first claimed, and the retained understanding is a real benefit the ranker does not provide. The surviving case for the ranker is cold-start recall, not token savings — which is what REQ-0032 pins down.
