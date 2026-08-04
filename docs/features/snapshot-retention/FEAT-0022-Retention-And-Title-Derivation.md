---
type: "[[feature]]"
id: FEAT-0022
aliases: ["FEAT-0022"]
title: "Retention runs on every sync, and `title` stops being a second copy: implements ADR-0018"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018", "ISS-0030", "your-trainer ISS-0371", "fleet measurement 2026-08-03/04"]
goal: "Make retention a property of the system rather than a duty nobody performs, and end title drift the way ADR-0009 ended status drift — with the narrative that grew into your-trainer's titles moved into the note files rather than truncated away or parked in the snapshot's scratch fields."
requirements: []
tasks: ["[[TASK-0082]]", "[[TASK-0083]]", "[[TASK-0084]]", "[[TASK-0085]]"]
release: ""
related: ["[[ADR-0018]]", "[[ADR-0009]]", "[[ISS-0030]]", "[[ISS-0031]]", "[[ISS-0032]]"]
tests: ["[[TST-0003]]"]
reviewed_by: model:claude-opus-5
review_date: 2026-08-04
review_verdict: changes-requested
review_note: "Clean-context independent review (fresh session, notes + diff only; same model family as the author, recorded here as provenance). Findings on [[ISS-0032]]. The design holds and its measurement is mostly exact — 659 drifted titles, 1,756 terminal / 142 held / 1,614 prunable, 75/659 verbatim containment, the −28% and +2% size effects, and every per-repo cell of TASK-0085's table all reproduce exactly on re-measurement. Five blocking defects, all but one an amendment leftover: ADR-0018's hold table (:98-103, :24) still publishes the pre-amendment figures — 19/58 and 36/238 reproduce only when `goal:` also holds, the rule dc101e5 removed, against 8/69 and 34/240 today; TASK-0082 contradicts itself on `goal:` at :36 vs :38, as does FEAT-0022:69; TASK-0082/0083/0084 each put fleet-wide completion in their DoD while TASK-0085 depends on all three, so no task can be ticked and this feature cannot close; TASK-0085 is missing from `tasks:` above though the body, its own `parent:` and the snapshot all carry it, and no validator check binds the two; and title derivation states no fail-safe where the prune does (TASK-0082:47), which blanks 9 entries fleet-wide whose notes are zero-byte or unparseable, with 161 CHG-* entries additionally unresolvable by ID. Seven non-blocking, including a condition-3 inversion test that cannot fail, and the 405/227/168/10 and 28-orphan figures which reproduce under no stated method. Defects are spread across all six notes: ADR-0018 (#1, #10), FEAT-0022 (#4, #7), TASK-0082 (#2, #6), TASK-0083 and TASK-0084 (#3, #5), TASK-0085 (#8, #11). Not stamped on the individual tasks."
---

# Retention on every sync, and `title` stops being a second copy

## Goal

Implements [[ADR-0018-What-The-Generator-Owns|ADR-0018]]. Two changes to `sync-snapshot.py`, plus the one-time reconciliation the first of them requires.

- **Retention runs automatically**, inside the sync that already runs at pre-commit and in CI — not as a subcommand anyone has to remember, because ISS-0030 exists precisely because the remembering never happened.
- **`title` joins the derived set**, so the 659 drifted titles across the fleet are reconciled once and cannot recur.

## Why the title half may matter more than the pruning half

It is the counter-intuitive result and worth stating plainly, because the obvious priority is wrong.

`your-trainer`'s titles are **60% of its snapshot** — 231,506 of 386,354 bytes. Deriving them from the notes removes **28% of the file before a single entry is pruned**. The same change in `project-os-cockpit` and `project-os-dev` makes their files ~2% *larger*, because those repos abbreviated their snapshot titles instead of inflating them.

That two-way drift is the diagnosis: `title:` has no contract, so each repo invented one. Pruning removes entries that should not be there; title derivation removes a whole *class* of divergence, permanently.

## Scope

- **TASK-0082** — the prune step, run automatically after status sync.
- **TASK-0083** — `title` derived from the note, with a drift check for the transition.
- **TASK-0084** — reconcile the fleet's drifted titles, moving narrative into the note files where it earns its place.
- **TASK-0085** — the fleet rollout: inert by default, opt in per repo, dogfood repo first and the largest last.

## Ordering, and why it is not the obvious one

**TASK-0083 before TASK-0082**, and TASK-0084 between them.

Pruning first would delete entries whose titles carry narrative that exists nowhere else — `your-trainer` has 413 titles that differ from their notes, and 0 of its 709 terminal entries carry `note:` prose, so ADR-0018's condition 6 holds none of them back. Prune first and that commentary goes to git history only. Derive titles first and the divergence is surfaced, triaged, and either relocated or discarded deliberately.

Measured on 2026-08-04, that risk is concrete rather than theoretical: of `your-trainer`'s 413 drifted titles, 212 are >90% covered by their note (safe to discard), 193 are partially covered, and **8 exist essentially nowhere else**.

## Out of scope

- **Serving orientation from the hook, and the query interface** ([[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]]). Deferred by decision on 2026-08-04; this feature is retention only.
- **Adding entries.** ADR-0018 is explicit that the generator may remove and never add; `--report-unregistered` stays advisory.
- **A `SNAP-RETENTION` validator check.** Once retention runs automatically the check would assert that the tool ran, which is worth having and is not needed to make the tool correct. Revisit after this lands.

## Risks

- **This is the first operation in the system that deletes lines from a tracked file**, and it will run in twelve repos. The rollout is [[TASK-0085-Fleet-Rollout|TASK-0085]] rather than a gesture at `TASK-0072`'s discipline: both halves ship **inert**, each repo opts in via its own snapshot key, and and the order puts `project-os-dev` first among repos with content (dogfooding: defects surface in minutes) with `your-trainer` last at 709 entries.
- **Idempotence is the acceptance criterion, not a nicety.** A date-keyed window makes an untouched repo drift overnight and breaks `sync-snapshot.py --check` in CI. Count-based, per ADR-0018 and REQ-0019.
- **`your-trainer` is the stress case for both halves** — largest snapshot, most drifted titles, zero curated `note:` prose to protect entries. Anything that works there works everywhere.

## Acceptance

- [x] In a repo that has opted in, a `done` task outside the count-based retention window disappears from `items.*` on the next sync, without anyone invoking anything. A repo that has not opted in is unaffected — that is the design (`TASK-0085`), not a gap.
- [x] Running sync twice in a row produces no second diff; `--check` is clean on an untouched repo the following day.
- [x] No note file is ever modified or deleted by the prune.
- [x] An entry with non-empty `note:` is held from pruning AND reported; clearing the field releases the hold on the next run. (`goal:` does not hold — it is derived under ADR-0018 rule 1.)
- [x] In a repo that has opted in, snapshot `title` matches note `title` for every registered item whose note supplies one. Whether a drift *check* survives the migration is `TASK-0083`'s decision — it argues for deleting it once derivation makes drift structurally impossible, per ADR-0011's objection to permanently-silent rules.
- [x] `sync-snapshot.py`'s header no longer disclaims a decision it now makes (ADR-0018's last consequence).
