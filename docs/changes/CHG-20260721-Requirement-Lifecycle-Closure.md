---
type: "[[change]]"
id: CHG-20260721-Requirement-Lifecycle-Closure
aliases: ["CHG-20260721-Requirement-Lifecycle-Closure"]
title: "Requirements advance on evidence: close-out step, approval gate, REQ-* validator checks, and a 12-requirement backfill"
status: merged
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
commit: ""
pr: ""
reviewed_by: model:claude-opus-4-8
review_date: 2026-07-21
review_verdict: approved
impacts:
  - "project-os: tools/skills/close-out (new requirement-advancement step), feature-scaffold (approval gate), status-transition, snapshot-sync, issue-intake"
  - "project-os: tools/instructions/STATUSES.md, QUALITY.md, SNAPSHOT.md, HANDOFF.md, HOOKS.md, OBSIDIAN.md"
  - "project-os: docs/__templates__/SCHEMAS.md, requirement.md, release.md"
  - "project-os: tools/scripts/validate-docs.py (REQ-STALE/REQ-PREMATURE/REQ-BOXES, requirements metrics)"
  - "project-os: SNAPSHOT.yaml template (commented session block removed)"
  - "project-os-dev: REQ-0001..REQ-0012 backfilled; REQ-0010 superseded by new REQ-0015"
issues: [ISS-0004]
features: [FEAT-0012]
---

# Requirement lifecycle closure

## What changed

Fixes [[ISS-0004-Requirements-Never-Advance|ISS-0004]] per [[ADR-0006-Requirement-Advancement-On-Evidence|ADR-0006]]. Requirements previously froze at `draft`/`approved` while their features shipped, because no lifecycle step ever touched them.

- **Close-out advances requirements** (`close-out/SKILL.md` step 3): walk each linked requirement, tick criteria with an evidence pointer, reconcile departures (amend/narrow/supersede with rationale — never tick to fit), set `implemented` once all implementing features are `done`. `verified` stays test-gated.
- **Approval gate** (`feature-scaffold/SKILL.md` step 7): a feature may not go `in-progress` against a `draft` requirement.
- **Canonical surfaces** (`SCHEMAS.md`): frontmatter `acceptance:` is the criteria of record; body checkboxes are the per-criterion verification record.
- **Mechanical enforcement** (`validate-docs.py`): REQ-STALE (error — `draft`/`approved` while all implementing features are `done`), REQ-PREMATURE (warning), REQ-BOXES (warning), plus `requirements_total`/`requirements_implemented` metrics. `REQ` was also missing from `METRIC_PREFIXES`, so requirement counts silently computed as zero.
- **Backfill**: all 12 pre-existing requirements verified criterion-by-criterion against the shipped template. 11 advanced to `implemented`; REQ-0010 superseded by new [[REQ-0015-Relationship-Model|REQ-0015]].

## Gaps closed rather than amended away

Verification found criteria that were genuinely unmet; these were fixed instead of narrowed:

- **HOOKS.md** — added a `Rule:` traceability line to all seven contracts (only 2 of 7 referenced a rule; REQ-0003).
- **HANDOFF.md / SNAPSHOT.md / snapshot-sync** — purged the `session`/`claimed_by`/`last_heartbeat` mandates that contradicted accepted ADR-0003 for months; handoff now runs off snapshot, notes and git (REQ-0005).
- **feature-scaffold / issue-intake** — added the "record the negative" risk-scan clause that only close-out had (REQ-0007).
- **SNAPSHOT.md** — documented the `releases.latest`/`releases.history` block, previously undocumented (REQ-0009).
- **OBSIDIAN.md** — wrote the missing "Workspace setup (three-pane cockpit)" section (REQ-0012).
- Incidental: release template said `published` (not a valid release status — `released`); `release-verification/SKILL.md` had two steps numbered 6.

## Verification

- Synthetic fixture exercised REQ-STALE (direct and reverse links), REQ-PREMATURE, REQ-BOXES (including boxes outside the acceptance section, correctly ignored), and negative cases (all-ticked, mixed feature statuses, no implementing features); a follow-up run confirmed the checks go quiet once requirements are advanced.
- `generate-adapters.py --check` clean (32 artifacts).
- Hardened validator clean on project-os and project-os-dev; project-os-dev's own (older) validator also clean.
- Cockpit `implemented` status guarded by a new test (`tests/test_index.py::test_implemented_status_sorts_and_collapses_with_the_done_family`), adequacy-checked: it fails when the rank/collapse entries are removed and passes when restored. Suite 225 passed, 1 skipped.

## Independent review (2026-07-21)

Authored by `model:claude-fable-5`, reviewed by `model:claude-opus-4-8` — see the independence caveat below. Initial verdict **changes-requested**; all blocking findings fixed in-turn, then re-verified by the same reviewer against the live repos, which returned **approved**.

Blocking findings, all independently re-tested after the fix:

- REQ-0015 ticked a criterion the validator did not satisfy — `implements` was missing from `RELATIONSHIP_FIELDS`, so a dangling feature reference also silently disabled REQ-STALE. Added `implements`/`supersedes`/`superseded` to the checked fields; the criterion is now true rather than reworded away.
- REQ-BOXES was evadable by having no acceptance section at all — and REQ-0013 was already in that state. The check now also fires when an `implemented`/`verified` requirement has frontmatter criteria but no verification record; REQ-0013 was given one.
- `count_acceptance_boxes` was not fence-aware: a `# comment` inside a fenced block ended the section and hid every criterion below it. Made fence-aware, and `*`/`+` bullets are now recognised alongside `-`.
- REQ-STALE ignored `cancelled`/`superseded` implementing features, so those requirements would freeze forever — the exact symptom ISS-0004 exists to end. It now treats all terminal feature statuses as resolved.
- This change note was missing from `items.changes`, which bypassed the validator's REVIEW check. Registered.
- Four evidence pointers cited wrong line numbers; replaced with section/quote anchors, which do not rot.

Second-pass findings, closed in the same session: the `cancelled`/`superseded` widening of REQ-STALE was implemented but described nowhere (STATUSES.md, QUALITY.md, close-out and the validator docstring now match the code); REQ-BOXES accepted a partial verification record (now warns when box count != criteria count); the cockpit change had no guarding test (added, adequacy-checked); and `review_verdict: approved` had been written into the notes *before* the reviewer issued it — a rule against anticipating verdicts is now in `independent-review/SKILL.md`.

**Independence caveat.** This change was authored by a Claude model and reviewed by a different Claude model (`claude-opus-4-8`). `independent-review/SKILL.md` rule 1 asks for a different model *family* or a human; two Claude models share a training lineage, so this review is weaker evidence than a Codex/Gemini or human pass would be. Recorded rather than glossed, per the same rule.

## Known follow-up

project-os-dev still runs an older vendored validator, so REQ-* and DEFER-* checks do not yet gate this repo — they were run explicitly from the template. Propagating `tools/` here (and to the wider fleet) is a separate sync rollout; a dry run reports ~30 locally diverged template-owned files, so it needs a deliberate pass rather than a `--force`.
