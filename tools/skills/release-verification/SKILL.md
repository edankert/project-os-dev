---
type: skill
id: SKILL-RELEASE-VERIFICATION
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
tags: [skills, testing, release]
---

# Skill: Release verification

## When to use
- Before any release (version tag, deployment, merge to production)
- When a stakeholder asks "is this ready to ship?"
- Periodically to assess test coverage staleness

## Inputs
- `../../../SNAPSHOT.yaml`
- Release scope: either a list of feature IDs, or "all features changed since last release"
- Last release reference: git tag, date, or "all time" for first release

## Outputs
- Release test matrix (table of all acceptance tests with staleness verdicts)
- List of tests that need re-running before release can proceed
- Updated test statuses after re-runs

## Checklist

### 1. Determine release scope
- If specific features are provided: use those as the scope.
- If "since last release": identify the last release tag (git tag) or date, then find all features with tasks that have `updated` dates after that point.
- List all in-scope feature IDs.

### 2. Collect acceptance tests
For each in-scope feature:
- Find all `TST-*` notes linked via `features` containing this feature ID.
- Find all `REQ-*` linked to this feature (via feature's `requirements` list), then find all `TST-*` linked to those requirements (via test's `requirements` field).
- Deduplicate the test list.

Also include any `TST-*` with `level: acceptance` and `scope: system` — these are cross-feature acceptance tests that should always be verified before release.

### 3. Check staleness for each test
For each test in the collected list:
1. Read the test's `last_run` date.
2. Find the latest `updated` date among all tasks under the linked feature(s).
3. Determine the verdict:
   - **CURRENT**: `last_run` exists AND is after the latest task update AND `status: passing` → no re-run needed.
   - **STALE**: `last_run` exists but is before the latest task update → feature changed since test last ran, needs re-run.
   - **UNTESTED**: `last_run` is empty or test is `status: draft`/`ready` → never been run, needs first run.
   - **FAILING**: `status: failing` regardless of dates → known failure, must be fixed.

### 4. Produce the release test matrix
Present the results as a table:

```
| Test | Level | Status | Last Run | Linked Feature | Latest Change | Verdict |
|------|-------|--------|----------|----------------|---------------|---------|
| TST-0005 | acceptance | passing | 2026-03-01 | FEAT-0008 | 2026-03-07 | STALE |
| TST-0012 | e2e | passing | 2026-03-08 | FEAT-0008 | 2026-03-07 | CURRENT |
| TST-0018 | acceptance | ready | — | FEAT-0015 | 2026-03-06 | UNTESTED |
| TST-0020 | acceptance | failing | 2026-03-05 | FEAT-0003 | 2026-03-04 | FAILING |
```

### 5. Check acceptance test tiers
If the project uses the acceptance test tier system (see `../../instructions/TESTING.md`):
- Read `../../../docs/tests/ACCEPTANCE_TESTS.md`.
- **Tier 1 + Tier 2** tests must ALL be checked (passing). Any unchecked test is a release blocker.
- **Tier 3** tests do not gate the release — they are informational.
- A test may be marked as a **release exception** if it cannot be completed. Exceptions must be documented in the release note with justification.

### 6. Gate the release
- If ANY Tier 1/Tier 2 acceptance test is unchecked, or any `TST-*` note has verdict **STALE**, **UNTESTED**, or **FAILING**: **STOP.**
- Report: "Release blocked. N tests need attention before release can proceed."
- List each blocking test with its verdict and what action is needed:
  - STALE → re-run the test procedure
  - UNTESTED → run the test procedure for the first time
  - FAILING → fix the regression, then re-run
- Reset STALE and UNTESTED tests to `status: ready` to signal they need re-running.

### 6. Re-run tests
For each test that needs re-running:
1. Read the test note's Preconditions and Procedure sections.
2. If `kind: manual`: present the procedure to the user for execution. The user runs through the steps and reports PASS or FAIL.
3. If `kind: automated` and `entrypoint` is set: run the entrypoint command and capture the result.
4. Update the test note:
   - `status: passing` or `status: failing`
   - `last_run: <today's date>`
   - `updated: <today's date>`
   - Add evidence to the Evidence section
5. Update `../../../SNAPSHOT.yaml` with the new test status.

### 7. Final release gate
- Re-check the matrix: all tests must now be **CURRENT** and `status: passing`.
- If all pass: "Release verification complete. All N acceptance tests passing."

### 8. Create/update release note
When all tests pass:
1. Allocate a new `REL-*` ID from `counters.REL` in SNAPSHOT.yaml.
2. Create `docs/releases/REL-####-<version>.md` from `docs/__templates__/release.md`:
   - `version`: the release version
   - `tag`: the git tag (suggest `v<version>`)
   - `date`: today's date
   - `status: staged` (not yet deployed)
   - `features`: list of all in-scope feature IDs
   - `changes`: list of CHG-* IDs created since the previous release
   - `tests_verified`: list of all TST-* IDs verified in this cycle
   - `previous_release`: the prior REL-* ID (from `releases.latest` in SNAPSHOT.yaml, if present)
3. Add the release to `items.releases` in SNAPSHOT.yaml.
4. Update `releases.latest` and prepend to `releases.history` in SNAPSHOT.yaml.
5. Suggest a git tag: `git tag -a v<version> -m "Release <version>"`.

### 9. Ship the release
After deployment/merge to production:
1. Update the REL-* note: `status: released`.
2. Update `releases.latest.status` and the corresponding `releases.history` entry to `released`.
3. Create a `CHG-*` note documenting the release if appropriate.

### 10. Post-release
- The `last_run` dates on all re-run tests now reflect the release verification date.
- On the next release, only tests linked to features that changed after this date will be flagged as STALE.
- This creates a natural cycle: change → stale → re-verify → current → change → stale → ...

### Rollback
If a release is rolled back:
1. Update the REL-* note: `status: rolled-back`.
2. Update `releases.latest` to point to `previous_release` (or the last `released` entry in history).
3. Update the history entry status to `rolled-back`.
4. Create an `ISS-*` to track the rollback cause.
