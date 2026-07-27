---
type: "[[design]]"
id: DES-0000
aliases: ["DES-0000"]
title: ""
status: draft
phase:
owner: unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: []
asset: ""          # rendered artifact beside this note, e.g. "overview-redesign.html"
implements: []     # the [[FEAT-...]] / [[PHASE-...]] this design specifies
supersedes: ""
superseded_by: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# <Design title>

## Problem

<What is wrong with the current surface, or what does not exist yet? A design that
opens with its solution cannot be argued with.>

## Approach

<The shape of the proposal, in prose. The artifact shows it; this says why it is
that shape.>

## Regions

<Every region the artifact declares with `data-design-region`, and what each is
for. Annotations anchor to these IDs, so a region that is not named here cannot
be commented on — and a design that cannot name its own parts has not been
thought through.>

- `<region-id>` — <what it is, and what question it answers for the reader>

## Tokens

<Colour, spacing and type-scale values the implementation must match. Declared
here so the implementation can be checked against them rather than compared by
eye — a token re-typed into a stylesheet is exactly the drift that produced
ISS-0023.>

## Out of scope

<What this design deliberately does not address.>

## Revisions

<Each revision is a commit against the asset, not a new note. Record the reason
here so it survives the conversation that produced it.>

- YYYY-MM-DD — <what changed and why>

## Review

<Region-anchored comments land here. Verdicts go in the frontmatter, transcribed
from a review that actually happened — never anticipated.>
