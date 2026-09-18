---
type: instruction
id: INSTR-QUALITY
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-18
tags: [instructions, quality]
---

# Quality and close-out rules

These rules define what "done" means for work tracked in this documentation system.

> **State vocabulary and per-type gates are normative in `STATUSES.md`**, which also records who writes each status. This file describes the close-out process; where the two disagree, `STATUSES.md` wins and the disagreement is a bug to file.

## Minimum close-out for any implemented task
- The steps are stated once in `LIFECYCLE.md`, "Close-out (must happen after work)"; this file says what "done" must mean before any of them is taken.

## Documentation Fidelity
- `metrics.counts` in `../../SNAPSHOT.yaml` must match the computed counts (definitions in `SNAPSHOT.md`); `bash tools/scripts/validate-docs.sh --fix-metrics` rewrites the block when it drifts.
- Every snapshot item's `file` path must exist on disk.
- A discrepancy between the filesystem and the snapshot is a build failure: `tools/scripts/validate-docs.sh` exits non-zero on it at the session Stop hook, at pre-commit (`tools/scripts/install-git-hooks.sh`) and in CI (`.github/workflows/validate-docs.yml`). It checks snapshot-to-filesystem agreement, frontmatter and status consistency, counter integrity, link-graph integrity and the verification invariant. Reason: convention-only rules get skipped under context pressure; the validator does not. Reconcile drift with `../skills/snapshot-sync/SKILL.md`; `../skills/docs-audit/SKILL.md` covers what the validator cannot.

## Verification gating (tests)
- The gate on each terminal status (task `done`, issue `fixed`, feature `done`, requirement `implemented`) is stated once in `STATUSES.md`, "The contract at a glance". This section says how to satisfy it.
- Verification is an automated test linked and `passing`, or a manual `[[test]]` note with a clear procedure that a human has run and whose result the note records.
- The rule behind this section is ADR-0017: whether the software works is shown by running it wherever that is possible. Where it is not, the claim is labelled as not run, dated and set to expire. A gate never takes the word of the person asking to close the item.
- Do not tick an acceptance criterion the delivered system does not satisfy. If the work departed from a criterion, amend, narrow or supersede it with recorded rationale (`../skills/close-out/SKILL.md`, step 3 "Requirement advancement"); ticking to fit is a fake `done`.
- A `deferred` task never resolves a feature's scope: descope it through the deferral procedure (`STATUSES.md`, "Deferral and re-adoption"); never flip it to `done` or drop it from the list.
- If a terminal status must be set without passing tests (a docs-only or config-only change), record `verification_waiver: <reason>` **and `waiver_expires: YYYY-MM-DD`** in the note frontmatter. A waiver with both is reported as a warning; one with no expiry, an unparseable expiry, or a past one is an **error**, because an open-ended waiver is a rule deletion written in the passive voice (ADR-0010). A silent skip is a build failure.

## Independent review (clean-context)
- **The gate is keyed on a status, not on a note being touched**: a `TST-*` reaching `passing`, a requirement reaching `implemented`, a feature reaching `done`. Each requires an independent review pass per `../skills/independent-review/SKILL.md`.
- **One review per feature, sized to its diff** (ADR-0047). The review of a feature reaching `done` covers its linked tests and requirements, and records its verdict on each of them; they do not get separate reviews. Each review is two reviewers run at once on the same packet, their reports combined by the author (Edwin, 2026-09-18, after a measured comparison in project-os-dev TASK-0130); a person reviewing alone is enough. Small features that close together may share one review. A phase is never reviewed as a whole. The procedure, the packet the review starts from and its tool-call budget are stated once in `../skills/independent-review/SKILL.md`.
- **Independent means a clean context**: a session that starts from the notes and the diff alone, never the author's reasoning trace, and is not the session that authored the work. A human pass also satisfies this and remains the strongest option. Self-review is forbidden.
- Model family is not the gate (ADR-0013 records the experiment). The boundary is session and context, not vendor.
- **A gate runs at most two rounds** (ADR-0028). Round one reviews the work. Round two verifies the fixes to round one's blocking findings and nothing else — it is not a fresh sweep for new defects. Reason: past round two a reviewer produces more findings and fewer true ones per finding, and one change in this fleet was reviewed eight times, of which rounds four to seven found no code defect at all.
- **A finding is fixed in the feature that caused it** (ADR-0047, which replaces ADR-0028's severity bar). A finding about code the feature changed is fixed before the feature closes, whether or not it blocks; a test that cannot fail on the feature's main claim counts as such a finding. Blocking decides only whether round two runs: a finding blocks when it refutes a claim about behaviour or an acceptance criterion.
- **The filing bar.** A finding becomes an `ISS-*` only when its fix needs a decision the owner has not made, the defect is in code the feature did not change, or the fix is too large for the session. Anything else is fixed, or recorded in the reviewed note's review section and dropped. A stale figure, a wording nit or a duplicated history line is not an issue.
- **A third disagreement is adjudicated, not looped.** If round two still returns `changes-requested`, do not run round three. Run one exchange between the reviewer and a separate critic in which every disagreement cites specific code, put both positions in front of the adjudicator side by side rather than as a conversation, and hand the owner a decision. **The author never answers the reviewer in turns**: a reviewer facing a follow-up rebuttal abandons true findings, the more so when that rebuttal reasons at length and is wrong (ADR-0028 records the evidence).
- **A `CHG-*` note does not owe a review** (ADR-0019): the change itself is reviewed at the three gates above while the work is live, and reviewing the note later reviews the prose.
- **An acceptance test does not owe a review either.** It rests at `active` and never reaches `passing` (`STATUSES.md` `[[test]]`); the review of an acceptance test is the walk, and gating it would ask for the same evidence twice.
- Record the outcome in the reviewed note's frontmatter (`reviewed_by`, `review_date`, `review_round`, `review_verdict`).

## Verification expectations (generic)
- Prefer a reproducible command, test or check that demonstrates the change.
- If verification is manual, record the exact steps and expected outputs in the task or workflow note.
- For a test guarding a fix, record adequacy evidence (does the test fail when the fix is broken?): `TESTING.md`, "Test adequacy".
- The message the user reads is held to the same rule as the notes: before reporting progress, audit each claim against a tool result from this session, and report only work you can point to evidence for. If a test fails, say so with its output; if a step was skipped, say that; if something is not yet verified, say so. Reason: an evidence-free claim in chat is the fake `done` that ticked-with-evidence criteria keep out of notes.
