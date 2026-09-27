---
type: "[[issue]]"
id: ISS-0104
aliases: ["ISS-0104"]
title: "A check that covers an issue is always a regression check, so a change to the behaviour it states never reopens it"
status: fixed
phase: ""
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["your-trainer ISS-0414, decided by Edwin on 2026-09-27: 'ISS-0414: take your recommendation, option 1'"]
reported_by: user:edwin
question: ""
severity: medium
component: "testing"
parent: ""
related: ["[[ISS-0069-A-Regression-Check-A-Change-Overlaps-Cannot-Be-Reopened]]"]
tests: []
---

# A check that covers an issue is always a regression check, so a change to the behaviour it states never reopens it

## Problem

A tester can be shown a check as done after a change has made it untrue. `TESTING.md` works out each check's kind from two fields. A non-empty `command:` makes it an automated test. Otherwise, a `covers:` that names an `ISS-*` makes it a regression test, and a regression test is never invalidated (marked as needing a new result) by a later change. Some of those checks state how the product behaves now, so a change to that behaviour leaves them ticked. The check's author has no way to say "this one is a feature check" without deleting the `ISS-*` link, and that link is the only record of which defect the check guards. your-trainer's TST-0451, TST-0633 and TST-0642 are the cases that raised it ([[your-trainer#ISS-0414]]).

> [!quote] As decided — 2026-09-27 (user:edwin)
> ISS-0414: take your recommendation, option 1

## Decided

Option 1 of your-trainer ISS-0414: **a check may declare its own kind, and the derivation becomes the default rather than the rule.**

- An acceptance check may carry `kind: feature` or `kind: regression` in its frontmatter. When present, it wins over what `covers:` would give.
- A non-empty `command:` still makes a check automated. A `kind:` beside a `command:` is a validator error, and so is any other `kind:` value.
- With no `kind:`, the check's kind is worked out as before.
- The `ISS-*` stays in `covers:`, so the link to the defect survives.

This replaces the rule [[ISS-0069-A-Regression-Check-A-Change-Overlaps-Cannot-Be-Reopened|ISS-0069]] added on 2026-09-18, which said to split such a check in two. Setting `kind: feature` needs no second note.

## Expected

A check with `covers: [ISS-0387]` and `kind: feature` is listed under feature tests by the release test generator, the validator and the cockpit, and an invalidation reopens it.

## Actual

The same check is a regression test everywhere, whatever the author meant, and an invalidation never reopens it.

## Next Actions
- [x] project-os: `release-test.py` and `validate-docs.py` honour `kind:`, the validator refuses an unknown value and a `kind:` beside a `command:`, with tests. `TESTING.md`, `SCHEMAS.md` and `test.md` say so.
- [x] project-os-cockpit: `acceptance.kind_of` honours `kind:`, with a test, and the bundled copies are refreshed. The cockpit is released into project-os.
- [x] Sync the template to project-os-dev and your-trainer. your-trainer sets `kind: feature` on TST-0451, TST-0633 and TST-0642, and closes ISS-0414.

## Fixed, 2026-09-27

- **project-os `275673f`**: `release-test.py` reads `kind:` after `command:` and before `covers:`. The validator's CHECK-KIND refuses an unknown value and a `kind:` beside a `command:`. `TESTING.md`, `SCHEMAS.md`, `test.md` and `acceptance-tests.md` say so. New cases in `test-ledger-checks.sh` and `test-release-test-preparation.py` each fail when their line of the change is removed.
- **project-os-cockpit `d1df13c`** (its ISS-0316): `acceptance.kind_of` reads it the same way, and the bundled copies match. Released into project-os as `1200759`.
- **your-trainer `d082c854`, `de971acd`**: synced; TST-0451, TST-0633 and TST-0642 declare `kind: feature`, and ISS-0414 is fixed. REL-0017 owes the same checks as before on both platforms.
- Change note: [[CHG-20260927-A-Check-May-Declare-Its-Own-Kind]].
