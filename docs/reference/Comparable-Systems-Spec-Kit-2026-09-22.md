---
type: "[[reference]]"
id: REFERENCE-SPEC-KIT-2026-09
aliases: ["Spec Kit deep read", "Spec Kit 2026-09"]
title: "Comparable systems deep read (September 2026): GitHub Spec Kit at v1.0.9, read from its own templates rather than its documentation"
status: active
owner: user:edwin
created: 2026-09-22
updated: 2026-09-22
scope: "project"
source:
  - "https://github.com/github/spec-kit"
  - "https://github.github.com/spec-kit/"
  - "https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/"
  - "https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html"
  - "https://developer.microsoft.com/blog/spec-driven-development-spec-kit/"
related: ["[[Comparable-Systems-Review-2026-07]]", "[[Comparable-Systems-Sighting-Productics-2026-09-20]]", "[[ISS-0079-Converge-Pass]]", "[[ISS-0080-Ambiguity-Markers]]", "[[ISS-0081-Observable-Criteria]]", "[[ISS-0082-Reviewer-Owned-Notes]]", "[[ISS-0083-Override-Layering]]"]
---

# Comparable systems deep read, September 2026: GitHub Spec Kit at v1.0.9

## Purpose

A close read of one system the July survey already covers in a table row. [[Comparable-Systems-Review-2026-07]] says to supersede rather than edit in place, so this is filed beside it, the same way [[Comparable-Systems-Sighting-Productics-2026-09-20]] was.

It exists because Spec Kit changed substantially between July and now, and because July's row named one borrow — a layered template override stack — that was left unfiled. Five items were filed out of this read: [[ISS-0079-Converge-Pass]], [[ISS-0080-Ambiguity-Markers]], [[ISS-0081-Observable-Criteria]], [[ISS-0082-Reviewer-Owned-Notes]] and [[ISS-0083-Override-Layering]]. All five are parked at `triage` on Edwin's instruction of 2026-09-22; nothing here is scheduled.

Read on 2026-09-22 from the repository's own `templates/`, `templates/commands/`, `scripts/` and `docs/` at `main`, not from the marketing pages.

## What changed since the July survey

July recorded Spec Kit as "CLI + slash commands, broadest agent support", distinguished by a constitution, `/clarify` and `/analyze` gates, and a template override stack. Four things are new since then.

1. **`/speckit-converge`** — a post-implementation pass that appends unbuilt work as new tasks. It did not exist in July and is the strongest idea in the toolkit.
2. **`/speckit-checklist`** — reviewer-owned requirements-quality checklists that the implementing command reads as a gate and is forbidden to write.
3. **Extensions, presets and bundles** with public catalogs (`extensions/catalog.json`, `bundles/catalog.json`, plus `.community.json` counterparts). The override stack July described is now a full composition model with declared precedence.
4. **Git is optional.** The active feature is whatever `.specify/feature.json` names, not the checked-out branch. Branches moved into an opt-in `git` extension.

Scale, measured from the GitHub API on 2026-09-22: 138,297 stars, 12,394 forks, 302 open issues, MIT, created 2025-08-21. Releases run roughly weekly; v1.0.9 shipped 2026-09-21.

## How it reaches a repository

Spec Kit is a Python CLI on PyPI, installed globally and run once against a repo. It is a code generator, not a library.

```bash
uv tool install specify-cli
specify init my-project --integration copilot     # new repo
specify init --here --force --integration <key>   # existing repo
```

What `init` writes:

| Path | Holds |
|---|---|
| `.specify/memory/constitution.md` | The project's governing principles, versioned with Ratified and Last Amended dates |
| `.specify/templates/overrides/` | Per-repo artifact overrides, highest precedence |
| `.specify/presets/` | Installed preset packs |
| `.specify/extensions.yml` | Hook bindings, read by the command prompts themselves |
| `.specify/feature.json` | Which feature directory is active |
| `scripts/bash/`, `scripts/powershell/`, `scripts/python/` | The same six helpers in three languages, parity-tested in the project's own suite |
| agent-specific command files | `.github/skills/*/SKILL.md` for Copilot; roughly thirty integration keys, all generated from one source |
| `specs/###-feature-name/` | Per feature: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `tasks.md`, `checklists/requirements.md` |

The workflow is nine commands. `/speckit-constitution` runs once per project; then `specify → clarify → plan → checklist → tasks → analyze → implement → converge`, with the short path dropping clarify, checklist and analyze. Three extension families sit beside it: bug (`assess`/`fix`/`test`), idea assessment (`intake`/`research`/`define`/`shape`/`decide`), and git.

## The difference that matters

Spec Kit asks how one feature gets built correctly from a written intent. project-os asks what is true about a whole project and how that stays true across hundreds of items. Four consequences follow.

**The unit of organisation is a folder, not an item.** Spec Kit's unit is `specs/007-csv-export/`. project-os's unit is an item with a stable ID in a project-wide graph — FEAT, REQ, ISS, ADR, TASK, RISK, TST, CHG, PHASE — with links a validator enforces. This repo carries 239 feature notes, 79 issues and 34 decisions, each addressable from anywhere. Spec Kit's equivalent is 239 folders with no edges between them, and its own documentation admits the cost: the flow-forward persistence model "risks scattered context across multiple directories".

**There is no project state.** `feature.json` names a directory. Nothing answers what is in flight, how many items exist, or what status anything holds. `SNAPSHOT.yaml` has no counterpart.

**Enforcement is prose addressed to the model.** This is the sharpest architectural difference and July already found it. Read `templates/commands/analyze.md`: the hook system is written as instructions telling the agent to open `.specify/extensions.yml`, parse it, find `hooks.before_analyze`, judge whether each hook is mandatory, and run it. A model that skims that paragraph skips the gate and nothing notices. project-os's `tools/adapters/claude-code/hooks/document-first-gate.sh` fires in the harness and blocks the edit whether or not the model read the rule.

