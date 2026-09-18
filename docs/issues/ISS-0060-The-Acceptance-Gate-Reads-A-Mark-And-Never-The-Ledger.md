---
type: "[[issue]]"
id: ISS-0060
aliases: ["ISS-0060"]
title: "The validator's acceptance gate reads a mark: on the test note and never the release ledger, so a repository that keeps its verdicts in the ledger can never satisfy it — and on 2026-11-20 the warning becomes an error"
status: fixed
phase: ""
severity: medium
owner: user:edwin
created: 2026-09-09
updated: 2026-09-18
component: tools
source: ["Filed from project-os-deck on 2026-09-09; its own ISS-0016 carries the evidence and says the fix belongs here because tools/scripts/ is template-owned"]
related: ["[[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path]]", "[[project-os-cockpit#ADR-0037]]"]
tasks: []
tests: []
---

# The gate looks for the verdict where the ledger model stopped putting it

## Problem

**A feature that reaches `done` with its acceptance walk marked `pass` in the release ledger still produces a warning saying the walk is unsettled.** `tools/scripts/validate-docs.py`, `_acceptance_is_settled`, reads a `mark:` field in the test note's frontmatter. A repository on the ledger model does not put verdicts there: an acceptance test rests at `status: active` and its verdict is an event in `docs/releases/ledgers/*.json` (project-os-cockpit#ADR-0037, and `tools/instructions/STATUSES.md`, `[[test]]`). The word `ledger` appears nowhere in the validator.

**The vocabulary in the message is a generation behind as well.** It asks for a mark that is `done`, `incomplete` or `canceled`, which `tools/instructions/TAXONOMY.md` lists under "Legacy values, read forever and never written". The current words are `pass`, `partial`, `na`, `excused`, `blocked`, `question` and `fail`, and the ledger holds `pass`.

**It is a warning today and an error on 2026-11-20.** `PROMOTIONS` in the same file carries `"VERIFY-ACCEPTANCE": "2026-11-20"`. On that date every feature such a repository closes fails the build, for a rule its notes are designed not to satisfy.

## Repro

In `project-os-deck`, whose three walked features are `pass` in `docs/releases/ledgers/WORKING-app.json`:

```
$ bash tools/scripts/validate-docs.sh
WARN  [VERIFY-ACCEPTANCE] FEAT-0003 is done but the acceptance test TST-0012 covering it is not settled -- its mark is not done/incomplete/canceled
WARN  [VERIFY-ACCEPTANCE] FEAT-0007 is done but the acceptance test TST-0008 covering it is not settled -- its mark is not done/incomplete/canceled
validate-docs: OK
```

## Evidence

- `tools/scripts/validate-docs.py`, `_acceptance_is_settled` — reads `fm.get("mark")`, and nothing else.
- The same file's `PROMOTIONS` table — `"VERIFY-ACCEPTANCE": "2026-11-20"`.
- `grep -n "ledger" tools/scripts/validate-docs.py` returns only comments about `tools/GRANDFATHERED.yaml`.
- `project-os-deck/docs/issues/ISS-0016-The-Acceptance-Gate-Reads-A-Field-This-Repo-Does-Not-Use.md` — where this was found, with the same evidence.

## What a fix has to decide

**Two things, and the second is the one worth arguing about.**

**Where the verdict lives.** The gate should read the ledger where a repository has one, and keep reading `mark:` where it does not — both models are live across the fleet, and a repository that has not migrated must keep gating correctly. That is the same both-forms tolerance `_acceptance_is_settled` already applies to the character and word forms of a mark.

**Which vocabulary settles it.** `done`/`incomplete`/`canceled` are legacy; `pass`/`na`/`excused`/`reconciled` settle and `fail`/`blocked`/`question`/`partial` do not. The message should name the words the taxonomy actually has, because a person reading it goes looking for a field to write and finds one the taxonomy told them never to write.

**Why this is filed rather than patched downstream.** `tools/scripts/` is template-owned and `tools/scripts/sync-project-os.sh` overwrites a local patch, so a fix in a downstream repository lasts until the next sync.

## Next Actions
- [ ] Decide whether the gate reads the ledger, or declares which repositories it applies to
- [ ] Correct the vocabulary in the message either way, since it is wrong under both models

## Fixed, 2026-09-18

a978752: where `docs/releases/ledgers/` holds a ledger, VERIFY-ACCEPTANCE settles a check from it, the way `walk-sheet.py` resolves a ledger; other repos still read `mark:`. Warnings that could not be cleared dropped from 61 to 19 in project-os-cockpit and from 19 to 14 in project-os-deck. `test-ledger-checks.sh` gained 15 cases. project-os-cockpit keeps its own validator and still has the defect; that is its own work.

Checked as part of FEAT-0036 (TASK-0140).
