---
type: "[[task]]"
id: TASK-0166
aliases: ["TASK-0166"]
title: "A backticked repo path or a cited section heading that resolves nowhere is reported"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["Edwin, 2026-09-25: 'Complete and test PHASE-0003 fully'"]
parent: "[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]"
effort: M
due: ""
depends: []
blocks: []
related: []
tests: ["[[TST-0025]]"]
---

# A backticked repo path or a cited section heading that resolves nowhere is reported

## Definition of Done
- [x] Backticked paths in instruction and skill files that look like repo paths are resolved against disk, relative to the citing file and to the repo root — CITATION; also the adapter, agent and template folders. Skipped: placeholders, context-relative paths, a project's own `docs/` content, and `_OPTIONAL_CITATIONS`.
- [x] A cited section (`FILE.md`, "Heading") is resolved against that file's headings — and its bold lead-ins, backticks ignored.
- [x] Measured over the fleet first — two real findings in the template, both fixed: TESTING.md cited SCHEMAS.md's walk-order section by a heading that had changed, and instructions/README.md used `scripts/build.sh` as an example, which reads as a dead citation where a repo has `scripts/`. One finding in each other repo (the TESTING.md one), so it warns until 2026-12-24.
- [x] A harness asserts an unresolved path and an unresolved heading are reported and resolvable ones are not, and a mutation removing the check fails it — TST-0025, D5 to D7. The harness also caught a scoping bug: a `tools/...` path was skipped because `docs/tools/...` landed under `docs/`.

## Notes
ISS-0052 also names "quoted sentences that appear in no file" and bare `ADR-####` ids that mean different decisions per repo. The bare-id case is already covered by CONTEXT.md's rule that an upstream decision is cited as `[[project-os-dev#ADR-####]]`; quoted-sentence matching is prose inference and is out of scope for a mechanical check.
