---
type: "[[requirement]]"
id: REQ-0017
aliases: ["REQ-0017"]
title: "Each work-item type must have exactly one terminal status, and every status-keyed metric must count against it"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: high
scope: lifecycle-rules
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0013]
related: [ADR-0008, ISS-0008, REQ-0016]
tests: []
acceptance:
  - "Issue `closed` is merged into `fixed`; issues have one terminal status plus the descoping outcome `wont-fix`."
  - "No work-item type has two statuses that both mean delivered, differing only in whether verification has happened."
  - "`metrics.issues_open` counts every issue that is not terminal or descoped, so no resolved-but-unverified population is invisible."
  - "Every status-keyed metric definition in SNAPSHOT.md and compute_metric_counts is restated against the collapsed vocabulary and agrees with it."
  - "The 54 existing `closed` issues are migrated to `fixed` with no loss of information, and the verification distinction they carried survives in linked TST-* notes and evidence pointers."
  - "Fleet metrics are recomputed after the merge, and the resulting rise in issues_open is recorded per repo so it is not misread as a regression."
---

# One terminal status per work-item type

## Statement

Each work-item type shall have exactly one status meaning "delivered", alongside the descoping outcomes that resolve scope without claiming delivery (`cancelled`, `superseded`, `wont-fix`). Where a type currently has two — issue `fixed` and `closed` — they shall be merged. Every metric that counts by status shall be redefined against the resulting vocabulary so that no population of items falls outside every count.

## Acceptance Criteria

- [x] Issue `closed` merged into `fixed` — evidence: `STATUSES.md` issue section; `validate-docs.py` ALLOWED_STATUS and `TERMINAL["issues"]`
- [x] No type carries two delivered-statuses distinguished only by verification — evidence: `STATUSES.md` review; requirement `verified` already retired by ADR-0007
- [x] `metrics.issues_open` counts all non-terminal, non-descoped issues — evidence: `validate-docs.py` `compute_metric_counts`; `fixed` is now terminal so the limbo it counted is gone
- [x] Status-keyed metric definitions restated and agreeing — evidence: `tools/instructions/SNAPSHOT.md` "Metrics"
- [x] 54 `closed` issues migrated; verification distinction preserved in TST links — evidence: migrate-status-vocabulary.py run across 10 repos (54 issue closed->fixed)
- [x] Fleet metrics recomputed post-merge — evidence: `--fix-metrics` fleet-wide; your-trainer issues_open 17 -> 47

## Rationale from usage

Of 324 issues that ever reached `fixed`, **10 (3%)** went on to `closed`. The two-step encodes "implemented" versus "verified", and 97% of items never take the second step — so the distinction is not being made, while `metrics.issues_open` excludes both states and hides 313 items ([[ISS-0008-Issues-Open-Metric-Excludes-Fixed|ISS-0008]]).

The distinction itself is not lost. Verification lives in `TST-*` notes with their own status and in per-criterion evidence pointers — exactly where [[ADR-0007-Requirement-Terminality-And-Ownership|ADR-0007]] put it when it retired `verified` for the same reason.

## Impact analysis (2026-07-25)

- [[REQ-0006-Verification-Gating|REQ-0006]] — **strengthened, not weakened.** The `VERIFY` gate currently keys on issue `closed`; after the merge it keys on `fixed`, which means it fires on 313 items it previously never reached. Migration must land the gate change and the data change together, or 313 issues become terminal without ever passing the gate.
- [[REQ-0014-Requirement-Lifecycle-Advancement|REQ-0014]] — aligned. Requirements already have one terminal status (`implemented`) per ADR-0007; this generalises that shape to issues.
- [[REQ-0016-Declared-Statuses-Observed-In-Use|REQ-0016]] — same feature, complementary: REQ-0016 removes values nobody writes, this one removes a value people write but never reach.
- [[REQ-0013-Deferral-Semantics|REQ-0013]] — aligned. `deferred` is explicitly *not* terminal and is unaffected by this requirement.

**No conflicts found.** One sequencing constraint to respect: the `VERIFY` change and the data migration are a single atomic change.

## Traceability

- Feature: [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]]
- Decision: [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]] clause 2
- Fixes: [[ISS-0008-Issues-Open-Metric-Excludes-Fixed|ISS-0008]]