**Verification is an LLM reading three files.** `/speckit-analyze` is explicitly read-only and advisory. `validate-docs.sh` is deterministic, wired into pre-commit and CI, and has an `--as-committed` mode.

## What is worth taking

Each of these is filed; the issue holds the argument and this section holds the evidence.

**A convergence pass** → [[ISS-0079-Converge-Pass]]. `/speckit-converge` runs after implementation. It reads spec, plan and tasks as the sole statement of intent, inspects the code as it stands, works out what is still unmet, and appends the remainder as new tasks under a `## Phase N: Convergence` heading. Its operating constraints are strict: append-only, never rewrite or renumber an existing task, never touch spec or plan, never edit code, and when the code already satisfies everything leave `tasks.md` byte-for-byte unchanged with no empty header. You loop implement and converge until it returns clean. project-os has nothing that re-derives remaining work from requirement text against the code. Close-out is a checklist the agent walks; independent review is adversarial but bounded to one feature packet; the validator checks structure and never meaning.

**Ambiguity as a marker that survives** → [[ISS-0080-Ambiguity-Markers]]. The spec template leaves `[NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]` inline wherever intent is unclear. `/speckit-clarify` then scans against a fixed taxonomy — functional scope, domain and data model, interaction flow, non-functional attributes, integrations, edge cases, constraints — asks at most five targeted questions, and writes the answers back into the spec. project-os makes the same judgement once, at intake, and leaves no trace when it decides an ambiguity is tolerable.

**Observable outcomes separated from system behaviour** → [[ISS-0081-Observable-Criteria]]. The spec template mandates two numbered sections: `FR-###` functional requirements ("System MUST validate email addresses") and `SC-###` success criteria, required to be technology-agnostic and measurable ("Users can complete account creation in under 2 minutes"). `/speckit-analyze` builds a coverage inventory keyed on those identifiers and reports requirements with no task and tasks with no requirement. It deliberately excludes post-launch business metrics from the buildable set.

**An artifact the implementing agent may read but not write** → [[ISS-0082-Reviewer-Owned-Notes]]. `templates/checklist-template.md` states that `[x]` means a reviewer confirmed a requirements-quality criterion, that it does not mean implementation is complete, and that `/speckit-implement` reads the checkbox state as a gate and must not modify the markers.

**Layered composition instead of divergence detection** → [[ISS-0083-Override-Layering]]. Artifacts resolve through project overrides, then extensions, then presets, then built-ins, with `wrap`, `prepend` and `append` strategies for combining rather than replacing, and hooks stacking additively rather than winner-takes-all. This is July's unfiled groomable, now filed, and the new catalog layer makes the case stronger than it was.

## What it lacks

1. **No decision record.** There is no ADR type. The constitution holds standing principles; a one-off architectural choice with its rationale and rejected alternatives lives in `plan.md` inside one feature folder, where the next feature will not find it.
2. **No project life beyond features.** Issues are an extension. There are no risks, no releases, no change notes and no phases.
3. **Persistence is a policy handed back to the user.** `docs/concepts/spec-persistence.md` names three models — flow-back, flow-forward, living spec — and tells the team to pick one and document the choice. project-os answers the same question once, in its lifecycle rules.
4. **Tests are optional by default.** `templates/tasks-template.md` says outright that tests are only included if the specification explicitly requests them. A feature can reach completion with no verification artifact. project-os gates a terminal status on passing `[[test]]` notes.
5. **The overhead is unmeasured.** The one public hands-on account, [Scott Logic, November 2025](https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html), rebuilt a 689-line feature and produced 2,577 lines of markdown — 3.7 lines of document per line of code — at 33.5 minutes of agent time plus 3.5 hours of human review, against 8 plus 15 plus 9 minutes building the same feature iteratively, with a trivial uninitialised-variable bug shipping anyway. Spec Kit publishes no counter-evidence.
6. **Churn.** The `--ai` flag family was removed at v0.10.0 and older walkthroughs show commands that no longer run. Weekly releases against 138,000 users is a lot of moving ground.

## Judgement calls in this read

Recorded so a later reader can disagree with them specifically.

- **The Scott Logic figure is one data point and it is not clean.** The author rebuilt a feature they had already built, on a greenfield slice, which is the case most favourable to the iterative comparison. It is quoted because it is the only published measurement, not because it settles anything. The honest position is that neither Spec Kit nor project-os has a payoff measurement, and after [[PHASE-0008-Measured-Note-Ranking]] the cost of getting one is known.
- **Five items is more than this read justifies scheduling.** They are filed so the reasoning survives, not because all five should be built. [[ISS-0081-Observable-Criteria]] and [[ISS-0082-Reviewer-Owned-Notes]] are the two most likely to turn out to be ceremony on a system that already has acceptance criteria and owners.
- **The prose-hooks criticism is about Spec Kit's architecture, not its quality.** Their command templates are careful, and the hook protocol even tells the agent to report a parse failure rather than skip silently. The point is that a careful prompt and a failing build are different kinds of guarantee.
- **`/speckit-converge` is untested here.** It is read from its command definition, which is a specification of intended behaviour. Nobody has run it.

## Maintenance

A dated deep read of one entrant, not a living document. Supersede rather than edit in place, per [[Comparable-Systems-Review-2026-07]].

If it is revisited, re-check whether `/speckit-converge` survived contact with real projects, whether anything in the toolkit grew a cross-feature graph, and whether the extension catalog attracted third-party publishers or stayed a GitHub-only shelf.
