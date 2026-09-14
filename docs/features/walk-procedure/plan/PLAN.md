---
type: "[[plan]]"
title: "Delivery plan — a written procedure per sitting, a validator, and the sheet that prints owed steps"
status: done
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
implements: ["[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
related: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[PHASE-0005-The-Walk-Reads-As-A-Script]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — the procedure

## Where the work lands

Every file changes in `~/Dev/repos/project-os`, except TASK-0123, which syncs into your-trainer and project-os-cockpit and records the result here.

## Delivery sequence

1. **[[TASK-0119-The-Procedure-Format|TASK-0119]]: the format.** Template, `SCHEMAS.md` entry and TESTING.md text. Nothing parses a shape that is not written down.
2. **[[TASK-0120-The-Procedure-Validator|TASK-0120]]: the validator.** Its fixture harness becomes TST-0010's command. Before the sheet uses procedures, so the sheet never prints an unchecked one.
3. **[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure|TASK-0121]]: the sheet.** `walk-sheet.py` filters a procedure to owed steps. Can start beside TASK-0120 once TASK-0119 lands.
4. **[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure|TASK-0122]]: the skill.** Needs the validator to call.
5. **[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit|TASK-0123]]: sync.** Last. Carries FEAT-0030's work too.

## Dependencies

- **Hard:** ADR-0045, accepted 2026-09-14 with its three open boxes answered: one file per sitting under `docs/tests/acceptance/walk/`, aiming to cover every live check, and expectation lines quoting the check's Expect text word for word. Nothing blocks TASK-0119.
- **Soft:** the cockpit bundles `walk-sheet.py` byte for byte, so the validator should live in or beside that module rather than in `validate-docs.py`, or the cockpit needs a second bundle. Decide in TASK-0120.
- **Downstream waits on this:** project-os-cockpit PHASE-044 starts once TASK-0119 fixes the format; your-trainer TASK-0905 (sync) and TASK-0906 (procedures) wait for TASK-0123.

## Answered questions

- **Where the validator runs.** Settled 2026-09-14: **both**. `walk-sheet.py --check` is the command a person runs and the one the two release skills call; `validate-docs.sh` also calls it, for every platform with a ledger, because the staleness the question worried about arrives as a **ledger event** and a ledger event *is* a commit — to `docs/releases/ledgers/*.json`. The code sits in `walk-sheet.py` so the cockpit keeps one byte-identical bundle. `validate-docs.sh` passes `--quiet`, so only a real disagreement speaks on a commit; the worklist remarks belong to the hand-run command. Recorded on [[TASK-0120-The-Procedure-Validator|TASK-0120]].

## What landed

All five tasks, 2026-09-14, in template commits c3cdb4c, a0c80e3 and 0f1b673. The soft dependency was taken up: the validator lives in the module the cockpit bundles, and `walk_sheet_bundled.py` is byte-identical again.
