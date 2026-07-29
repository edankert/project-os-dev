---
type: "[[adr]]"
id: ADR-0015
aliases: ["ADR-0015"]
title: "If project-os is ever hosted, it is an intent layer over git — never a git host, never an agent runtime"
status: proposed
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
source: ["design conversation 2026-07-29: 'what if we created a hosted solution where project-os was the main driver'"]
decision: "Park the hosted product; do not build it yet. If it is ever built, three positions are pre-committed: git remains the object store and is written as an output, never replaced; the git host and the runner are pluggable adapters, so no single vendor is a foundation; and agents run on the user's machine with the user's keys, never on the service"
context: "Code hosting assumes a human authored the diff, so review is line-by-line and provenance is 'who committed'. Agent-authored change breaks both: the diff is the least informative artifact, and intent lives in a spec the platform cannot see. The question is whether project-os should become the hosting layer that does see it"
alternatives:
  - "Build a full git host with issues, CI and review — rejected: it re-implements a solved, commodity problem, costs the entire engineering budget, and makes the product's value depend on the layer that is already free"
  - "Replace git with a semantic or patch-theoretic store (Pijul, Darcs) — rejected: the problems are in the review surface and the unit of intent, not in content-addressed storage. Jujutsu demonstrates the layering works and is adopted precisely because nobody has to migrate"
  - "Build on GitHub as the assumed backend — rejected: it contradicts the pitch, excludes the maintainers most likely to want this, and makes the product commoditisable by the vendor it depends on. GitHub becomes a supported adapter, not a foundation"
  - "Run agents on the service — rejected on measurement: ~6,000 agent-hours/month for 100 seats is $30k-90k/month against ~$350 of infrastructure, 20-50x everything else. It is also worse architecture; agents need the developer's environment"
  - "Build it now — rejected: ADR-0014 delivers most of the value inside the existing repos, and until it is in use across the fleet there is no evidence the hosted version is worth building"
consequences:
  - "The repository stays a complete, portable artifact — clone it and the whole record is there, no service required. This is the property that makes adoption and departure both cheap, and it is not negotiable"
  - "Evidence custody sits with the service, not the repo: a note may reference a verification, never constitute one. This is what ADR-0014's tokens are for, and it is why a third-party runner is a weaker fit than an owned one"
  - "The service writes the repo, so git becomes downstream. Direct human edits are surfaced as drift rather than merged; two-way sync is deliberately not attempted"
  - "Monotonic ID counters do not survive multi-party allocation and would need content-addressed identity with friendly aliases"
  - "Parking has a cost: if the thesis is right, the window is open now. That is accepted in exchange for evidence from the fleet"
related: [ADR-0014, ADR-0009]
supersedes: ""
superseded: ""
---

# An intent layer, not a git host

> **Status: `proposed`, and deliberately parked.** This records a direction and the reasoning behind it so the argument survives outside a chat transcript. It is not a plan, and nothing is scheduled against it. Accepting it means accepting the three pre-committed positions *if* the product is ever built — not a decision to build it.

## Context

Git hosting assumes a human wrote the diff. Both of its core surfaces follow from that: review is line-by-line, and provenance is *who committed*. With a human, the commit message is a fair proxy for intent because the human held the intent.

Agent-authored change breaks the assumption in both directions. The diff is often the *least* informative artifact available — a defect fixed on 2026-07-28 was one line in a `Content-Security-Policy` meta tag and meant "no inbox image has ever rendered"; the change beside it was ~300 lines of renderer and meant "the inbox is a tray now". And the intent lives in a specification the hosting platform cannot see, so what gets reviewed is a derivation with its premises missing.

The observable consequence is not that maintainers object to machines writing code. It is that **the cost of verifying a contribution now exceeds the cost of writing it**, so the rational response is to refuse the contribution. That is the problem worth attacking, and it is a problem about evidence, not about hosting.

## Decision

**Park the product.** Do not build it until [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]] has been in use across the fleet long enough to say whether typed evidence actually reduces unsupported claims. `project-os-bench` can answer that, and it is the cheap experiment that gates the expensive one.

If it is ever built, three positions are pre-committed.

### 1. Git is demoted, not replaced

Git becomes what the filesystem is to an IDE: real, authoritative, and not what you look at. The service writes it — one commit per intent transition, message derived from the note — and the repo remains a complete artifact that a clone fully reproduces.

Replacing the store would discard merge, bisect, blame, mirroring and every tool anyone owns, to fix problems that are not in the store. Jujutsu settles the argument empirically: it keeps git underneath, replaces the working model entirely, and is adopted *because* migration is not required.

The consequence to accept up front: git is **downstream**. Someone will edit the repo directly, and two-way sync between a generated repo and a hand-edited one is where systems of this shape usually die. Direct edits are detected and surfaced as drift. Less elegant, far more survivable.

### 2. The git host and the runner are adapters

Not GitHub. Not Forgejo. Adapters, with one shipped first because that is where the first users are.

This is the posture project-os already takes with editors: plain Markdown and YAML, Obsidian optional, no tool required. A product arguing that git hosting is the wrong model cannot require a git-hosting account, and it cannot rest its value on a vendor shipping the same features next quarter.

Forgejo is the current best fit for a self-hosted default — one Go binary, a few hundred MB, and GitHub-Actions-compatible CI in the same process.

### 3. Agents run on the user's machine

Decided by measurement, not preference. At 100 seats and three agent-hours per person per day — roughly 6,000 agent-hours a month — inference lands somewhere between **$30k and $90k per month**, against **~$350** for the entire rest of the infrastructure as a git-host-adapter service. Inference is 20–50× everything else combined.

It is also the better architecture. Agents need the developer's environment, credentials, and running application; today's verification of a UI defect required driving a live Electron process over CDP, which is not a thing a server does.

The service consumes results and produces evidence. It does not think.

## What the product would be, in one sentence

**The index and the verifier — not the host and not the runtime.**

Its one capability that a git host structurally cannot have is continuous checking of *claims against reality*: every ticked box in the graph, its evidence token, its revision, and whether that evidence still holds. Git hosts have no claims to check. That is the whole moat, it is the maintainer's actual complaint, and ADR-0014 is the prerequisite that makes it possible.

## Why parking is the right call

The costs argue for building — infrastructure is roughly $350/month at 100 seats, and perhaps 30–40% of the client already exists in `project-os-cockpit`. Six to nine engineer-months is the real price.

But the thesis rests on an untested premise: that typed, continuously-checked evidence makes reviewing agent-authored work materially cheaper. That is testable **this month, in eleven repos, for free**. If it is true, the hosted version has a foundation and a demonstration. If it is false, no amount of platform rescues it, and the six months would have been spent proving it the expensive way.

## Consequences

See frontmatter. The one to keep in view: parking is not free. If the thesis is right the window is open now, and this trades that risk for evidence — which is the same trade the rest of this system is built on, and it would be inconsistent to make it any other way.
