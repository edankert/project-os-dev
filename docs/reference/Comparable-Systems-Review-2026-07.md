---
type: "[[reference]]"
id: REFERENCE-COMPARABLE-SYSTEMS
aliases: ["Comparable systems review"]
title: "Comparable systems review (July 2026): project-os against the spec-driven-development generation and the formal requirements-management tools"
status: active
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
scope: "project"
source:
  - "https://github.com/github/spec-kit"
  - "https://github.com/Fission-AI/OpenSpec"
  - "https://kiro.dev/docs/steering/"
  - "https://github.com/bmad-code-org/BMAD-METHOD"
  - "https://github.com/MrLesk/Backlog.md"
  - "https://doorstop.readthedocs.io/en/v2.0/reference/item/"
  - "https://github.com/itsallcode/openfasttrace"
  - "https://strictdoc.readthedocs.io/"
  - "https://sphinx-needs.readthedocs.io/"
  - "https://arxiv.org/pdf/2606.27045"
related: [ADR-0016, ISS-0017, ISS-0018, ADR-0014, ADR-0010, ADR-0009]
---

# Comparable systems review, July 2026

## Purpose

A survey of systems occupying the same problem space as project-os, what each does better, and which of those differences are worth adopting. Conducted 2026-07-29 against `SNAPSHOT.yaml`, `CONTEXT.md`, `LIFECYCLE.md`, `TRACEABILITY.md` and `validate-docs.py` as they stood that day.

This is background material, not lifecycle state. Three items were filed out of it — [[ISS-0017-Review-Verdicts-Never-Expire]], [[ISS-0018-Traceability-Stops-At-The-Docs-Boundary]] and [[ADR-0016-Ceremony-Proportionate-To-The-Change]]. Everything else is recorded here so it is recoverable without repeating the research.

## The three families

**Agent-native spec frameworks** — the direct peers: markdown in git, driven by an LLM.

