---
type: "[[issue]]"
id: ISS-0018
aliases: ["ISS-0018"]
title: "The link graph stops at the docs boundary: no requirement names the code that implements it, so `implemented` is asserted by the agent seeking the transition and an unimplemented requirement is undetectable"
status: open
severity: medium
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: tooling
source: ["landscape review 2026-07-29: OpenFastTrace coverage tags, StrictDoc requirement-to-source links"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0007, ADR-0010, ADR-0014, REQ-0006]
tests: []
---

# The link graph stops at the docs boundary

## Problem

`TRACEABILITY.md` specifies the required links for every note type. Every one of them points at another note. The graph is complete and closed — and it never touches source code.

The only field that reaches outward is `external:` on a task (e.g. `TASK-0074`, `external: "../project-os-cockpit/docs/issues/ISS-0026-Bundled-Validator-Drift.md"`), which is a path to *another note in another repo*, unvalidated as a link and pointing at documentation rather than implementation.

The consequence is specific and load-bearing. `STATUSES.md` gives requirement terminality as: *"every acceptance criterion ticked-with-evidence or reconciled — never gated on tests (ADR-0007)"*, written by *"agent, at feature close-out"*. So `implemented` rests entirely on ticked boxes plus evidence prose. There is no artefact anywhere in the system that connects `REQ-0021` to a line of code, and therefore no check that can report **"this requirement is terminal and nothing implements it."**

This is the assertion problem [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] named, at the level of the requirement rather than the test. ADR-0010 fixed it for `TST-*` by having the runner write the status. `implemented` has no equivalent instrument, and it is the status the project uses *"to report what still needs building"* (QUALITY.md).

## Expected

A requirement with no implementing code is a finding, produced by a tool, not a judgement the closing agent is trusted to make about its own work.

## Actual

Nothing looks. A requirement can reach `implemented` with every box ticked, every evidence clause honest-looking, and no code written — and every gate in the system passes, because every gate reads notes.

## Prior art

[OpenFastTrace](https://github.com/itsallcode/openfasttrace) is the minimal version and the closest fit: coverage tags in source comments name the specification item they cover, `oft trace` walks both sides and produces a report of uncovered items, and the CI action fails the build on a gap. The tag carries a revision, so coverage of a *changed* requirement reports as outdated rather than silently green — the same revision idea as [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]], arrived at independently for the code side.

[StrictDoc](https://strictdoc.readthedocs.io/) does the same with bidirectional requirement-to-source links plus a browsable traceability graph. [Sphinx-Needs](https://sphinx-needs.readthedocs.io/) covers it with dynamic functions that compute a requirement's status from its linked items at build time.

All three predate the agent-native tools by a decade, and none of the agent-native comparables ([Spec Kit](https://github.com/github/spec-kit), [OpenSpec](https://github.com/Fission-AI/OpenSpec), Kiro, [Backlog.md](https://github.com/MrLesk/Backlog.md)) has this either. It is the clearest thing the formal requirements-management world has that the whole spec-driven-development generation dropped.

## Scope caveat

`project-os-dev` is a documentation repo tracking a documentation template — its "code" is the ~3,700 lines under `tools/scripts/`, and its requirements genuinely are about that code, so it can dogfood this. But the value is overwhelmingly in the **fleet** repos with real application code, and the design must be judged there. A mechanism that only works in a repo whose product is documentation is not worth building.

The second caveat is cost. Coverage tags mean editing source files to carry documentation IDs, which is a real tax on the code and an invitation to stale tags. `ISS-0005`'s finding is relevant here: of 23 feature-less requirements, 9 are a genuine residue — 5 policies and 3 conventions. Policies and conventions have no implementing line of code and never will, so any coverage rule needs an explicit "not code-covered" class or it will report a permanent false-positive population — which [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] forbids parking at warning severity.

## Next Actions

- [ ] Decide whether the link lives in code (OFT-style tags, discoverable by grep) or in the note (a `covers:`/`sources:` list of paths + symbols, keeping source files clean at the cost of drifting silently on rename).
- [ ] Decide the "not code-covered" class for policy/convention requirements, and whether it is a status, a field, or a requirement type. See [[ISS-0005-Feature-Less-Requirement-Triage]] for the population.
- [ ] Prototype against one fleet repo with real application code before touching the template.
- [ ] Reconcile with [[ADR-0014-Evidence-Is-Typed-And-Checkable|ADR-0014]]: a coverage tag is arguably an evidence token, and if so this is a sixth token rather than a new subsystem.
