---
type: "[[adr]]"
id: ADR-0009
aliases: ["ADR-0009"]
title: "SNAPSHOT.yaml is generated from the notes, not authored alongside them"
status: accepted
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: ["review:2026-07-25-fleet-state-audit"]
decision: "Note frontmatter becomes the single authored source of item state. `items.*`, `counters`, and `metrics` in SNAPSHOT.yaml are generated from `docs/**` by a script run at pre-commit and in CI; `project`, `retention`, `focus`, and `team` remain hand-authored. The validator checks that exist only to detect hand-sync failure (ITEM-STATUS, COUNTER, METRICS) are deleted, because the failure becomes structurally impossible"
context: "97% of the 863 commits that touch SNAPSHOT.yaml also touch a note in the same commit — every status change is written twice, by hand. A further 494 commits changed a note without touching the snapshot at all, which is where drift originates. Three validator checks (ITEM-STATUS, COUNTER, METRICS) exist solely to detect the two copies disagreeing, and `--fix-metrics` already concedes the principle for one of the three"
alternatives:
  - "Invert it — make the snapshot canonical and generate note frontmatter — rejected: notes are the human and Obsidian editing surface, Bases views read note frontmatter, and every skill writes notes. Generating the surface people edit is backwards"
  - "Keep dual-write and harden the validator — rejected: the validator already detects this class of drift and has for months; detection has not prevented 494 note-only commits. The fix for a synchronisation bug is to remove the second copy, not to check it more often"
  - "Delete SNAPSHOT.yaml and have agents read docs/ directly — rejected: the one-file resume property is the snapshot's entire purpose (SNAPSHOT.md, 'Goals'), and a 3,775-note fleet would put the whole archive in context to answer 'what is active'"
  - "Generate on demand rather than at commit — rejected: the snapshot must be readable at session start without running anything, and it must be diffable in review. A committed generated artefact gives both"
consequences:
  - "ITEM-STATUS, COUNTER, and METRICS violations become unrepresentable; the three checks are deleted rather than kept as dead code"
  - "ID allocation stops being a manual counter increment — `counters` becomes max-observed, so the LIFECYCLE 'Counter Integrity' rule and its whole class of error disappears"
  - "Retention (active-and-recent pruning) becomes generator policy applied deterministically, replacing a manual close-out step that is skipped under context pressure"
  - "The `snapshot-sync` skill loses most of its reason to exist; what remains is reconciling genuine note-level contradictions, which is `docs-audit` territory"
  - "This amends ADR-0005: deferral's manual bookkeeping (`origin:`, the parent's `deferred:` list) becomes derived. The invariant ADR-0005 established — deferred never satisfies parent completeness — is preserved unchanged and still enforced; only the hand-maintained provenance moves to derivation"
  - "The generator becomes a single point of failure for every agent's context across 10 repos — tracked as [[RISK-0002-Snapshot-Generator-Single-Point-Of-Failure|RISK-0002]] and mitigated by deterministic ordering, a --check mode, and a fixture suite before rollout"
  - "Output must be stably ordered and diff-readable, or every commit churns the file and review becomes impossible"
  - "`focus` stays hand-authored and becomes more important: it is then the only place a human states intent rather than reports state"
supersedes: ""
superseded: ""
related: [ADR-0003, ADR-0005, ADR-0004, FEAT-0015]
---

# The snapshot is generated

## Context

`SNAPSHOT.yaml` is described in `SNAPSHOT.md` as "the canonical, machine-readable active-context snapshot". In practice it is a *second copy* of state that already exists in note frontmatter, kept in step by hand, by an LLM, under context pressure.

The measurement across 10 repos:

- **863** commits touch `SNAPSHOT.yaml`. **834 of them (97%)** also touch a `docs/**.md` note. The dual-write is not occasional; it is the norm.
- **494** commits changed a note *without* touching the snapshot. That is the drift population.
- **29** commits changed the snapshot alone.

Three of the validator's checks exist only because of this duplication:

- `ITEM-STATUS` — "status drift: snapshot=X note=Y"
- `COUNTER` — an allocated ID exceeds its hand-maintained counter
- `METRICS` — recorded counts disagree with computed counts

`METRICS` already has `--fix-metrics`, which recomputes the block from the notes and rewrites it. That flag is this ADR in miniature, applied to one field: nobody defends hand-authored metrics, they just had not yet generalised the argument.

Meanwhile the LIFECYCLE rules carry an "Atomic Sync Rule" and a "Counter Integrity" rule whose entire content is *remember to write it twice*, and close-out carries a manual retention/pruning step.

## Decision

### 1. Notes are the authored source of item state

Every field the validator currently cross-checks — `status`, `file`, relationships, IDs — is authored once, in the note. Nothing writes item state directly into `SNAPSHOT.yaml`.

### 2. `items.*`, `counters`, `metrics` are generated

A `tools/scripts/sync-snapshot.py` walks `docs/**`, reads frontmatter, and emits those three blocks. It runs:

- at **pre-commit**, alongside the existing validator hook, writing the file;
- in **CI** with `--check`, failing if the committed file differs from the generated one.

`counters` becomes the maximum observed ID per prefix, so allocating an ID means creating a note — nothing else.

### 3. `project`, `retention`, `focus`, `team` stay authored

