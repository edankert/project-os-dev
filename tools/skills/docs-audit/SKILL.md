---
type: skill
id: SKILL-DOCS-AUDIT
status: active
owner: group:maintainers
created: 2026-07-05
updated: 2026-09-04
tags: [skills, audit, consistency]
---

# Skill: Docs audit (cross-document consistency, one bounded round)

## Why this exists
Documentation-as-database systems accumulate cross-document defects — stale references, schema mismatches between notes, statuses that drifted apart — and single-file review cannot detect them *by construction*: each file looks fine on its own. This skill is the periodic full-graph sweep that catches what per-edit checks miss. It used to claim such systems converge after several rounds; twelve rounds over this template did not converge, which is why the audit is now one bounded round on a cadence rather than a loop (ADR-0026).

## When to use
- On a cadence: during backlog grooming, before a release (`../release-prep/SKILL.md`), and after any large import/merge/sync.
- After running `../../scripts/sync-project-os.sh` (template sync can orphan references).
- When `tools/scripts/validate-docs.sh` passes but behavior suggests the docs are lying (the validator checks structure, not meaning).

## Inputs
- `../../../SNAPSHOT.yaml` and the full note graph under `../../../docs/`.
- `tools/scripts/validate-docs.sh` output (run it first — never spend LLM effort on what the validator catches mechanically).

## Outputs
- Fixed notes/snapshot entries for every confirmed inconsistency.
- `ISS-*` notes (status `triage`) for inconsistencies that need human judgment to resolve.
- An audit record: a short `CHG-*` note when the audit changed anything, stating rounds run and defect counts per round.

## Audit dimensions (each pass covers all of these)
1. **Mechanical baseline**: `bash tools/scripts/validate-docs.sh` must pass before and after the audit.
2. **Stale references**: prose (not just frontmatter) mentioning files, paths, IDs, commands, or flags that no longer exist. This is empirically the largest defect class in systems like this.
3. **Cross-note contradiction**: two notes describing the same behavior differently (e.g. a `CHG-*` says a path moved, a `WF-*` still documents the old path; a feature note claims a capability its open `ISS-*` says is broken).
4. **Schema/contract mismatch**: notes that reference each other's fields or artifacts inconsistently (a `TST-*` entrypoint that doesn't match the workflow it verifies; a `REQ-*` acceptance criterion no linked test actually checks).
5. **Status semantics**: items whose status is technically allowed but semantically wrong (an `open` risk whose trigger condition disappeared; a `passing` test whose entrypoint no longer exists).
6. **Instruction/template drift** (template repos): instruction files, templates, and `SCHEMAS.md` describing different shapes for the same note type, and any normative rule stated in full in more than one file. The rule this dimension checks is project-os-dev ADR-0024, carried by REQ-0027: every normative rule is stated in exactly one file and every other document links to it. A restatement is a copy the next amendment can miss (four issues in fourteen months: ISS-0006, ISS-0041, ISS-0042, ISS-0043). The fix is always to delete the copy and link, never to correct the copy. This dimension runs at each backlog-grooming pass and before each release, one bounded round each time (ADR-0026).

## Checklist

**The audit is one round. It does not repeat until clean** (ADR-0026).

1. Run the mechanical validator; fix anything it reports first. Never spend a pass on what a check catches.
2. Run **three passes in parallel, at one commit**, each in its own clean context. Each pass sweeps the full graph across all six dimensions above, cross-file rather than file-by-file: follow each item's links outward and check that both ends agree.
3. **Brief each pass with the domain and the rule, never with what an earlier pass found.** A pass handed the previous findings confirms the previous findings: one clean pass here was followed by a pass that re-read the same corpus without the table and found 21 defects.
4. **Union what the passes report. Do not filter by agreement.** Passes sample different parts of a large corpus, so overlap measures sampling, not truth — two passes at adjacent commits here found 25 findings each and shared almost none, including two severe defects that one pass each found alone.
5. **Verify every finding against its reproduction before fixing it.** A finding arrives with a command or a file:line that demonstrates it; run that, and discard what does not reproduce. This is what controls false positives, and it is the step agreement was supposed to do and cannot.
6. Fix what is confirmed and unambiguous. File an `ISS-*` for anything needing a decision, and **do not decide it inside the sweep**.
7. **Record the residue and stop.** What was found and not fixed goes on the issue, with why. Do not start another round: a second round on the same corpus produces more findings and fewer true ones per finding.
8. Record the audit in a `CHG-*` note if anything changed (passes run, found, confirmed, fixed, residue).

What one round missed is caught by the cadence in "When to use", not by re-running now.

## What the sweep hands back
Two lists, and only the second is for a person:
- **Fixed** — confirmed findings, already applied.
- **Decisions owed** — each as an `ISS-*`, because the answer changes what gets built and only the owner can give it.

Findings themselves are not a human queue. A reviewer that reports 25 items per pass will exhaust the reader long before it exhausts the corpus, and a reader who stops evaluating is worse than no reader.

## Independence recommendation
Run the audit in a clean context: a session that has not been maintaining these docs. The rule is stated once, in `../../instructions/QUALITY.md` "Independent review (clean-context)", and `../independent-review/SKILL.md` explains why. The maintaining session normalised its own drift into the graph; a fresh context reads the notes as they are, not as they were intended.
