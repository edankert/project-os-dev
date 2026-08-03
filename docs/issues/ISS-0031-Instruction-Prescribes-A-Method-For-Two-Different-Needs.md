---
type: "[[issue]]"
id: ISS-0031
aliases: ["ISS-0031"]
title: "The startup instruction prescribes one method — read the whole snapshot — for two different needs, and agents comply with it 5 times in 260; whether the 255 that grep instead are actually oriented is unmeasured"
status: open
severity: medium
owner: user:edwin
created: 2026-08-03
updated: 2026-08-03
component: docs
source: ["fleet measurement 2026-08-03: 590 sessions", "ISS-0030 correction"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ISS-0030, ADR-0009, ADR-0017]
tests: []
---

# One prescribed method, two different needs

## Problem

Every startup surface tells an agent to read the snapshot:

- `CLAUDE.md:5` — *"Read SNAPSHOT.yaml at session start to understand current project state and focus."*
- `~/.claude/CLAUDE.md:18` — *"Read SNAPSHOT.yaml at session start to understand active work context"*
- `CONTEXT.md:13` — the documentation set is the *"authoritative, **task-starting context**"*
- the `SessionStart` hook — *"REMINDER: Read SNAPSHOT.yaml to understand current project state, focus, and active work before proceeding."*

Measured across 120 `your-trainer` transcripts, agents access the file **255** times by grep or bash, **29** times by partial read, and **5** times in full. Fleet-wide, a full read appears in 31 of 590 sessions.

So the instructed action is taken in roughly 2% of accesses. That is not a compliance problem to be fixed by insisting harder, and it is not obviously a defect in the agents either. **The instruction names one method for two needs that are not the same:**

- **Orientation** — *what is in flight, what is the focus, what changed recently, what should I not touch?* This is what `CLAUDE.md` and `CONTEXT.md` are actually asking for. It is synoptic, it is needed once, and **it cannot be satisfied by grep**, because grep answers a question you already knew to ask. An agent that only ever greps never reads `focus:` at all — the single most orientation-bearing field in the file.
- **Lookup** — *what is TASK-0123's status? which feature owns this?* Targeted, needed repeatedly, and grep is the correct tool. Loading 1,065 items to answer it is waste, and YAML's structure exists precisely so it need not happen.

Nothing in the instruction surface distinguishes them, so the guidance is wrong for one of the two whichever way it is written.

## What is *not* established

**That the behaviour is more correct than the instruction.** It is more efficient — that is measured. Whether the 255 grepping accesses leave an agent as well-oriented as one full read would is **not measured**, and the temptation to assume it does is exactly the error [[ISS-0030-Retention-Is-Policy-Nothing-Performs|ISS-0030]] had to retract on 2026-08-03: an inference about agent behaviour, presented beside real measurements, read as one of them.

What the corpus shows is *what agents do*, not *whether the outcome was good*. Those are different claims and only the first has evidence.

## Why a blanket rule cannot be right anyway

Snapshot size spans an order of magnitude across repos running the same instruction: `project-os` ~700 tok, `project-os-dev` ~15,400, `your-trainer` ~96,600. A full read is trivially cheap in the first and meaningful in the last. One sentence cannot be correct for both, and today the same sentence ships to all twelve.

## Relationship to ISS-0030

They are the same problem seen from two ends, and neither should be decided without the other.

- ISS-0030 says the snapshot accumulates until two-thirds of it is terminal.
- This issue says the instruction asks for a whole-file read of it.

If the snapshot were pruned to active-and-recent, **the whole file would be the orientation slice** — small enough to read, and containing nothing but what orientation needs. That is a better argument for retention than the one ISS-0030 was originally filed on, and it means the two issues share a fix rather than competing for one.

## Options

1. **Split the instruction by need.** Say explicitly: read `focus:` and the active items to orient; grep for everything else. Costs one paragraph, needs no tooling, and matches what agents already do — while giving the orientation half a home it currently lacks.
2. **Serve the orientation slice.** ~~A `--brief` output (focus plus non-terminal items) that is cheap in any repo regardless of snapshot size.~~ **Superseded 2026-08-03 by option 5, which is strictly better:** a `--brief` an agent must be *told* to run inherits the ~2% uptake this issue documents. Two measurements also refined it — filtering to non-terminal items only gives 1.3×–3.5× reduction (your-trainer's "brief" is still ~28k tokens), so the slice has to be *in-flight* rather than merely non-terminal to be cheap.

5. **Serve it from the hook, so nothing has to be invoked.** The `SessionStart` hook already fires and already emits text into context; it currently spends that on a reminder to read the file. Emitting focus, counts and in-flight items instead costs 513–3,418 tokens in five of six repos and removes the compliance question entirely, because the agent does nothing. This is [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]] clause 1 applied one level up: where something can be delivered, deliver it rather than asking and hoping. **Scoped as [[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]] (2026-08-03), together with a format-independent query for the lookup half.**
3. **Prune, and leave the instruction alone** (ISS-0030). Makes the blanket instruction correct again by making the file small — but only until it drifts, which is ISS-0030's whole point.
4. **Do nothing until measured.** Defensible: the cost of the current state is unknown, and option 1 is only obviously right if grep-only orientation is actually worse.

Options 1 and 3 compose. Option 2 supersedes both if built.

## How this gets settled

`project-os-bench` **TASK-0008** (orientation probe) is already the instrument: fixed questions, fresh agent, scored against ground truth extracted from the notes. It was designed to compare snapshot-present against snapshot-absent; the arm this issue needs is a third one — **snapshot present but accessed only by grep** — which costs almost nothing to add and answers the question directly.

Until it runs, this issue records an open question, not a defect with a known fix.

## Next Actions

- [x] Options scoped as [[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]] (2026-08-03) — option 5 for orientation (TASK-0080), a format-independent query for lookup (TASK-0081). Option 2 superseded; see above.
- [ ] Add the grep-only arm to `project-os-bench` TASK-0008. Still wanted: it does not gate TASK-0081 (format-dependent lookup is a defect on its own evidence) but it is the only thing that would *quantify* TASK-0080's value, which FEAT-0021 records as sound-but-unmeasured.
- [ ] Reconcile the startup instruction surface once the hook serves orientation — `CLAUDE.md`, the user-level `CLAUDE.md`, `CONTEXT.md` and HC-002 — stated once per REQ-0018. Tracked on TASK-0080; if it is not done, this issue reappears with the roles reversed.
- [ ] Check whether the same instruction/behaviour gap exists for `tools/instructions/` and `tools/skills/` — measured at 0.5% of context, which is either healthy selectivity or evidence the playbooks are not being read at all. The instruction surface says "read them when relevant" and nothing verifies that judgement.
