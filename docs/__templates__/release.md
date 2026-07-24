---
type: "[[release]]"
id: REL-0000
aliases: ["REL-0000"]
title: ""
status: draft
version: ""
tag: ""
date: ""
platform:
owner: unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
features: []
changes: []
tests_verified: []
previous_release: ""
related: []
tags: []
---

# {{title}}

## Scope

### Features Included
| ID | Title | Status |
|---|---|---|
| FEAT-#### | Feature name | done |

### Features NOT Included (deferred)
| ID | Title | Status | Reason |
|---|---|---|---|
| FEAT-#### | Feature name | todo | Reason for deferral |

### Issues Fixed
| ID | Title | Platform |
|---|---|---|
| ISS-#### | Issue title | platform |

### Known Issues (shipping with)
| ID | Title | Severity | Notes |
|---|---|---|---|
| ISS-#### | Issue title | low/medium/high | Workaround or impact note |

## Verification

### Acceptance Tests
- **Tier 1 (Feature Tests):** All passing / N exceptions
  - List any exceptions with justification
- **Tier 2 (Regression Tests):** All passing
- **Tier 3 (Verification Tests):** Status (passing / removed)

### Unit Tests
- Platform A: N tests, all passing
- Platform B: N tests, all passing

### Build
- versionCode: N
- versionName: "X.Y.Z"
- Build type: Release

## Notes

### User-Facing Release Notes
<!-- Plain-language description for app store / changelog -->

### Migration Notes
<!-- Database migrations, breaking changes, upgrade steps -->

### Post-Release Actions
- [ ] Remove Tier 3 acceptance tests (if verified by unit tests)
- [ ] Update SNAPSHOT focus to next milestone
- [ ] Tag repo: `git tag v<version>`
- [ ] Push tag: `git push origin v<version>`
- [ ] Update REL-* status to `published`