These are intent and configuration, not state. They are small, they change rarely, and no note holds them.

### 4. Retention becomes generator policy

`retention: active-and-recent` stops being a close-out instruction and becomes a rule the generator applies: terminal items older than the window are omitted from `items.*`, deferred items are never omitted (per ADR-0005), and the note remains the archive.

### 5. Checks that exist to detect hand-sync failure are deleted

`ITEM-STATUS`, `COUNTER`, and `METRICS` are removed from `validate-docs.py`. They are not weakened or downgraded — the states they detect can no longer occur. Every other check (LINK, VERIFY, DEFER-SCOPE, REQ-*, FEATURE-REQ, NOTE-DUP-ID) is unaffected, because those test relationships between *notes*, not agreement between two copies.

## Relationship to ADR-0005

ADR-0005 made deferral a descoping operation with four hand-performed steps: descope from the parent's list, record `origin:`, assign a forward home, mirror in the snapshot. Steps 1, 2 and 4 are bookkeeping that a generator can do:

- the parent's `deferred:` list is computable from the children;
- `origin:` is recoverable from the note's own history, and from the parent link the deferral replaced;
- the snapshot mirror is generated by definition.

Step 3 (a forward home) stays authored, because choosing when work resumes is a decision.

**The invariant is untouched**: a parent may not reach a terminal status while a deferred item sits in its scope. `DEFER-SCOPE` remains an error. What this ADR removes is the four-step turn, not the rule it was protecting — which is the point of ADR-0005 that survives, and the reason ISS-0002 does not regress.

## Consequences

See frontmatter. The one that needs watching is [[RISK-0002-Snapshot-Generator-Single-Point-Of-Failure|RISK-0002]]: today a bad hand-edit corrupts one repo's snapshot and the validator catches it; after this change, a generator bug corrupts all 10 and the validator is comparing the output against itself. Deterministic ordering, a fixture suite, and `--check` in CI are preconditions for rollout, not follow-ups.

## Amendment (2026-07-25) — the generator is built; write authority is NOT granted

`sync-snapshot.py` exists, reuses the validator's parsers, is deterministic, and has a `--check` mode. The shadow run required by [[REQ-0019-Snapshot-Generated|REQ-0019]] was then executed against all 10 hand-written snapshots, and it **failed the gate** — deliberately, and usefully.

### What the shadow run found

Every one of the 10 repos diverges, 107 to 4,077 diff lines. Classified across the fleet:

| Diff class | Lines | What it means |
|---|---|---|
| Items **added** by the generator | 180 items | Notes that exist on disk but no snapshot entry ever mentioned |
| Items **removed** by retention | 153 items | Count-based pruning keeps a different set than hand curation did |
| `title` / `status` / `owner` / `file` reformatted | ~1,400 | Quoting normalised; `path:` legacy alias becomes `file:` |
| `related` / `phase` populated from frontmatter | ~300 | Real links the snapshot did not mirror |
| Comments dropped | ~80 | Hand-written explanation with no home in frontmatter |

### The finding: a snapshot is not a pure function of `docs/`

ADR-0009's premise was that `items.*` duplicates note frontmatter. The shadow run shows it is **duplication plus curation**:

- **Comments.** `# ID allocation helpers`, `# Pruned: FEAT-0001..0006 (all done)`, the rationale beside a counter. Real information, no frontmatter field to hold it.
- **Selective retention.** Hand curation kept what the author judged relevant. Count-based pruning cannot reproduce a judgement, only approximate it — hence 153 removals that no rule derived.
- **Editorial `goal:` / `note:` prose**, already handled by carrying it forward, which is itself an admission the file is not fully derived.

The 180 additions are the generator being **right** and the snapshots being **stale** — genuine drift that no check caught, which is evidence *for* the ADR. The 153 removals are the generator being **different**, not right.

### Decision: `--check` now, write authority deferred

The plan's own gate ([[TASK-0060-Snapshot-Generator|TASK-0060]]) reads: *"Until the generator reproduces all 10 existing snapshots under `--check` with only explainable diffs, nothing else in this feature is safe to start."* The diffs are explainable. They are not small, and applying them would, in one commit per repo, change what every agent sees at session start — 180 items appearing, 153 disappearing.

So:

- **`sync-snapshot.py` ships in `--check` mode** and is wired nowhere that writes. It is already useful: it is the only thing that has ever detected the 180 unregistered notes.
- **`ITEM-STATUS`, `COUNTER` and `METRICS` are NOT deleted.** Their premise — that hand-sync failure is possible — remains true while the snapshot is hand-written. Deleting them now would remove the only checks covering a file the generator does not yet own.
- **[[TASK-0061-Wire-Generation-Retire-Checks|TASK-0061]] is blocked**, by its own stated precondition rather than by discovery.

### What unblocks it

A decision, not more code: accept a one-time curated→generated migration (losing ~80 comment lines fleet-wide, and normalising retention to a rule) in exchange for the dual-write disappearing. That is a trade worth making, and it is the user's to make — the evidence to make it is now in hand rather than hypothetical, which is what this phase owed.

**No completed state is affected either way.** Retention only ever prunes *terminal* items from the index; the notes remain the archive, exactly as `SNAPSHOT.md` specifies. Nothing in this amendment changes a status.
