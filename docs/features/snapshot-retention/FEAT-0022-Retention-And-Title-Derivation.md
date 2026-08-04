---
type: "[[feature]]"
id: FEAT-0022
aliases: ["FEAT-0022"]
title: "Retention runs on every sync, and `title` stops being a second copy: implements ADR-0018"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018", "ISS-0030", "your-trainer ISS-0371", "fleet measurement 2026-08-03/04"]
goal: "Make retention a property of the system rather than a duty nobody performs, and end title drift the way ADR-0009 ended status drift — with the narrative that grew into your-trainer's titles moved into the note files rather than truncated away or parked in the snapshot's scratch fields."
requirements: []
tasks: ["[[TASK-0082]]", "[[TASK-0083]]", "[[TASK-0084]]"]
release: ""
related: ["[[ADR-0018]]", "[[ADR-0009]]", "[[ISS-0030]]", "[[ISS-0031]]"]
tests: []
---

# Retention on every sync, and `title` stops being a second copy

## Goal

Implements [[ADR-0018-What-The-Generator-Owns|ADR-0018]]. Two changes to `sync-snapshot.py`, plus the one-time reconciliation the first of them requires.

- **Retention runs automatically**, inside the sync that already runs at pre-commit and in CI — not as a subcommand anyone has to remember, because ISS-0030 exists precisely because the remembering never happened.
- **`title` joins the derived set**, so the 657 drifted titles across the fleet are reconciled once and cannot recur.

## Why the title half may matter more than the pruning half

It is the counter-intuitive result and worth stating plainly, because the obvious priority is wrong.

`your-trainer`'s titles are **60% of its snapshot** — 231,506 of 386,354 bytes. Deriving them from the notes removes **28% of the file before a single entry is pruned**. The same change in `project-os-cockpit` and `project-os-dev` makes their files ~2% *larger*, because those repos abbreviated their snapshot titles instead of inflating them.

That two-way drift is the diagnosis: `title:` has no contract, so each repo invented one. Pruning removes entries that should not be there; title derivation removes a whole *class* of divergence, permanently.

## Scope

- **TASK-0082** — the prune step, run automatically after status sync.
- **TASK-0083** — `title` derived from the note, with a drift check for the transition.
- **TASK-0084** — reconcile the fleet's drifted titles, moving narrative into the note files where it earns its place.
- **TASK-0085** — the fleet rollout: inert by default, opt in per repo, cheapest first.

## Ordering, and why it is not the obvious one

**TASK-0083 before TASK-0082**, and TASK-0084 between them.

Pruning first would delete entries whose titles carry narrative that exists nowhere else — `your-trainer` has 413 titles that differ from their notes, and 0 of its 709 terminal entries carry `note:` prose, so ADR-0018's condition 6 holds none of them back. Prune first and that commentary goes to git history only. Derive titles first and the divergence is surfaced, triaged, and either relocated or discarded deliberately.

Measured on 2026-08-04, that risk is concrete rather than theoretical: of 405 measurable divergences in `your-trainer`, 227 are already >90% present in their note (safe to discard), 168 are partial, and **10 exist essentially nowhere else**.

## Out of scope

- **Serving orientation from the hook, and the query interface** ([[FEAT-0021-Serve-Orientation-Answer-Lookup|FEAT-0021]]). Deferred by decision on 2026-08-04; this feature is retention only.
- **Adding entries.** ADR-0018 is explicit that the generator may remove and never add; `--report-unregistered` stays advisory.
- **A `SNAP-RETENTION` validator check.** Once retention runs automatically the check would assert that the tool ran, which is worth having and is not needed to make the tool correct. Revisit after this lands.

## Risks

- **This is the first operation in the system that deletes lines from a tracked file**, and it will run in twelve repos. The rollout is [[TASK-0085-Fleet-Rollout|TASK-0085]] rather than a gesture at `TASK-0072`'s discipline: both halves ship **inert**, each repo opts in via its own snapshot key, and the order is ascending cost — the first genuine prune is `obsidian-supernote-sync` at three entries, `your-trainer` is last at 709.
- **Idempotence is the acceptance criterion, not a nicety.** A date-keyed window makes an untouched repo drift overnight and breaks `sync-snapshot.py --check` in CI. Count-based, per ADR-0018 and REQ-0019.
- **`your-trainer` is the stress case for both halves** — largest snapshot, most drifted titles, zero curated `note:` prose to protect entries. Anything that works there works everywhere.

## Acceptance

- [ ] A `done` task older than the retention window disappears from `items.*` on the next sync, in every repo, without anyone invoking anything.
- [ ] Running sync twice in a row produces no second diff; `--check` is clean on an untouched repo the following day.
- [ ] No note file is ever modified or deleted by the prune.
- [ ] An entry with non-empty `note:`/`goal:` is held from pruning AND reported; clearing the field releases the hold on the next run.
- [ ] Snapshot `title` matches note `title` for every registered item, fleet-wide, and drifting one is a validator finding.
- [ ] `sync-snapshot.py`'s header no longer disclaims a decision it now makes (ADR-0018's last consequence).
