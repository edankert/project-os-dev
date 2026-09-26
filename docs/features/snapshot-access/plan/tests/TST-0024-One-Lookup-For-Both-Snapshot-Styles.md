---
type: "[[test]]"
id: TST-0024
aliases: ["TST-0024"]
title: "One lookup answers the same way whatever the snapshot's YAML style, and falls back to the note"
status: active
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["[[TASK-0081]]"]
scope: feature
level: unit
entrypoint: "../project-os/tools/scripts/test-snapshot-query.sh"
command: "bash ../project-os/tools/scripts/test-snapshot-query.sh"
features: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]"]
tasks: ["[[TASK-0081]]"]
artifacts: []
evidence: []
adequacy: "2026-09-25, template working tree, 12 assertions. Five mutations in a full copy of the template: Q1 block lists not read, 2 failures; Q2 no note fallback, 2; Q3 inline maps not read, 3; Q4 a missing id exits 0, 1; Q5 --in-flight ignores status, 1. Pristine 12 of 12. Round 2, after FEAT-0021's review, 22 assertions: C1 a change's slug dropped from item keys, 4 failures; C2 an ambiguous date guessed, 1; C3 a list at its key's own indent ignored, 1; C4 quotes ignored when splitting a list, 1; C5 ids with a filter allowed, 1; C6 the query named where it does not exist, 1. Pristine 22 of 22."
related: ["[[TST-0007]]"]
---

# One lookup answers the same way whatever the snapshot's YAML style, and falls back to the note

## Purpose

`tools/scripts/snapshot-query.py` exists because grep answers differently by the snapshot's style: an inline item's line holds its status, a block item's does not. The harness builds the same items in both styles and checks the answers are identical.

## Procedure

`bash tools/scripts/test-snapshot-query.sh` in `~/Dev/repos/project-os`. Cross-repo, like [[TST-0007]].

1. One item: the same line from a block snapshot and an inline one; the same `--json`, block lists included; `version: 1`.
2. Filters: `--status`, `--collection` with `--status`, and `--in-flight` (doing, not backlog).
3. An id the snapshot does not carry is answered from its note, marked as such; an unknown id exits 1 and says where it looked; no id and no filter is a usage error.
4. The session-start orientation names the query only where the script exists.
5. Change notes: found by their full id in both styles, including a date with a letter; a date two changes share is ambiguous, one a single change has is answered; `--collection changes` lists them.
6. Lists at their key's own indent, a quoted comma inside a list, and an empty value; ids with a filter are a usage error.

## Expected results

- Exit 0: 22 of 22, 2026-09-25, after the review round.
