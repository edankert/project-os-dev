---
type: "[[task]]"
id: TASK-0167
aliases: ["TASK-0167"]
title: "Re-measure whether the docs-audit drift dimension still earns a cadence slot once the three checks exist"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["Edwin, 2026-09-25: 'Complete and test PHASE-0003 fully'"]
parent: "[[ISS-0052-Three-More-Drift-Classes-Should-Be-Checks]]"
effort: M
due: ""
depends: []
blocks: []
related: []
tests: []
verification_waiver: "A measurement: its evidence is the table below, reproducible by running validate-docs.py on worktrees of the two commits."
waiver_expires: 2026-12-25
---

# Re-measure whether the docs-audit drift dimension still earns a cadence slot once the three checks exist

## Definition of Done
- [x] With TASK-0164 to TASK-0166 in place, the drift classes of ADR-0026's table are counted again on this repo and the template: what the checks now catch, and what a sweep would still have to find.
- [x] The finding is recorded on ISS-0052 and ADR-0026, with a recommendation on the cadence slot.

## Result

**Measured 2026-09-25 (TASK-0167).** The four new checks were run, with today's validator, on the template at the two commits the drift passes read: `19ba330` (pass 11) and `e2bee28` (pass 12).

| Class | Checks at `19ba330` | Checks at `e2bee28` | What the passes found by hand |
|---|---|---|---|
| Index misses its directory | 4 indexes, 7 entries | 1 index, 2 entries | 8 instances across both passes |
| Enforced field undocumented | 12 fields | 12 fields | 3 instances, pass 12 |
| Citation resolves nowhere | 1 | 0 | 22 instances across both passes |

For indexes and fields, the checks find everything the passes found and more, in milliseconds on every commit; those two classes no longer need a sweep. For citations they find a small part: most of the 22 were a quote that does not say what the citing file claims, or a bare `ADR-####` that means a different decision, which only reading can judge. Together with the README trigger-list copies (the fifth class, decided "no") and rules restated in two files (ISS-0048's class, RULE-ONCE declined), the sweep's remaining work is reading for meaning.

**Recommendation.** The drift dimension keeps its cadence slot (release-prep and grooming, ADR-0026), with a narrower brief: skip what INDEX-COVERAGE, FIELD-UNDOCUMENTED, CITATION and BASE-STATUS report, and read for citations that misquote, restated rules and README copies. That cuts a pass's reading without dropping the classes only a reader finds. Changing the docs-audit skill's brief is Edwin's call and is not done here.
