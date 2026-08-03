---
type: "[[issue]]"
id: ISS-0030
aliases: ["ISS-0030"]
title: "Retention is a policy nothing performs, configured by three flags no code reads, and its normative rule still names the `closed` status ADR-0008 deleted — the fleet's snapshots have grown to 96k tokens and are re-served on every request"
status: open
severity: medium
owner: user:edwin
created: 2026-08-03
updated: 2026-08-03
component: tooling
source: ["fleet measurement 2026-08-03: 590 sessions, 19.3B cache-read tokens", "downstream:your-trainer/ISS-0371"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0008, ADR-0009, ADR-0016, REQ-0019, REQ-0020, ISS-0011]
tests: []
---

# Retention is a policy nothing performs

## Problem

`SNAPSHOT.md` states the rule: *"The snapshot is not a full historical database."* Three mechanisms were supposed to hold that line. None of them does.

**1. Nothing prunes.** `sync-snapshot.py` lists `retention` under `LEFT ALONE`, deliberately. Pruning is a manual duty owed at every close-out, performed by an agent, checked by nothing.

**2. The configuration is decorative.** Every repo carries three retention flags:

```yaml
keep_closed_issues_in_snapshot: false
keep_done_tasks_in_snapshot: false
keep_done_features_in_snapshot: false
```

`grep -rn` across `tools/` in both this repo and the template returns **no script reading any of them**. They are documentation of an intention shaped like configuration, which is worse than no configuration: `your-trainer` sets `keep_closed_issues_in_snapshot: false` and retains 205 `fixed` issues, and nothing about that file suggests the flag is inert.

**3. The normative rule names a status that no longer exists.** `SNAPSHOT.md:117`:

```
- issues: anything not `closed`
```

[[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]] deleted issue `closed` and merged it into `fixed`. An agent applying that rule literally retains every `fixed` issue forever — which is exactly what the fleet has done. This is the [[ISS-0011-Phase-Resolved-Kept-Wont-Fix|ISS-0011]] shape a third time: a status rename that missed a consumer, silently, because nothing compares prose to code. The adjacent lines are fine — `risks: anything not closed` is still correct, because risks genuinely close — which is precisely why the stale line reads as plausible.

**4. No check exists.** The only retention code in the validator is `DEFER-RETENTION`, which enforces the *opposite* concern (deferred items must never be pruned). Nothing looks at the accumulation.

## Measured cost

Snapshot sizes across the fleet, 2026-08-03:

| repo | bytes | ~tokens |
|---|---:|---:|
| your-trainer | 386,354 | **~96,600** |
| project-os-cockpit | 199,970 | ~50,000 |
| your-health | 174,517 | ~43,600 |
| your-applications.com | 153,865 | ~38,500 |
| project-os-dev | 61,560 | ~15,400 |
| your-sudoku | 58,468 | ~14,600 |
| project-os (template) | 2,845 | ~700 |

`your-trainer` holds 1,065 items of which **709 are terminal** (451 `done` tasks, 205 `fixed` issues, 53 `done` features).

The snapshot is loaded at session start and re-served on every subsequent request. Measured across 590 sessions in `~/.claude/projects`: **cache reads are 19.3 billion tokens, 70% of indicative spend**, against 11% for actual generation. For `your-trainer` alone — 449 sessions — re-serving its snapshot costs on the order of 1.7 billion cache-read tokens, roughly $2,600 at Opus list.

The four largest snapshots are the four oldest active repos. The correlation is with age, not with complexity, which is what identifies this as accumulation rather than legitimate size.

## What this issue is *not* asking for

`TASK-0063` ("Encode retention as generator policy") already tried this and was **cancelled on evidence**, and that decision should not be relitigated. A shadow run of the whole-file generator against all 10 repos would have added 180 items, dropped 153, and destroyed ~80 lines of curated comments. `sync-snapshot.py`'s header records the conclusion precisely:

> a snapshot is not a pure function of `docs/`. It is duplication *plus curation*

That holds. Membership is a curation decision, and a generator that computes it destroys the curated half to fix the duplicated half.

TASK-0063's cancellation note was also explicit that the motivation survived it:

> The underlying motivation stands and is not lost — it is recorded in REQ-0020's amendment as a legitimate future target, to be pursued through a mechanism that does not require generating the snapshot.

**That mechanism was never built.** This issue is that gap: the motivation was preserved in a note and then nothing happened for six weeks while every snapshot in the fleet kept growing. A future target with no owner, no task and no check is indistinguishable from a dropped one.

## Expected

Either retention is performed, or it is enforced, or it stops being claimed. The current state — claimed in prose, configured by dead flags, performed by nobody, checked by nothing — is the worst of the three.

## Actual

Twelve repos carrying a policy that exists only as a sentence, four of them with snapshots between 38k and 97k tokens riding on every request.

## Options, none of which requires generating the snapshot

Listed because the choice is a decision, not an implementation detail, and the cancelled task's constraint rules out the obvious answer.

1. **A validator finding.** `SNAP-RETENTION` reports terminal items retained beyond a reproducible window. Costs nothing to run, needs no generation, makes the manual duty visible instead of assumed. Constrained by [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]]: it must be an error with a dated cutover, or not exist — so the fleet backfill has to precede it, exactly as [[ISS-0007]] taught.
2. **A prune subcommand.** `sync-snapshot.py --prune`, run deliberately by a human or agent, never automatically. It sidesteps the cancellation entirely: the objection was to *generating* membership on every run, not to a tool that performs a curation decision when asked. This is the option most consistent with what was actually rejected.
3. **Delete the three flags.** If retention stays a judgement call, configuration that no code reads should not exist. Cheapest, and honest.

Options 1 and 2 compose well; 3 is orthogonal and probably right regardless.

Whatever is chosen, `SNAPSHOT.md:117` must be corrected to `fixed` independently — that line is simply wrong today and misleads any agent that reads it.

## Relationship to ADR-0016

The manual-duty framing is a live instance of what [[ADR-0016-Ceremony-Proportionate-To-The-Change|ADR-0016]] (proposed) argues about. Retention is ceremony assigned to close-out, unenforced, and therefore skipped — and the skip is invisible because a bloated snapshot looks exactly like a busy project. Whichever option is chosen should note that a duty nobody can see being skipped is not a duty.

## Blast radius

Every repo in the fleet. The fix to the stale `SNAPSHOT.md` line propagates through `sync-project-os.sh`; the flags exist in all twelve snapshots; any new check needs a fleet-wide count before it is armed, per ISS-0007.

## Next Actions

- [ ] Correct `SNAPSHOT.md:117` from `closed` to `fixed`, independent of the larger decision — it is wrong today.
- [ ] Decide between the validator finding, the prune subcommand, and deleting the flags; record it as an ADR if the answer is anything other than "delete the flags".
- [ ] Measure the fleet-wide terminal-item population before arming any check (ISS-0007 precedent).
- [ ] Confirm whether `recent_changes_max: 25` is honoured anywhere, or is a fourth dead key.
- [ ] Link the downstream instances: `your-trainer` ISS-0371 (filed), and check `project-os-cockpit`, `your-health` and `your-applications.com`, which are on the same curve.
- [ ] Consider whether `SNAP-RETENTION` belongs in the ISS-0011 family of "one fact restated where nothing compares the copies" — the flags, the prose rule and the absent implementation are three statements of one policy that already disagree.
