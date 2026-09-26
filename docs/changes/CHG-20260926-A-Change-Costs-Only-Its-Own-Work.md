---
type: "[[change]]"
id: CHG-20260926-A-Change-Costs-Only-Its-Own-Work
title: "Commits and stops take seconds, each fact is written once, and finished notes move out of the way"
status: merged
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[PHASE-0009-A-Change-Costs-Only-Its-Own-Work]]", "[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
commit: "project-os 97e97e1..8f524e6"
pr: ""
impacts: []
issues: ["[[ISS-0087]]", "[[ISS-0088]]", "[[ISS-0089]]", "[[ISS-0090]]", "[[ISS-0091]]", "[[ISS-0092]]", "[[ISS-0093]]", "[[ISS-0094]]", "[[ISS-0095]]", "[[ISS-0096]]", "[[ISS-0097]]", "[[ISS-0098]]", "[[ISS-0099]]", "[[ISS-0100]]", "[[ISS-0101]]", "[[ISS-0102]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[ADR-0049-A-Walk-Step-May-Cite-A-Check-Without-Quoting-It]]"]
---

# Commits and stops take seconds, each fact is written once, and finished notes move out of the way

## Summary

On your-trainer a commit now waits 2.2 s in the pre-commit hook instead of 54.9 s, and a stop after a write 2.1 s instead of 39.9 s. A task is written once, on the task; the lists that name it are generated. Finished tickets whose release is out can move to `docs/archive/`, out of search and out of the validator's content checks.

## Impact

- No screen changed: the template's scripts, hooks and instructions, and this repo's notes.

What an agent or a maintainer notices:

- **The checks answer in seconds.** Every note is parsed once, with libyaml, and cached on disk by path, size and mtime (`validate-docs.py`, `note-index.py`). `validate-docs.sh` ends with one verdict line for every step, and walk problems start with `ERROR [WALK]`. Both Stop hooks sync the snapshot before validating.
- **Each fact is written once.** With `retention.derive_lists: true` (on in this repo), the sync writes a parent's `tasks:`, a phase note's lists, the snapshot's copies and a live task's snapshot entry from each child's `parent:` and `phase:` (`derive-lists.py`). Supersession is written on the new note, and the sync stamps the old note's pointer and status (`derive-pointers.py`). A feature filed for later gets its feature note only.
- **Walk steps may cite a check by its tag alone**, and the sheet prints the check's current Expect words, so rewording a check breaks no such walk (ADR-0049). `walk-tags.py` converts quoted lines where nothing is lost, and `--refresh` re-quotes one whose check was reworded.
- **Finished notes stay out of the way.** Editing a ticket that was finished at the last release warns FROZEN-EDIT. A content rule no longer judges a note finished before the rule arrived, and `--changed` shows only findings about changed files. `archive-notes.py` moves released, finished tickets to `docs/archive/`, and `.ignore` keeps search out of it. `snapshot-query.py --search` and `--links-to` list live notes first and fold finished ones into a count.
- **New rules to follow.** WRITING.md rules 11 and 12: a note says what is true now, and links a rule rather than restating it. LIFECYCLE: search with the Grep tool or `rg`, not `grep -r`.
- **One-off tools** for a repo's owner to run: `archive-notes.py` (1,063 notes in your-trainer), `migrate-ledger-fields.py` (236 of your-trainer's 654 LEDGER-FIELD notes cleared, the rest thinned), `walk-tags.py` (232 of 956 quoted lines convertible in your-trainer), `session-cost.py` (the measurement).

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: updated (TASK-0168 to TASK-0183, all done)
- issues: updated (ISS-0087 to ISS-0102, all fixed)
- tests: new (TST-0026 to TST-0039)
- workflows: not-applicable
- decisions: new (ADR-0049, amending ADR-0045)
- risks: not-applicable (no new dependency: libyaml is optional and the old parser is the fallback; no new env var beyond PROJECT_OS_NO_CACHE, which only turns the cache off)
- changes: new (this note)
- snapshot: updated (`derive_lists` on; the focus cleared)

## Follow-ups

- Two PHASE-0009 exit criteria stay open: whether VERIFY-ACCEPTANCE on tasks of an unreleased version counts as a finding about finished notes, and the after-measurement of opened notes once sessions run with the new tools.
- The fleet takes the tools by sync; your-trainer and the cockpit decide when to turn on `derive_lists`, archive, and run the ledger migration. The cockpit's bundled `walk-sheet.py` needs refreshing for tag-only lines to show there.
- Most of the fleet's test harnesses still count an empty assertion result as a pass (their `check()` does `[[ "$2" -ne 0 ]]`); the ones added in this phase guard against it.
