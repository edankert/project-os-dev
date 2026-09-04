---
type: skill
id: SKILL-RELEASE-VERIFICATION
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-09-04
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

### 3. Settle each test by its kind
The verdict model is stated once, in `../../instructions/STATUSES.md` `[[test]]` and `../../instructions/TESTING.md` "Release gating"; this step applies it to each collected test:
- **A test with a `command:`** is settled by CI (`../../instructions/STATUSES.md` `[[test]]`). Its verdict here is **CI**; nothing is re-run by hand.
- **An acceptance check** (`level: acceptance`, no `command:`) is settled per release and platform in the ledger. Unsettled for this release and platform is **BLOCKED**.
- **A manual test** (no `command:`, any other level) carries a hand-written verdict and `last_verified:`. **CURRENT**: `status: passing` and `last_verified` inside the staleness window and after the latest `updated` among the tasks under its features. **STALE**: `last_verified` older than that. **UNTESTED**: `status: ready` or `draft`. **FAILING**: `status: failing`.

### 4. Produce the release test matrix
Present the results as a table:

```
| Test | Level | Kind | Status | Last verified | Linked Feature | Latest Change | Verdict |
|------|-------|------|--------|---------------|----------------|---------------|---------|
| TST-0005 | acceptance | walked | active | (ledger) | FEAT-0008 | 2026-03-07 | BLOCKED |
| TST-0012 | e2e | command: | active | (CI) | FEAT-0008 | 2026-03-07 | CI |
| TST-0014 | system | manual | passing | 2026-03-01 | FEAT-0008 | 2026-03-07 | STALE |
| TST-0018 | acceptance | walked | active | (ledger: no entry) | FEAT-0015 | 2026-03-06 | UNTESTED |
| TST-0020 | acceptance | walked | active | (ledger: fail) | FEAT-0003 | 2026-03-04 | FAILING |
```

### 5. Check the acceptance suite
Sections and gating are stated once, in `../../instructions/TESTING.md` ("The three sections", "Release gating"); this step applies them.
- Read the acceptance suite (`TST-*` notes at `level: acceptance`, stored per `../../instructions/LIFECYCLE.md` "Test storage", or `docs/tests/ACCEPTANCE_TESTS.md` in a repo that has not migrated) and list every check that "Release gating" calls a blocker for this release and platform; record any release exception as it says.

### 6. Gate the release
- If any manual acceptance check is unsettled, or any `TST-*` note has verdict **STALE**, **UNTESTED**, or **FAILING**: **STOP.**
- Report: "Release blocked. N tests need attention before release can proceed."
- List each blocking test with its verdict and what action is needed:
  - STALE or UNTESTED → run the manual procedure (step 7)
  - FAILING → fix the regression, then run it again
  - BLOCKED → walk the acceptance check and record it in the ledger
- Do not reset a status by hand: a manual test's status is written when it is run (step 7), and a `command:` test has none.

### 7. Re-run tests
For each test that needs re-running:
1. Read the test note's Preconditions and Procedure sections.
2. If the test has no `command:` (a manual test): present the procedure to the user for execution. The user runs through the steps and reports PASS or FAIL.
3. If the test carries a `command:`: nothing to record (`../../instructions/STATUSES.md` `[[test]]`).
4. For a manual test, update the test note:
   - `status: passing` or `status: failing`
   - `last_verified: <today's date>`
   - `updated: <today's date>`
   - Add evidence to the Evidence section
5. The snapshot follows the note (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"); do not re-type the status.

### 8. Final release gate
- Re-check the matrix: every manual test **CURRENT**, every acceptance check settled in the ledger, and the CI run green.
- If all pass: "Release verification complete. All N acceptance tests passing."

### 9. Create/update release note
When all tests pass:
1. Allocate a new `REL-*` ID from `counters.REL` in SNAPSHOT.yaml.
2. Create `docs/releases/REL-####-<version>.md` from `docs/__templates__/release.md`:
   - `version`: the release version
   - `tag`: the git tag (suggest `v<version>`)
   - `date`: today's date
   - `status: draft` (prepared and verified, not yet live)
   - `features`: list of all in-scope feature IDs
   - `changes`: list of CHG-* IDs created since the previous release
   - `tests_verified`: list of all TST-* IDs verified in this cycle
   - `previous_release`: the prior REL-* ID (from `releases.latest` in SNAPSHOT.yaml, if present)
3. Add the release to `items.releases` in SNAPSHOT.yaml.
4. Update `releases.latest` and prepend to `releases.history` in SNAPSHOT.yaml.
5. Suggest a git tag: `git tag -a v<version> -m "Release <version>"`.

### 10. Ship the release
After deployment/merge to production:
1. Update the REL-* note: `status: released`.
2. Update `releases.latest.status` and the corresponding `releases.history` entry to `released`.
3. Create a `CHG-*` note documenting the release if appropriate.

### 11. Post-release
- The `last_verified` dates on all re-run manual tests now reflect the release verification date.
- On the next release, only tests linked to features that changed after this date will be flagged as STALE.
- This creates a natural cycle: change → stale → re-verify → current → change → stale → ...

### Rollback
If a release is rolled back:
1. Update the REL-* note: `status: reverted`.
2. Update `releases.latest` to point to `previous_release` (or the last `released` entry in history).
3. Update the history entry status to `reverted`.
4. Create an `ISS-*` to track the rollback cause.
