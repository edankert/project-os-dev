---
type: "[[issue]]"
id: ISS-0045
aliases: ["ISS-0045"]
title: "Nothing says a review or design deliverable is filed in the repo"
status: open
phase: "[[PHASE-0003]]"
severity: low
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: docs
source: ["[[Prompting-Guide-Review-2026-09-03]]", "Edwin, 2026-09-03, in session"]
related: ["[[ISS-0040-Standing-Documents-Have-No-Manifest-And-No-Freshness-Signal]]", "[[FEAT-0025-Writing-Rules-For-The-Final-Message-And-Length-Limits]]", "[[FEAT-0019-Design-Note-Type]]"]
tasks: []
tests: []
---

# Nothing says a review or design deliverable is filed in the repo

## Problem

When the LLM writes a document for a person, such as a review, a report or a design, nothing in the template says where it lands. Claude Code's own harness tells the model to publish a claude.ai page, and that is where the 2026-09-03 prompting-guide review went first. The repo copy at [[Prompting-Guide-Review-2026-09-03]] was made afterwards, by hand, when Edwin asked.

> **As reported.** "can we make it so the LLM always provides the review/design documents in the project and ideally shows them through the cockpit?"

The display side already exists. The cockpit lists `reference` notes in its References group and frames a `design` note's HTML asset in its design bench. What is missing is the rule that puts the document there.

There is a second, smaller gap. The cockpit serves an HTML asset only for a design the register knows (`tools/cockpit/src/project_os_cockpit/server.py`, the `/design-asset/` route). It refuses any other file under `docs/` by path, deliberately, because serving arbitrary HTML from the docs root is an attack surface. So a rich HTML deliverable can be shown in the cockpit only as a design note, or after the cockpit learns to accept an `asset:` field on reference notes under the same sandbox.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -n "docs/reference" tools/instructions/LIFECYCLE.md tools/skills/close-out/SKILL.md tools/instructions/WRITING.md
```

Nothing instructs filing a deliverable. `docs/reference/README.md` describes the area as a place for material that arrives from elsewhere, not as the home for what the agent produces.

## Expected

One close-out rule in the template: a document written for a person lands in `docs/reference/` as a `reference` note, in Markdown, and any page published outside the repo is a copy whose URL goes in the note's `source:`. The cockpit then shows it in References with no code change, and Obsidian, git diff, the validator and the docs audit all see it.

Optionally, and in `project-os-cockpit` rather than the template: the design-asset route also accepts an `asset:` on a `reference` note, with the same sandbox and the same self-contained-HTML constraint the design-authoring skill states. Markdown should stay the record either way.

## Actual

The rule is absent. This repo already follows the practice by hand: `docs/reference/` holds two earlier reviews (`Comparable-Systems-Review-2026-07.md`, `Intake-Quality-Without-Reading-2026-07-29.md`) and now a third. A convention held by one person's habit is not a rule the next session will follow.

## Evidence

- `docs/reference/` in this repo, three review notes filed by hand.
- The cockpit's References group and `/design-asset/` route, read on 2026-09-03.
- The 2026-09-03 review's first home was https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc, not the repo.

## Next Actions

- [ ] Add the one-sentence rule to `tools/instructions/LIFECYCLE.md` "Close-out" and to `tools/skills/close-out/SKILL.md`, beside the change-note step. Sequence it with [[TASK-0090]] and [[TASK-0098]], which edit the same file.
- [ ] Decide whether the cockpit should frame HTML assets on reference notes. If yes, file it in `project-os-cockpit` and link the issue here.
- [ ] Add `docs/reference/` to the docs-audit stale-reference sweep so filed deliverables are checked like other notes (relates to [[ISS-0040-Standing-Documents-Have-No-Manifest-And-No-Freshness-Signal]]).

## Sibling search

No sibling found (searched `docs/issues/` for: deliverable, docs/reference, artifact, cockpit). [[ISS-0040-Standing-Documents-Have-No-Manifest-And-No-Freshness-Signal]] is adjacent, since reference notes are the population it measures, and is linked rather than merged.

## Risk scan

Run against the LIFECYCLE.md triggers. No new risks: prose rule only. The optional cockpit change would widen a served-file surface and would carry its own risk scan in that repo.
