---
type: "[[adr]]"
id: ADR-0007
aliases: ["ADR-0007"]
title: "Requirement terminality is `implemented` (retire `verified`); a requirement implements at most one feature; features gate on their requirements' criteria"
status: accepted
owner: user:edwin
created: 2026-07-24
updated: 2026-07-24
source: ["downstream:your-sudoku"]
decision: "Retire the requirement `verified` status so `implemented` is terminal and gated on acceptance-criteria evidence; make `implements:` name at most one feature (deleting the many-to-many case); add the missing reverse gate so a feature cannot be `done` until every requirement that names it has its criteria resolved, applied forward-only. The status of feature-less requirements (constraints vs unlinked deliverables) is deferred to a separate triage, not decided here"
context: "Across 7 downstream repos 79 requirements are `verified`; 56 (71%) reference no test and 0 carry a verification_waiver — the requirement-level test gate is satisfied almost nowhere, while the parallel evidence (TST notes, ticked criteria) already lives elsewhere. Separately, 190 features are `done` of which 177 (93%) passed no test-or-waiver gate, and nothing checks that a feature's requirements are satisfied before it closes"
alternatives:
  - "Keep `verified` and enforce the test gate harder — rejected: 71% non-compliance over months across every repo is a signal the requirement-level gate is the wrong instrument, not that seven repos are all negligent; verification already lives in TST notes and acceptance checkboxes"
  - "Auto-advance requirements to `verified` when their feature closes — rejected: promotes 257 requirements on a feature-done gate that is itself 93% unenforced; it moves the false claim to a status with less scrutiny (one word vs enumerated criteria) rather than removing it"
  - "Per-project switch (requirement_verification: on|off) — rejected: formalises the drift this investigation uncovered and forces every agent to check a repo's mode before reading a status"
  - "Keep requirement→feature many-to-many and gate the last feature to close — rejected: makes closure order-dependent (whoever closes last inherits a sibling's unfinished criteria); only 10 of 444 requirements are many-to-many, so deleting the case is cheaper than modelling it"
  - "Introduce a requirement kind: (functional | constraint) now — rejected: the ~15 feature-less 'constraints' are heterogeneous (product policies → ADR-shaped, design conventions → styleguide, build invariants → fitness functions/tests) and several are just mislinked deliverables; a single bucket for them would be a grab-bag designed ahead of triage. Deferred: triage first, add a mechanism only against a proven residue"
consequences:
  - "`verified` is removed from the requirement taxonomy; `implemented` becomes terminal and REQ-BOXES becomes an error (not a warning) at terminal — the acceptance checkboxes become the enforced evidence surface"
  - "Requirement verification does not disappear: it lives in TST-* notes (their own passing/failing status) and in per-criterion evidence pointers; what is retired is recording it a *second* time as a requirement status word"
  - "`implements:` names at most one feature (scalar, not a list); the 10 existing many-to-many requirements are migrated by picking the true owner or splitting + duplicating criteria — duplication is deliberate and may drift, accepted for ~10 notes as the price of unambiguous ownership"
  - "A feature-less requirement gates no feature automatically (the reverse gate only inspects requirements that name the feature), so the model works without a constraint marker; whether each feature-less requirement is a legitimate constraint or an unlinked deliverable is decided by a follow-up triage, not this ADR"
  - "The missing reverse gate is added: a feature cannot be `done` while any requirement that names it has unresolved criteria (unless that requirement is descoped) — applied FORWARD-ONLY; the 114 already-`done` features whose linked criteria are unresolved are grandfathered"
  - "This revises ADR-0006: its `implemented → verified` clause and its 'shared requirements advance when the last feature closes' consequence are removed; its evidence-based ticking, reconcile-never-tick-to-fit, approval-precedes-implementation, and canonical-surfaces clauses are retained"
  - "Cockpit: `implemented` moves from the Delivered band to Done (it is now terminal), partly unwinding the amber Delivered band added 2026-07-22; a second cockpit release and 9-repo sync follow"
  - "Migration touches template + validator, ~79 `verified → implemented` demotions, 10 many-to-many splits/reassignments, and 5 field-drift link fixes; the feature-less requirements are triaged separately (see follow-up; [[ISS-0005-Feature-Less-Requirement-Triage]] resolved 14 of 23 and left 9 for a filing decision)"
supersedes: ""
superseded: ""
related: [ADR-0006, ADR-0005, ADR-0004]
---

# Requirement terminality and ownership

## Context

