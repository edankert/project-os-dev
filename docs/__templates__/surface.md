---
type: "[[surface]]"
id: SUR-0000
aliases: ["SUR-0000"]
title: ""
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
# A surface is a screen unless this says otherwise. The four rules for the
# cases that get it wrong -- states, dialogs, checks that cross screens, and a
# screen placed differently per platform -- are stated once in
# tools/instructions/TAXONOMY.md, "`kind` (surfaces)".
kind: screen        # screen | flow | subsystem | surface-less
# Which platforms this surface exists on. Empty means all of them -- the same
# opt-in rule release contents and the acceptance gate use. A screen that sits
# in a different place on each platform is still ONE surface (rule 4).
platforms: []
# The screen this one opens from, for a dialog, sheet, panel or section.
parent: ""
# The screenshot keys that capture this surface: `key`, or `key:state` where
# the key captures it in one state. TAXONOMY.md, "`gallery` (surfaces)".
gallery: []
related: []
tags: [surface]
---

# <Surface>

## What it is

<One paragraph. Where a person finds it, and what they can do there. Where the
product ships on more than one platform, say where each platform puts it. If
this cannot be written without listing tests, it is not a surface.>

## Boundaries

<What is deliberately NOT part of this surface, and which surface owns it
instead. A surface with no stated edge absorbs its neighbours.>

## Coverage

<Left empty at creation. The checks covering this surface are DERIVED from
`area:` — do not list them here. A second, hand-maintained copy of a
relationship is what ADR-0032 spent a decision removing.>
