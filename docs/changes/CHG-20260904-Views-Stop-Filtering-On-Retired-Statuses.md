---
type: "[[change]]"
id: CHG-20260904-Views-Stop-Filtering-On-Retired-Statuses
aliases: ["CHG-20260904-Views-Stop-Filtering-On-Retired-Statuses"]
title: "Obsidian views stop filtering on retired statuses, and eleven more rules go back to one home"
status: merged
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
source: ["The ISS-0048 drift sweep, pass 11, run 2026-09-04 in a clean context over template 19ba330"]
commit: "acdcccb, 7c13209, e2bee28"
pr: ""
impacts: ["docs/__bases__/", "tools/instructions/", "docs/__templates__/SCHEMAS.md", "tools/adapters/claude-code/hooks/", "tools/scripts/validate-docs.py"]
issues: ["[[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File]]", "[[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make]]", "[[ISS-0050-Surface-Statuses-Live-Outside-The-File-That-Enforces-Them]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]", "[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]"]
---

# Obsidian views stop filtering on retired statuses, and eleven more rules go back to one home

## Summary

Anyone who opened a project-os repo in Obsidian saw an empty "Features (Open)" table. The view filtered on `in-progress` and `in-review`, and PHASE-0002 renamed those statuses to `doing` and `review` seven weeks ago. "Issues (Open)" filtered on three more values that no longer exist. The shipped views now use the vocabulary `STATUSES.md` actually defines, and the same retired words are gone from six documents and two hooks that had copied them.

This is the eleventh sweep pass under [[ISS-0048-Thirty-Six-Rules-Are-Still-Stated-In-More-Than-One-File|ISS-0048]] and the first to read the `.base` views, `docs/STYLEGUIDE.md`, `docs/releases/README.md`, `tools/sync/MANIFEST.yaml` and the rule-bearing regions of `validate-docs.py`. It found 25 restatements and 10 bad citations there.

## Impact

**A reader sees this one.** The two Obsidian view files ship to every downstream repo, so every repo's navigator had a dead "Features (Open)" table until now.

**Two hooks changed behaviour.** `model-routing-hint.sh` had a branch for a `blocked` status that does not exist, so it never ran; both it and the harness assertion that pinned it are gone. `verification-gate.py` matched `implemented` as a terminal status, which HOOKS.md HC-003 explicitly says is not a trigger; the match is removed. Neither change alters a case that could occur in practice, and the harness went from 34 assertions to 31 with no failures.

**One contract statement reversed.** `SYNCING.md` called `.github/workflows/validate-docs.yml` "Optional seed only". `tools/sync/MANIFEST.yaml` says template-owned, and carries the reason: as `seed` it was copied once and never overwritten, so validator and CI changes stopped at the template until TASK-0072 found it. An agent following the instruction file would have restored the bug. SYNCING.md now points at the manifest for ownership instead of keeping its own list.

**One schema claim was false and now is not.** `SCHEMAS.md` told every repo that "the validator refuses" seven removed acceptance fields. The validator pre-commit and CI run refuses none of them and still reads `mark:`; the cockpit's separate copy refuses twelve. The schema now says what is true and names the divergence as open. Deciding which validator wins is [[ISS-0049-The-Schema-Claims-A-Refusal-The-Shipped-Validator-Does-Not-Make|ISS-0049]].

**Two rules gained a home.** The 90-day manual-verification staleness window and its `verification.staleness_days` override existed only as a constant in the validator; `STATUSES.md` now states both. HC-005 listed four of the five risk-scan triggers next to a pointer at the full list; the partial copy is gone.

Also: `docs/OWNERSHIP.md` restated the rules its instruction file owns and now links them; `SCHEMAS.md` called `tier` and `migrated_from` removed and then used both as live four lines later; `TAXONOMY.md` documented `burden` after `SCHEMAS.md` recorded it removed; four citations pointed at files, sections or directions that do not exist; and four index files had fallen behind their directories.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: updated — [[REQ-0027-Every-Normative-Rule-Is-Stated-Once]] still cannot tick criteria 1 and 3; they wait on two consecutive clean passes
- tasks: not-applicable — the sweep is tracked on the issue, not as tasks
- issues: updated — ISS-0048 pass table; new — ISS-0049, ISS-0050
- tests: not-applicable — no new test; `test-hooks.sh` lost the three assertions that pinned a status which cannot occur
- workflows: not-applicable
- decisions: not-applicable — ADR-0024 unchanged
- risks: not-applicable — the one hazard found (two validators drifting apart) is carried by ISS-0049
- changes: new — this note
- snapshot: updated — focus moved to ISS-0048; ISS-0049 and ISS-0050 added

## Follow-ups

- [ ] Pass 12 at `e2bee28`. Two consecutive clean passes close ISS-0048; none currently stands.
- [ ] `docs/__templates__/SCHEMAS.md` in project-os-dev is merge-owned and two months behind the template (`updated: 2026-05-08` against `2026-07-21`), missing `origin`, `acceptance_exception` and the ADR-0032 removal of a feature's `tests` list. Hand-merge is owed and was out of this pass's scope.
- [ ] `compass_artifact_wf-84fa61ff-...md` has sat at the template repo root since `d3f9a8f` with no frontmatter and no ID. It is a research report about project-os and belongs under `docs/reference/` as a `reference` note.