This decision comes out of a downstream investigation in `../your-sudoku` that started as "requirements marked `implemented` never show as completed in the cockpit" and unwound into several coupled facts about how the template models requirement completion. All figures below are measured across the 9 project-os repos on this machine (7 of which have requirements).

**1. The requirement-level `verified` gate is satisfied almost nowhere.** Of 79 `verified` requirements, only 23 (29%) reference a `TST-*` note; 56 (71%) reference no test at all, and **not one** of the 79 carries a `verification_waiver` — the single instrument `QUALITY.md` provides for going terminal without passing tests has never been used, in any repo, once. Where a reason is stated it is most often "the implementing feature is done" (feature completion used as a proxy) or an undocumented manual pass; the largest bucket states no reason at all.

**2. Nothing enforces it, because the gate is opt-in.** `validate-docs.py`'s VERIFY check loops over an item's *linked* tests and fires only once the item is already terminal. No link → empty loop → silent pass. You are audited only if you already complied. This is why 71% sailed through and why zero waivers were ever demanded.

**3. The feature gate is no stronger.** 190 features are `done`; 177 (93%) have neither a linked test nor a waiver. "Feature done" today means "every task was marked done by the same agent that marked them done" — self-report, not verification. So routing requirement closure *through* feature-done (a tempting simplification) would promote 257 requirements on a gate that has never fired.

**4. The relationship is one-feature-to-many-requirements, with a 10-note exception.** Requirements link exactly one feature in 375 of 385 cases; only 10 are many-to-many. Separately, some requirements have no feature link at all — a mix of unlinked deliverables (a gap), false orphans linked via the older `specifies:`/`scope:` field, and genuine cross-cutting invariants. That mix is heterogeneous enough that classifying it is its own task; this ADR deliberately does not. (A figure of 59 was quoted here when this ADR was written; the triage in [[ISS-0005-Feature-Less-Requirement-Triage]] established the true count as **23** — the original scan read only single-line `implements:` and missed block-form YAML lists.)

Together these say: `verified` is a status that means nothing in practice, the completion gate runs the wrong direction (or not at all), and the many-to-many case is a rounding error worth deleting.

## Decision

### 1. Retire `verified`; `implemented` is terminal

The requirement lifecycle becomes `draft → approved → implemented`, with `implemented` terminal. `retired`, `deferred`, `cancelled`, and `superseded` are unchanged. A requirement is `implemented` when its acceptance criteria are each **ticked with evidence or reconciled** (amended/superseded), per ADR-0006 — which this ADR keeps. `REQ-BOXES` is promoted from warning to **error** at the terminal status: a terminal requirement with an unticked, unreconciled criterion is a build failure. The acceptance checkboxes, not a status word, are the evidence surface.

Verification is not abandoned. It lives where it is actually done: `TST-*` notes carry their own `passing`/`failing` status, and each ticked criterion carries an evidence pointer. What is removed is the redundant second ledger — re-recording verification as a requirement status that, across 1,200+ notes, was set on delivery or on nothing far more often than on proof.

### 2. A requirement implements at most one feature

`implements:` is a **scalar** (`[[FEAT-…]]`) or empty — never a list of two or more. A requirement naming two or more features is a validator error. The 10 existing many-to-many requirements are migrated case by case: pick the true owner and drop the rest, or split into per-feature requirements and duplicate the shared criteria. Duplication can drift and is accepted deliberately for ~10 notes — unambiguous ownership is worth more than normalisation at this scale.

This ADR does **not** decide what a *zero*-feature requirement means. Some are unlinked deliverables (a gap to fix), some are genuine feature-exempt invariants, five are links misfiled under `specifies:`/`scope:`. Sorting them is a separate triage (see Follow-up). Until then, zero features is permitted, not an error.

### 3. Features gate on their requirements' criteria (the missing reverse check)

A feature may not become `done` while any requirement that **names it in `implements:`** has an unresolved acceptance criterion — unless that requirement is descoped (`deferred`/`cancelled`/`superseded`). Because clause 2 makes ownership at-most-one, this is fully mechanical: the feature owns the whole of each requirement that names it, so "criteria resolved" is unambiguous, with no shared-requirement / last-to-close subtlety.

A feature-less requirement names no feature, so it gates nothing — which is exactly the behaviour a cross-cutting invariant should have, achieved without any `kind:` marker. The model is correct whether or not the triage later adds one.

This gate is **forward-only**. It applies to features closing after this ADR is implemented. The 114 already-`done` features whose linked criteria are currently unresolved are grandfathered; enforcing retroactively would red every repo's CI on the next commit and punishes history for a rule that did not exist when the work closed.

### 4. Cockpit follows

