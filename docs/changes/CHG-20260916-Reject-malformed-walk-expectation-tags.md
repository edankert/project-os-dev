---
type: "[[change]]"
id: CHG-20260916-Reject-malformed-walk-expectation-tags
title: "Reject malformed walk expectation tags"
status: merged
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["Your Trainer FEAT-0122: TST-0657.9a was silently ignored by the shared walk parser"]
commit: ""
pr: ""
impacts: []
issues: []
features: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
---

# Reject malformed walk expectation tags

## Summary
The shared walk validator will reject a backticked `TST-` token that is not a valid numeric expectation tag. The generator currently treats a tag such as `TST-0657.9a` as ordinary prose, so an owed observation can disappear without a useful error.

## Impact

- No screen changed in this repository: the shared validator reports an invalid procedure and keeps the existing per-check fallback available to consumers.

## Documentation Coverage (All Types Considered)
Set each item to one of: `updated`, `new`, `not-applicable`, `deferred`.

- features: updated
- requirements: not-applicable
- tasks: updated
- issues: not-applicable
- tests: updated
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups
- [x] Reject malformed tokens even when another valid tag on the same line satisfies owed coverage. A focused fixture supplies both tags and checks the named error.
- [x] Prove the rejected procedure falls back to complete per-check rows and sync the exact implementation into both consumers. Nine preparation tests and 157 sheet assertions pass; all four generator copies are byte identical.
