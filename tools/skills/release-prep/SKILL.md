---
type: skill
id: SKILL-RELEASE-PREP
status: active
owner: group:maintainers
created: 2026-03-16
updated: 2026-03-16
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
- `../../../docs/tests/ACCEPTANCE_TESTS.md`

## Outputs
- `../../../docs/releases/REL-####-v<version>.md` (release note from template)
- Updated `../../../SNAPSHOT.yaml` (release entry, counters, focus)
- Updated version in build configuration
- Audit report of open issues and acceptance test status

## Checklist

### 1. Audit open issues
- List all `ISS-*` in SNAPSHOT with status `triage` or `open`.
- For each: recommend **fix before release** (if severity ≥ medium) or **ship as known issue** (if low).
- Present the list to the user for decision.

### 2. Check acceptance tests
- Read `../../../docs/tests/ACCEPTANCE_TESTS.md`.
- Count unchecked tests in Tier 1 and Tier 2.
- If any are unchecked: list them and flag as **release blockers**.
- If any cannot be completed: ask user to mark as **release exception** with justification.
- Tier 3 tests do not block — note their status for post-release cleanup.

### 2b. Docs consistency audit
- Run `bash tools/scripts/validate-docs.sh` (mechanical) and `../docs-audit/SKILL.md` (cross-document, to quiescence) before drafting the release note — releases are the last chance to catch stale references before they ship as documentation.

### 3. Create release note
1. Allocate `REL-####` from `counters.REL` in SNAPSHOT.
2. Create `../../../docs/releases/REL-####-v<version>.md` from `../../../docs/__templates__/release.md`.
3. Populate:
   - **Features Included:** All `FEAT-*` with status `done` or `active` that are shipping.
   - **Features NOT Included:** Any `FEAT-*` with status `todo` or `backlog` with reason for deferral.
   - **Issues Fixed:** All `ISS-*` with status `fixed` that were fixed since the previous release.
   - **Known Issues:** All `ISS-*` shipping unfixed (from step 1 audit).
   - **Verification:** Acceptance test status summary, unit test counts.
   - **Build:** Version code/name, build type, min/target SDK.
   - **User-Facing Release Notes:** Plain-language description for app store / changelog.
   - **Post-Release Actions:** Checklist of steps after deployment.

### 4. Update SNAPSHOT
- Add `items.releases.<REL-ID>` with `status: draft`, `version`, `file`.
- Set `focus.release` to the new REL-ID.
- Increment `counters.REL`.
- Update `metrics.releases_total`.

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
Acceptance tests: Tier 1 all passing (N exceptions), Tier 2 all passing
Unit tests: N passing
Build: OK
Status: READY TO SHIP / BLOCKED (reasons)
```

### 8. After deployment
Once the release is deployed/uploaded:
1. Update `REL-*` status to `published`.
2. Clear `focus.release`.
3. Remove Tier 3 acceptance tests.
4. Tag the repo: `git tag -a v<version> -m "Release <version>"`.
5. Push: `git push origin main && git push origin v<version>`.
