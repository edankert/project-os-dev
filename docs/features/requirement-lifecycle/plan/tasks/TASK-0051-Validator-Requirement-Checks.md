---
type: "[[task]]"
id: TASK-0051
aliases: ["TASK-0051"]
title: "Validator: REQ-STALE, REQ-PREMATURE, REQ-BOXES checks"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "tooling change verified mechanically — synthetic fixture exercised REQ-STALE (direct and reverse link), REQ-PREMATURE, REQ-BOXES (incl. boxes outside the acceptance section correctly ignored) and the negative cases (all-ticked, mixed feature statuses, no implementing features); negative test confirmed the checks go quiet once requirements are advanced"
source: []
parent: "[[FEAT-0012-Requirement-Lifecycle-Closure]]"
effort: M
due: ""
depends: [TASK-0050]
blocks: []
related: [ADR-0006, REQ-0014]
tests: []
waiver_expires: 2026-10-23

---

# Validator requirement checks

## Definition of Done

- [x] **REQ-STALE** (error): a requirement in `draft`/`approved` whose `implements:` features are **all** `done` — message points at the close-out advancement step. Requires at least one resolvable feature; requirements with no implementing features are exempt.
- [x] **REQ-PREMATURE** (warning): a feature in `in-progress`/`in-review`/`done` linked to a `draft` requirement.
- [x] **REQ-BOXES** (warning): a requirement in `implemented`/`verified` whose note body still has unticked `- [ ]` acceptance criteria.
- [x] Checks read both snapshot entries and note frontmatter (effective status), consistent with the DEFER-* checks from FEAT-0011.
- [x] Verified against a synthetic fixture exercising each path plus the negative cases (all-features-done vs some-done; no-features; ticked boxes).

## Steps

- [x] Edit `~/Dev/repos/project-os/tools/scripts/validate-docs.py`.
- [x] Fixture run + clean runs on project-os and project-os-dev (the latter only after TASK-0052 backfill, since REQ-STALE will legitimately fire on the current state).

## Notes

`implements:` on a requirement means "implemented **by** these features" — all must be `done` before REQ-STALE fires, never any.
