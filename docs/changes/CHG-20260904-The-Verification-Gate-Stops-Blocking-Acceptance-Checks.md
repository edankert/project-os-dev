---
type: "[[change]]"
id: CHG-20260904-The-Verification-Gate-Stops-Blocking-Acceptance-Checks
aliases: ["CHG-20260904-The-Verification-Gate-Stops-Blocking-Acceptance-Checks"]
title: "The verification gate stops blocking features that carry an acceptance check"
status: merged
owner: user:edwin
created: 2026-09-04
updated: "2026-09-04"
source: ["[[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule]]", "The ISS-0048 drift sweep, pass 12"]
commit: "ad61433"
pr: ""
impacts: ["tools/adapters/claude-code/hooks/verification-gate.py", "tools/instructions/HOOKS.md", "tools/instructions/QUALITY.md", "tools/scripts/test-hooks.sh"]
issues: ["[[ISS-0051-The-Verification-Hook-Blocks-Every-Feature-That-Follows-The-Acceptance-Rule]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]", "[[TST-0007-The-Hooks-Emit-What-The-Contracts-Say]]"]
---

# The verification gate stops blocking features that carry an acceptance check

## Summary

Setting a feature to `done` was denied if the feature had an acceptance check — which `feature-scaffold/SKILL.md` tells you to give every feature. The blocking HC-003 hook demanded `status: passing` of every linked test, and an acceptance check rests at `active` by design. The hook now carries the two exemptions the repo-wide validator already had, so the ordinary case goes through.

## Impact

**Who noticed.** Anyone running the Claude Code adapter who followed the scaffold skill. The denial read `Verification gate (HC-003): terminal status set while linked tests are not passing: FEAT-xxxx -> TST-yyyy is 'active'`, on a feature whose only fault was having the check it was told to write. A test carrying `command:` produced the same denial, though ADR-0025 says such a test records no verdict at all.

**What changed in the hook.** `tst_exemption()` skips a test with a non-empty `command:` and a test at `level: acceptance`, checked in that order because an acceptance check that gains a `command:` is automated (`TESTING.md`, rule 3). A manual test at anything other than `passing` still blocks, unchanged.

**The hook does not check acceptance settledness**, and that is deliberate. Settledness is an event in the release ledger; this hook reads frontmatter and cannot see one. `VERIFY-ACCEPTANCE` in the validator keeps that half, and HC-003 now says which gate owns which.

**A waiver now needs an expiry in both gates.** The validator already errored on an open-ended `verification_waiver:` (ADR-0010); the hook accepted one. The hook now denies it and names `waiver_expires:`. `QUALITY.md` claimed "the validator reports the waiver as a warning", which was wrong for exactly the case that fails; it now states that a missing, unparseable or past expiry is an error.

**The exemptions are stated once.** They live in `HOOKS.md` HC-003 and both implementations read that list, instead of each carrying its own copy — which is how they diverged.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: not-applicable — tracked on the issue, as ISS-0047 was
- issues: updated — ISS-0051 `fixed`; ISS-0048's pass-12 row records where it came from
- tests: updated — TST-0007 gains six assertions and links ISS-0051
- workflows: not-applicable
- decisions: not-applicable — ADR-0025 and ADR-0010 unchanged, both cited
- risks: not-applicable — a blocking hook was loosened to match the validator, and the harness now pins both directions
- changes: new — this note
- snapshot: updated — ISS-0051 membership and status

## Follow-ups

- [ ] The two gates still differ in reach: the validator gates on the reverse `covers:` index, the hook on the subject's `tests:`. HC-003 records the difference rather than claiming parity. Closing it means teaching the hook the reverse index.
- [ ] `docs/__templates__/SCHEMAS.md` here remains merge-owned and two months behind the template; unchanged by this work.
