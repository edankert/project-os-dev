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
| FEAT-#### | Feature name | backlog | Reason for deferral |

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
- **Feature tests:** all settled / N exceptions
  - List any exceptions with justification
- **Regression tests:** all settled
- **Automated tests:** green in CI (no verdict is recorded here)

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
- [ ] Update SNAPSHOT focus to next milestone
- [ ] Tag repo: `git tag v<version>`
- [ ] Push tag: `git push origin v<version>`
- [ ] Update REL-* status to `released`
