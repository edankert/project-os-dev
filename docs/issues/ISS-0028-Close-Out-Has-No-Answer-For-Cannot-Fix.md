---
type: "[[issue]]"
id: ISS-0028
aliases: ["ISS-0028"]
title: "Close-out says to run the validator and fix what it reports, and has no answer for 'cannot fix' — which is exactly the case that needs a human and therefore the one that must leave a record"
status: open
severity: low
owner: user:edwin
created: 2026-07-30
updated: 2026-07-30
component: docs
source: ["project-os-cockpit FEAT-0051, 2026-07-30 — a validator badge that reported a count with nothing behind it"]
phase: "[[PHASE-999-Parking-Lot]]"
related: []
depends: []
tests: []
---

# Close-out has no answer for "cannot fix"

## The finding

`LIFECYCLE.md` step 7: *"Run `bash tools/scripts/validate-docs.sh` and fix anything it reports."*
`tools/skills/close-out/SKILL.md`: *"Run `bash tools/scripts/validate-docs.sh` and fix every reported error before finishing."*

Both assume every error is fixable by whoever is closing out. When one is not — a decision the human has to make, a note only they can write — the instruction runs out, and the error simply stays. Nothing records that it exists, why it survived, or that anyone looked at it.

## Why it matters

The validator gates pre-commit and CI, so an unfixed error is loud. What is missing is not the alarm — it is the **record**. There is nowhere to say "this is known, here is why, here is who decides", so the same error is re-encountered and re-diagnosed every session, by whoever hits it next.

It also leaves a whole class of finding with no home. `project-os-cockpit` shipped a per-project validator badge and the user's first reaction was that the number was unreadable — because a count is all a transient condition can be until something promotes it into a record.

## Proposed rule

**At close-out, every validator error is either fixed or filed.**

Anything still failing that you cannot or should not fix becomes an `ISS-*` carrying the error's `[CODE]` and message verbatim, linking the note it names. Deduped on `(code, subject)` — subject being the error's note ID, its repo-relative path, or the literal `SNAPSHOT.yaml` for snapshot-level errors — so a recurring error updates one issue rather than minting a new one each session. Closing that issue is what fixing it looks like; no separate bookkeeping.

**Not an automatic filer.** Considered and declined downstream (Edwin, 2026-07-30): issues appearing without anyone asking is a worse failure than one occasionally missed, and close-out is where the check already runs. The dependency on the agent performing the step is the same one every other close-out obligation carries.

## Next Actions

- [ ] Add the sentence to `LIFECYCLE.md` step 7 and `tools/skills/close-out/SKILL.md`
- [ ] Decide whether the dedup key belongs in the instruction or in `TRACEABILITY.md`
- [ ] Consider whether the validator should carry a `--json` mode, so an agent filing these does not have to re-parse its report lines

## Notes

Running downstream in `project-os-cockpit` since 2026-07-30, in `CLAUDE.md` rather than the instruction — `tools/instructions/` is template-owned, so a local edit becomes divergence the next sync reports. That repo carries a guard which fails if the template ever adopts the rule, so the local copy gets deleted rather than left to drift alongside it.

Same shape as [[ISS-0025]] and [[ISS-0027]]: a close-out obligation the template states half of.
