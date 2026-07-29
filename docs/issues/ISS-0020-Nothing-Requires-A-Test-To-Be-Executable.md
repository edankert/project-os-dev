---
type: "[[issue]]"
id: ISS-0020
aliases: ["ISS-0020"]
title: "Nothing requires a `TST-*` to carry a `command:`, and no metric distinguishes executable from manual tests — so the project cannot report how much of its verification actually runs"
status: open
severity: medium
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: tooling
source: ["intake 2026-07-29: articles repo, quality-without-reading thesis, finding 2"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0017, ADR-0010, REQ-0022, REQ-0023]
tests: []
---

# Nothing requires a test to be executable, and nothing measures the ratio

## Problem

Two halves, and the second is the one worth fixing first.

**Nothing requires `command:`.** [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] governs what happens *once* a test carries a command — the runner writes the status, hand-editing is an error. It says nothing about whether a test should carry one. The only place the validator raises the subject is `validate-docs.py:1457-1462`, in the manual branch:

```
%s is a manual test with no last_verified:; record when the procedure was last performed,
or give it a command: so it can be executed (%s)
```

The clause is an alternative *remedy* inside a message about a missing date. Supply `last_verified:` and the finding clears with no command in sight. The verification gate is fully satisfied by a manual test with a date, forever, as long as the date keeps being refreshed.

**Nothing measures the ratio.** `SNAPSHOT.md:96` defines the test metrics as: *"`tests_total` / `tests_passing` / `tests_failing`: all `TST-*`; by status `passing` / `failing`."* Status only. An executable test that a runner stamped `passing` and a manual test whose author typed `passing` are the same row in `metrics.counts`.

So the question *"how much of our verification actually runs?"* has no answer anywhere in the system — not in the snapshot, not in the validator, not in the cockpit. Under the thesis that prompted this, that ratio is the single best available proxy for whether a project's oracle is real, and it is the cheapest thing on this list to produce.

## Expected

`metrics.counts` distinguishes executable from manual tests, and the ratio is reportable without reading every `TST-*` note.

## Actual

Both are indistinguishable in every aggregate surface. In this repo the ratio happens to be knowable by inspection because there are only two tests; that is not a property that survives contact with a real project.

## Why the metric before the requirement

The instinct is to require `command:`. That should be resisted, for the reason ADR-0010 already gave: forcing a command round a judgement produces *fake* automation — a shell wrapper whose exit code encodes nothing, written to clear a gate. [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]] clause 2 is explicit that the answer to an unexecutable claim is to make it **visible and perishable**, not illegal, and manual tests already are both (`last_verified:`, `TEST-STALE`).

The metric is the honest intervention. It makes the ratio a number the project can look at and decide about, without any rule compelling a particular answer — which is also what makes it safe to add: it cannot be gamed into a false green, because it does not gate anything.

`ADR-0014`'s evidence tokens are ordered by strength for precisely this reason (`mutation:` > `test:` > `runtime:` > `human:` > `asserted:`), and the same logic applies one level up: count the strengths, don't outlaw the weak ones.

## Fix sketch

- `sync-snapshot.py` derives `tests_executable` (has `command:`) and `tests_manual` (no `command:`) into `metrics.counts`, alongside the existing status counts. Derived, per [[ADR-0009-Snapshot-Is-Generated|ADR-0009]] — never hand-written.
- `SNAPSHOT.md` documents both, in the same sentence that documents the existing three.
- Consider whether the validator reports the ratio informationally. Careful here: [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] forbids a permanent warning tier, and a ratio nobody is required to improve is exactly a permanent warning. If it is reported at all it should be a line in the summary, not a finding.
- The cockpit is the natural home for the ratio as a *surface*, and that is a separate repo's work.

Both new metrics are additive and cannot fail a build, so this needs no cutover and no grandfathering — which is the whole reason it is cheap.

## Not in scope

Requiring `command:` on any test, and any gate keyed on the ratio. If the measured ratio turns out to be alarming, that is the evidence for a follow-up decision; it is not this issue.

## Blast radius

Additive to `sync-snapshot.py` and `SNAPSHOT.md`, so every repo picks it up on the next sync with no migration. Two new keys appear in `metrics.counts` fleet-wide; `sync-snapshot.py --check` will report drift in CI on the first run after the change until each repo's snapshot is regenerated, which is the normal shape of a generator change (`TASK-0072`).

## Next Actions

- [ ] Add `tests_executable` / `tests_manual` to the generator and to `SNAPSHOT.md`.
- [ ] Measure the fleet-wide ratio once, and record the number — it is the input to any later decision about requiring commands.
- [ ] Decide whether the ratio is surfaced in the validator summary, the cockpit, or neither.
