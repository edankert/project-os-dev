---
type: "[[surface]]"
id: SUR-0000
aliases: ["SUR-0000"]
title: ""
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
# The place in the product this names — a screen, a flow, a subsystem a person
# can point at. NOT a grouping of tests: `area:` on a check names one of these,
# and the whole point of the type is that the name is written once, here,
# instead of retyped on every check that touches it.
kind: screen        # screen | flow | subsystem | surface-less
# Which platforms this surface exists on. Empty means all of them — the same
# opt-in rule release contents and the acceptance gate use.
platforms: []
# What this surface is part of, when the product has that structure.
parent: ""
related: []
tags: [surface]
---

# <Surface>

## What it is

<One paragraph. Where a person finds it, and what they can do there. If this
cannot be written without listing tests, it is not a surface.>

## Boundaries

<What is deliberately NOT part of this surface, and which surface owns it
instead. A surface with no stated edge absorbs its neighbours.>

## Coverage

<Left empty at creation. The checks covering this surface are DERIVED from
`area:` — do not list them here. A second, hand-maintained copy of a
relationship is what ADR-0032 spent a decision removing.>
