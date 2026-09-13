---
type: skill
id: SKILL-RELEASE-PREP
status: active
owner: group:maintainers
created: 2026-03-16
updated: 2026-09-03
tags: [skills, release]
---

# Skill: Release preparation

## When to use
- When the user decides to prepare a release for deployment.
- Before running `release-verification` (this skill prepares; that skill verifies).

## Inputs
- Target version number (e.g., "1.1.0")
- Platform (e.g., "android", "ios", "web")
- `../../../SNAPSHOT.yaml`
- the acceptance suite — `TST-*` notes at `level: acceptance`, stored per `../../instructions/LIFECYCLE.md` "Test storage", or `docs/tests/ACCEPTANCE_TESTS.md` in a repo that has not migrated (`../../instructions/TESTING.md`)

## Outputs
- `../../../docs/releases/REL-####-v<version>.md` (release note from template)
- Updated `../../../SNAPSHOT.yaml` (release entry, counters, focus)
- Updated version in build configuration
- Audit report of open issues and acceptance test status

## Checklist

### 1. Audit open issues
- List all `ISS-*` in SNAPSHOT with status `triage` or `open`.
- For each: recommend **fix before release** (if severity ≥ medium) or **ship as known issue** (if low).
- Which of them block the release is the user's decision (`../../instructions/LIFECYCLE.md`, "When to pause for the user"); present the list with the recommendations and carry on with the steps below that do not depend on it.

### 2. Generate the walk sheet
- For each platform the release note names, run `python3 tools/scripts/walk-sheet.py --release <REL-####> --platform <platform>`. That is what the person walking this release reads: the screens it changed, then every owed check in the project's order with its setup, steps and expected result on the page. The rules are stated once in `../../instructions/TESTING.md`, "The walk".
- Report the owed row count and the sitting count per platform, and put the sheet where the walker can find it: `--out <path>` writes it, and the release note's Verification section carries the line "Walk sheet: `<path or command>`".
- Rows under **Unplaced**, or a sheet saying its order is unauthored, are the walk order's worklist rather than a defect in the sheet: fix `docs/tests/acceptance/WALK.md` (`TESTING.md`, "The walk", rule 3).
- If a check cannot be run, recording a **release exception** with justification is the user's decision (`TESTING.md`, "Release gating"; pause rule: `../../instructions/LIFECYCLE.md`, "When to pause for the user").
- A repo that has not migrated to notes has no ledger and no sheet; read `docs/tests/ACCEPTANCE_TESTS.md` and list every check "Release gating" calls a blocker.

### 2b. Docs consistency audit
- Run `bash tools/scripts/validate-docs.sh` (mechanical) and `../docs-audit/SKILL.md` (cross-document, one bounded round) before drafting the release note — releases are the last chance to catch stale references before they ship as documentation.

### 3. Create release note
1. Allocate `REL-####` from `counters.REL` in SNAPSHOT.
2. Create `../../../docs/releases/REL-####-v<version>.md` from `../../../docs/__templates__/release.md`.
3. Populate:
   - **Features Included:** All `FEAT-*` with status `done` (or `review` when shipping ahead of final verification) that are shipping.
   - **Features NOT Included:** Any `FEAT-*` with status `backlog`, `planned`, or `doing`, with reason for deferral.
   - **Issues Fixed:** All `ISS-*` with status `fixed` that were fixed since the previous release.
   - **Known Issues:** All `ISS-*` shipping unfixed (from step 1 audit).
   - **Verification:** Acceptance test status summary, unit test counts.
   - **Build:** Version code/name, build type, min/target SDK.
   - **User-Facing Release Notes:** Plain-language description for app store / changelog.
   - **Post-Release Actions:** Checklist of steps after deployment.

### 4. Update SNAPSHOT
- Add `items.releases.<REL-ID>` with `status: draft`, `version`, `file`.
- Set `focus.release` to the new REL-ID.
- `counters.REL` and `metrics` are derived by the sync script (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation").

### 5. Bump version
- Update the application version in the build configuration:
  - Android: `versionCode` + `versionName` in `build.gradle.kts`
  - iOS: `CURRENT_PROJECT_VERSION` + `MARKETING_VERSION` in `project.pbxproj`
  - Other: as appropriate for the platform
- The version in the build config must match the release note's `version` field.

### 6. Build verification
- Run unit tests: all must pass.
- Build the release artifact (signed AAB/IPA/binary).
- Verify the build succeeds without errors.

### 7. Present summary
Present a release readiness summary:
```
Release: v<version> (REL-####)
Features: N shipped, M deferred
Issues fixed: N
Known issues: N (all low severity / N medium+)
Acceptance checks: all manual checks settled (N exceptions); automated checks green in CI
Unit tests: N passing
Build: OK
Status: READY TO SHIP / BLOCKED (reasons)
```

### 8. After deployment
Once the release is deployed/uploaded (release statuses are stated once in `../../instructions/STATUSES.md` `[[release]]`; `../release-verification/SKILL.md` owns the `draft` → `released` transition):
1. Update `REL-*` status to `released` once verification completes.
2. Clear `focus.release`.
3. Tag the repo: `git tag -a v<version> -m "Release <version>"`.
4. Push: `git push origin main && git push origin v<version>`.
