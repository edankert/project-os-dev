---
type: "[[issue]]"
id: ISS-0049
aliases: ["ISS-0049"]
title: "The schema claims a refusal the shipped validator does not make"
status: triage
phase: "[[PHASE-0003]]"
severity: high
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
component: tooling
source: ["The ISS-0048 drift sweep, pass 11, run 2026-09-04 in a clean context over template 19ba330"]
related: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
tasks: []
tests: []
---

# The schema claims a refusal the shipped validator does not make

## Problem

`docs/__templates__/SCHEMAS.md` tells every project-os repo that seven frontmatter fields were removed from acceptance tests and that "the validator refuses each of them". The validator those repos actually run refuses none of them. Two different programs answer to the name "the validator", they disagree, and the schema describes the one almost nobody runs.

`tools/scripts/validate-docs.py` is the entrypoint that pre-commit, CI and `validate-docs.sh` all call. It has no list of removed fields and no check that rejects them; it still reads `mark:` off a note to decide whether a walked test is settled. `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py` does have the check, under `LEDGER_MOVED_FIELDS` — and it names twelve fields, not seven, having also swept in `section`, `ordinal`, `migrated_from`, `merged_from` and `burden`. The bundled copy is 3498 lines against the canonical 2827.

## Repro

```bash
cd ~/Dev/repos/project-os
grep -c LEDGER_MOVED_FIELDS tools/scripts/validate-docs.py                                   # 0 — the shipped entrypoint has no such check
grep -n  LEDGER_MOVED_FIELDS tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py   # 1941 — twelve fields
grep -n  "the validator refuses each of them" docs/__templates__/SCHEMAS.md                  # 219 — says seven
wc -l tools/scripts/validate-docs.py tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py
```

## Expected

One statement about what the validator refuses, true of the validator the repos run.

## Actual

The schema promises an enforcement that does not exist on the path every repo uses, so a note carrying `mark:` or `verdict_date:` passes pre-commit and CI while the schema says it cannot. A reader who trusts SCHEMAS.md writes notes the system silently accepts and the cockpit later rejects.

## Evidence

- `docs/__templates__/SCHEMAS.md:219` — "**Seven fields were removed** and the validator refuses each of them, *in a repo that keeps ledgers*".
- `tools/scripts/validate-docs.py:282-315` — `_SETTLED_MARKS` and `_acceptance_is_settled`, which read `fm.get("mark")`.
- `tools/cockpit/src/project_os_cockpit/validate_docs_bundled.py:1941-1952` — `LEDGER_MOVED_FIELDS`, twelve entries.

## Next Actions

- [ ] Decide which way the two validators converge: the canonical script gains the removed-field check, or SCHEMAS.md stops claiming an enforcement that lives only in the cockpit. Adding the check to the canonical script would start erroring on notes in downstream repos that have not migrated, so it lands under the grandfathering rule (`STATUSES.md`, "Grandfathering") if it lands at all.
- [ ] Decide whether the list is seven fields or twelve; the two copies disagree today.
- [ ] Settle the second half of the same divergence: `SCHEMAS.md:217` says `docs/releases/ledgers/` is "a directory the release skills create at the first release", and neither `release-prep/SKILL.md` nor `release-verification/SKILL.md` mentions the path, creates it, or defines a file format. Only the cockpit knows it.

## Sibling search

Sibling found: [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]], the sweep this came out of. Searched `docs/issues/` for: validator, cockpit, bundled, mark, ledger. This is not another restatement — it is one rule with two implementations that disagree, which is the failure ADR-0024 predicts when a copy is allowed to exist.

## Risk scan

One new hazard, recorded here rather than as a `RISK-*` because it is bounded by this issue: whichever way the decision goes, the canonical validator and the bundled copy drift again unless something checks them against each other. No new dependency, env var, path or credential.
