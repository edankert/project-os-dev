---
type: "[[issue]]"
id: ISS-0026
aliases: ["ISS-0026"]
title: "A TST note's ## Coverage section is a hand-written register of its own suite's assertions that nothing derives or checks, and other notes cite its entries as evidence — one register was wrong in three consecutive review rounds"
status: open
severity: medium
owner: user:edwin
created: 2026-07-30
updated: 2026-07-30
component: docs
source: ["project-os-cockpit ISS-0066, 2026-07-30 — four independent-review rounds on one TST note"]
phase: "[[PHASE-999-Parking-Lot]]"
related: []
depends: []
tests: []
---

# Coverage registers drift by hand

## The finding

The `TST-*` template carries a `## Coverage` section: a numbered prose list of what the suite asserts. **Nothing derives it from the suite and nothing checks it against the suite** — yet other notes cite its entries by name as evidence, and requirement and phase exit criteria are ticked against it.

In `project-os-cockpit`, four independent-review rounds on a single TST note each found the register describing its own suite inaccurately, in a different way:

| Round | Finding |
|---|---|
| 1 | A requirement criterion ticked with an evidence pointer that did not resolve |
| 2 | The register listed 11 items for a 24-assertion file, omitting all four new guards |
| 3 | An entry attributed a test that lives in a different file — one round after another entry was corrected for exactly that |
| 4 | Accurate. Verdict `approved` |

Two entries were **missing for three consecutive rounds** while being cited by name elsewhere.

## Why this is a format problem, not an author problem

Every individual fix was correct and cheap. What never happened was the register becoming *reliable* — because keeping it accurate means hand-syncing prose to code on every test change, and **nothing fails when that is skipped**.

This is the same class the system already solved twice and should recognise:

- **ADR-0009** — statuses were dual-written to notes and `SNAPSHOT.yaml` until `sync-snapshot.py` made the note the authored source and the snapshot derived.
- **ADR-0010** — a test's `status:` was hand-written until the runner began writing it from the exit code.

A Coverage register is the same dual-write with no sync step: the suite is the truth, the prose is a copy, and only the copy is read.

## Expected

Either the register is derived from the suite, or it stops being cited as evidence.

## Next Actions

- [ ] Decide which. Deriving it (a script that lists test names from the file the note declares, the way `sync-snapshot.py` derives counters) is closest to how this system has solved the same shape before
- [ ] If derived: the note declares the file, the script writes the list, and a `--check` mode fails on drift — matching `sync-snapshot.py`'s contract exactly
- [ ] If not derived: `TRACEABILITY.md` and `QUALITY.md` should stop treating a Coverage entry as a citable evidence pointer, and the template should say the section is commentary

## Notes

The narrow alternative — "review harder" — is what produced four rounds. The reviewer read the shrinking error count as convergence rather than a treadmill, which is fair for one note and does not scale to a fleet where nobody reviews four times.
