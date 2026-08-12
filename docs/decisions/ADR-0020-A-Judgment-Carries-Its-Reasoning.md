---
type: "[[adr]]"
id: ADR-0020
aliases: ["ADR-0020"]
title: "A judgment carries its reasoning — every human verb may record a note, and a decision may state its open threads as criteria"
status: accepted
owner: user:edwin
created: 2026-08-12
updated: 2026-08-12
source: ["Edwin 2026-08-12, opening ADR-0010 in project-os-cockpit to decide it: 'this is not as straight forward as simply accepting, it asks questions but I cannot answer these or provide additional comments in the tool'", "Measured 2026-08-12 across six write paths in project-os-cockpit"]
decision: "Every human-owned verb may carry an optional note, appended to the decided note under one `## Decision record` heading as a dated, attributed Obsidian callout. A decision note may carry an `## Acceptance` section whose criteria are its open threads, tickable one at a time with evidence."
context: "A project-os tool could record THAT a human decided and never WHY: of six write paths, exactly one carried the person's own words and only onto a checkbox line."
alternatives:
  - "A `Comment` verb that records prose without deciding — rejected: it creates a commented-but-undecided state nothing reads, the shape a downstream repo had already cancelled a feature over"
  - "Free-text in frontmatter — rejected: frontmatter is for fields a machine reads, and a paragraph in a YAML scalar is legible to neither reader"
  - "A separate decision log file — rejected: the reasoning belongs where the decision is, or the next reader finds one without the other"
  - "Block `Accept` until every criterion is ticked — rejected: a person may decide while a thread stands, and the record should show that rather than prevent it"
consequences:
  - "`DECISIONS.md` and `OBSIDIAN.md` carry both conventions; the callout is part of the record's vocabulary rather than a rendering flourish"
  - "A tool rendering project-os notes must render callouts, degrading an unknown type to a blockquote with its title kept rather than printing the marker"
  - "The note APPENDS and is quoted line by line, so a second decision never edits the first and hostile prose cannot alter the file it lands in"
  - "Most ADRs stay a plain yes/no: the Acceptance section is available, not required"
supersedes: ""
superseded: ""
related: [ADR-0011, ADR-0013]
---

# A judgment carries its reasoning

## Context

Opening a `proposed` ADR in the cockpit offers two verbs and no fields. That is fine for a decision that is a yes or a no. It is wrong for one that proposes an option and leaves threads open inside its own consequences — accepting stamps every thread at once, and there is nowhere to say *"yes to option 3, but not consequence 3 as written"*.

Measured in `project-os-cockpit` on 2026-08-12, across every path that records a human judgment:

| endpoint | the person's own words? |
|---|---|
| transition, review, design verdict, decide | **no** |
| test run | steps only |
| **criterion tick** | **yes** |

**One in six**, and it can only attach prose to a checkbox line. The system could record that a human decided and never why — which is the half of a decision that survives being right.

## Decision

**1. Every human-owned verb may carry an optional note.** It is appended to the note being decided, under a single `## Decision record` heading, as a dated and attributed Obsidian callout.

**2. A decision note may carry an `## Acceptance` section** whose criteria are its own open threads, answered one at a time with evidence through the machinery a feature's criteria already use.

## Why a callout, and why in the note

**One syntax, two readers.** Obsidian renders `> [!note]` natively; a project-os tool renders it too. Inventing a marker would have made the record legible in exactly one place, which is the failure every convention here exists to avoid.

**In the note, because that is where the decision is.** A separate log means the next reader finds the decision without the reasoning, or the reasoning without the decision. The note is the durable artifact; the reasoning is part of it.

**Appending, because a decision record that can be rewritten is not one.** A second decision adds a second callout and the first stands as written.

## Why criteria and not a new mechanism

The parser, the tick, the evidence field and the guards all exist and are used by every feature. Pointing them at a decision note cost **no new write path** — the downstream implementation found the machinery already ungated by type, so the only new thing was the convention. A mechanism that already works and is already guarded beats one designed for the case in hand.

## Consequences

- Both conventions are in `DECISIONS.md` and `OBSIDIAN.md` as of this decision.
- Rendering callouts becomes a requirement of any tool that displays project-os notes, with the unknown-type degradation stated so a downstream tool does not have to guess.
- Accepting a decision with criteria open is **allowed**, and the unticked ones are the honest residue rather than an error state.
