---
type: "[[issue]]"
id: ISS-0059
aliases: ["ISS-0059"]
title: "A new project starts with no acceptance ledger, so its first verdict takes the pre-migration write path — the one kept for repositories that have not migrated, which a project created today has not"
status: triage
phase: ""
severity: medium
owner: user:edwin
created: 2026-09-06
updated: 2026-09-06
component: templates
source: ["Edwin, 2026-09-06, recording the first acceptance verdict in a project initialised from the template three days earlier: 'why did this happen for a new project, is this an issue with the project-os functionality, what do we need to do to fix this?'"]
related: ["[[project-os-cockpit#ISS-0285]]", "[[project-os-cockpit#ISS-0286]]", "[[project-os-cockpit#ADR-0037]]"]
tasks: []
tests: []
---

# A new project starts on the pre-ledger write path

## Problem

**The template ships `docs/releases/` with a README and no `ledgers/` directory.** A verdict on an acceptance walk is an event in `docs/releases/ledgers/WORKING-<platform>.json`, so a project that has none has nowhere to put one.

The tool then falls back to the path it keeps for repositories that have not migrated to ledgers. A project created this week has not migrated anything, so it lands there by default — and that path has a different verdict vocabulary, which is where it goes wrong ([[project-os-cockpit#ISS-0285]]).

## Measured

`project-os-deck` was initialised from this template on 2026-09-06. Three days later it had six acceptance notes, no `docs/releases/ledgers/` directory, and every attempt to record a verdict was refused. The person recording it lost a page of written reasoning.

## Why this is the template's half

The cockpit's half is that the dialog offers verdicts its write path will refuse. The template's half is prior: **a new project should not begin on a compatibility path at all.** Nothing in the initialisation says a ledger is needed, nothing creates one, and nothing fails until somebody walks their first check — which is often weeks later, and by then it reads as a tool bug rather than a missing file.

## Options

1. **Ship `docs/releases/ledgers/` with a README**, the way `docs/issues/` and `docs/tests/` are shipped: the directory exists, empty, and explains what goes in it. Smallest change, and it makes the shape discoverable before anything needs it.
2. **Have the first verdict create the ledger**, which is the cockpit's change rather than the template's, and leaves the question of what platform to name.
3. **Ask at initialisation** what surfaces this project is verified on, and write the ledgers then. Most informative, most friction.

Option 1 is recommended, and it composes with either of the others.

## What the platform should be called

Related but separate: [[project-os-cockpit#ISS-0286]]. A project with one codebase should record its suite once, against the application, and keep per-operating-system ledgers for the few checks that are genuinely about an operating system. If the template ships an example, it should show that shape rather than an operating-system name, or every new project will copy the wrong default.
