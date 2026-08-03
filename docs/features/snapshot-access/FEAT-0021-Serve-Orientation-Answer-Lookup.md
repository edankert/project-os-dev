---
type: "[[feature]]"
id: FEAT-0021
aliases: ["FEAT-0021"]
title: "Serve orientation, answer lookup: the startup hook emits the in-flight slice instead of a reminder, and a format-independent query replaces grep against YAML"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-03
updated: 2026-08-03
source: ["fleet measurement 2026-08-03: 590 sessions", "user decision 2026-08-03", "ISS-0031"]
goal: "Stop instructing agents to read the snapshot and start giving them what reading it was for. Orientation is served by the SessionStart hook at 513–3,418 tokens in five of six repos; lookup gets a query interface, because grep against YAML returns different information depending on which of the fleet's two styles a repo uses."
requirements: []
tasks: ["[[TASK-0080]]", "[[TASK-0081]]"]
release: ""
related: ["[[ISS-0031]]", "[[ISS-0030]]", "[[ADR-0017]]", "[[ADR-0002]]"]
tests: []
---

# Serve orientation, answer lookup

## Goal

[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs|ISS-0031]] established that one prescribed method — *"Read SNAPSHOT.yaml at session start"* — covers two needs it cannot both serve, and that agents take the instructed action in **5 of 260 accesses**. This feature addresses each need with the mechanism that fits it, rather than restating the instruction more firmly.

- **Orientation** is *served*, by the hook that already fires.
- **Lookup** is *answered*, by a query that does not depend on the file's YAML style.

## Why not simply add a tool and instruct agents to run it

Because that solves a compliance problem by adding a second instruction whose compliance nobody has measured. The measured uptake of the existing startup instruction is ~2%. A `pos brief` that agents must be told to run inherits exactly that number.

[[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]] clause 1 is the applicable principle one level up: where something can be derived and delivered, deliver it rather than asking a party to do it and hoping. The `SessionStart` hook already fires, already emits text into context, and currently spends that budget on a *reminder to read the file*. Spending it on the file's orientation-bearing content instead removes the compliance question rather than relocating it — the agent does nothing, so there is nothing to comply with.

## Measured basis

**The orientation slice is affordable** — focus, counts, and in-flight items only (`doing`/`review`/`open`/`triage`), with fields trimmed to title/status/file/parent/phase:

| repo | full file | in-flight slice | items |
|---|---:|---:|---:|
| project-os-cockpit | 49,992 | **513** | 4 |
| your-applications.com | 38,466 | **778** | 11 |
| your-sudoku | 14,617 | **1,294** | 16 |
| project-os-dev | 15,881 | **1,663** | 18 |
| your-health | 46,396 | **3,418** | 67 |
| your-trainer | 96,636 | **11,573** | 58 |

**Grep is format-dependent, and both formats are in the fleet.** The same query returns different information depending on a repo's YAML style:

| repo | style | `grep "TASK-XXXX:"` returns |
|---|---|---|
| your-trainer | inline flow-map | 879 bytes — **includes `status`** |
| project-os-dev | block | 15 bytes — the ID alone; the next line is `file:`, **not `status`** |

An agent asking for an item's status gets it in one repo and silently does not in another. That is a correctness defect in the dominant access path (255 of 260 accesses), not an ergonomic complaint, and it is the load-bearing argument for TASK-0081.

## Scope

- **TASK-0080** — the `SessionStart` hook emits the in-flight slice. Changes hook contract **HC-002**, whose current rule is a reminder ("Implementations: Claude Code `hooks/snapshot-freshness.sh` (SessionStart reminder); Codex/generic `bash tools/agents/bootstrap.sh`").
- **TASK-0081** — a format-independent query for lookup, with stable output.

## Out of scope

- **Pruning** ([[ISS-0030-Retention-Is-Policy-Nothing-Performs|ISS-0030]]). Independent and complementary: this feature makes the file's *size* matter less by never requiring a whole-file read, which weakens the token argument for retention while leaving the retrieval-quality argument intact.
- **Write operations.** A `pos task create` interface is a larger idea from the 2026-07-29 comparable-systems review; this feature is read-only, and adding writes would put note authoring behind a tool that ADR-0009 deliberately keeps in the notes.

## Known complications

**`your-trainer`'s slice is 11,573 tokens for 58 items, while `your-health` fits 67 items in 3,418.** The difference is title length — `ISS-0359`'s title is a paragraph of crash-report forensics. So either the emitter truncates titles at a fixed width, or that repo has a title-as-abstract problem distinct from its retention one. Decide before building; a hook that injects 11.5k tokens into every session in one repo has re-created the cost this whole line of work was checking for.

**HC-002 is a tool-agnostic contract with per-tool implementations** ([[ADR-0002]]). Changing it means the contract, the Claude Code hook, and the Codex/generic `bootstrap.sh` move together, and the change propagates to twelve repos via `sync-project-os.sh`.

**The query tool inherits the discovery problem.** Agents reach for grep without being told; they will not reach for a project-specific command unless something puts it in front of them. The one surface that reliably reaches them is the hook output — which this feature is already changing, and which can therefore advertise the query at the point of use. That coupling is the reason to build both halves together rather than separately.

## The honest counter-case

[[ISS-0031]] option 4 — *do nothing until measured* — remains defensible for the orientation half. `project-os-bench` TASK-0008 with a grep-only arm would establish whether grep-only orientation is actually worse before anything is built.

The two halves differ on this. **TASK-0081 does not need the measurement**: format-dependent lookup is a defect on its own evidence. **TASK-0080 is sound on ADR-0017's principle but unquantified in value** — serving beats instructing regardless, yet how much it buys is exactly what TASK-0008 would measure. Sequencing TASK-0081 first, and letting TASK-0080 wait on the bench result, is a legitimate reading of this feature and should be revisited at planning rather than settled here.

## Acceptance

- [ ] A session in any fleet repo begins with focus, counts and in-flight work already in context, without the agent reading `SNAPSHOT.yaml`.
- [ ] The emitted slice stays within a stated token budget in every repo, including the worst case, or the emitter truncates to hold it.
- [ ] An item's status can be retrieved by one command that returns the same shape regardless of the repo's YAML style.
- [ ] HC-002, its implementations and the startup instruction surface agree, with the rule stated once (REQ-0018) rather than restated per adapter.
