---
type: "[[change]]"
id: CHG-20260927-A-Check-May-Declare-Its-Own-Kind
title: "An acceptance check may declare kind: feature or kind: regression, and that wins over the kind its covers: gives"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[ISS-0104-A-Check-Cannot-Say-It-Is-A-Feature-Check-When-It-Covers-An-Issue]]"]
commit: "project-os 275673f, 1200759; project-os-cockpit d1df13c; your-trainer d082c854, de971acd"
pr: ""
impacts: ["tools/instructions/TESTING.md", "docs/__templates__/SCHEMAS.md", "docs/__templates__/test.md", "docs/__templates__/acceptance-tests.md", "tools/scripts/release-test.py", "tools/scripts/validate-docs.py", "tools/scripts/test-ledger-checks.sh", "tools/scripts/test-release-test-preparation.py", "tools/cockpit/src/project_os_cockpit/acceptance.py"]
platforms: []
issues: ["[[ISS-0104-A-Check-Cannot-Say-It-Is-A-Feature-Check-When-It-Covers-An-Issue]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ISS-0069-A-Regression-Check-A-Change-Overlaps-Cannot-Be-Reopened]]"]
---

# An acceptance check may declare kind: feature or kind: regression, and that wins over the kind its covers: gives

## Summary

A check author can now say which kind of test a check is. Before, a check that named an `ISS-*` in `covers:` was always a regression test, and a later change never reopened it, even when the check stated how the product behaves now. Now `kind: feature` or `kind: regression` on the note decides it, and the `ISS-*` stays in `covers:` as the record of the defect. A `command:` still makes a check automated. Edwin chose this on 2026-09-27 as option 1 of your-trainer ISS-0414, and it replaces ISS-0069's rule of splitting such a check in two.

## Impact

- **`TESTING.md`**, "The three test kinds": the order is `command:`, then `kind:`, then `covers:`. "When to invalidate" says to give an overlapped regression check `kind: feature` instead of splitting it.
- **Validator**: CHECK-KIND, a new error, refuses a `kind:` other than `feature` or `regression`, and a `kind:` beside a `command:`.
- **`release-test.py`** and the **cockpit's** `acceptance.kind_of` read the declared kind, so the release test sheet, the validator and the Tests page agree.
- **Templates**: `SCHEMAS.md` lists the field under "Acceptance fields", and `test.md` has a commented `kind:` line.
- **your-trainer**: TST-0451, TST-0633 and TST-0642 declare `kind: feature`. Its REL-0017 owes the same checks as before on Android and iOS, because a kind alone invalidates nothing.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable (tracked as ISS-0104)
- issues: updated (ISS-0104 fixed; project-os-cockpit ISS-0316 fixed; your-trainer ISS-0414 fixed)
- tests: updated (test-ledger-checks.sh, test-release-test-preparation.py, project-os-cockpit tests/test_invalidation_scope.py)
- workflows: not-applicable
- decisions: not-applicable (Edwin's decision is quoted in ISS-0104)
- risks: not-applicable (no new dependency, variable, path or credential)
- changes: new
- snapshot: updated
