---
type: "[[issue]]"
id: ISS-0017
aliases: ["ISS-0017"]
title: "A review verdict never expires: `reviewed_by`/`review_date`/`review_verdict` survive any later edit to the note they approved, so an approved note and a rewritten-since-approval note are indistinguishable"
status: open
severity: medium
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: tooling
source: ["landscape review 2026-07-29: Doorstop item fingerprints and suspect links"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0014, ADR-0010, ADR-0013]
tests: []
---

# A review verdict never expires

## Problem

`QUALITY.md` closes the independent-review section with: *"Record the outcome in the reviewed note frontmatter (`reviewed_by`, `review_date`, `review_verdict`)."* The validator reads those fields — `REVIEW` errors when a settled item carries `changes-requested`, and warns when a settled item has no verdict at all (promoting to error 2026-10-23).

Nothing invalidates the verdict when the note changes afterward.

A note reviewed and approved on Monday, rewritten on Tuesday, still reads `review_verdict: approved` on Wednesday, and the validator is clean. The verdict is a claim about a version of the note; the frontmatter records it as a claim about the note. There is no version in it.

This is the same defect class [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] removed for tests — a status asserted at one moment and read as current forever — surviving in the one place the system trusts most, because a review verdict is the evidence of last resort for exactly the transitions ([[TST]] notes, [[CHG]] notes, requirement `implemented`, feature `done`) that no automated gate can settle.

## Evidence

No content hash, fingerprint or revision exists anywhere in the tooling:

```
$ grep -rln "fingerprint\|sha256\|content_hash" tools/
(no matches)
```

`review_date` is the only temporal field, and it is a date typed by the reviewing agent, not derived from anything. Comparing it to `updated:` would be a partial signal at best — `updated:` is also hand-written, and a note can be materially rewritten without it moving.

## Repro

1. Take any note carrying `review_verdict: approved` (e.g. [[CHG-20260721-Requirement-Lifecycle-Closure]], `reviewed_by: model:claude-opus-4-8`).
2. Rewrite its body — change what was reviewed, not just prose.
3. Run `bash tools/scripts/validate-docs.sh`.

## Expected

The note reports as **unreviewed**. Its recorded verdict describes content that no longer exists, and a gate resting on that verdict should refuse until someone re-reviews.

## Actual

Clean. `REVIEW` sees a verdict field with the value `approved` and asks nothing further.

## Prior art

Doorstop solves exactly this, and has since v1:

- **Item fingerprints.** `doorstop review` saves a hash of the item's reviewed content into the item. Edit the item and the stored hash no longer matches, so validation reports it unreviewed until the reviewer re-stamps it. The stamp is the *reviewer's*, not the author's — and it cannot be preserved by accident, only re-issued deliberately.
- **Suspect links.** A link stores the *parent's* fingerprint at the time the child was linked. Change a requirement and every child link is reported suspect, cleared only by `doorstop clear` after someone has looked. This is the mechanism project-os lacks for the case that matters most here: amending a requirement silently leaves every note that implements it carrying an approval of the older text.

The relevant difference is authorship. Doorstop assumes a human types the stamp; project-os is maintained by an LLM, which makes an *automatic content hash* strictly better than [OpenFastTrace's](https://github.com/itsallcode/openfasttrace) alternative of hand-written revision integers (`[impl~~42->req~name~17]`). Nobody — human or agent — reliably remembers to bump an integer, and an agent that can type the revision it needs is back in the ADR-0010 conflict of interest.

## Relationship to ADR-0014

[[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]] already contains the mechanism, applied to a different surface. Its section 2 gives evidence a revision so a claim can go stale, and its consequence list calls that *"the first check in the system that can invalidate a claim without anyone editing the note."*

A review verdict is a claim of exactly that kind. It should carry the same revision and go stale by the same rule — which means this is most likely **not a separate design**, but the review-surface case of ADR-0014's revision, and should be scoped as such rather than growing a second, parallel staleness mechanism. Whether the revision is a git blob hash, a content hash of the note minus its own review fields, or the commit the review ran against, is the open question; the note's own fields must be excluded either way, or stamping the verdict invalidates it.

## Blast radius

Every repo carrying the validator. The population is not hypothetical — `REVIEW` is currently warn-only precisely because the fleet carries 207 settled items without verdicts, and the ones that *do* carry verdicts are the ones this issue makes untrustworthy.

## Next Actions

- [ ] Decide whether this is folded into [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]]'s revision mechanism or specified separately; prefer folding.
- [ ] Choose the revision source (git blob hash vs content hash excluding review fields) and confirm stamping cannot self-invalidate.
- [ ] Decide whether link suspicion (parent-fingerprint-on-child) is in scope or a follow-up — it is the larger and more valuable half, and the more expensive one.
- [ ] Author a `TST-*` proving the inversion: stamp, edit, expect a finding.
