---
type: "[[issue]]"
id: ISS-0005
aliases: ["ISS-0005"]
title: "Feature-less requirement triage (ADR-0007 follow-up): 14 of 23 resolved mechanically; 9 are a real residue — 5 policies, 3 conventions, 1 unscheduled deliverable"
status: open
phase: "[[PHASE-999-Parking-Lot]]"
severity: low
owner: user:edwin
created: 2026-07-24
updated: 2026-07-24
reviewed_by: "model:claude-fable-5"
review_date: 2026-07-24
review_verdict: approved
review_note: "Same-family review (authored by Claude-family Opus, reviewed by model:claude-fable-5) — NOT independent per QUALITY.md; a cross-vendor or human pass is still owed."
source: ["[[ADR-0007-Requirement-Terminality-And-Ownership]]"]
related: ["[[ADR-0007-Requirement-Terminality-And-Ownership]]"]
---

# ISS-0005 — Feature-less requirement triage

Carries out the follow-up ADR-0007 deferred: sorting requirements that name no feature into their real homes, and deciding whether a residue exists that justifies a mechanism.

## Correction: 23, not 59

ADR-0007 records "59 feature-less requirements". **The true figure was 23.** The scan that produced 59 matched only single-line `implements:` and missed block-form YAML lists —

```yaml
implements:
  - "[[FEAT-0017]]"
```

— so 36 correctly-linked requirements were counted as orphans. your-health alone accounts for 36 block-form notes; it was reported as having 38 orphans and actually had 2. Spot-checked against git history: `REQ-0031` has named `FEAT-0017` since before this work began.

This is the third symptom of the same defective regex. It also produced the "10 many-to-many" estimate that turned out to be 11 during the ADR-0007 migration. The lesson worth keeping: **frontmatter has three interchangeable shapes** (inline wikilinks, inline bare IDs, block lists) and any scan that reads one shape silently under-reports. The validator's `extract_ids` handles all three; ad-hoc `grep`/`re.search` passes do not, and every count in this investigation that came from an ad-hoc pass was wrong in the same direction.

## Outcome

| Category | Count | Action |
|---|---|---|
| **A. Field drift** — feature named in `specifies:`/`scope:`/`related:`, or claimed by a feature's `requirements:`, but absent from `implements:` | 7 | **Fixed** — link moved into `implements:` |
| **B. Unlinked deliverables** — genuine feature work, never linked | 7 | **Fixed** — owner assigned |
| **C. Policies** — cross-cutting invariants binding all features | 5 | **Open** — see below |
| **D. Conventions** — design-system / content standards | 3 | **Open** — see below |
| **E. Unscheduled deliverable** — real work, no feature exists yet | 1 | **Open** — needs a feature when scheduled |

### A — field drift (fixed)
`project-os-cockpit` REQ-0018→FEAT-0030, REQ-0019→FEAT-0032, REQ-0020→FEAT-0034, REQ-0021→FEAT-0038; `your-applications.com` REQ-0027→FEAT-0027, REQ-0028→FEAT-0032; `your-trainer` REQ-0190→FEAT-0101.

### B — unlinked deliverables (fixed)
`your-applications.com` REQ-0001/0002/0003/0004/0005/0015 → FEAT-0001 (Site infrastructure), REQ-0009 → FEAT-0006 (Our Promise pledge).

Linking REQ-0190 surfaced a REQ-STALE error immediately (its feature FEAT-0101 was `done` while it sat at `approved`), so it was advanced to `implemented` and its prose `## Acceptance` paragraph split into four criteria of record. **None is ticked** — the criteria are recorded, the evidence is not.

### C — policies (open, 5)

`your-applications.com` REQ-0006 *Static HTML only*, REQ-0007 *Data sovereignty*, REQ-0008 *No subscription model*, REQ-0010 *No advertisements*; `your-health` REQ-0028 *Privacy / local-first*.

These bind every feature, present and future. Assigning any one an owning feature would make the invariant read `implemented` the moment that feature closed, while it must still hold for everything built afterwards. `your-health` REQ-0028 states this plainly in its own body — it lists FEAT-0009 and FEAT-0012 under "**Reinforced by**", not "implemented by".

They are ADR-shaped: each is a decision with consequences and rejected alternatives.

### D — conventions (open, 3)

`your-applications.com` REQ-0011 *Store listing asset structure* (a `marketing/` layout convention for **other** repos — not even this site's deliverable), REQ-0012 *Tablet-first split-screen messaging* ("must be communicated in all external-facing materials"); `your-trainer` REQ-0151 *Action-surface button layout conventions* (three layout patterns, consistent ordering and destructive-styling).

`your-trainer` already has `docs/STYLEGUIDE.md`, which is where REQ-0151 belongs.

### E — unscheduled deliverable (open, 1)

`your-health` REQ-0012 *Healthspan Score* (`draft`) — genuine future work; no feature exists yet. Correct as-is; it needs a feature when the work is scheduled, not a mechanism.

## The residue question ADR-0007 asked

ADR-0007 said a mechanism should be added *only* if a residue remains that is genuinely feature-exempt and fits none of the existing homes. **It does not.** All 8 open non-deliverable notes have a natural home — ADR for the 5 policies, styleguide for the 3 conventions. No `kind:` field, and certainly no `constraint` type, is warranted.

Note the 5 policies are *already* effectively feature-exempt with no mechanism at all: they name no feature, so the FEATURE-REQ gate never inspects them and they block nothing. The model works. What is left is a filing question, not a modelling one.

## Recommendation (not yet actioned — needs sign-off)

Converting a requirement into an ADR or styleguide section **removes a requirement note**, which is not reversible by a status flip. Proposed, pending the owner's call:

1. `your-applications.com` — one ADR, "Product pledge: local-first, no ads, no subscriptions, static site", superseding REQ-0006/0007/0008/0010 with links from each. REQ-0009 (*User pledge visibility*) correctly stays a requirement: publishing the pledge page is deliverable work, now owned by FEAT-0006.
2. `your-health` — REQ-0028 → an ADR, or link it to the existing privacy ADR-0004 it already cites.
3. `your-trainer` — REQ-0151 → a section in `docs/STYLEGUIDE.md`; supersede the requirement pointing at it.
4. `your-applications.com` REQ-0011/0012 → a conventions/reference note, or keep as requirements owned by a "brand standards" feature if one is ever created.

Superseding (not deleting) preserves the audit trail: the note stays, `status: superseded`, pointing at its new home.

## Also found

`your-applications.com` has **stale feature statuses**: FEAT-0001 *Site infrastructure*, FEAT-0002 *Homepage*, and FEAT-0006 *Our Promise pledge* are all `backlog`, yet `public/` contains `index.html`, `our-promise.html`, two `privacy.html` pages and the shared stylesheet — the work shipped. The category-B links are correct regardless, but they now point `implemented` requirements at `backlog` features. Closing those features properly means ticking their requirements' criteria with evidence, which is close-out work rather than triage. Filed here rather than forced.
