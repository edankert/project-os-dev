---
type: "[[task]]"
id: TASK-0045
aliases: ["TASK-0045"]
title: "External tool wiring: prettier, markdownlint, yamllint, lychee, mutation tools"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-07-17
updated: 2026-07-17
verification_waiver: "config-only change set; verified mechanically — pre-commit + CI now run generate-adapters --check; lychee workflow is schedule/dispatch-only"
source: []
parent: "[[FEAT-0010-Template-Completeness-Program]]"
fixes: []
effort: S
due: ""
depends: [TASK-0041]
blocks: []
related: []
tests: []
waiver_expires: 2026-10-23

---

# External tool wiring

## Definition of Done

- [x] `.prettierrc` with `proseWrap: never` ships in the template (MARKDOWN.md already mandates the behavior); markdownlint + yamllint configs ship alongside.
- [x] Lychee external-URL link check added as a CI job (internal links stay with validate-docs).
- [x] TESTING.md names concrete mutation-testing tools per stack (mutmut / Stryker / cargo-mutants) for the `mutation_score` field.
- [x] New config files added to SYNCING.md's template-owned list.
