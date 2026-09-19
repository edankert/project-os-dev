---
type: "[[task]]"
id: TASK-0143
aliases: ["TASK-0143"]
title: "The template fixes the cleanup found: a broken snapshot fails, regression checks split, PHASES.md drops its table, Cursor gets the writing rules"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["[[ISS-0070-A-Snapshot-That-Does-Not-Parse-Still-Passes-Validation]]", "[[ISS-0069-A-Regression-Check-A-Change-Overlaps-Cannot-Be-Reopened]]", "[[ISS-0072-PHASES-Md-Repeats-Every-Phase-Status-And-Drifts-From-The-Phase-Notes]]", "project-os-cockpit ISS-0273"]
parent: "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[TASK-0142-A-Merge-File-Nobody-Edited-Takes-The-Template]]"]
tests: []
---

# The template fixes the cleanup found

## Definition of Done
- [x] A `SNAPSHOT.yaml` that does not parse is a `SNAP-PARSE` error, and `sync-snapshot.py` refuses it and exits 1. `test-snapshot-parse.sh` fails without the fix. ([[ISS-0070-A-Snapshot-That-Does-Not-Parse-Still-Passes-Validation|ISS-0070]])
- [x] `TESTING.md` says to split a regression check that also states current behaviour when a change overlaps it. ([[ISS-0069-A-Regression-Check-A-Change-Overlaps-Cannot-Be-Reopened|ISS-0069]])
- [x] The template's `PHASES.md` says a phase's status lives only in its note, and ships no example table. The table in project-os-dev is removed. project-os-bench and articles keep theirs, which have no status column. ([[ISS-0072-PHASES-Md-Repeats-Every-Phase-Status-And-Drifts-From-The-Phase-Notes|ISS-0072]])
- [x] Cursor gets a `writing.mdc` rule generated from `WRITING.md` (project-os-cockpit ISS-0273).
- [x] Synced to the fleet with TASK-0142, in one sync.

## Not in this task
[[ISS-0053-A-Note-With-Unparseable-Frontmatter-Passes-Silently|ISS-0053]] stays open. The half about frontmatter that does not parse was fixed on 2026-09-18 (NOTE-FRONTMATTER). What is left, warning on a misspelled key such as `elated:`, needs a list of allowed keys per note type, which does not exist yet.

## Done, 2026-09-19
Template `01031af`, synced to all twelve fleet repos in one sync. `test-snapshot-parse.sh` fails on the old code (2 of 8 assertions) and passes on the new; the template's full CI test set passes. project-os-bench and articles keep their phase tables, which have no status column (see ISS-0072).
