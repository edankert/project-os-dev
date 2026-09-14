---
type: "[[task]]"
id: TASK-0116
aliases: ["TASK-0116"]
title: "TAXONOMY.md says a surface is a screen by default and states the four rules once; surface.md points there and gains the capture-key map if ADR-0044 puts it on the note"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]"]
parent: "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"
effort: S
due: ""
depends: []
blocks: ["[[TASK-0117-A-Change-Note-Names-The-Screens-It-Changed]]", "[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
related: ["[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tests: []
---

# TAXONOMY.md states what a surface is

## What

A person writing a surface note reads, in one place, that a surface is a screen unless its `kind` says otherwise, and how to handle the four cases that confuse it. Today TAXONOMY.md lists the four `kind` values and says a surface is "a place in the product", which let the first large corpus use test categories.

## Definition of Done

- [x] ADR-0044 is accepted (or amended) before this starts. *(Accepted 2026-09-14.)*
- [x] `tools/instructions/TAXONOMY.md`, "`kind` (surfaces)", says `screen` is the default and states ADR-0044's four rules: a state is not a surface; a dialog, sheet or panel is a child with `parent:`; a check that walks several screens names their parent (or the screen it starts on); a screen placed differently per platform is one surface.
- [x] `docs/__templates__/surface.md` points at that section and restates none of it. Its "What it is" prompt asks where each platform places the screen.
- [x] `surface.md` and `SCHEMAS.md` gain the `gallery:` field Edwin chose on 2026-09-14: a list of `key` or `key:state` entries, for example `gallery: [equipment-hub, "equipment-hub-dataonly:data-only"]`. The validator accepts it.
- [x] TAXONOMY.md says the 12 to 15 surface target (from project-os-cockpit FEAT-0130) applies to top-level screens only, with children below.
- [x] `bash tools/scripts/validate-docs.sh` passes in the template.

## Steps

- [x] Write the four rules as one short paragraph each, with a your-trainer example for each (the equipment panel, the HR-zone interval sheet, a check crossing Workouts and the ride cockpit).
- [x] Update `surface.md` and, if needed, `SCHEMAS.md`.

## Notes

- [[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them|ISS-0050]] is about surface statuses living outside the validator. Check whether this edit makes it worse; do not fix it here.

## What landed, 2026-09-14

`TAXONOMY.md`, "`kind` (surfaces)", opens with the rule — a surface is a screen unless its `kind` says otherwise — and states ADR-0044's four rules under "The four rules", one paragraph each with a your-trainer example: the equipment panel in data-only mode, the HR-zone interval sheet as a child of the ride cockpit, a check that opens Workouts and then rides, and the equipment panel sitting in two different places on Android and iOS. The 12 to 15 target is named there as applying to top-level screens only.

`gallery:` got its own heading, "`gallery` (surfaces)", rather than a line inside the `kind` section, because a walk sheet's captures are a different question from what a surface is.

**`SCHEMAS.md` had no `surface.md` entry at all**, which is why the `gallery:` field had nowhere to be documented. One was written: naming, the four fields, and the reason `## Coverage` is not a list of checks.

The validator needed no change to accept `gallery:` — `validate-docs.py` has no frontmatter field allowlist, so an unknown key is simply carried. Checked by running it, not by reading the code: `bash tools/scripts/validate-docs.sh` is OK in all six repos with the field in their template.

[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them|ISS-0050]] is untouched and no worse: this edit adds no status vocabulary and moves none.
