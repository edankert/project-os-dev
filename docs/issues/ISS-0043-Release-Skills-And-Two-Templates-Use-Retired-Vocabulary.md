---
type: "[[issue]]"
id: ISS-0043
aliases: ["ISS-0043"]
title: "Release skills and two templates use vocabulary the taxonomy retired"
status: fixed
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
component: docs
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 1.3", "https://claude.ai/code/artifact/4d82b4ff-73ed-42ab-97c0-9a2d0f98fcfc"]
related: ["[[ISS-0009-Fleet-Status-Vocabulary-Drift]]", "[[ADR-0008-States-Must-Earn-Their-Keep]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]"]
tasks: []
tests: []
---

# Release skills and two templates use vocabulary the taxonomy retired

## Problem

An agent running release-prep today will look for `CHK-*` files that no repo has, count "Tier 1 and Tier 2" in a system whose own testing rules say there is no tier system, and write statuses (`staged`, `rolled-back`, `in-review`, `in-progress`) that the release and feature status lists do not contain. The release skills predate the taxonomy collapse and were never swept.

Eight rows, all in the template repo:

| Where | Says | Current rule |
|---|---|---|
| `release-prep/SKILL.md:21,37`, `release-verification/SKILL.md:67` | `docs/tests/acceptance/CHK-*.md` | acceptance checks are `TST-*` at `level: acceptance` (TESTING.md:129) |
| `release-prep/SKILL.md:38,41,84,94`, `release-verification/SKILL.md:68,73`, `__templates__/release.md:49-52,72` | Tier 1 / 2 / 3 | "There is no tier system" (TESTING.md:13) |
| `__templates__/SCHEMAS.md:221` | `tier` is a required field | same contradiction, in the schema |
| `release-prep/SKILL.md:50-51`, `feature-scaffold/SKILL.md:52` | `in-review`, `in-progress` | feature statuses are `review` and `doing` |
| `release-prep/SKILL.md:91`, `release-verification/SKILL.md:104` | `staged` | removed by ADR-0008; release-prep says so one line later |
| `release-verification/SKILL.md:126,128` | `rolled-back` | release statuses are `draft`, `released`, `reverted` |
| `release-verification/SKILL.md:84-85`, `TAXONOMY.md:55` | `kind: manual` / `automated` | `kind` was removed; `command:` decides |
| `__templates__/README.md:21-22`, `__templates__/acceptance-tests.md:17` | "Includes `check.md`", `type: [[check]]` | there is no `check.md` and no `check` type |

## Repro

```bash
cd ~/Dev/repos/project-os
grep -rn "CHK-\|Tier [123]\|in-review\|in-progress\|rolled-back" tools/skills/release-prep tools/skills/release-verification docs/__templates__/release.md
grep -n "tier" docs/__templates__/SCHEMAS.md
```

## Expected

The release skills and the two templates use the vocabulary STATUSES.md and TESTING.md define today.

## Actual

Eight rows of retired vocabulary. Three of them are inside files that state the current rule elsewhere in the same file.

## Evidence

Every row above re-verified in the template on 2026-09-03.

## Next Actions

- [x] One sweep of `release-prep/SKILL.md` and `release-verification/SKILL.md` against STATUSES.md and TESTING.md as they stand.
- [x] Drop `tier` from `SCHEMAS.md` and `release.md`, and from the acceptance block in `docs/__templates__/test.md`.
- [x] Remove the `check.md` lines from `docs/__templates__/README.md` and `acceptance-tests.md`.
- [x] Move the `kind` heading in TAXONOMY.md to the retired list.
- [x] Fix `feature-scaffold/SKILL.md:52` (`in-progress` to `doing`) in the same commit.
- [ ] Run the docs-audit skill afterwards; its "instruction/template drift" dimension is what would have caught all eight.

## Resolution

Fixed in the template by commit `0049206` on 2026-09-03 (CHG-20260903-Prompting-Guide-Contradictions there). The sweep found a second problem underneath the vocabulary: the release-verification skill's verdict model still resets tests by hand and judges staleness from `last_run`. That is a model change, not a word change, so it is split out as [[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand|ISS-0046]]. The docs-audit run is still owed; it is the one action left unticked.

## Sibling search

Siblings found: [[ISS-0009-Fleet-Status-Vocabulary-Drift]] (the same vocabulary, in notes rather than skills) and ISS-0041, ISS-0042 filed the same day. Searched `docs/issues/` for: vocabulary, tier, CHK, staged, drift. Family rule proposed as [[ADR-0024-A-Normative-Rule-Is-Stated-Once]].

## Risk scan

Run against the LIFECYCLE.md triggers. One trigger fires: `SCHEMAS.md` losing a required field is a schema change that downstream repos inherit at the next sync. No `RISK-*` note — the field is required by no validator check and written by no repo, so removing it cannot invalidate an existing note. Recorded here as the negative result the scan asks for.