| System | Shape | Distinguishing idea |
|---|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit) | CLI + slash commands, broadest agent support | A **constitution** of governing principles; `/clarify` and `/analyze` as explicit pre-implementation gates; a template **override stack** |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Lightest weight; scored highest in a Feb 2026 independent 13-category evaluation | A **living spec** plus per-change **proposal folders** that archive on completion |
| [Kiro](https://kiro.dev/docs/steering/) (AWS) | VS Code fork, spec-driven in the IDE | **EARS notation** for requirements; **steering files** with three inclusion modes; natural-language agent hooks |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 12+ agent personas simulating an agile team | **Scale-adaptive levels 0–4** routing by complexity; expansion packs |
| [Backlog.md](https://github.com/MrLesk/Backlog.md) | Markdown task board, git-native | A **typed interface** — CLI with `--json`, MCP server, TUI kanban, web board — over the same markdown |

**Formal requirements-management tools** — twenty years older, no agent affordances, and they solved several problems project-os is currently rediscovering.

| System | Distinguishing idea |
|---|---|
| [Doorstop](https://doorstop.readthedocs.io/en/v2.0/reference/item/) | **Item fingerprints** (review invalidated by edit) and **suspect links** (child links invalidated when the parent changes) |
| [OpenFastTrace](https://github.com/itsallcode/openfasttrace) | **Coverage tags in source code**, revisioned; `oft trace` reports uncovered requirements; CI action fails the build |
| [StrictDoc](https://strictdoc.readthedocs.io/) | Bidirectional requirement-to-source links, browsable traceability graph, custom grammars via a real parser |
| [Sphinx-Needs](https://sphinx-needs.readthedocs.io/) | **Dynamic functions** computing field values at build time; typed extra fields with JSON Schema constraints |

**The critical literature** — Thoughtworks placing SDD in *Assess* rather than *Adopt* and insisting executable code remains the source of truth; [The Spec Growth Engine](https://arxiv.org/pdf/2606.27045) on spec-anchored, code-coupled, drift-enforced architectures; and the recurring 2026 community finding that the dominant failure is **silent spec-code drift**, with over-specification of small work close behind.

## Where project-os is ahead

Stated because most of the gaps below are cheap to close and these are not.

1. **Enforcement is a program, not a prompt.** Spec Kit's `/speckit.analyze` performs cross-artifact consistency checking by asking the model. project-os has ~48 named check codes in a 1,795-line validator wired into pre-commit and CI. Prompts do not fail builds.
2. **Test status stamped by execution** ([[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]]) has no equivalent in any system surveyed. Kiro, Spec Kit and OpenSpec all let the agent tick its own boxes — the exact failure mode ADR-0010 names.
3. **No permanent warning tier** ([[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]]) is a governance idea none of them have; the SDD tools have no severity model at all.
4. **Deferral as descoping** ([[ADR-0005-Deferral-As-Descoping|ADR-0005]]) — no comparable, in either family, has a concept of parked scope that cannot satisfy a parent.
5. **Derived state** ([[ADR-0009-Snapshot-Is-Generated|ADR-0009]]) — Backlog.md is nearest, but it derives a task board, not a full item graph with counters and metrics.
6. **The fleet is the unit.** Spec Kit supports many agents, per project. project-os is alone in governing ten repos from one template with divergence detection.

## The gaps, ranked

### Filed

**1. Review verdicts never expire** → [[ISS-0017-Review-Verdicts-Never-Expire]]. Doorstop's fingerprints and suspect links. The strongest single borrow, and probably a case of [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]]'s revision rather than a new mechanism.

**2. Traceability stops at the docs boundary** → [[ISS-0018-Traceability-Stops-At-The-Docs-Boundary]]. OpenFastTrace and StrictDoc reach into source; project-os's graph is closed over notes, so `implemented` is asserted by the party seeking it.

**3. No proportionate fast path** → [[ADR-0016-Ceremony-Proportionate-To-The-Change]]. BMAD's scale-adaptive levels and Thoughtworks' explicit caution. The one gap that is a design flaw rather than a missing feature.

### Not filed — groomable, in rough priority order

**A typed interface instead of hand-editing plus a validator.** Backlog.md exposes its markdown through a CLI (`--json` everywhere), an MCP server, a TUI board and a web UI, and *discourages hand-editing* to keep frontmatter well-formed. project-os does the opposite: hand-editing is the interface and a large validator catches the resulting malformation afterward. A `pos task create --parent FEAT-0019` would make a whole class of checks structurally impossible — which is [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]'s own argument ("the failure it detects becomes structurally impossible") applied to note *creation* rather than snapshot state. project-os has not followed its own principle there. Note the tension with the Obsidian cockpit, which is a read/navigate surface rather than a write surface; a CLI would be the write side.

**EARS notation for acceptance criteria.** project-os specifies exhaustively how a requirement *moves* — advancement, criteria of record, staleness, premature-implementation — and says nothing about how one is *phrased*. EARS (from Rolls-Royce, adopted by Kiro) gives a closed grammar: ubiquitous, event-driven `WHEN … THE SYSTEM SHALL`, state-driven `WHILE`, optional `WHERE`, unwanted `IF … THEN`. It makes testability mechanically checkable and maps one criterion to one `TST-*`. OpenSpec reaches the same place with `SHALL` plus WHEN/THEN scenario blocks. A validator check that `acceptance:` entries match an EARS shape is a small addition to existing REQ-BOXES machinery. Risk: it can become ceremony on requirements that are policies rather than behaviours — see the ISS-0005 residue.

**A proposal state for requirement changes.** OpenSpec keeps a living spec and represents each change as a reviewable proposal that archives on completion. project-os amends requirements in place with `supersedes:` and narrates afterward in a `CHG-*`. So there is no artefact representing *"proposed change to a requirement, reviewable before it takes effect"* — and in a system where the LLM edits the requirements, that is precisely where a human gate belongs. Do not copy the folder shape; the `DES-*` type from [[FEAT-0019]] is the natural place for a proposal state to grow.

**Schema as data, not as prose plus Python.** Sphinx-Needs declares typed fields with JSON Schema constraints and computes derived values at build time. project-os states its schema as prose in `docs/__templates__/SCHEMAS.md` and restates it in validator Python. That is the same duplication class [[REQ-0018]] eliminated for state rules, still live between the schema document and the code that enforces it — and the ISS-0011→ISS-0015 chain is exactly what that class of duplication produces when it goes unnoticed.

**A layered template override stack.** Spec Kit resolves templates through project overrides → presets → extensions → core defaults, so a repo customises *without* diverging. project-os's MANIFEST detects baseline divergence and treats it as drift to reconcile. Layering is the better model for a template distributed to ten repos, and would remove a recurring class of sync friction.

**Steering-file inclusion modes.** Kiro loads guidance in three modes: always, manual (`#file-name` reference), and conditional (`inclusion: fileMatch` with a glob). project-os's `CLAUDE.md` splits into always-active core rules and "read when relevant" reference instructions — the same idea, but the conditional tier is prose advice rather than a mechanism, so it depends on the agent choosing to read. Worth revisiting whenever the adapters are regenerated; may be partly solved already by Claude Code skills.

## Judgement calls in this review

Recorded so a later reader can disagree with them specifically.

- **The ceremony critique is aimed at the rule, not at this repo's volume.** 210 notes for ~3,700 lines of Python looks damning, but this repo's *product* is the documentation system, so much of that volume is deliverable rather than overhead. The defensible claim is narrower: there is no declared fast path, and an undeclared exception cannot be audited.
- **ISS-0011 → ISS-0015 is not evidence of ceremony cost.** Five review rounds over a status-table guard looks like the ceremony signature, but that chain was a deliberate calibration experiment (`TASK-0077`) with a known answer. It was excluded from the argument.
- **ISS-0018 may not be worth building.** Coverage tags tax source files and go stale on rename, and the policy/convention requirements have no implementing code at all. It is filed because the hole is real and structural, not because the fix is obviously correct.

## Maintenance

A dated snapshot of a fast-moving field, not a living document. If it is revisited, re-check: whether OpenSpec's proposal model has been adopted more widely, whether any agent-native system has grown code-side traceability, and whether Thoughtworks has moved SDD out of *Assess*. Supersede rather than edit in place.
