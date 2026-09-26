---
type: "[[change]]"
id: CHG-20260925-Snapshot-Lookup-And-Four-Drift-Checks
title: "One snapshot lookup for both YAML styles, and four drift classes caught by the validator"
status: merged
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["Edwin, 2026-09-25: 'Complete and test PHASE-0003 fully'"]
commit: ""
pr: ""
impacts: ["tools/scripts/snapshot-query.py", "tools/scripts/snapshot-slice.py", "tools/scripts/validate-docs.py", "docs/__templates__/SCHEMAS.md", "docs/INDEX.md", "tools/adapters/claude-code/ADAPTER.md", "tools/instructions/HOOKS.md", "tools/instructions/TESTING.md", "tools/instructions/README.md"]
issues: ["[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]", "[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently]]"]
features: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TST-0024]]", "[[TST-0025]]", "[[PHASE-0003-Prompting-Guide-Conformance]]"]
---

# One snapshot lookup for both YAML styles, and four drift classes caught by the validator

## Summary

An agent can look up any item with `python3 tools/scripts/snapshot-query.py <ID>`. It gets the same answer whether the snapshot is written in block or inline style, and the note's own answer when the snapshot has pruned the item. The session-start orientation names the command. `validate-docs.sh` now reports four kinds of drift that only an LLM sweep used to find.

## Impact

- Quoted snapshot values are now read with YAML's escapes (`\"`, `\u2019`, `''`), so the orientation and the lookup show the text the author wrote.

- No screen changed: scripts, the validator and documentation.

The new validator checks:

- FRONTMATTER-TYPO: a misspelt link field such as `elated:`. An error; 0 findings in the fleet.
- INDEX-COVERAGE: an index missing entries of its directory. Warns until 2026-12-24; 38 findings in 13 repos.
- FIELD-UNDOCUMENTED: a field the validator reads that SCHEMAS.md does not define. Warns until 2026-12-24; nine in each repo that has not merged the template's SCHEMAS.md.
- CITATION: a cited path or section that resolves nowhere. Warns until 2026-12-24; one in each other repo, fixed by the next sync.

The template also fixes the sources of most index findings: its `docs/INDEX.md`, and the CLAUDE.md template in `ADAPTER.md`. SCHEMAS.md now documents the nine fields.

Risk scan: no new `RISK-*`. No dependency, variable or path contract; `snapshot-query.py` imports two scripts in the same folder, both standard library only. Timed on your-trainer, the largest repo, on 2026-09-25: two runs each gave 28.4 and 29.0 seconds for the old validator and 28.3 and 29.4 for the new, so the new checks add no measurable time.

## Documentation Coverage (All Types Considered)

- features: updated (FEAT-0021)
- requirements: not-applicable
- tasks: new and done (TASK-0081, TASK-0163 to TASK-0167)
- issues: fixed (ISS-0052, ISS-0053)
- tests: new (TST-0024, TST-0025)
- workflows: not-applicable
- decisions: updated (ADR-0026, the drift re-measurement)
- risks: not-applicable
- changes: new (this note)
- snapshot: updated

## Follow-ups

- [ ] Each other repo clears its INDEX-COVERAGE, FIELD-UNDOCUMENTED and CITATION warnings before 2026-12-24: most go with a sync of the template and a merge of SCHEMAS.md.
- [ ] Edwin: whether to narrow the docs-audit drift dimension's brief, as ADR-0026's follow-up recommends.
