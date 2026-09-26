---
type: "[[task]]"
id: TASK-0081
aliases: ["TASK-0081"]
title: "A format-independent query for lookup, because grep returns different information per YAML style"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-08-03
updated: 2026-09-25
source: ["fleet measurement 2026-08-03", "ISS-0031"]
parent: "[[FEAT-0021]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ISS-0031]]", "[[ADR-0009]]"]
tests: ["[[TST-0024]]"]
---

# A query that does not depend on the file's YAML style

## The defect being fixed

Lookup is 255 of 260 snapshot accesses, and it is performed with grep against a file the fleet writes in two different styles:

| repo | style | `grep "TASK-XXXX:"` returns |
|---|---|---|
| your-trainer | inline flow-map | 879 bytes — **includes `status`** |
| project-os-dev | block | 15 bytes — the ID alone; the next line is `file:`, **not `status`** |

An agent asking "what is TASK-0079's status?" gets an answer in one repo and, in the other, gets a line that does not contain the answer with nothing indicating anything is missing. `grep -A5` papers over it until an entry has six fields, and the failure stays silent either way.

This is a correctness defect on the dominant path, and it is what justifies the task independently of any measurement.

## Shape

Read-only, over `SNAPSHOT.yaml` plus note frontmatter, with output stable enough to be parsed:

- one item by ID — status, file, parent, phase, links
- items by status / collection / phase
- what is in flight (the same slice TASK-0080 emits, so both halves share one implementation)
- `--json` on everything, per the convention every other script in `tools/scripts/` already follows

Where to put it is an open question worth deciding deliberately: a new `tools/scripts/query-snapshot.py`, or a subcommand of `sync-snapshot.py`, which already parses the file and already owns the "what is derived" boundary. The second avoids a thirteenth script; the first keeps a read-only tool out of a file whose job is mutation.

## Constraints

- **Read-only.** Writes stay in the notes (ADR-0009). A `create`/`update` interface is a much larger idea from the 2026-07-29 comparable-systems review and is explicitly out of scope for FEAT-0021.
- **Notes are the fallback, as in the validator.** `resolves()` checks the snapshot *then* `note_index`; a query that only reads the snapshot will answer "not found" for pruned-but-real items, which is exactly wrong once ISS-0030 is acted on.
- **Stable output.** If agents are to rely on it, the shape must be versioned or at least not churn; unstable output is worse than grep because it fails in ways grep does not.

## The discovery problem, which this task cannot solve alone

Agents reach for grep without being told. They will not reach for a project-specific command unless something puts it in front of them, and the measured uptake of telling them in `CLAUDE.md` is ~2%.

The only surface that reliably reaches an agent is the hook output — which TASK-0080 is already changing. So the query should be advertised there, at the point of use, and that coupling is the reason both tasks belong to one feature. **A query nobody invokes is worse than no query**, because it looks like the problem was addressed.

## Definition of Done

- [x] One command answers an item's status identically in a block-style and an inline-style repo; verified against `project-os-dev` and `your-trainer` specifically — evidence: `snapshot-query.py` 2026-09-25 answered TASK-0081 here (block) and TASK-0965 in your-trainer (inline) with status, file, parent and phase; TST-0024 asserts identical output for the same items in both styles
- [x] Falls back to note frontmatter when an ID is absent from the snapshot — evidence: TASK-0100, pruned from this snapshot, is answered from its note and marked so; TST-0024
- [x] `--json` output, shape documented in the script — version 1, in the module docstring
- [x] Location decided and the reasoning recorded — a new read-only `tools/scripts/snapshot-query.py`, because `sync-snapshot.py` writes the snapshot and a lookup should not share a file with mutation. It imports `snapshot-slice.py`'s parser, widened to read every field, so the orientation and the lookup read the snapshot one way
- [x] Advertised in the hook output from TASK-0080 — the orientation's closing line names `snapshot-query.py <ID>`; HC-002 says so; TST-0024 asserts it
- [x] A `TST-*` with a `command:` — [[TST-0024]], 12 assertions, five mutations each failing it
