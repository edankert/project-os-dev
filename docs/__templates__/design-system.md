---
type: "[[design]]"
id: DES-0000
aliases: ["DES-0000"]
title: "<Project> design system"
role: system            # `system` = the standing reference designs conform to; `proposal` = a time-bounded design
status: draft
owner: unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: []
asset: "design-system.html"   # living style guide: every token, component and state, rendered
viewport:               # px width when the artifact IS a surface; omit for a scrolling document
implements: []
supersedes: ""
superseded_by: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# <Project> design system

> One per project. Every project answers **the same questions in the same order** — the answers
> differ, the schema does not. That is what makes two projects comparable by diff rather than by
> archaeology, and what makes convergence an editing job if it is ever wanted.

## Principles

<How this project applies the fleet design philosophy. This is the bridge between the shared
principles and the specific values below — three or four lines, each naming a principle and what
it means *here*. If a principle does not apply to this project, say so and why; a principle
silently ignored is worse than one explicitly waived.>

## Palette

<Semantic **roles** first, values second. Roles are what stay stable across a redesign; hexes are
not, and a palette documented as a list of colours goes stale the first time one changes.>

| Role | What it means | Light | Dark |
|---|---|---|---|
| surface | | | |
| ink | | | |
| accent | | | |

<State the roles this project actually has. If the app carries status or severity colour, those
are roles too, and they are the ones most likely to drift — name their single source.>

## Typography

<Families, the scale, and **what each level is for**. A scale without purposes is a list of sizes:
"20px" is not a decision, "the only thing above the fold that names the current state" is.>

## Spacing & density

<The base unit and the scale derived from it. If spacing is currently ad-hoc, say so plainly and
record the observed values — an honest "no scale yet, these are the numbers in use" is a finding
someone can act on; an invented scale that the code does not follow is fiction.>

## Icons

<Which set, at what sizes. And the rule that matters most: **when may an icon appear without a
text label?** An icon-only control is a guess unless its meaning is conventional; write down which
ones qualify here.>

## Widgets

<The recurring components — chip, card, list row, badge, empty state — and their states. For each,
say which states must be **visually distinct without colour**, because that is the rule most often
assumed and least often checked.>

## Motion

<What animates, what deliberately does not, and durations. "Nothing animates" is a legitimate and
complete answer; leaving this blank is not, because it hides whether the silence was chosen.>

## Accessibility floor

<Contrast minimums, focus visibility, and the never-colour-alone rule. These are the constraints a
design may not trade away for aesthetics — stating them here is what makes a review able to reject
a design rather than merely dislike it.>

## Conformance

<How the implementation is checked against this note. Name the test, and name which side is
upstream when they disagree: a parity check with no declared direction of authority accumulates
waivers instead of fixes.>
