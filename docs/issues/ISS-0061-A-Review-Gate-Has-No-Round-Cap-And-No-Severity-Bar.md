---
type: "[[issue]]"
id: ISS-0061
aliases: ["ISS-0061"]
title: "A review gate loops without a cap and any true finding blocks it, so one change was reviewed eight times and four of those rounds found no code defect"
status: fixed
phase: "[[PHASE-0003]]"
severity: medium
owner: user:edwin
created: 2026-09-10
updated: "2026-09-10"
source: ["Edwin, 2026-09-10: 'another review cycle seems to be going on forever'"]
component: docs
parent: ""
related: ["[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]", "[[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them]]", "[[ISS-0034-Cockpit-Features-Done-Still-Short-And-The-Suite-Does-Not-Guard-Either-Fix]]", "[[ISS-0035-Metric-Fix-Missed-The-Bundled-Validators-And-The-Notes-Still-Describe-Round-Two]]", "[[ISS-0036-Round-Four-Engineering-Resolved-Record-Still-Misstates-It]]", "[[ISS-0037-Round-Five-Corrections-Landed-On-One-Note-Of-Two]]", "[[ISS-0038-The-Seventeen-Names-Fourteen-Files-That-Do-Supply-Titles]]", "[[ISS-0039-The-Restatement-Reached-Three-Surfaces-Of-Four]]", "[[ADR-0026-When-A-Drift-Sweep-Stops]]"]
tests: []
---

# A review gate loops without a cap and any true finding blocks it

## Problem

The independent-review gate has no round cap and no severity bar, so a reviewer's smallest true observation holds a terminal status shut for another full round. One change here was reviewed eight times, and rounds four through seven found no code defect at all — each blocked on a stale number in a note. The person waiting on the work sees a review that does not end.

> [!quote] As reported — 2026-09-10 (user:edwin)
> At the moment, I notice that another review cycle seems to be going on forever.

## Repro

```bash
# The rule that loops, with no cap and no severity qualifier anywhere near it:
grep -n "and loop" tools/skills/independent-review/SKILL.md
# 50: ... file `ISS-*` notes for the findings, keep the item out of terminal status, and loop.

# Nothing in the gate bounds rounds or grades findings:
grep -rn -i -E "round|budget|severity|blocking" tools/instructions/QUALITY.md
# (no match)

# The eight-round review, and what its late rounds found:
sed -n '88p' docs/changes/CHG-20260804-Retention-And-Field-Derivation.md

# The severity of each round's blocking issue, in order:
for n in 0033 0034 0035 0036 0037 0038 0039; do
  f=$(ls docs/issues/ISS-$n-*.md)
  echo "ISS-$n $(grep -m1 '^severity:' $f) $(grep -m1 '^status:' $f)"
done
```

## Expected

A gate that ends. Round one reviews the work, round two verifies the fixes, and a finding that does not refute a behavioural claim or an acceptance criterion is filed rather than blocking.

## Actual

The loop is unbounded and every true finding is a blocker. The eight-round review on `CHG-20260804` went: three rounds of real engineering defects, then four rounds that found none and blocked on the record, then approval. The seven issues those rounds produced carry severities `high, medium, medium, low, low, low, low` — a monotonic decay in which each `low` blocked exactly as hard as the `high`. All seven are still `open` five weeks later, so the loop also left a backlog it did not clear.

## Evidence

- `tools/skills/independent-review/SKILL.md:50` — "keep the item out of terminal status, and loop", with no cap.
- `tools/instructions/QUALITY.md`, "Independent review (clean-context)" — six bullets, none about rounds or severity.
- `docs/changes/CHG-20260804-Retention-And-Field-Derivation.md:88` — "Reviewed clean-context **eight times** ... Rounds four to seven each found **none**".
- `docs/issues/ISS-0033-*.md` through `docs/issues/ISS-0039-*.md` — one issue per round, severity decaying `high → low`, all `open`.

**Sibling search: a sibling family exists** (searched: `review round`, `review cycle`, `review gate`, `independent review` over `docs/issues/`). ISS-0033 through ISS-0039 are seven issues of exactly this kind, one per round of a single change, and ISS-0036 through ISS-0039 each open by stating the engineering was clean for another consecutive round. Seven is well past the second-instance harvest trigger in `tools/skills/issue-intake/SKILL.md` step 2, so the family nominated a rule rather than an eighth one-off: [[ADR-0028-A-Review-Gate-Runs-Two-Rounds|ADR-0028]].

**Risk scan: no trigger applies.** No new dependency, env var, artifact path, long-running step or credential surface — the change edits two instruction files. The one hazard is stated in ADR-0028's consequences rather than as a `RISK-*`: a gate may now close with true findings outstanding, which moves them onto `triage` and onto grooming.

## Next Actions

- [x] Research whether the gate should copy ADR-0026's parallel-ensemble shape, and whether reviewers exchanging positions helps — recorded in ADR-0028's Context.
- [x] Decide: [[ADR-0028-A-Review-Gate-Runs-Two-Rounds|ADR-0028]], Option 4, accepted 2026-09-10.
- [x] Land the cap, the severity bar and the escalation rule in the template's `QUALITY.md`, and link them from `independent-review/SKILL.md` step 5.
- [x] Sync the vendored copies in this repo.
- [ ] The cap is unchecked until [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]] lands. Carried there, not here.
