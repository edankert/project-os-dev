---
type: "[[issue]]"
id: ISS-0063
aliases: ["ISS-0063"]
title: "The walk sheet reads every acceptance note under docs/ and the cockpit reads only docs/tests/acceptance/; no repo has such a note today, so the divergence is latent rather than live"
status: open
owner: user:edwin
created: 2026-09-13
updated: 2026-09-18
source: ["Measured while landing TASK-0113 against your-trainer, 2026-09-13"]
question: "Should walked acceptance checks be allowed outside docs/tests/acceptance/? Recommendation: no. TESTING.md already says walked checks live there; automated ones with a command: may stay beside their feature."
severity: low
component: tooling
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[TASK-0113-The-Generator-And-Its-Fixture-Test]]"]
tests: []
---

# The sheet and the cockpit disagree about what the suite is

## Problem

Two tools meant to compute one walk read two different sets of notes. `tools/scripts/walk-sheet.py` treats every `[[test]]` at `level: acceptance` anywhere under `docs/` as a check, which is what `LIFECYCLE.md` "Test storage" allows — a feature-scoped check lives under `docs/features/<slug>/plan/tests/`. The cockpit's `acceptance.load_notes` globs `docs/tests/acceptance/TST-*.md` and nothing else. A check filed in the allowed second place would appear on a generated sheet and never on the cockpit's page, so a badge and a sheet would report different owed counts for one corpus — the disagreement ADR-0029 rule 7 exists to prevent.

**The measurement that opened this issue was wrong, and the correction matters more than the issue.** It reported 649 notes against 431 on your-trainer and blamed directory scope. The gap was **217 retired checks**: the generator read `type:` and `level:` and never `status:`, so it asked checks that had been retired. That is project-os-cockpit ISS-0303, fixed upstream on 2026-09-13, and with it fixed the two load the same 431 notes with no difference at all.

What is left is latent. Counted across the fleet the same day, **zero** acceptance notes live outside `docs/tests/acceptance/` in any repo — your-trainer 649/0, project-os-cockpit 39/0, project-os-deck 17/0, your-sudoku 64/0. The divergence is real in the code and has no instances, so it costs nothing today and would cost a wrong owed count the first time somebody files a check beside its feature.

## Evidence

- 2026-09-13, after the retired-check fix: `walk-sheet.load_checks` and `acceptance.load` both return **431** on your-trainer, with an empty difference. Owed sets agree exactly, 39 on android and 327 on ios.
- Before that fix the same two returned 649 and 431, the 218 extra being retired notes plus one ADR that merely mentions `level: acceptance` in its prose.
- `grep -rl "^level: acceptance" <repo>/docs | grep -v /docs/tests/acceptance/` finds no test note in any of the four repos that keep a suite.
- `project-os-cockpit/src/project_os_cockpit/acceptance.py:1089` — `sorted(checks_dir.glob("TST-*.md"))`, non-recursive.
- `tools/instructions/LIFECYCLE.md`, "Test storage (hybrid)" — a feature-scoped test is legal, and an acceptance check for a feature is named there explicitly.

## Next Actions

- [ ] Decide which scoping is the rule: the cockpit widens to every acceptance note under `docs/`, or `TESTING.md` narrows acceptance checks to `docs/tests/acceptance/` and `LIFECYCLE.md`'s hybrid rule stops applying to them. The second is closer to what all four repos already do.
- [ ] Whichever wins, state it once in `TESTING.md` and make both readers cite it.

## Checked against the template, 2026-09-18: a question for Edwin

The cockpit reads acceptance checks from one folder, while `walk-sheet.py` reads every `level: acceptance` note, and LIFECYCLE.md allows them inside a feature folder. This repo has 7 such notes, all automated, and keeps no ledgers, so nothing differs yet.

Checked as part of FEAT-0036 (TASK-0140).