`implemented` is now terminal, so in `project_os_cockpit/statuses.py` it moves from the Delivered band to Done. This partly unwinds the amber Delivered band introduced 2026-07-22 (ISS-0023) — Delivered keeps `staged`/`monitoring`, which are still genuinely non-terminal. A second cockpit release and template sync propagate it.

## Relationship to ADR-0006

ADR-0006 established evidence-based advancement and is **kept**, with two revisions:

- Its clause "`implemented → verified` remains gated on passing `TST-*`" is void — `verified` no longer exists.
- Its consequence "requirements shared by several features only advance when the last one closes" is void — shared requirements no longer exist (clause 2).

Retained from ADR-0006: tick only with evidence; reconcile, never tick to fit; approval precedes implementation; frontmatter `acceptance:` is criteria of record and body checkboxes are the verification record.

## Consequences

See frontmatter for the full list. The load-bearing ones: `implemented` becomes an honest terminal state that means "delivered, criteria evidenced", enforced rather than advisory; a feature can no longer close over unbuilt requirements; and the many-to-many ambiguity is deleted rather than modelled. The cost is a one-time migration (79 demotions, 10 splits, 5 link fixes) and the loss of a glance-level "proven vs delivered" distinction that, in 56 of 79 cases, was not true anyway — it survives, queryable, in the TST links and checkboxes.

## Follow-up (out of scope for this ADR)

The 59 feature-less requirements are triaged separately, because they are not one kind of thing:

- **Unlinked deliverables** (e.g. "Healthspan Score", "Strava OAuth Callback Page") — assign the owning feature. These are the gap clause 2 leaves open.
- **Field-drift orphans** (5) — feature named in `specifies:`/`scope:` but not `implements:`; move the link.
- **Product/architecture policies** ("No advertisements", "Data sovereignty", "Static HTML only", "Privacy/local-first") — likely belong as ADRs.
- **Design-system conventions** ("One hue per metric", "Action-surface button layout") — likely belong in a styleguide / `reference` note.
- **Build-enforced invariants** ("Translation parity enforced by build-time checks") — likely belong as tests / fitness functions.

Only if a residue remains that is genuinely a feature-exempt, verifiable requirement fitting none of those homes should a mechanism (a `kind:` field, not a new type — far less surface, no ID churn) be added, in its own ADR written against the real leftovers rather than a guessed category.

## Implementation — landed 2026-07-24

1. `STATUSES.md`, `SCHEMAS.md`, `requirement.md` template — retire `verified`; make `implements:` scalar.
2. `QUALITY.md`, `close-out`, `status-transition`, `test-authoring`, `independent-review`, `release-verification` skills — drop the `verified` step; re-anchor independent review on TST/CHG notes; rewrite advancement so criteria-resolution gates feature-done and the status stamp is its consequence.
3. `validate-docs.py` — `TERMINAL["requirements"] = "implemented"`; REQ-BOXES → error at terminal; new FEATURE-REQ forward-only gate; `implements:` at-most-one cardinality check.
4. `statuses.py` (cockpit) — `implemented` Delivered → Done; release + sync.
5. Data migration across repos — demote 79 `verified`, split/reassign 10 many-to-many. The remaining feature-less requirements are handled by the separate triage above.

### Outcome

All five landed; every one of the 9 repos validates clean.

- **79 requirements** demoted `verified → implemented` (your-health 39, project-os-cockpit 15, edankert.com 9, your-applications.com 7, obsidian-supernote-sync 4, your-trainer 3, your-sudoku 2).
- **11 REQ-OWNER violations** resolved — one more than the 10 forecast, because the scan that produced the estimate read only wikilink-form `implements:` and missed a bare-ID note. Each kept its true owner in `implements:`; the displaced features moved to `related:` so no link was lost.
- **2 new findings**, surfaced by `implemented` becoming terminal and therefore test-gated for the first time: your-sudoku REQ-0086 and REQ-0087 were `implemented` while their only linked test (TST-0013) is `blocked` — the OpenCV/ML-Kit cases have never executed — and their feature FEAT-0022 is still `in-progress`. Both demoted to `approved`. This is precisely the class of claim the ADR exists to stop, caught within minutes of the gate going live.
- **Forward-only worked as designed**: 114 grandfathered features and ~200 pre-existing unresolved criteria report as warnings, not errors, so no repo's CI broke. Post-cutover work is held to the gate.
- The parity test written for the earlier Delivered band ([[TST-0019]] in project-os-cockpit) failed 7 of 13 cases the moment `statuses.py` changed, naming every stale surface — the intended behaviour, and the reason the cockpit half took one pass instead of six.
