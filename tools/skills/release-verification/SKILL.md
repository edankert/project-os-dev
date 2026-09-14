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

### 3a. Check the procedures the walk will print
- Run `python3 tools/scripts/walk-sheet.py --check --platform <platform>`. A sitting with a written procedure is walked from that script, and the script is authored text that can disagree with the owed set after a single ledger event (`../../instructions/TESTING.md`, "The walk", rule 9).
- Report each refusal in the matrix's notes and rewrite it with `../walk-procedure/SKILL.md` before the walk starts. This is not a release blocker on its own: a refused procedure falls back to per-check rows and nothing owed is hidden.

### 4. Produce the release test matrix
Present the results as a table:

```
| Test | Level | Kind | Status | Last verified | Sitting | Linked Feature | Latest Change | Verdict |
|------|-------|------|--------|---------------|---------|----------------|---------------|---------|
| TST-0005 | acceptance | walked | active | (ledger) | 2 — On the bench | FEAT-0008 | 2026-03-07 | BLOCKED |
| TST-0012 | e2e | command: | active | (CI) | — | FEAT-0008 | 2026-03-07 | CI |
| TST-0014 | system | manual | passing | 2026-03-01 | — | FEAT-0008 | 2026-03-07 | STALE |
| TST-0018 | acceptance | walked | active | (ledger: no entry) | 1 — Fresh install | FEAT-0015 | 2026-03-06 | UNTESTED |
| TST-0020 | acceptance | walked | active | (ledger: fail) | Unplaced | FEAT-0003 | 2026-03-04 | FAILING |
```

Fill **Sitting** from the walk sheet, so the matrix and the sheet agree on the order rather than offering two. A row with no sitting is not an acceptance check.

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

### 7. Walk the sheet, and re-run the other tests
**Acceptance checks are walked from the sheet, in its order, one sitting at a time.** Generate it with `python3 tools/scripts/walk-sheet.py --release <REL-####> --platform <platform>` (`../release-prep/SKILL.md` step 2). Start with the survey: open the screens the release changed before walking a single scripted check. Then take the sittings in order — each names the state it needs and what must be on the bench, so a sitting is set up once and walked through.

1. Every row carries its own Setup, Steps and Expect. Do not open the note to walk a row; open it only to fix its text.
2. Record each verdict as a **ledger event** with `method: manual`, through the cockpit's mark dialog or the ledger write path. **Write nothing on the check's note**: an acceptance check rests at `active` and carries no verdict (`../../instructions/STATUSES.md` `[[test]]`; `TESTING.md`, "The walk", rule 6).
3. A row whose text is wrong — an expired premise, a behaviour the platform never had, a setup sentence that makes a cheap check look expensive — gets its text fixed in the same action that records the verdict (`TESTING.md`, "A check is walkable by a stranger"). "Setup: not stated" on a row is that invitation.
4. Regenerate the sheet to see what is left. It is derived, so it is never edited and never corrected by hand.

For a **manual test that is not an acceptance check** (no `command:`, any other level): present the procedure to the user, then update the note with `status: passing` or `failing`, `last_verified:`, `updated:` and the evidence. A test carrying a `command:` records nothing (`../../instructions/STATUSES.md` `[[test]]`). The snapshot follows the note (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"); do not re-type the status.

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
